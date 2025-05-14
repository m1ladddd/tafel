from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt, QLineF

class PowerLine(QGraphicsLineItem):
    """Representeert een stroomlijn in het netwerk met uitschakelfunctie"""
    
    def __init__(self, x1, y1, x2, y2, power_flow=0.0, capacity=100.0, name=""):
        super().__init__(x1, y1, x2, y2)
        self.power_flow = power_flow  # Vermogensstroom in MW
        self.capacity = capacity      # Lijncapaciteit in MW
        self.name = name
        self.active = True            # Lijnstatus: actief of uitgeschakeld
        self.setFlag(QGraphicsLineItem.ItemIsSelectable, True)
        self.update_appearance()
        
    def update_appearance(self):
        """Update lijndikte en kleur op basis van belasting en status"""
        if not self.active:
            # Uitgeschakelde lijn is gestippeld grijs
            pen = QPen(QColor(100, 100, 100), 2, Qt.DashLine)
            self.setPen(pen)
            return
            
        # Lijndikte op basis van capaciteit
        thickness = max(2, min(8, int(self.capacity / 20)))
        
        # Lijnkleur op basis van vermogensstroom als percentage van capaciteit
        if abs(self.capacity) < 0.001:  # Vermijd deling door nul
            load_percent = 0
        else:
            load_percent = abs(self.power_flow) / self.capacity * 100
            
        if load_percent < 50:
            # Groen bij lage belasting
            color = QColor(0, 255, 0)
        elif load_percent < 75:
            # Geel bij gemiddelde belasting
            color = QColor(255, 255, 0)
        elif load_percent < 90:
            # Oranje bij hoge belasting
            color = QColor(255, 165, 0)
        else:
            # Rood bij kritieke belasting
            color = QColor(255, 0, 0)
            
        pen = QPen(color, thickness)
        self.setPen(pen)
        
    def set_active(self, active_state):
        """Zet de lijn aan of uit"""
        if self.active != active_state:
            self.active = active_state
            self.update_appearance()
            return True
        return False
        
    def toggle(self):
        """Schakel lijnstatus om"""
        return self.set_active(not self.active) 