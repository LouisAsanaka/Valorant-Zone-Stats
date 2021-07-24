from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from src.models.models import GameMap


class MapRowView(QWidget):

    def __init__(self, parent, game_map: GameMap):
        super().__init__(parent)

        self.game_map: GameMap = game_map
        self.map_name: str = self.game_map.display_name
        self.loaded_image: QPixmap = QPixmap(self.game_map.background_image_path)

        self.font: QFont = QFont('Segoe UI', 24, QFont.Bold)
        font_metrics: QFontMetrics = QFontMetrics(self.font)
        bounding_rect: QRect = font_metrics.tightBoundingRect(self.map_name)
        self.text_offset_x, self.text_offset_y = bounding_rect.width() / 2, bounding_rect.height() / 2

        self.selected: bool = False

    def paintEvent(self, event: QPaintEvent):
        painter: QPainter = QPainter(self)
        painter.drawPixmap(0, 0, self.loaded_image)

        if self.selected:
            painter.setPen(Qt.yellow)
        else:
            painter.setPen(Qt.white)
        painter.setFont(self.font)

        bounding_box: QRect = self.rect()
        width, height = bounding_box.width(), bounding_box.height()
        painter.drawText(width / 2 - self.text_offset_x, height / 2 + self.text_offset_y, self.map_name)


class MapListView(QListWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.setMaximumWidth(456)

        self._init_ui()

    def _init_ui(self):
        pass

    def insert_map_row(self, game_map: GameMap):
        item = QListWidgetItem()
        self.addItem(item)

        row = MapRowView(self, game_map)
        item.setSizeHint(row.minimumSizeHint())

        # Associate the custom widget to the list entry
        self.setItemWidget(item, row)
