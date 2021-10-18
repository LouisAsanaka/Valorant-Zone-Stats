from pprint import pprint
from typing import Callable, Optional, List, Tuple, Dict, Any

from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *

from src.models.models import GameMap, MapZone


# Source: https://stackoverflow.com/a/29026916
class InteractiveGraphicsView(QGraphicsView):

    def __init__(self, scene: QGraphicsScene, parent=None):
        super(InteractiveGraphicsView, self).__init__(scene, parent)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setRenderHints(QPainter.Antialiasing)

    def wheelEvent(self, event):
        # Zoom Factor
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        # Set Anchors
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)

        # Save the scene pos
        old_pos = self.mapToScene(event.pos())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

        # Get the new position
        new_pos = self.mapToScene(event.pos())

        # Move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())


class ZonePolygonItem(QGraphicsPolygonItem):

    hidden_pen: QPen = QPen(Qt.transparent, 0)
    hidden_brush: QBrush = QBrush(Qt.transparent, Qt.SolidPattern)

    def __init__(self, polygon: QPolygonF, zone: MapZone, clicked_callback: Callable[[Any], None]):
        super().__init__(polygon)
        self.zone: MapZone = zone
        self.clicked_callback = clicked_callback

        self.regular_pen: Optional[QPen] = None
        self.highlighted_pen: Optional[QPen] = None
        self.regular_brush: Optional[QBrush] = None
        self.highlighted_brush: Optional[QBrush] = None

        self.highlighted: bool = False

    def store_pens(self, regular_pen: QPen, highlighted_pen: QPen):
        self.setPen(regular_pen)
        self.regular_pen = regular_pen
        self.highlighted_pen = highlighted_pen

    def store_brushes(self, regular_brush: QBrush, highlighted_brush: QBrush):
        self.setBrush(regular_brush)
        self.regular_brush = regular_brush
        self.highlighted_brush = highlighted_brush

    def set_regular_colors(self):
        self.setPen(self.regular_pen)
        self.setBrush(self.regular_brush)

    def set_highlighted_colors(self):
        self.setPen(self.highlighted_pen)
        self.setBrush(self.highlighted_brush)

    def set_hidden_colors(self):
        self.setPen(self.hidden_pen)
        self.setBrush(self.hidden_brush)

    def toggle_highlighted(self):
        self.highlighted = not self.highlighted

    def mousePressEvent(self, event):
        self.clicked_callback(self)


