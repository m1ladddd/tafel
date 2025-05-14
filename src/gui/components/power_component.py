import os
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QPixmap, QImage
from PySide6.QtCore import Qt, QRectF, QPointF

class PowerComponent(QGraphicsPixmapItem):
    """Realistische weergave van energiecomponenten met afbeeldingen"""
    
    def __init__(self, x, y, component_type, name="", power=0.0, voltage=0.0):
        super().__init__()
        self.component_type = component_type
        self.name = name
        self.power = power
        self.voltage = voltage
        
        # Laad juiste afbeelding op basis van componenttype
        self.load_image()
        
        # Positioneer de afbeelding
        self.setPos(x - self.pixmap().width()/2, y - self.pixmap().height()/2)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
    def load_image(self):
        # Standaard afbeeldingen pad - pas aan naar behoefte
        images_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "images")
        os.makedirs(images_path, exist_ok=True)
        
        # Map componenttypen naar afbeeldingsbestanden
        image_files = {
            "generator": "generator.png",
            "solar": "solar_panel.png",
            "wind": "wind_turbine.png",
            "coal": "coal_plant.png",
            "nuclear": "nuclear_plant.png",
            "load": "house.png",
            "industrial": "factory.png",
            "bus": "substation.png",
            "storage": "battery.png",
            "transformer": "transformer.png"
        }
        
        # Gebruik een standaardafbeelding als het componenttype niet wordt gevonden
        image_file = image_files.get(self.component_type, "default.png")
        image_path = os.path.join(images_path, image_file)
        
        # Als de afbeelding niet bestaat, maak een placeholder
        if not os.path.exists(image_path):
            self.create_placeholder_image()
        else:
            self.setPixmap(QPixmap(image_path))
    
    def create_placeholder_image(self):
        # Maak een gekleurde rechthoek op basis van componenttype
        colors = {
            "generator": QColor(50, 205, 50),    # Groen
            "solar": QColor(255, 255, 0),        # Geel
            "wind": QColor(173, 216, 230),       # Lichtblauw
            "coal": QColor(169, 169, 169),       # Donkergrijs
            "nuclear": QColor(255, 165, 0),      # Oranje
            "load": QColor(255, 99, 71),         # Rood
            "industrial": QColor(139, 69, 19),   # Bruin
            "bus": QColor(135, 206, 250),        # Lichtblauw
            "storage": QColor(255, 215, 0),      # Goud
            "transformer": QColor(210, 180, 140) # Tan
        }
        
        color = colors.get(self.component_type, QColor(200, 200, 200))
        
        # Maak een kleine gekleurde afbeelding als placeholder
        size = 40
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        painter = QPainter(image)
        painter.setPen(Qt.black)
        painter.setBrush(QBrush(color))
        
        if self.component_type == "generator":
            # Teken een generatorsymbool
            painter.drawEllipse(5, 5, size-10, size-10)
            painter.drawLine(size//2, 0, size//2, size)
            painter.drawLine(0, size//2, size, size//2)
        elif self.component_type == "load":
            # Teken een huisachtige vorm
            painter.drawRect(5, 20, size-10, size-25)
            painter.drawPolygon([
                QPointF(5, 20), 
                QPointF(size//2, 5), 
                QPointF(size-5, 20)
            ])
        elif self.component_type == "transformer":
            # Teken transformatorsymbool
            painter.drawEllipse(5, 5, size-10, size-10)
            painter.drawEllipse(10, 10, size-20, size-20)
        elif self.component_type == "storage":
            # Teken batterijsymbool
            painter.drawRect(5, 5, size-10, size-10)
            painter.drawLine(size//2, 10, size//2, size//2 - 2)
            painter.drawLine(size//4, size//2, 3*size//4, size//2)
            painter.drawLine(size//4 + 5, size//2 + 5, 3*size//4 - 5, size//2 + 5)
        elif self.component_type == "bus":
            # Teken bussymbool
            painter.drawEllipse(5, 5, size-10, size-10)
        
        painter.end()
        
        self.setPixmap(QPixmap.fromImage(image))
        
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        
        # Teken naam en vermogenswaarde
        painter.setPen(Qt.white)
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        # Positioneer tekst onder het component
        rect = QRectF(0, self.pixmap().height(), 
                     self.pixmap().width(), 20)
        
        # Formatteer tekst
        if self.component_type in ["generator", "solar", "wind", "nuclear", "coal"]:
            text = f"{self.name}\n{self.power:.2f} MW"
        elif self.component_type in ["load", "industrial"]:
            text = f"{self.name}\n{abs(self.power):.2f} MW"
        else:
            text = self.name
            
        painter.drawText(rect, Qt.AlignCenter, text) 