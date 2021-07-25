from src.models.models import Match, GameMap

import os
import sys
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Any
from peewee import Model, Metadata, SqliteDatabase, FixedCharField, CharField, DateTimeField, IntegerField
from playhouse.shortcuts import model_to_dict

import logging

from src.api.api import ValorantAPI, ValorantConstants
from src.utils import get_executable_relative_path


ZoneStats = Dict[str, Dict[str, Any]]
ZoneKillPositions = List[Dict[str, Any]]
MapKillPositions = Dict[str, ZoneKillPositions]

ZoneStatsTemplate = {'k': 0, 'd': 0, 'presence': 0.0}
KillPositionsTemplate = []


class ApiService:

    QueueTypes = ('competitive', 'unrated', 'custom')

    def __init__(self, region):
        self.api = ValorantAPI(region=region)
        self.puuid: Optional[str] = None
        self.is_authed: bool = False

    @staticmethod
    def get_regions() -> Tuple[str]:
        return ValorantAPI.Regions

    def set_region(self, region: str):
        self.api.set_region(region)

    def try_auth(self) -> bool:
        self.puuid, _ = self.api.get_auth(force=True, cache_headers=True)
        if self.puuid is not None:
            self.is_authed = True
            return True
        return False

    # def get_maps_info(self):
    #     self.maps = {}
    #     maps_info = self.api.get_maps()
    #     for map_info in maps_info:
    #         self.maps[map_info['mapId']] = map_info

    def needs_auth(func):
        def wrapper(self, *args, **kwargs):
            if not self.is_authed:
                raise RuntimeWarning('Currently not authorized!')
            return func(self, *args, **kwargs)
        return wrapper

    @needs_auth
    def get_full_username(self, puuid: str) -> Optional[str]:
        names = self.api.get_names_from_puuids(puuid)
        return names[0] if names else None

    @needs_auth
    def get_all_match_history(self, puuid: str, queue: str):
        return self.api.get_all_match_history(puuid, queue=queue)

    @needs_auth
    def get_match_info(self, match_id: str) -> Dict:
        return self.api.get_match_info(match_id)


db = SqliteDatabase(None, pragmas=(('cache_size', -1024 * 64), ('journal_mode', 'wal')))


class ThreadSafeDatabaseMetadata(Metadata):
    def __init__(self, *args, **kwargs):
        # database attribute is stored in a thread-local.
        self._local = threading.local()
        super(ThreadSafeDatabaseMetadata, self).__init__(*args, **kwargs)

    def _get_db(self):
        return getattr(self._local, 'database', self._database)

    def _set_db(self, db):
        self._local.database = self._database = db
    database = property(_get_db, _set_db)


class BaseModel(Model):
    class Meta:
        # Instruct peewee to use our thread-safe metadata implementation.
        model_metadata_class = ThreadSafeDatabaseMetadata


class MatchModel(BaseModel):
    match_id = FixedCharField(max_length=36, unique=True)
    puuid = FixedCharField(max_length=36)
    my_team = FixedCharField(max_length=4)
    my_match_score = IntegerField()
    opponent_match_score = IntegerField()
    match_date = DateTimeField()
    my_kills = IntegerField()
    my_deaths = IntegerField()
    my_assists = IntegerField()
    my_score = IntegerField()
    raw_json = CharField()
    queue = CharField()

    class Meta:
        database = db


