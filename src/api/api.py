import requests as r
from urllib import parse
from pprint import pprint
from requests.cookies import create_cookie
import traceback
import os
import base64
from typing import Optional, Dict, Tuple, Union, List
import urllib3
import json
import yaml
import re
from enum import Enum
from src.utils import logger

urllib3.disable_warnings()


class ValorantConstants:
    
    Maps = {
        'Port': 'Icebox',
        'Duality': 'Bind',
        'Bonsai': 'Split',
        'Ascent': 'Ascent',
        'Triad': 'Haven',
        'Foxtrot': 'Breeze',
        'Range': 'Range'
    }

    GameModes = {
        'unrated': 'Unrated',
        'competitive': 'Competitive',
        'spikerush': 'Spike Rush',
        'deathmatch': 'Deathmatch',
        'ggteam': 'Escalation',
        'newmap': 'Breeze'
    }

    Agents = {
        '5f8d3a7f-467b-97f3-062c-13acf203c006': 'Breach',
        'f94c3b30-42be-e959-889c-5aa313dba261': 'Raze',
        '6f2a04ca-43e0-be17-7f36-b3908627744d': 'Skye',
        '117ed9e3-49f3-6512-3ccf-0cada7e3823b': 'Cypher',
        '320b2a48-4d9b-a075-30f1-1f93a9b638fa': 'Sova',
        '1e58de9c-4950-5125-93e9-a0aee9f98746': 'Killjoy',
        '707eab51-4836-f488-046a-cda6bf494859': 'Viper',
        'eb93336a-449b-9c1b-0a54-a891f7921d69': 'Phoenix',
        '41fb69c1-4189-7b37-f117-bcaf1e96f1bf': 'Astra',
        '9f0d8ba9-4140-b941-57d3-a7ad57c6b417': 'Brimstone',
        '7f94d92c-4234-0a36-9646-3a87eb8b5c89': 'Yoru',
        '569fdd95-4d10-43ab-ca70-79becc718b46': 'Sage',
        'a3bfb853-43b2-7238-a4f1-ad90e9e46bcc': 'Reyna',
        '8e253930-4c05-31dd-1b6c-968525494517': 'Omen',
        'add6443a-41bd-e414-f6ad-e58d267f4e95': 'Jett',
        '601dbbe7-43ce-be57-2a40-4abd24953621': 'KAY/O',
        '': '?'
    }

    Ranks = {
        0: "Unrated",
        1: "Unrated",
        2: "Unused 1",
        3: "Iron 1",
        4: "Iron 2",
        5: "Iron 3",
        6: "Bronze 1",
        7: "Bronze 2",
        8: "Bronze 3",
        9: "Silver 1",
        10: "Silver 2",
        11: "Silver 3",
        12: "Gold 1",
        13: "Gold 2",
        14: "Gold 3",
        15: "Platinum 1",
        16: "Platinum 2",
        17: "Platinum 3",
        18: "Diamond 1",
        19: "Diamond 2",
        20: "Diamond 3",
        21: "Immortal",
        22: "None",
        23: "None",
        24: "Radiant"
    }

    SkinKeys = {
        'skin_chroma': '3ad1b2b2-acdb-4524-852f-954a76ddae0a',
        'skin_info': 'bcef87d6-209b-46c6-8b19-fbe40bd95abc',
        'gun_buddy': 'dd3bf334-87f3-40bd-b043-682a57a8dc3a',
        'skin_level': 'e7c63390-eda7-46e0-bb7a-a6abdacd2433'
    }

    class Team(Enum):
        Red = 'Red'
        Blue = 'Blue'


