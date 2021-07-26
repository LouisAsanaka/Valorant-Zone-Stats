from src.api.api import ValorantAPI
from typing import Optional, Tuple, Dict


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
        self.region = self.api.set_region(region.upper())
        self.shard = self.api.set_shard(region.upper())
    

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
