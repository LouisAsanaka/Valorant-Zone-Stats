from PySide2.QtCore import *
from PySide2.QtWidgets import *

from typing import Dict

from src.ui.views.map_tab.map_queue_type_view import MapQueueTypeView


class MapQueueTypeController(QObject):

    def __init__(self, map_queue_type_view: MapQueueTypeView):
        super().__init__()

        self.view: MapQueueTypeView = map_queue_type_view
        self.init_queue_types_list()

    def init_queue_types_list(self):
        self.view.queue_type_box.addItems(['Competitive', 'Unrated', 'Custom'])

    def show_analytics(self, analytics: Dict):
        # self.view.show_matches_used(analytics['matchesUsed'])
        pass
