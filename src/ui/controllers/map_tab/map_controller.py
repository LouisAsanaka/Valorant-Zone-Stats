from PySide2.QtCore import QObject, Slot, QRect

from typing import Optional

from src.services.services import ZoneStats, MapKillPositions
from src.models.models import GameMap
from src.ui.views.map_tab.map_view import MapCanvas, ZonePolygonItem


class MapController(QObject):

    def __init__(self, map_view: MapCanvas):
        super().__init__()
        self.view: MapCanvas = map_view
        self.view.zone_clicked.connect(self.on_zone_clicked)

        self.current_map: Optional[GameMap] = None
        self.stored_zone_stats: Optional[ZoneStats] = None
        self.stored_kill_positions: Optional[MapKillPositions] = None

    @Slot(ZonePolygonItem)
    def on_zone_clicked(self, zone_polygon: ZonePolygonItem):
        self.view.clear_kills()
        if zone_polygon.highlighted:
            self.view.revert_zones_and_kills_to_default()
        else:  # Should highlight the clicked polygon
            self.view.highlight_zone(zone_polygon)
            self.view.draw_kills(self.stored_kill_positions[zone_polygon.zone.name])
            # TODO: Debug draw all kills
            # for kills in self.stored_kill_positions.values():
            #     self.view.draw_kills(kills)
        zone_polygon.toggle_highlighted()
        # print(zone_polygon.zone.name)

    def store_map_stats(self, game_map: GameMap, zone_stats: Optional[ZoneStats],
                        kill_positions: Optional[MapKillPositions]):
        self.current_map = game_map

        geo: QRect = self.view.graphics_view.geometry()
        size: int = min(geo.width() - 2, geo.height() - 2)
        self.view.set_map(game_map)
        self.view.set_size(size, size)

        self.stored_zone_stats = zone_stats
        self.stored_kill_positions = kill_positions

    def render_map_zones(self, with_stats: bool = True):
        if self.current_map is None:
            return
        if with_stats and self.stored_zone_stats is None:
            return
        self.view.draw_map()
        self.view.clear_kills()
        if with_stats:
            self.view.draw_zones(self.stored_zone_stats)
