from PySide2.QtCore import QObject, Signal

from datetime import datetime
import json
import math
from typing import Iterator, Tuple, Dict, List, Optional, Union

from shapely.geometry import Point, Polygon

from src.utils import logger


class MapZone:

    def __init__(self, name: str, polygon: Polygon):
        self.name = name
        self.polygon = polygon

    def contains(self, point: Point) -> bool:
        return self.polygon.contains(point)

    def get_points(self) -> Iterator[Tuple[float, float]]:
        return zip(*self.polygon.exterior.coords.xy)

    def top_left(self) -> Tuple[float, float]:
        # Inspired by https://gis.stackexchange.com/a/216665
        centroid: Point = self.polygon.centroid
        max_score = 0
        top_left_point = None
        for point in self.get_points():
            dx, dy = centroid.x - point[0], centroid.y - point[1]
            angle = math.degrees(math.atan2(dy, dx))
            weighed_distance = math.hypot(dx, dy) * 0.5
            score = weighed_distance - weighed_distance * abs(angle + -45) / 180
            if score > max_score:
                top_left_point = point
                max_score = score
        return top_left_point

    def __str__(self):
        return self.name


class GameMap:

    def __init__(self, map_metadata: Dict):
        self.map_metadata: Dict = map_metadata

        self.uuid: str = map_metadata['uuid']
        self.map_id: str = map_metadata['mapId']
        self.display_name: str = map_metadata['displayName']
        self.image_path: str = map_metadata['mapImage']
        self.background_image_path: str = map_metadata['backgroundImage']
        self.scale_x, self.scale_y = map_metadata['multiplier']['x'], map_metadata['multiplier']['y']
        self.offset_x, self.offset_y = map_metadata['offset']['x'], map_metadata['offset']['y']
        self.zones: Dict[str, MapZone] = {}
        for zone in self.map_metadata['zones']:
            name: str = zone['name']
            polygon = Polygon(map(lambda p: (p['x'], 1-p['y']), zone['points'])) #the files are stored with the zone  y's at 1-y so we need to reverse it back
            self.zones[name] = MapZone(name, polygon)

    def get_zones(self) -> Dict[str, MapZone]:
        return self.zones

    def get_zone_from_game_coords(self, game_x: int, game_y: int) -> Optional[MapZone]:
        return self.get_point_zone(Point(*self.normalize_point(game_x, game_y)))

    def get_point_zone(self, point: Point) -> Optional[MapZone]:
        for zone in self.zones.values():
            if zone.contains(point):
                return zone
        return None

    def normalize_point(self, game_x: int, game_y: int) -> Tuple[float, float]:
        # Yes swapping the game_x and game_y here, this is correct
        ret = (game_y * self.scale_x + self.offset_x, game_x * self.scale_y + self.offset_y)
        return ret


class Match:

    def __init__(self, match_model: Dict):
        self.match_id: str = match_model['match_id']
        self.puuid: str = match_model['puuid']
        self.my_team: str = match_model['my_team']
        self.my_match_score: int = match_model['my_match_score']
        self.opponent_match_score: int = match_model['opponent_match_score']
        self.date: datetime = datetime.fromisoformat(match_model['match_date']) \
            if isinstance(match_model['match_date'], str) else match_model['match_date']
        self.my_kills: int = match_model['my_kills']
        self.my_deaths: int = match_model['my_deaths']
        self.my_assists: int = match_model['my_assists']
        self.my_score: int = match_model['my_score']
        self.match_info: Optional[Union[str, Dict]] = match_model['raw_json']
        self.queue: str = match_model['queue']
        self.stats: Optional[Dict] = None if match_model['stats'] is None else json.loads(match_model['stats'])
        self.map_id: str = match_model['map_id']

    # @staticmethod
    # def load_match_from_file(file_path: Union[str, Path]):
    #     with open(file_path, 'r') as f:
    #         return Match(json.load(f))

    def get_match_id(self) -> str:
        return self.match_id

    def get_start_time(self) -> datetime:
        return self.date

    def get_player_team(self) -> str:
        return self.my_team

    def get_rounds(self) -> Optional[List[Dict]]:
        if isinstance(self.match_info, str):
            self.match_info = json.loads(self.match_info)
        return self.match_info['roundResults']

    def get_kills(self) -> Optional[List[Dict]]:
        if isinstance(self.match_info, str):
            self.match_info = json.loads(self.match_info)
        return self.match_info['kills']

    def get_map_id(self) -> str:
        if self.map_id == '':
            if isinstance(self.match_info, str):
                self.match_info = json.loads(self.match_info)
            return self.match_info['matchInfo']['mapId']
        return self.map_id

    def unload_match_info(self):
        """
        Unload match info to save memory. Cannot be reverted.
        """
        self.match_info = None


class PlayerData(QObject):

    puuid_changed = Signal(str)
    username_changed = Signal(str)
    matches_changed = Signal()

    def __init__(self):
        super().__init__()

        self.puuid: Optional[str] = None
        self.full_username: Optional[str] = None
        self.available_matches: List[Match] = []

    def set_puuid(self, puuid: str):
        self.puuid = puuid
        self.puuid_changed.emit(puuid)

    def set_full_username(self, username: str):
        self.full_username = username
        self.username_changed.emit(username)

    def set_available_matches(self, matches: List[Match]):
        del self.available_matches
        logger.debug(f'Loading {len(matches)} matches into the UI...')
        self.available_matches = matches
        self.matches_changed.emit()

    def unload_info_from_matches(self):
        """
        Save memory by unloading unnecessary match information.
        """
        for match in self.available_matches:
            match.unload_match_info()

