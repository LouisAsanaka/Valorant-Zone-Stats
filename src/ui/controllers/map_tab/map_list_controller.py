from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from src.services.services import MapService
from src.ui.views.map_tab.map_list_view import MapListView, MapRowView


class MapListController(QObject):

    map_selected = Signal(str)

    def __init__(self, map_list_view: MapListView, map_service: MapService):
        super().__init__()
        self.view: MapListView = map_list_view
        self.map_service: MapService = map_service

        self._populate_list()
        self.view.setCurrentRow(0)
        self.current_game_map: str = self.view.itemWidget(self.view.currentItem()).map_name
        self.view.itemClicked.connect(self.on_map_name_clicked)

    def get_current_map_display_name(self) -> str:
        return self.current_game_map

    def _populate_list(self):
        for map_name, map_id in self.map_service.get_map_names().items():
            self.view.insert_map_row(self.map_service.get_map(map_id))

    @Slot(QListWidgetItem)
    def on_map_name_clicked(self, item: QListWidgetItem):
        row_widget: MapRowView = self.view.itemWidget(item)

        self.current_game_map = row_widget.map_name
        self.map_selected.emit(self.current_game_map)
