from PySide2.QtCore import QObject, Slot, QRect

from typing import Optional, Dict

from src.models.models import GameMap
from src.ui.views.map_tab.map_view import MapCanvas, ZonePolygonItem


class MapController(QObject):

    def __init__(self, map_view: MapCanvas):
        super().__init__()
        self.view: MapCanvas = map_view
        self.view.zone_clicked.connect(self.on_zone_clicked)

        self.current_map: Optional[GameMap] = None
        self.current_stats: Optional[Dict] = None

    @Slot(ZonePolygonItem)
    def on_zone_clicked(self, zone_polygon: ZonePolygonItem):
        self.view.clear_kills()
        if zone_polygon.highlighted:
            self.view.revert_zones_and_kills_to_default()
        else:  # Should highlight the clicked polygon
            self.view.highlight_zone(zone_polygon)
            self.view.draw_kills(self.current_stats[zone_polygon.zone.name]['events'])
            # TODO: Debug draw all kills
            # for zone_stats in self.current_stats.values():
            #     self.view.draw_kills(zone_stats['events'])
        zone_polygon.toggle_highlighted()
        # print(zone_polygon.zone.name)

    def set_map_and_stats(self, game_map: GameMap, stats: Dict):
        self.current_map = game_map
        self.current_stats = stats

    def render_map_zones(self):
        geo: QRect = self.view.graphics_view.geometry()
        size: int = min(geo.width() - 2, geo.height() - 2)
        self.view.set_map(self.current_map)
        self.view.set_size(size, size)

        self.view.draw_map()
        self.view.clear_kills()
        self.view.draw_zones(self.current_stats)
