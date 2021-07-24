from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from typing import Optional

from src.models.models import PlayerData
from src.ui.views.general_tab.general_tab import GeneralTab
from src.ui.views.map_tab.map_tab import MapTab


class MainView(QMainWindow):

    close_event_signal = Signal(QCloseEvent)

    def __init__(self):
        super().__init__(None)

        self.player_data: Optional[PlayerData] = None

        self._init_ui()

    def _init_ui(self):
        self.resize(1000, 800)
        self.setWindowTitle('Valorant Zone Stats')
        self.setWindowIcon(QIcon('resources/ui/favicon.ico'))

        self.tabs: QTabWidget = QTabWidget(self)

        self.general_tab: GeneralTab = GeneralTab(self.tabs)
        self.general_tab_id: int = self.tabs.addTab(self.general_tab, 'General')

        self.map_tab: MapTab = MapTab(self.tabs)
        self.map_tab_id: int = self.tabs.addTab(self.map_tab, 'Map')

        central_widget: QWidget = QWidget()
        stack: QStackedLayout = QStackedLayout()
        stack.addWidget(self.tabs)
        central_widget.setContentsMargins(6, 6, 6, 6)
        central_widget.setLayout(stack)
        self.setCentralWidget(central_widget)

    def set_player_data(self, data: PlayerData):
        self.player_data = data
        self.general_tab.set_player_data(data)
        self.map_tab.set_player_data(data)

    def set_map_tab_enabled(self, status: bool = True):
        self.tabs.setTabEnabled(self.map_tab_id, status)

    def closeEvent(self, close_event):
        super(MainView, self).closeEvent(close_event)
        self.close_event_signal.emit(close_event)
