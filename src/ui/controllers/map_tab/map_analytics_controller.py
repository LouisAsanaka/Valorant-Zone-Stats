from PySide2.QtCore import *
from PySide2.QtWidgets import *

from typing import Dict

from src.ui.views.map_tab.map_analytics_view import MapAnalyticsView


class MapAnalyticsController(QObject):

    def __init__(self, map_analytics_view: MapAnalyticsView):
        super().__init__()

        self.view: MapAnalyticsView = map_analytics_view

    def show_analytics(self, analytics: Dict):
        self.view.show_matches_used(analytics['matchesUsed'])
