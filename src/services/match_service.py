import traceback
import os
import sys
import json
import threading
from pprint import pprint
from datetime import datetime, timezone
from typing import List, Optional, Dict, Tuple, Callable
from peewee import Model, Metadata, SqliteDatabase, FixedCharField, CharField, DateTimeField, IntegerField
from playhouse.shortcuts import model_to_dict
from playhouse.migrate import SqliteMigrator, migrate

from src.api.api import ValorantConstants
from src.utils import FileManager, logger
from src.services.api_service import ApiService
from src.services.map_service import MapService
from src.models.models import Match, GameMap


db = SqliteDatabase(None, pragmas=(('cache_size', -1024 * 64), ('journal_mode', 'wal')))


def execute_migrations():
    migrator = SqliteMigrator(db)

    columns = {}
    for column in db.get_columns('matchmodel'):
        columns[column.name] = True

    migrations = []

    if 'queue' not in columns:
        logger.debug('Column "queue" does not exist! Migrating...')
        queue_field = CharField(default='competitive')
        migrations.append(migrator.add_column('matchmodel', 'queue', queue_field))

    if 'map_id' not in columns:
        logger.debug('Column "map_id" does not exist! Migrating...')
        map_id_field = CharField(default='')
        migrations.append(migrator.add_column('matchmodel', 'map_id', map_id_field))

    if 'stats' not in columns:
        logger.debug('Column "stats" does not exist! Migrating...')
        stats_field = CharField(default=None, null=True)
        migrations.append(migrator.add_column('matchmodel', 'stats', stats_field))

    if migrations:
        logger.debug(f'Performing {len(migrations)} migrations...')
        migrate(*migrations)
    else:
        logger.debug(f'No migrations needed.')


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
    stats = CharField(default=None, null=True)
    map_id = CharField()

    class Meta:
        database = db


