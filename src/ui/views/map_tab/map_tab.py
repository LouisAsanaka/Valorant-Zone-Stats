from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from typing import Optional

from src.models.models import PlayerData

from .map_view import MapCanvas
from .map_list_view import MapListView
from .map_filters_view import MapFiltersView
from .map_analytics_view import MapAnalyticsView


class MapTab(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('MapTab')

        self.player_data: Optional[PlayerData] = None

        self._init_ui()

    def _init_ui(self):
        container: QGridLayout = QGridLayout()
        self.setLayout(container)

        self.map_list_view: MapListView = MapListView(self)
        self.map_filters_view: MapFiltersView = MapFiltersView(self)
        self.map_analytics_view: MapAnalyticsView = MapAnalyticsView(self)
        self.map_canvas = MapCanvas(self)

        container.addWidget(self.map_list_view, 0, 0, 2, 1)
        container.addWidget(self.map_filters_view, 0, 1, 1, 1)
        container.addWidget(self.map_analytics_view, 0, 2, 1, 1)
        container.addWidget(self.map_canvas.graphics_view, 1, 1, 1, 2)

        container.setRowStretch(0, 1)
        container.setRowStretch(1, 5)
        container.setColumnStretch(0, 1)
        container.setColumnStretch(1, 3)
        container.setColumnStretch(2, 1)

    def set_player_data(self, data: PlayerData):
        self.player_data = data
