from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from typing import Optional


class MapFiltersView(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout()

        player_side_layout = QHBoxLayout()

        self.player_side_button_group: QButtonGroup = QButtonGroup(self)
        player_side_layout.addWidget(self._create_button('Both', 'both', css_name='playerSide',
                                                         group=self.player_side_button_group, checked=True))
        player_side_layout.addWidget(self._create_button('Attacker', 'attacker', css_name='playerSide',
                                                         group=self.player_side_button_group))
        player_side_layout.addWidget(self._create_button('Defender', 'defender', css_name='playerSide',
                                                         group=self.player_side_button_group))

        player_side_frame = QFrame(self)
        player_side_frame.setObjectName('playerSideFrame')
        player_side_frame.setLayout(player_side_layout)
        self.layout.addWidget(player_side_frame)

        plant_time_layout = QHBoxLayout()

        self.plant_time_button_group: QButtonGroup = QButtonGroup(self)
        plant_time_layout.addWidget(self._create_button('Both', 'both', css_name='plantTime',
                                                        group=self.plant_time_button_group, checked=True))
        plant_time_layout.addWidget(self._create_button('Pre-plant', 'preplant', css_name='plantTime',
                                                        group=self.plant_time_button_group))
        plant_time_layout.addWidget(self._create_button('Post-plant', 'postplant', css_name='plantTime',
                                                        group=self.plant_time_button_group))

        plant_time_frame = QFrame(self)
        plant_time_frame.setObjectName('plantTimeFrame')
        plant_time_frame.setLayout(plant_time_layout)
        self.layout.addWidget(plant_time_frame)

        self.setLayout(self.layout)

    def _create_button(self, display_name: str, actual_name: str, css_name: str, group: Optional[QButtonGroup] = None,
                       checked: Optional[bool] = False) -> QPushButton:
        button: QPushButton = QPushButton(display_name, self)
        button.setMinimumHeight(50)
        button.setCheckable(True)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.name = actual_name
        button.setProperty('cssClass', css_name)
        if group is not None:
            group.addButton(button)
        if checked:
            button.setChecked(True)
        return button
