from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from typing import Optional, List


class MapFiltersView(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.layout = QHBoxLayout()

        self.player_side_button_group: QButtonGroup = QButtonGroup(self)
        self.layout.addWidget(self._create_button('Both', 'both', group=self.player_side_button_group, checked=True))
        self.layout.addWidget(self._create_button('Attacker', 'attacker', group=self.player_side_button_group))
        self.layout.addWidget(self._create_button('Defender', 'defender', group=self.player_side_button_group))

        self.setLayout(self.layout)

    def _create_button(self, display_name: str, actual_name: str, group: Optional[QButtonGroup] = None,
                       checked: Optional[bool] = False) -> QPushButton:
        button: QPushButton = QPushButton(display_name, self)
        button.setCheckable(True)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.name = actual_name
        button.setProperty('cssClass', 'filter-button')
        if group is not None:
            group.addButton(button)
        if checked:
            button.setChecked(True)
        return button
