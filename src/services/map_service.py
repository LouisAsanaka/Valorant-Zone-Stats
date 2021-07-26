from pathlib import Path
import json
from typing import Dict, Optional
from src.models.models import GameMap


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