class MatchService:

    def __init__(self, api_service: ApiService):
        self.api_service: ApiService = api_service

        logging.debug(f'Current working directory: {os.getcwd()}')
        logging.debug(f'Executable directory: {sys.executable}')
        db.init(get_executable_relative_path('matches.db'))
        db.connect()
        db.create_tables([MatchModel])

        try:
            with open(get_executable_relative_path('storage.json'), 'r') as f:
                self.ignored_match_ids: Dict = json.loads(f.read())
        except Exception as e:
            logging.error(f'Could not load storage.json: {str(e)}')
            self.ignored_match_ids = {}

    def _opposing_team(self, my_team: str) -> str:
        if my_team == ValorantConstants.Team.Blue.value:
            return ValorantConstants.Team.Red.value
        return ValorantConstants.Team.Blue.value

    def _get_queue(self, pfid: str, queue_id: str) -> str:
        if pfid == 'Matchmaking':
            return queue_id
        elif pfid == 'CustomGame':
            return 'custom'

    def _get_all_stored_match_ids(self, puuid: str, queue: Optional[str] = None):
        if queue is None:
            query = MatchModel.select(MatchModel.match_id) \
                .where(MatchModel.puuid == puuid) \
                .order_by(MatchModel.match_date.desc())
        else:
            query = MatchModel.select(MatchModel.match_id) \
                .where(MatchModel.puuid == puuid, MatchModel.queue == queue) \
                .order_by(MatchModel.match_date.desc())

        hashmap = {}
        for match in query:
            hashmap[match.match_id] = True
        return hashmap

    def _store_match(self, match_info: Dict, puuid: str) -> Optional[dict]:
        try:
            player_info = next(player for player in match_info['players'] if player['subject'] == puuid)
            my_team: str = player_info['teamId']
            opponent_team: str = self._opposing_team(my_team)
            my_match_score: int = -1
            opponent_match_score: int = -1
            for team_stats in match_info['teams']:
                if team_stats['teamId'] == my_team:
                    my_match_score = team_stats['roundsWon']
                elif team_stats['teamId'] == opponent_team:
                    opponent_match_score = team_stats['roundsWon']
            posix_time: int = match_info['matchInfo']['gameStartMillis']
            match_date: datetime = datetime.fromtimestamp(posix_time / 1000, tz=timezone.utc)
            my_kills: int = player_info['stats']['kills']
            my_deaths: int = player_info['stats']['deaths']
            my_assists: int = player_info['stats']['assists']
            my_score: int = player_info['stats']['score']
            queue: str = self._get_queue(match_info['matchInfo']['provisioningFlowID'],
                                         match_info['matchInfo']['queueID'])

            logging.debug(f'({my_match_score} - {opponent_match_score}), {my_kills}/{my_deaths}/{my_assists}')

            model = MatchModel.create(match_id=match_info['matchInfo']['matchId'], puuid=puuid, my_team=my_team,
                                      my_match_score=my_match_score, opponent_match_score=opponent_match_score,
                                      match_date=match_date, my_kills=my_kills, my_deaths=my_deaths,
                                      my_assists=my_assists, my_score=my_score, raw_json=json.dumps(match_info),
                                      queue=queue)
            return model_to_dict(model)
        except KeyError:
            logging.debug('Malformed match info.')
            return None

    def store_new_matches(self, puuid: str):
        all_matches: List[Match] = []
        try:
            stored_match_history: Dict = self._get_all_stored_match_ids(puuid)

            online_match_history = []
            expected_total: int = 0
            for queue in ApiService.QueueTypes:
                result: Dict = self.api_service.get_all_match_history(puuid, queue=queue)
                online_match_history.extend(result['History'])
                expected_total += result['Total']

            logging.debug(
                f'Found {len(online_match_history)} matches (expected {expected_total}) to process...')

            # First fetch the games already in the database
            for match_id in stored_match_history:
                stored_model = MatchModel.select().where(MatchModel.match_id == match_id).get()
                all_matches.append(Match(match_model=model_to_dict(stored_model)))

            # Sort the match IDs by descending date before storing into the database
            online_match_history.sort(key=lambda m: datetime.fromtimestamp(m['GameStartTime'] / 1000, tz=timezone.utc),
                                      reverse=True)

            # Then fetch, store, and append the new matches
            for match in online_match_history:
                match_id = match['MatchID']
                if match_id not in stored_match_history and match_id not in self.ignored_match_ids:
                    logging.debug(f'Match with ID {match_id} not found, storing...')
                    match_info = self.api_service.get_match_info(match_id)
                    # Only add 5v5s, no other custom gamemode
                    if match_info['matchInfo']['gameMode'] == '/Game/GameModes/Bomb/BombGameMode.BombGameMode_C':
                        all_matches.append(Match(match_model=self._store_match(match_info, puuid)))
                    else:
                        self.ignored_match_ids[match_id] = True
            all_matches.sort(key=lambda m: m.date, reverse=True)
        except RuntimeWarning:  # not authenticated, use local matches
            query = MatchModel.select().order_by(MatchModel.match_date.desc())
            for match in query:
                all_matches.append(Match(match_model=model_to_dict(match)))
        return all_matches

    def _create_zone_dict(self, game_map: GameMap, template: Any) -> Dict:
        stats: Dict = {}
        for zone_name in game_map.get_zones():
            stats[zone_name] = template.copy()
        return stats

    def _get_kill_info(self, kill_event: Dict) -> Tuple[str, Dict, str, Optional[Dict]]:
        victim = kill_event.get('victim', None)
        killer = kill_event.get('killer', None)

        victim_pos = kill_event['victimLocation']
        for player_pos in kill_event['playerLocations']:
            if player_pos['subject'] == killer:
                killer_pos = player_pos['location']
                break
        else:
            killer_pos = None
        return victim, victim_pos, killer, killer_pos

    def analyze_all(self, matches: List[Match], game_map: GameMap, puuid: str, side: str) \
            -> Tuple[ZoneStats, MapKillPositions, int]:
        total_stats: ZoneStats = self._create_zone_dict(game_map, template=ZoneStatsTemplate)
        all_kill_positions: MapKillPositions = self._create_zone_dict(game_map, template=KillPositionsTemplate)
        events_per_zone: Dict[str, int] = {}
        total_events: int = 0
        matches_used: int = 0
        for match in matches:
            if match.match_info['matchInfo']['mapId'] != game_map.map_id:
                # print('Map does not match!')
                continue
            # print(f'{match.my_match_score} - {match.opponent_match_score}')
            match_stats, kill_positions = self.analyze(match, game_map, puuid, side)
            for zone_name, zone_stats in match_stats.items():
                k, d = zone_stats['k'], zone_stats['d']
                total_stats[zone_name]['k'] += k
                total_stats[zone_name]['d'] += d

                all_kill_positions[zone_name].extend(kill_positions[zone_name])

                if zone_name not in events_per_zone:
                    events_per_zone[zone_name] = 0
                events_per_zone[zone_name] += k + d
                total_events += k + d
            matches_used += 1
        for zone_name, events_in_zone in events_per_zone.items():
            total_stats[zone_name]['presence'] = events_in_zone / total_events if total_events != 0 else 0.0
        return total_stats, all_kill_positions, matches_used

    def analyze(self, match: Match, game_map: GameMap, puuid: str, side: str) \
            -> Tuple[ZoneStats, MapKillPositions]:
        stats: ZoneStats = self._create_zone_dict(game_map, template=ZoneStatsTemplate)
        kill_positions: MapKillPositions = self._create_zone_dict(game_map, template=KillPositionsTemplate)

        player_team: str = match.get_player_team()

        for kill_event in match.get_kills():
            event_pos: Optional[Dict[str, int]] = None
            positional_info: Optional[Dict[str, Any]] = None
            stat_key: Optional[str] = None

            round_id: int = kill_event.get('round', -1)
            if round_id == -1:
                continue
            victim, victim_pos, killer, killer_pos = self._get_kill_info(kill_event)
            if victim == puuid:  # Got killed here
                event_pos = victim_pos
                stat_key = 'd'
                positional_info = {'role': 'victim', 'killer_pos': killer_pos, 'victim_pos': victim_pos}
            elif killer == puuid:  # Killed someone here
                event_pos = killer_pos
                stat_key = 'k'
                positional_info = {'role': 'killer', 'killer_pos': killer_pos, 'victim_pos': victim_pos}

            # Event either doesn't have to do with this player or killer could not be located
            if event_pos is None:
                continue
            if side == 'attacker':
                # Player starts as attacker, but this event occurred after 12 rounds (aka defender side)
                if player_team == ValorantConstants.Team.Red.value and round_id >= 12:
                    continue
                # Player starts as defender, but this event occurred before 12 rounds (aka attacker side)
                elif player_team == ValorantConstants.Team.Blue.value and round_id < 12:
                    continue
            elif side == 'defender':
                # Player starts as attacker, but this event occurred before 12 rounds (aka defender side)
                if player_team == ValorantConstants.Team.Red.value and round_id < 12:
                    continue
                # Player starts as defender, but this event occurred after 12 rounds (aka attacker side)
                elif player_team == ValorantConstants.Team.Blue.value and round_id >= 12:
                    continue

            zone = game_map.get_zone_from_game_coords(event_pos['x'], event_pos['y'])
            if zone is None:
                # print('Could not find zone!')
                continue
            stats[zone.name][stat_key] += 1
            kill_positions[zone.name].append(positional_info)
        return stats, kill_positions

    def on_close(self):
        db.close()
        with open(get_executable_relative_path('storage.json'), 'w') as f:
            f.write(json.dumps(self.ignored_match_ids))


