from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from typing import Optional, List

from src.models.models import Match, PlayerData
from src.ui.widgets.widgets import QHLine


class MatchRowView(QFrame):

    def __init__(self, parent, match: Match):
        super().__init__(parent)
        self._init_ui(match)

    def _init_ui(self, match: Match):
        self.hbox: QHBoxLayout = QHBoxLayout()
        self.setLayout(self.hbox)

        self.date_label: QLabel = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.date_label.setText(match.get_start_time().astimezone().strftime('%Y-%m-%d %H:%M:%S'))
        self.hbox.addWidget(self.date_label)

        self.score_label: QLabel = QLabel()
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.score_label.setText(f'{match.my_match_score} - {match.opponent_match_score}')
        self.hbox.addWidget(self.score_label)


class GeneralTab(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName('GeneralTab')

        self.player_data: Optional[PlayerData] = None

        self._init_ui()

    def _init_ui(self):
        container: QVBoxLayout = QVBoxLayout()
        container.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setLayout(container)

        top_box: QHBoxLayout = QHBoxLayout()

        self.fetch_user_button: QPushButton = QPushButton('Fetch User')
        self.fetch_user_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.fetch_user_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding))
        self.fetch_user_button.setMaximumHeight(80)
        top_box.addWidget(self.fetch_user_button)

        self.name_label: QLabel = QLabel('My Username')
        self.name_label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setObjectName('nameLabel')
        self.name_label.setMaximumHeight(80)
        top_box.addWidget(self.name_label)

        self.fetch_matches_button: QPushButton = QPushButton('Fetch Matches')
        self.fetch_matches_button.setDisabled(True)
        self.fetch_matches_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.fetch_matches_button.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding))
        self.fetch_matches_button.setMaximumHeight(80)
        top_box.addWidget(self.fetch_matches_button)

        self.region_combo_box: QComboBox = QComboBox()
        top_box.addWidget(self.region_combo_box)

        container.addLayout(top_box)

        self.match_list_scroll_area = QScrollArea()
        self.match_list_scroll_area.setWidgetResizable(True)

        self.match_list_box: QVBoxLayout = QVBoxLayout()
        self.match_list_box.setAlignment(Qt.AlignTop | Qt.AlignVCenter)
        self.match_list_box.setSpacing(10)

        inner = QFrame(self.match_list_scroll_area)
        inner.setObjectName('MatchListFrame')
        inner.setLayout(self.match_list_box)
        self.match_list_scroll_area.setWidget(inner)
        self.match_rows: List[MatchRowView] = []

        container.addWidget(self.match_list_scroll_area)

    @Slot(str)
    def on_username_changed(self, name: str):
        self.set_message(name)

    @Slot()
    def on_matches_changed(self):
        # TODO: Reuse rows
        for widget in self.match_rows:
            self.match_list_box.removeWidget(widget)
            widget.deleteLater()
        self.match_rows = []

        matches: List[Match] = self.player_data.available_matches
        for match in matches:
            row: MatchRowView = MatchRowView(self.match_list_scroll_area, match)
            row.setMaximumHeight(70)
            self.match_list_box.addWidget(row)
            self.match_rows.append(row)

    def set_player_data(self, data: PlayerData):
        self.player_data = data
        self.player_data.username_changed.connect(self.on_username_changed)
        self.player_data.matches_changed.connect(self.on_matches_changed)

    def set_message(self, message: str):
        self.name_label.setText(message)
