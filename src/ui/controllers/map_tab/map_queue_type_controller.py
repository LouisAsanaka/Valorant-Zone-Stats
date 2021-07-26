from PySide2.QtCore import *
from PySide2.QtWidgets import *

from typing import Dict

from src.services.api_service import ApiService
from src.ui.views.map_tab.map_queue_type_view import MapQueueTypeView


class MapQueueTypeController(QObject):

    queue_type_changed: SignalInstance = Signal(str)

    def __init__(self, map_queue_type_view: MapQueueTypeView):
        super().__init__()

        self.view: MapQueueTypeView = map_queue_type_view
        self.init_queue_types_list()
        self.view.queue_type_box.currentIndexChanged.connect(self.on_queue_type_changed)

    def init_queue_types_list(self):
        for queue in ['all', *ApiService.QueueTypes]:
            self.view.queue_type_box.addItem(queue.capitalize(), queue)

    def get_queue_type(self):
        return self.view.queue_type_box.itemData(self.view.queue_type_box.currentIndex())

    @Slot(int)
    def on_queue_type_changed(self, index: int):
        self.queue_type_changed.emit(self.view.queue_type_box.itemData(index))

    def show_analytics(self, analytics: Dict):
        all_queues_index: int = 0
        total_matches_used: int = 0
        for i in range(self.view.queue_type_box.count()):
            queue: str = self.view.queue_type_box.itemData(i)
            if queue == 'all':
                all_queues_index = i
            else:
                matches_used: int = analytics[queue]['matches_used']
                self.view.queue_type_box.setItemText(i, f'{queue.capitalize()} ({matches_used})')
                total_matches_used += matches_used
        self.view.queue_type_box.setItemText(all_queues_index, f'All ({total_matches_used})')