class MapService:

    def __init__(self):
        self.game_maps: Dict[str, GameMap] = {}

    def load_maps(self):
        metadata_dir = Path('resources/maps').glob('*.json')
        for metadata_file in metadata_dir:
            with open(metadata_file, 'r') as f:
                metadata: Dict = json.loads(f.read())
                self.game_maps[metadata['mapId']] = GameMap(metadata)

    def get_map_names(self) -> Dict[str, str]:
        return {game_map.display_name: map_id for (map_id, game_map) in self.game_maps.items()}

    def get_maps(self) -> Dict[str, GameMap]:
        return self.game_maps

    def get_map(self, map_id: str) -> Optional[GameMap]:
        return self.game_maps.get(map_id, None)


class AnalyticsService:

    def __init__(self, match_service: MatchService, map_service: MapService):
        super().__init__()

        self.match_service: MatchService = match_service
        self.map_service: MapService = map_service

        self.analysis_status_mutex: threading.Lock = threading.Lock()
        self.analysis_status: bool = False

        self.stats_mutex: threading.Lock = threading.Lock()
        self.computed_stats: Dict[str, Dict[str, Tuple[Dict, MapKillPositions]]] = {}
        self.computed_analytics: Dict[str, Dict] = {}

    def is_analyzed(self) -> bool:
        with self.analysis_status_mutex:
            return self.analysis_status

    def set_analyzed(self, status: bool):
        with self.analysis_status_mutex:
            self.analysis_status = status

    def get_map_analytics(self, map_id: str) -> Dict:
        with self.stats_mutex:
            return self.computed_analytics[map_id]

    def get_map_side_stats(self, map_id: str, side: str) -> Tuple[Dict, MapKillPositions]:
        with self.stats_mutex:
            return self.computed_stats[map_id][side]

    def analyze_and_store(self, matches: List[Match], puuid: str):
        with self.stats_mutex:
            del self.computed_stats
            self.computed_stats = {}
            for map_id, game_map in self.map_service.get_maps().items():
                self.computed_stats[map_id] = {}

                matches_used: int = 0
                for side in ['attacker', 'defender', 'both']:
                    total_stats, kill_positions, matches_used = self.match_service.analyze_all(
                        matches, game_map, puuid, side)
                    # print(f'Used {matches_used} matches (map={game_map.display_name}) for stats analysis.')

                    view_friendly_stats = {}
                    for zone_name, stats_dict in total_stats.items():
                        k, d = stats_dict['k'], stats_dict['d']
                        if abs(d) < 0.001:
                            kd = round(float(k), 2)
                        else:
                            kd = k / d
                        view_friendly_stats[zone_name] = {
                            'presence': stats_dict['presence'],
                            'kd': kd
                        }
                    self.computed_stats[map_id][side] = view_friendly_stats, kill_positions
                # Map-specific analytics
                self.computed_analytics[map_id] = {
                    'matchesUsed': matches_used
                }
            # pprint(self.computed_stats)
            self.set_analyzed(True)

