import os
import sys
from src.utils import get_executable_relative_path
import logging

logging.basicConfig(level=logging.INFO)
# logging.basicConfig(filename=get_executable_relative_path('debug.log'),
#                     filemode='a',
#                     format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
#                     datefmt='%H:%M:%S',
#                     level=logging.DEBUG)

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

    app = App(sys.argv)
    sys.exit(app.exec_())