class MatchService:

    StatsVersion: int = 1

    def __init__(self, api_service: ApiService, map_service: MapService):
        self.api_service: ApiService = api_service
        self.map_service: MapService = map_service

        logger.debug(f'Current working directory: {os.getcwd()}')
        logger.debug(f'Executable directory: {sys.executable}')
        logger.debug(f'Storage directory: {FileManager.get_storage_path("")}')
        db.init(FileManager.get_storage_path('matches.db'))
        db.connect()
        db.create_tables([MatchModel])
        execute_migrations()

        try:
            with open(FileManager.get_storage_path('storage.json'), 'r') as f:
                self.ignored_match_ids: Dict = json.loads(f.read())
        except Exception as e:
            logger.error(f'Could not load storage.json: {str(e)}')
            logger.error(traceback.format_exc())
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
        hashmap = {}
        if ValorantConstants.DebugMatchUUID:
            hashmap[ValorantConstants.DebugMatchUUID] = True
            return hashmap
        if queue is None:
            query = MatchModel.select(MatchModel.match_id) \
                .where(MatchModel.puuid == puuid) \
                .order_by(MatchModel.match_date.desc())
        else:
            query = MatchModel.select(MatchModel.match_id) \
                .where(MatchModel.puuid == puuid, MatchModel.queue == queue) \
                .order_by(MatchModel.match_date.desc())

        
        for match in query:
            hashmap[match.match_id] = True
        return hashmap

    def _store_match(self, match_info: Dict, puuid: str) -> Optional[MatchModel]:
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
            map_id: str = match_info['matchInfo']['mapId']

            logger.debug(f'({my_match_score} - {opponent_match_score}), {my_kills}/{my_deaths}/{my_assists}')

            model = MatchModel.create(match_id=match_info['matchInfo']['matchId'], puuid=puuid, my_team=my_team,
                                      my_match_score=my_match_score, opponent_match_score=opponent_match_score,
                                      match_date=match_date, my_kills=my_kills, my_deaths=my_deaths,
                                      my_assists=my_assists, my_score=my_score, raw_json=json.dumps(match_info),
                                      queue=queue, stats=None, map_id=map_id)
            return model
        except KeyError as e:
            logger.error(f'Malformed match info: {str(e)}')
            logger.error(traceback.format_exc())
            return None

    def process_matches(self, puuid: str, progress_callback: Optional[Callable[[float], None]] = None):
        """
        Fetch new matches, load old matches, and analyze the games.
        :param puuid: the player to fetch the matches for
        :param progress_callback: optional callback with progress values (0 to 1)
        :return:
        """
        all_matches: List[Match] = []
        try:
            # Get a hashmap of all the stored match IDs
            stored_match_history: Dict = self._get_all_stored_match_ids(puuid)

            # Get a list of matches from VALORANT
            online_match_history = []
            expected_total: int = 0
            if not ValorantConstants.DebugMatchUUID:
                for queue in ApiService.QueueTypes:
                    result: Dict = self.api_service.get_all_match_history(puuid, queue=queue)
                    online_match_history.extend(result['History'])
                    expected_total += result['Total']

                logger.debug(
                    f'Found {len(online_match_history)} matches (expected {expected_total}) to process...')

            total_matches: int = len(stored_match_history) + len(online_match_history)
            matches_processed: int = 0

            if total_matches == 0:
                progress_callback(1.0)
                return []

            # First fetch the matches already in the database
            for match_id in stored_match_history:
                stored_model: MatchModel = MatchModel.select().where(MatchModel.match_id == match_id).get()

                match = Match(match_model=model_to_dict(stored_model))
                all_matches.append(match)

                modified: bool = False
                if match.map_id is None or match.map_id == '':
                    logger.debug(f'No map ID found for match {match_id}!')
                    stored_model.map_id = match.map_id = match.get_map_id()
                    logger.debug(f"Set map_id to {match.map_id}")
                    modified = True
                # Stats have not been calculated for this match or stats schema has been updated
                if ValorantConstants.DebugMatchUUID or match.stats is None or match.stats.get('version', 0) != MatchService.StatsVersion:
                    logger.debug(f'Going to update stats for match {match_id} on map: {match.map_id}!')
                    match.stats = self.analyze(match, self.map_service.get_map(match.map_id), puuid)
                    stored_model.stats = json.dumps(match.stats)
                    modified = True
                if modified:
                    stored_model.save()
                match.unload_match_info()

                matches_processed += 1
                progress_callback(matches_processed / total_matches)

            # Sort the match IDs by descending date before storing into the database
            online_match_history.sort(key=lambda m: datetime.fromtimestamp(m['GameStartTime'] / 1000, tz=timezone.utc),
                                      reverse=True)

            # Then fetch, store, and append the new matches
            for match_entry in online_match_history:
                match_id = match_entry['MatchID']
                if match_id not in stored_match_history and match_id not in self.ignored_match_ids:

                    logger.debug(f'Match with ID {match_id} not found, storing...')
                    match_info = self.api_service.get_match_info(match_id)
                    # Only add 5v5s, no other custom gamemode
                    if match_info['matchInfo']['gameMode'] == '/Game/GameModes/Bomb/BombGameMode.BombGameMode_C':
                        stored_model: MatchModel = self._store_match(match_info, puuid)
                        match = Match(match_model=model_to_dict(stored_model))

                        # Now compute the stats and update the stored model
                        match.stats = self.analyze(match, self.map_service.get_map(match.map_id), puuid)
                        match.unload_match_info()
                        stored_model.stats = json.dumps(match.stats)
                        stored_model.save()

                        all_matches.append(match)
                    else:
                        self.ignored_match_ids[match_id] = True

                matches_processed += 1
                progress_callback(matches_processed / total_matches)

            all_matches.sort(key=lambda m: m.date, reverse=True)
        except Exception as e:  # not authenticated, use local matches
            logger.error(f'Exception during match processing: {str(e)}')
            logger.error(traceback.format_exc())
            # query = MatchModel.select().order_by(MatchModel.match_date.desc())
            # for match in query:
            #     all_matches.append(Match(match_model=model_to_dict(match)))
        return all_matches

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

    def analyze(self, match: Match, game_map: GameMap, puuid: str):
        # Initialize analysis result dictionary
        result: Dict = {
            'version': MatchService.StatsVersion,
            'attacker': {
                'preplant': {
                    'zones': {}
                },
                'postplant': {
                    'zones': {}
                }
            },
            'defender': {
                'preplant': {
                    'zones': {}
                },
                'postplant': {
                    'zones': {}
                }
            }
        }
        for zone_name in game_map.get_zones():
            for side in ('attacker', 'defender'):
                for plant_time in ('preplant', 'postplant'):
                    result[side][plant_time]['zones'][zone_name] = {
                        'k': 0, 'd': 0, 'events': []
                    }

        player_team: str = match.get_player_team()

        plant_times: List[int] = [game_round.get('plantRoundTime', 1000000) for game_round in match.get_rounds()]
        
        for kill_event in match.get_kills():
            event_pos: Optional[Dict[str, int]] = None
            role_value: Optional[str] = None
            stat_key: Optional[str] = None

            round_id: int = kill_event.get('round', -1)
            if round_id == -1:
                continue
            victim, victim_pos, killer, killer_pos = self._get_kill_info(kill_event)
            if victim == puuid:  # Got killed here
                role_value = 'v'
                event_pos = victim_pos
                stat_key = 'd'
            elif killer == puuid:  # Killed someone here
                role_value = 'k'
                event_pos = killer_pos
                stat_key = 'k'

            # Event either doesn't have to do with this player or killer could not be located
            if event_pos is None or role_value is None or stat_key is None:
                continue

            # Which side was the player on?
            event_side: Optional[str] = None
            if player_team == ValorantConstants.Team.Red.value:
                if round_id < 12:
                    event_side = 'attacker'
                else:
                    event_side = 'defender'
            elif player_team == ValorantConstants.Team.Blue.value:
                if round_id < 12:
                    event_side = 'defender'
                else:
                    event_side = 'attacker'
            # Invalid team value
            if event_side is None:
                logger.warning(f'Processed kill event with invalid team value of {player_team}')
                continue

            round_time: int = kill_event.get('roundTime', -1)
            if round_time == -1:
                logger.warning(f'Processed kill event with invalid round time')
                continue
            event_plant_time: str = 'preplant' if round_time < plant_times[round_id] else 'postplant'

            zone = game_map.get_zone_from_game_coords(event_pos['x'], event_pos['y'])
            if zone is None:
                continue

            result[event_side][event_plant_time]['zones'][zone.name][stat_key] += 1
            if killer_pos is not None and victim_pos is not None:
                result[event_side][event_plant_time]['zones'][zone.name]['events'].append({
                    'r': role_value, 'k': [killer_pos['x'], killer_pos['y']], 'v': [victim_pos['x'], victim_pos['y']]
                })
        return result

    def on_close(self):
        db.close()
        with open(FileManager.get_storage_path('storage.json'), 'w') as f:
            f.write(json.dumps(self.ignored_match_ids))