class ValorantAPI:

    UUID = str
    Cookies = List[Dict]
    Headers = Dict[str, str]

    Regions = ('NA', 'EU', 'AP', 'KR', 'LATAM', 'BR', 'PBE')
    Shard_Overrides = {
        'LATAM': 'NA',
        'BR': 'NA',
    }
    Region_Overrides = {
        'PBE': 'NA',
    }
    CLIENT_PLATFORM = 'ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9'

    REAUTH_URL: str = 'https://auth.riotgames.com/authorize?redirect_uri=https%3A%2F%2Fplayvalorant.com%2Fopt_in&client_id=play-valorant-web-prod&response_type=token%20id_token'
    ENTITLEMENTS_URL: str = 'https://entitlements.auth.riotgames.com/api/token/v1'

    def __init__(self, region: str):
        self.version: Optional[str] = None
        self.lockfile_contents: Optional[Dict[str, str]] = None
        self.cookies_contents: Optional[ValorantAPI.Cookies] = None
        self.region: str = self.get_region(region.upper())
        self.shard: str = self.get_shard(region.upper())
        self.cached_headers: Optional[ValorantAPI.Headers] = None

    def _fill_headers(self, headers: Optional[Headers]):
        if headers is None:
            if self.cached_headers is None:
                raise RuntimeWarning('No auth headers found! Please call get_auth with cache_headers=True.')
            else:
                return self.cached_headers
        return headers

    def set_region_and_shard(self, region: str):
        self.region = self.get_region(region)
        self.shard = self.get_shard(region)

    @staticmethod
    def get_region(region: str) -> Optional[str]:
        region = region.upper()
        if region in ValorantAPI.Regions:
            return ValorantAPI.Region_Overrides.get(region, region)
        return ValorantAPI.Regions[0]

    @staticmethod
    def get_shard(region: str) -> Optional[str]:
        region = region.upper()
        if region in ValorantAPI.Regions:
            return ValorantAPI.Shard_Overrides.get(region, region)
        return ValorantAPI.Regions[0]

    @staticmethod
    def get_region_from_local_log() -> Optional[str]:
        log_file: str = os.path.join(os.getenv('LOCALAPPDATA'), R'VALORANT\Saved\Logs\ShooterGame.log')
        shared_url_regex = re.compile(r'shared\.(.+)\.a\.pvp\.net/v1/config/')
        try:
            with open(log_file) as f:
                for line in f:
                    if result := shared_url_regex.search(line):
                        return result.group(1).upper()
        except Exception as e:
            logger.error(f'Error occurred while reading VALORANT logs for region: {str(e)}')
            logger.error(traceback.format_exc())
        return None

    @staticmethod
    def get_lockfile_path() -> str:
        return os.path.join(os.getenv('LOCALAPPDATA'), R'Riot Games\Riot Client\Config\lockfile')

    def get_lockfile(self, force: bool = False) -> Optional[Dict[str, str]]:
        if self.lockfile_contents is not None and not force:
            return self.lockfile_contents
        try:
            with open(ValorantAPI.get_lockfile_path()) as lockfile:
                data = lockfile.read().split(':')
                keys = ['name', 'PID', 'port', 'password', 'protocol']
                self.lockfile_contents = dict(zip(keys, data))
                return self.lockfile_contents
        except Exception as e:
            logger.error(f'Could not get contents of lockfile: {str(e)}')
            logger.error(traceback.format_exc())
            return None

    @staticmethod
    def get_cookies_path() -> str:
        return os.path.join(os.getenv('LOCALAPPDATA'), R'Riot Games\Riot Client\Data\RiotClientPrivateSettings.yaml')

    def get_cookies(self, force: bool = False) -> Optional[Cookies]:
        if self.cookies_contents is not None and not force:
            return self.cookies_contents
        try:
            with open(ValorantAPI.get_cookies_path()) as cookie_file:
                cookies = yaml.safe_load(cookie_file)['private']['riot-login']['persist']['session']['cookies']
                return cookies
        except Exception as e:
            logger.error(f'Could not get contents of cookie file: {str(e)}')
            logger.error(traceback.format_exc())
            return None

    def _build_header(self, bearer_token: str, entitlement_token: str):
        return {
            'Authorization': f"Bearer {bearer_token}",
            'X-Riot-Entitlements-JWT': entitlement_token,
            'X-Riot-ClientPlatform': ValorantAPI.CLIENT_PLATFORM,
            'X-Riot-ClientVersion': self.get_current_version()
        }

    def _auth_with_cookies(self, force: bool, cache_headers: bool):
        try:
            cookies = self.get_cookies(force=force)
            session = r.Session()

            puuid: Optional[str] = None
            for cookie in cookies:
                if cookie['name'] == 'sub':
                    puuid = cookie['value']
                cookie_obj = create_cookie(cookie['name'], cookie['value'], domain=cookie['domain'],
                                           path=cookie['path'],
                                           secure=cookie['secureOnly'], rest={'HttpOnly': cookie['httpOnly']})
                session.cookies.set_cookie(cookie_obj)

            # Perform a reauth with stored cookies to get the entitlement token
            # Token is hidden in the redirect URL
            # https://github.com/techchrism/valorant-api-docs/blob/trunk/docs/Riot%20Auth/GET%20Cookie%20Reauth.md
            redirect = session.get(ValorantAPI.REAUTH_URL, allow_redirects=False)
            redirect_url: str = redirect.headers['Location']
            res_dict = dict(parse.parse_qsl(parse.urlsplit(redirect_url).fragment))
            if "access_token" not in res_dict:
                raise Exception("No access_token found for cookie re-auth, is valorant launched? Will try fallback option.")
            bearer_token = res_dict["access_token"]

            # Now get the entitlement token using the bearer token
            # https://github.com/techchrism/valorant-api-docs/blob/trunk/docs/Riot%20Auth/POST%20Entitlement.md
            response = session.post(ValorantAPI.ENTITLEMENTS_URL, headers={
                'Authorization': f'Bearer {bearer_token}',
                'Content-Type': 'application/json'
            })
            entitlements = response.json()
            payload = self._build_header(bearer_token=bearer_token,
                                         entitlement_token=entitlements['entitlements_token'])
            if cache_headers:
                self.cached_headers = payload
            return puuid, payload
        except Exception as e:
            logger.error(f'Could not authenticate with cookies: {str(e)}')
            logger.error(traceback.format_exc())
            return None, None

    def _auth_with_lockfile(self, force: bool, cache_headers: bool) -> Optional[Tuple[UUID, Headers]]:
        try:
            lockfile = self.get_lockfile(force=force)
            headers = {
                'Authorization': 'Basic ' + base64.b64encode(('riot:' + lockfile['password']).encode()).decode()
            }

            response = r.get(f"https://127.0.0.1:{lockfile['port']}/entitlements/v1/token",
                             headers=headers, verify=False)
            entitlements = response.json()
            payload = self._build_header(bearer_token=entitlements['accessToken'],
                                         entitlement_token=entitlements['token'])
            if cache_headers:
                self.cached_headers = payload
            return entitlements['subject'], payload
        except Exception as e:
            logger.error(f'Could not authenticate with lockfile: {str(e)}')
            logger.error(traceback.format_exc())
            return None, None

    def get_auth(self, force: bool = False, cache_headers: bool = True) -> Optional[Tuple[UUID, Headers]]:
        # Try the cookies method first, then the lockfile method
        puuid, headers = self._auth_with_cookies(force, cache_headers)
        if puuid is None or headers is None:
            return self._auth_with_lockfile(force, cache_headers)
        return puuid, headers

    def get(self, url: str, params: Optional[Dict] = None, headers: Optional[Headers] = None) -> Dict:
        response = r.get(url, headers=self._fill_headers(headers), params=params)
        return json.loads(response.text)

    def get_pd(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Headers] = None) -> Dict:
        return self.get(f'https://pd.{self.shard}.a.pvp.net{endpoint}', params, headers)

    def get_glz(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Headers] = None) -> Dict:
        return self.get(f'https://glz-{self.region}-1.{self.shard}.a.pvp.net{endpoint}', params, headers)

    def post(self, url: str, data: Optional[Dict] = None, headers: Optional[Headers] = None) -> Dict:
        response = r.post(url, headers=self._fill_headers(headers), data=data)
        return json.loads(response.text)

    def post_pd(self, endpoint: str, data: Optional[Dict] = None, headers: Optional[Headers] = None) -> Dict:
        return self.post(f'https://pd.{self.shard}.a.pvp.net{endpoint}', data, headers)

    def post_glz(self, endpoint: str, data: Optional[Dict] = None, headers: Optional[Headers] = None) -> Dict:
        return self.post(f'https://glz-{self.region}-1.{self.shard}.a.pvp.net{endpoint}', data, headers)

    def put(self, url: str, data: Optional[Union[Dict, str]] = None, headers: Optional[Headers] = None) -> Dict:
        response = r.put(url, headers=self._fill_headers(headers), data=data)
        return json.loads(response.text)

    def put_pd(self, endpoint: str, data: Optional[Union[Dict, str]] = None, headers: Optional[Headers] = None) -> Dict:
        return self.put(f'https://pd.{self.shard}.a.pvp.net{endpoint}', headers=headers, data=data)

    @staticmethod
    def get_valorant_api(endpoint: str) -> Optional[Dict]:
        data = r.get(f'https://valorant-api.com{endpoint}')
        return data.json().get('data', None)

    def get_current_version(self, force: bool = False) -> Optional[str]:
        if self.version is not None and not force:
            return self.version
        data = self.get_valorant_api('/v1/version')
        if data is None:
            return None
        # self.version = f"{data['branch']}-shipping-{data['buildVersion']}-{data['version'].split('.')[3]}"
        self.version = data['riotClientVersion']
        return self.version

    def get_weapons(self) -> Optional[Dict]:
        return self.get_valorant_api('/v1/weapons')

    def get_maps(self) -> Optional[Dict]:
        return self.get_valorant_api('/v1/maps')

    def get_names_from_puuids(self, puuids: Union[List[str], str]):
        if isinstance(puuids, str):
            puuids = [puuids]
        names = self.put_pd('/name-service/v2/players', json.dumps(puuids))
        return list(map(lambda x: f"{x['GameName']}#{x['TagLine']}", names))

    def get_mmr(self, puuid: str):
        return self.get_pd(f'/mmr/v1/players/{puuid}')

    def get_player_max_rank(self, puuid: str) -> Tuple[int, str]:
        mmr_info = self.get_mmr(puuid)
        seasons_info: Dict = mmr_info['QueueSkills']['competitive']['SeasonalInfoBySeasonID']

        max_rank: int = 0
        rank_act: Optional[str] = None

        try:
            for act_id in seasons_info.keys():
                act_rank: int = seasons_info[act_id]['CompetitiveTier']
                if max_rank is None or act_rank > max_rank:
                    max_rank = act_rank
                    rank_act = act_id
        except TypeError:
            pass
        return max_rank, rank_act

    def get_season_by_id(self, season_id: str) -> Tuple[Optional[str], Optional[str]]:
        season_info = self.get_valorant_api(f'/v1/seasons/{season_id}')
        if season_info is None:
            return None, None
        if season_info['parentUuid'] is None:  # Episode only, not act
            return season_info['displayName'], None
        episode_info = self.get_valorant_api(f"/v1/seasons/{season_info['parentUuid']}")
        if episode_info is None:
            return None, season_info['displayName']
        return episode_info['displayName'], season_info['displayName']

    def get_current_party_id(self, puuid: str):
        return self.get_glz(f'/parties/v1/players/{puuid}').get('CurrentPartyID', None)

    def get_party_members(self, party_id: str):
        return self.get_glz(f'/parties/v1/parties/{party_id}').get('Members', None)

    def get_match_history_info(self, puuid: str, start_index: int, end_index: int, queue: Optional[str] = None):
        def request(new_start: int, new_end: int):
            data = {'startIndex': new_start, 'endIndex': new_end, 'queue': '' if queue is None else queue}
            return self.get_pd(f'/match-history/v1/history/{puuid}', data)
        if end_index - start_index > 10:
            matches: List[Dict] = []
            total_count: int = 0
            for i in range(start_index, end_index, 10):
                match_info: Dict = request(i, i + 10)
                total_count = match_info.get('Total', 0)
                matches.extend(match_info.get('History', []))
            return {'BeginIndex': start_index, 'EndIndex': end_index, 'History': matches,
                    'Subject': puuid, 'Total': total_count}
        else:
            return request(start_index, end_index)

    def get_all_match_history(self, puuid: str, queue: Optional[str] = None):
        first_20_matches = self.get_match_history_info(puuid, start_index=0, end_index=20, queue=queue)
        total_matches_available: int = first_20_matches['Total']
        if total_matches_available > 20:
            remaining_matches = self.get_match_history_info(puuid, start_index=20, end_index=total_matches_available,
                                                            queue=queue)
            first_20_matches['History'].extend(remaining_matches['History'])
            first_20_matches['EndIndex'] = total_matches_available
        return first_20_matches

    def get_match_info(self, match_id: str):
        return self.get_pd(f'/match-details/v1/matches/{match_id}')
