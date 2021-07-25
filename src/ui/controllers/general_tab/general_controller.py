from PySide2.QtCore import *
from PySide2.QtWidgets import *

from pprint import pprint
import logging
from typing import Optional
import threading
from threading import Thread

from src.services.services import ApiService, MatchService
from src.models.models import PlayerData
from src.ui.views.general_tab.general_tab import GeneralTab

# from guppy import hpy
# h = hpy()


class FetchMatchWorker(QObject):
    progress: SignalInstance = Signal(float)
    result: SignalInstance = Signal(dict)
    finished: SignalInstance = Signal()

    def __init__(self, match_service: MatchService, puuid: str):
        super().__init__(None)
        self.match_service: MatchService = match_service
        self.puuid: str = puuid
        self.thread: Optional[Thread] = None

    def start(self):
        self.thread = Thread(target=self.run)
        self.thread.start()

    def run(self):
        logging.debug(f'Running on {threading.current_thread().name}')
        logging.debug(f'Fetching matches for {self.puuid}...')
        result = self.match_service.store_new_matches(self.puuid)
        self.result.emit(result)
        self.finished.emit()


class GeneralController(QObject):

    matches_fetched: SignalInstance = Signal()
    region_changed: SignalInstance = Signal(str)

    def __init__(self, general_view: GeneralTab, player_data: PlayerData, api_service: ApiService,
                 match_service: MatchService, settings: QSettings):
        super().__init__(general_view)

        self.player_data: PlayerData = player_data
        self.api_service: ApiService = api_service
        self.match_service: MatchService = match_service
        self.settings: QSettings = settings

        self.view: GeneralTab = general_view
        self.view.fetch_user_button.pressed.connect(self.on_fetch_user_pressed)
        self.view.fetch_matches_button.pressed.connect(self.on_fetch_matches_pressed)

        index: int = self.view.region_combo_box.findText(self.settings.value('region', 'NA'))
        if index != -1:
            self.view.region_combo_box.setCurrentIndex(index)
        self.view.region_combo_box.currentIndexChanged.connect(self.on_region_changed)

    @Slot()
    def on_fetch_user_pressed(self):
        if self.api_service.try_auth():
            self.player_data.set_puuid(self.api_service.puuid)
            self.player_data.set_full_username(self.api_service.get_full_username(self.api_service.puuid))
            self.view.fetch_matches_button.setDisabled(False)
        else:
            self.view.set_message('Auth Failed')

    @Slot()
    def on_fetch_matches_pressed(self):
        def on_finish():
            # logging.info(f'Running on {threading.current_thread().name}')
            self.worker.thread.join()
            self.worker.deleteLater()
            self.matches_fetched.emit()
            self.view.fetch_matches_button.setDisabled(False)

        self.worker = FetchMatchWorker(self.match_service, self.api_service.puuid)
        self.worker.result.connect(self.player_data.set_available_matches)
        self.worker.finished.connect(on_finish)
        self.worker.start()
        self.view.fetch_matches_button.setDisabled(True)

    @Slot(int)
    def on_region_changed(self, index: int):
        self.region_changed.emit(self.view.region_combo_box.itemText(index))