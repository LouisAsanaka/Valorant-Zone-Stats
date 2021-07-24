from PySide2.QtCore import *
from PySide2.QtWidgets import *

from src.ui.views.map_tab.map_filters_view import MapFiltersView


class MapFiltersController(QObject):

    player_side_changed = Signal(str)

    def __init__(self, map_filters_view: MapFiltersView):
        super().__init__()

        self.view: MapFiltersView = map_filters_view
        self.view.player_side_button_group.buttonClicked.connect(self.on_button_clicked)

        checked_button = self.view.player_side_button_group.checkedButton()
        self.current_side: str = checked_button.name

    def get_side(self) -> str:
        return self.current_side

    @Slot(QPushButton)
    def on_button_clicked(self, clicked_button: QPushButton):
        name: str = clicked_button.name
        if name is not self.current_side:
            self.current_side = name
            self.player_side_changed.emit(name)