class MapCanvas(QObject):

    zone_clicked = Signal(ZonePolygonItem)

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.game_map: Optional[GameMap] = None
        self.pixel_width, self.pixel_height = 0, 0

        self.scene = QGraphicsScene(parent)

        self.zone_polygons_and_text: List[Dict[str, Any]] = []
        self.kill_position_items: List[QGraphicsItem] = []

        self.pixmap: QGraphicsPixmapItem = self.scene.addPixmap(QPixmap())
        self.pixmap.setPos(QPointF(0.0, 0.0))
        self.pixmap.setTransformationMode(Qt.SmoothTransformation)

        self.text_font: QFont = QFont('Segoe UI', 8, QFont.Bold)

        self.graphics_view = InteractiveGraphicsView(self.scene, parent=parent)
        self.graphics_view.setBackgroundBrush(QBrush(Qt.black, Qt.SolidPattern))
        self.graphics_view.show()

    def set_size(self, width: int, height: int):
        self.pixel_width, self.pixel_height = width, height
        self.scene.setSceneRect(QRectF(0, 0, self.pixel_width, self.pixel_height))

    def set_map(self, game_map: GameMap):
        self.game_map = game_map

    def convert_normalized_to_pixel(self, norm_x: float, norm_y: float) -> Tuple[float, float]:
        return norm_x * self.pixel_width, norm_y * self.pixel_height

    def draw_map(self):
        map_image = QPixmap(self.game_map.image_path).scaled(self.pixel_width, self.pixel_height)
        self.pixmap.setPixmap(map_image)

    def draw_point(self, x: int, y: int, pen: QPen, brush: QBrush) -> QGraphicsEllipseItem:
        pixel_x, pixel_y = self.convert_normalized_to_pixel(*self.game_map.normalize_point(x, y))
        return self.scene.addEllipse(QRectF(pixel_x - 2, pixel_y + 2, 4, 4), pen, brush)

    def draw_line(self, from_x: int, from_y: int, to_x: int, to_y: int, pen: QPen) -> QGraphicsLineItem:
        pixel_from_x, pixel_from_y = self.convert_normalized_to_pixel(*self.game_map.normalize_point(from_x, from_y))
        pixel_to_x, pixel_to_y = self.convert_normalized_to_pixel(*self.game_map.normalize_point(to_x, to_y))
        pixel_from_y += 4
        pixel_to_y += 4
        line: QGraphicsLineItem = self.scene.addLine(QLineF(pixel_from_x, pixel_from_y, pixel_to_x, pixel_to_y), pen)
        # line.setTransformationMode(Qt.SmoothTransformation)
        return line

    def get_qt_polygon_from_zone(self, zone: MapZone) -> QPolygonF:
        points = list(map(lambda p: QPointF(*self.convert_normalized_to_pixel(*p)), zone.get_points()))
        return QPolygonF(points)

    def draw_zone_text(self, zone: MapZone, text: str):
        text: QGraphicsTextItem = self.scene.addText(text, font=self.text_font)
        text.setPos(*self.convert_normalized_to_pixel(*zone.top_left()))
        text.setDefaultTextColor(Qt.white)
        text.setZValue(100)
        return text

    def draw_zone(self, zone: MapZone, presence: float, kd: float) -> Tuple[ZonePolygonItem, QTextItem]:
        # polygon: QGraphicsPolygonItem = self.scene.addPolygon(self.get_qt_polygon_from_zone(zone),
        #                                                       QPen(QColor(0, 0, 255, 255), 2),
        #                                                       QBrush(QColor(0, 0, 255, 127), Qt.SolidPattern))
        polygon: ZonePolygonItem = ZonePolygonItem(self.get_qt_polygon_from_zone(zone), zone,
                                                   clicked_callback=lambda x: self.zone_clicked.emit(x))
        polygon.setCursor(Qt.PointingHandCursor)
        if abs(presence) < 0.0001:
            polygon.store_pens(regular_pen=QPen(QColor(251, 133, 0, 255), 2),
                               highlighted_pen=QPen(QColor(251, 133, 0, 255), 2))
            polygon.store_brushes(regular_brush=QBrush(QColor(251, 133, 0, 127), Qt.SolidPattern),
                                  highlighted_brush=QBrush(Qt.transparent, Qt.SolidPattern))
        else:
            if kd >= 1.0:
                polygon.store_pens(regular_pen=QPen(QColor(0, 255, 0, 255), 2),
                                   highlighted_pen=QPen(QColor(0, 255, 0, 255), 2))
                polygon.store_brushes(regular_brush=QBrush(QColor(0, 255, 0, 127), Qt.SolidPattern),
                                      highlighted_brush=QBrush(Qt.transparent, Qt.SolidPattern))
            else:
                polygon.store_pens(regular_pen=QPen(QColor(255, 0, 0, 255), 2),
                                   highlighted_pen=QPen(QColor(255, 0, 0, 255), 2))
                polygon.store_brushes(regular_brush=QBrush(QColor(255, 0, 0, 127), Qt.SolidPattern),
                                      highlighted_brush=QBrush(Qt.transparent, Qt.SolidPattern))
        self.scene.addItem(polygon)
        text = self.draw_zone_text(zone, text=f'{int(presence * 100)}%\nKD: {round(kd, 2)}')
        return polygon, text

    def draw_zones(self, stats: Dict[str, Dict[str, Any]]):
        self.zone_polygons_and_text = []
        for item in self.scene.items():
            if isinstance(item, ZonePolygonItem) or isinstance(item, QGraphicsTextItem):
                # print('Removing item...')
                self.scene.removeItem(item)
        for zone in self.game_map.get_zones().values():
            polygon, text = self.draw_zone(zone, presence=stats[zone.name]['presence'], kd=stats[zone.name]['kd'])
            self.zone_polygons_and_text.append({
                'polygon': polygon,
                'text': text
            })
        # TODO: remove some debug stuff
        # self.draw_point(1299, -4518, QPen(Qt.green, 2), QBrush(Qt.green, Qt.SolidPattern))
        # self.draw_point(1781, -4432, QPen(Qt.green, 1), QBrush(Qt.transparent, Qt.SolidPattern))
        # self.graphics_view.update()

    def highlight_zone(self, zone_polygon: ZonePolygonItem):
        clicked_text = None
        for item in self.zone_polygons_and_text:
            item['polygon'].set_hidden_colors()
            item['polygon'].highlighted = False
            self.scene.removeItem(item['text'])

            if item['polygon'] is zone_polygon:
                clicked_text = item['text']
        zone_polygon.set_highlighted_colors()
        if clicked_text is not None:
            self.scene.addItem(clicked_text)

    def revert_zones_and_kills_to_default(self):
        for item in self.zone_polygons_and_text:
            item['polygon'].set_regular_colors()
            self.scene.addItem(item['text'])
        self.clear_kills()

    def clear_kills(self):
        if not self.kill_position_items:
            return
        for item in self.kill_position_items:
            self.scene.removeItem(item)
        self.kill_position_items = []

    def draw_kills(self, events: List[Dict]):
        for event in events:
            items = None

            if 'k' not in event or event['k'] is None:
                continue
            killer_x, killer_y = event['k']
            victim_x, victim_y = event['v']
            if event['r'] == 'k':
                items = [
                    self.draw_point(killer_x, killer_y, QPen(Qt.green, 2), QBrush(Qt.green, Qt.SolidPattern)),
                    self.draw_point(victim_x, victim_y, QPen(Qt.green, 1), QBrush(Qt.transparent, Qt.SolidPattern)),
                    self.draw_line(killer_x, killer_y, victim_x, victim_y, QPen(Qt.lightGray, 1))
                ]
            elif event['r'] == 'v':
                items = [
                    self.draw_point(killer_x, killer_y, QPen(Qt.red, 1), QBrush(Qt.transparent, Qt.SolidPattern)),
                    self.draw_point(victim_x, victim_y, QPen(Qt.red, 2), QBrush(Qt.red, Qt.SolidPattern)),
                    self.draw_line(killer_x, killer_y, victim_x, victim_y, QPen(Qt.lightGray, 1))
                ]
            self.kill_position_items.extend(items)
