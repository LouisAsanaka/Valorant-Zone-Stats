import threading
from typing import List, Dict, Tuple

from src.models.models import Match
from src.services.map_service import MapService
from src.services.api_service import ApiService


class AnalyticsService:

    def __init__(self, map_service: MapService):
        self.map_service: MapService = map_service

        self.stats_mutex: threading.Lock = threading.Lock()
        self.statistics: Dict[str, Dict] = {}

    @staticmethod
    def _safe_divide(a: int, b: int, default: float = 0.0) -> float:
        return default if abs(b) < 0.001 else a / b

    @staticmethod
    def _get_sides(target_side: str) -> List[str]:
        if target_side == 'both':
            return ['attacker', 'defender']
        else:
            return [target_side]

    @staticmethod
    def _get_queues(target_queue: str) -> List[str]:
        if target_queue == 'all':
            return ApiService.QueueTypes
        else:
            return [target_queue]

    def get_map_analytics(self, map_id: str):
        with self.stats_mutex:
            result = {}
            for queue in ApiService.QueueTypes:
                result[queue] = {
                    'matches_used': self.statistics[map_id][queue]['matches']
                }
            return result

    def get_stats(self, map_id: str, target_side: str, target_queue: str):
        with self.stats_mutex:
            result = {}

            for zone in self.map_service.get_map(map_id).get_zones():
                result[zone] = {
                    'k': 0, 'd': 0, 'presence': 0, 'events': []
                }

            total_events: int = 0
            for side in self._get_sides(target_side):
                for queue in self._get_queues(target_queue):
                    total_events += self.statistics[map_id][queue][side]['total_events']
                    for zone_name, zone_stats in self.statistics[map_id][queue][side]['zones'].items():
                        result[zone_name]['k'] += zone_stats['k']
                        result[zone_name]['d'] += zone_stats['d']
                        result[zone_name]['presence'] += zone_stats['presence']
                        result[zone_name]['events'].extend(zone_stats['events'])

            for zone in result.keys():
                result[zone] = {
                    'kd': self._safe_divide(result[zone]['k'], result[zone]['d'], default=result[zone]['k']),
                    'presence': self._safe_divide(result[zone]['presence'], total_events, default=0.0),
                    'events': result[zone]['events']
                }

            # total_events: int = self.statistics[map_id][queue][side]['total_events']
            # for zone_name, zone_stats in self.statistics[map_id][queue][side]['zones'].items():
            #     result[zone_name] = {
            #         'kd': self._safe_divide(zone_stats['k'], zone_stats['d']),
            #         'presence': self._safe_divide(zone_stats['presence'], total_events),
            #         'events': zone_stats['events']
            #     }

            return result

    def aggregate_statistics(self, matches: List[Match]):
        with self.stats_mutex:
            for map_id, game_map in self.map_service.get_maps().items():
                self.statistics[map_id] = {}
                for queue in ApiService.QueueTypes:
                    self.statistics[map_id][queue] = {'matches': 0}
                    for side in ['attacker', 'defender']:
                        self.statistics[map_id][queue][side] = {'zones': {}, 'total_events': 0}
                        for zone_name in game_map.get_zones():
                            self.statistics[map_id][queue][side]['zones'][zone_name] = {
                                'k': 0,
                                'd': 0,
                                'presence': 0.0,
                                'events': []
                            }
            for match in matches:
                self.statistics[match.map_id][match.queue]['matches'] += 1
                # print(self.statistics[match.map_id][match.queue][side]['zones'])
                for side in ['attacker', 'defender']:
                    for zone in self.map_service.get_map(match.map_id).get_zones():
                        zone_stats = match.stats[side]['zones'][zone]
                        ref = self.statistics[match.map_id][match.queue][side]['zones'][zone]
                        ref['k'] += zone_stats['k']
                        ref['d'] += zone_stats['d']

                        events: int = zone_stats['k'] + zone_stats['d']
                        ref['presence'] += events
                        ref['events'].extend(zone_stats['events'])

                        self.statistics[match.map_id][match.queue][side]['total_events'] += events

        # with self.stats_mutex:
        #     del self.computed_stats
        #     self.computed_stats = {}
        #     for map_id, game_map in self.map_service.get_maps().items():
        #         self.computed_stats[map_id] = {}
        #
        #         matches_used: int = 0
        #         for side in ['attacker', 'defender', 'both']:
        #             total_stats, kill_positions, matches_used = self.match_service.analyze_all(
        #                 matches, game_map, puuid, side)
        #             # print(f'Used {matches_used} matches (map={game_map.display_name}) for stats analysis.')
        #
        #             view_friendly_stats = {}
        #             for zone_name, stats_dict in total_stats.items():
        #                 k, d = stats_dict['k'], stats_dict['d']
        #                 if abs(d) < 0.001:
        #                     kd = round(float(k), 2)
        #                 else:
        #                     kd = k / d
        #                 view_friendly_stats[zone_name] = {
        #                     'presence': stats_dict['presence'],
        #                     'kd': kd
        #                 }
        #             self.computed_stats[map_id][side] = view_friendly_stats, kill_positions
        #         # Map-specific analytics
        #         self.computed_analytics[map_id] = {
        #             'matchesUsed': matches_used
        #         }
        #     # pprint(self.computed_stats)
        #     self.set_analyzed(True)