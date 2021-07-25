from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *


class MapQueueTypeView(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout()

        self.queue_type_box: QComboBox = QComboBox(self)
        self.layout.addWidget(self.queue_type_box)

        # self.matches_used_label: QLabel = QLabel('Matches used: ')
        # self.matches_used_label.setObjectName('matchesUsedLabel')
        # self.matches_used_label.setAlignment(Qt.AlignCenter)
        #
        # self.layout.addWidget(self.matches_used_label)

        self.setLayout(self.layout)

    def show_matches_used(self, count: int):
        self.matches_used_label.setText(f'Matches used: {count}')
