from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
