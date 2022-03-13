from PySide2.QtCore import *
from PySide2.QtWidgets import *

from pprint import pprint
from typing import Optional, Tuple
import threading
from threading import Thread

from src.services.api_service import ApiService
from src.services.match_service import MatchService
from src.models.models import PlayerData
from src.ui.views.general_tab.general_tab import GeneralTab
from src.utils import logger
from src.api.api import ValorantConstants

# from guppy import hpy
# h = hpy()


class ProcessMatchWorker(QObject):
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
        logger.debug(f'Running on {threading.current_thread().name}')
        logger.debug(f'Processing matches for {self.puuid}...')
        result = self.match_service.process_matches(self.puuid, lambda x: self.progress.emit(x))
        self.result.emit(result)
        self.finished.emit()


class GeneralController(QObject):

    matches_processed: SignalInstance = Signal()
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
        if ValorantConstants.DebugMatchUUID:
            if ValorantConstants.DebugForceOurPUUID:
                self.player_data.set_puuid(ValorantConstants.DebugForceOurPUUID)
                self.api_service.puuid = ValorantConstants.DebugForceOurPUUID
            else:
                self.on_fetch_user_pressed()
            self.on_fetch_matches_pressed()
        
        self.init_region_list()

    def init_region_list(self):
        regions: Tuple[str] = self.api_service.get_regions()
        self.view.region_combo_box.addItems(regions)
        index: int = self.view.region_combo_box.findText(self.settings.value('region', regions[0]))
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
            self.matches_processed.emit()
            self.view.fetch_matches_button.setDisabled(False)

        self.worker = ProcessMatchWorker(self.match_service, self.api_service.puuid)
        self.worker.progress.connect(self.on_processing_progress_updated)
        self.worker.result.connect(self.player_data.set_available_matches)
        self.worker.finished.connect(on_finish)
        self.worker.start()
        self.view.progress_bar.setValue(0)
        self.view.fetch_matches_button.setDisabled(True)

    @Slot(float)
    def on_processing_progress_updated(self, progress: float):
        self.view.progress_bar.setValue(int(progress * 100))

    @Slot(int)
    def on_region_changed(self, index: int):
        self.region_changed.emit(self.view.region_combo_box.itemText(index))
