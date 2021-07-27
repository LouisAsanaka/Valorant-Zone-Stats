from PySide2.QtCore import *
from PySide2.QtWidgets import *

from src.ui.views.map_tab.map_filters_view import MapFiltersView


class MapFiltersController(QObject):

    player_side_changed = Signal(str)
    plant_time_changed = Signal(str)

    def __init__(self, map_filters_view: MapFiltersView):
        super().__init__()

        self.view: MapFiltersView = map_filters_view
        self.view.player_side_button_group.buttonClicked.connect(self.on_player_side_button_clicked)
        self.view.plant_time_button_group.buttonClicked.connect(self.on_plant_time_button_clicked)

        self.current_side: str = self.view.player_side_button_group.checkedButton().name
        self.current_plant_time: str = self.view.plant_time_button_group.checkedButton().name

    def get_side(self) -> str:
        return self.current_side

    def get_plant_time(self) -> str:
        return self.current_plant_time

    @Slot(QPushButton)
    def on_player_side_button_clicked(self, clicked_button: QPushButton):
        name: str = clicked_button.name
        if name is not self.current_side:
            self.current_side = name
            self.player_side_changed.emit(name)

    @Slot(QPushButton)
    def on_plant_time_button_clicked(self, clicked_button: QPushButton):
        name: str = clicked_button.name
        if name is not self.current_plant_time:
            self.current_plant_time = name
            self.plant_time_changed.emit(name)
