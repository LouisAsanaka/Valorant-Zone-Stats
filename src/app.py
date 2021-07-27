import os
import sys
from src.utils import FileManager
import logging

from PySide2.QtGui import *
from PySide2.QtWidgets import *

from src.ui.views.main_view import MainView
from src.ui.controllers.main_controller import MainController


class App(QApplication):

    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)

        database = QFontDatabase()
        font_id: int = database.addApplicationFont('resources/ui/Poppins-Regular.ttf')
        family = database.applicationFontFamilies(font_id)[0]
        self.setFont(family)

        with open('resources/ui/style.qss', 'r') as f:
            self.setStyleSheet(f.read())

        self.main_view: MainView = MainView()
        self.main_controller: MainController = MainController(self.main_view)
        self.main_controller.show()


if __name__ == '__main__':
    # Set working directory with PyInstaller
    try:
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS'.
        wd = sys._MEIPASS
    except AttributeError:
        wd = os.getcwd()
    os.chdir(wd)

    files_migrated: int = FileManager.migrate_files(['matches.db', 'settings.ini', 'storage.json', 'debug.log'])

    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(filename=FileManager.get_storage_path('debug.log'),
                        filemode='w',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    logging.debug(f"{files_migrated} files migrated.")

    app = App(sys.argv)
    sys.exit(app.exec_())
