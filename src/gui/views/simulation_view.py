from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QComboBox, 
                               QHBoxLayout, QGroupBox, QGridLayout)
from PySide6.QtCore import Slot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class SimulationView(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        # Hoofdlayout
        self.main_layout = QVBoxLayout(self)
        
        # Weergave opties
        self._create_display_options()
        
        # Grid status widget
        self._create_grid_status()
        
        # Matplotlib figuur voor visualisatie
        self._create_figure()
        
        # Verbind signalen
        self._setup_connections()
        
        # Initialiseer weergave
        self._update_plot()
    
    def _create_display_options(self):
        """Creëer opties voor weergave."""
        options_layout = QHBoxLayout()
        
        # Weergave type
        view_label = QLabel("Weergave:")
        self.view_type_combo = QComboBox()
        self.view_type_combo.addItems(["Power Flow", "Spanning", "Generator Status", "Netwerk Topologie"])
        options_layout.addWidget(view_label)
        options_layout.addWidget(self.view_type_combo)
        
        # Variabele selectie
        variable_label = QLabel("Variabele:")
        self.variable_combo = QComboBox()
        self.variable_combo.addItems(["P (MW)", "Q (MVAr)", "V (p.u.)", "Hoek (°)"])
        options_layout.addWidget(variable_label)
        options_layout.addWidget(self.variable_combo)
        
        # Weergave type
        display_label = QLabel("Type:")
        self.display_type_combo = QComboBox()
        self.display_type_combo.addItems(["Grafiek", "Tabel", "Netwerk Diagram", "Real-time Monitor"])
        options_layout.addWidget(display_label)
        options_layout.addWidget(self.display_type_combo)
        
        # Voeg options toe aan main layout
        self.main_layout.addLayout(options_layout)
        
        # Verbind signalen
        self.view_type_combo.currentIndexChanged.connect(self._update_plot)
        self.variable_combo.currentIndexChanged.connect(self._update_plot)
        self.display_type_combo.currentIndexChanged.connect(self._update_plot)
    
    def _create_grid_status(self):
        """Creëer een widget voor de grid status."""
        status_group = QGroupBox("Netwerk Status")
        status_layout = QGridLayout(status_group)
        
        # Rij 1
        status_layout.addWidget(QLabel("Aantal Knooppunten:"), 0, 0)
        self.nodes_label = QLabel("0")
        status_layout.addWidget(self.nodes_label, 0, 1)
        
        status_layout.addWidget(QLabel("Aantal Lijnen:"), 0, 2)
        self.lines_label = QLabel("0")
        status_layout.addWidget(self.lines_label, 0, 3)
        
        # Rij 2
        status_layout.addWidget(QLabel("Totale Belasting:"), 1, 0)
        self.load_label = QLabel("0 MW")
        status_layout.addWidget(self.load_label, 1, 1)
        
        status_layout.addWidget(QLabel("Totale Productie:"), 1, 2)
        self.generation_label = QLabel("0 MW")
        status_layout.addWidget(self.generation_label, 1, 3)
        
        # Rij 3
        status_layout.addWidget(QLabel("Netwerk Frequentie:"), 2, 0)
        self.frequency_label = QLabel("50.00 Hz")
        status_layout.addWidget(self.frequency_label, 2, 1)
        
        status_layout.addWidget(QLabel("Status:"), 2, 2)
        self.status_label = QLabel("Initialiseren...")
        status_layout.addWidget(self.status_label, 2, 3)
        
        # Voeg toe aan main layout
        self.main_layout.addWidget(status_group)
    
    def _create_figure(self):
        """Creëer matplotlib figuur voor visualisatie."""
        # Maak Figure en Canvas
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Voeg canvas toe aan layout
        self.main_layout.addWidget(self.canvas, 1)  # Stretch factor = 1
    
    def _setup_connections(self):
        """Verbind controller signalen."""
        self.controller.data_updated.connect(self.update_from_controller)
    
    def _update_plot(self):
        """Update de plot op basis van geselecteerde opties."""
        # Haal geselecteerde opties op
        view_type = self.view_type_combo.currentText()
        variable = self.variable_combo.currentText()
        display_type = self.display_type_combo.currentText()
        
        # Clear huidige figuur
        self.ax.clear()
        
        # Genereer wat voorbeelddata (in werkelijkheid zou je data van de controller halen)
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        # Bepaal titels en labels op basis van geselecteerde opties
        title = f"{view_type}: {variable}"
        ylabel = variable
        
        # Plot op basis van geselecteerde weergave
        if display_type == "Grafiek":
            self.ax.plot(x, y)
            self.ax.set_xlabel("Tijd (s)")
            self.ax.set_ylabel(ylabel)
            self.ax.set_title(title)
            self.ax.grid(True)
        elif display_type == "Tabel":
            # Voor een tabel zouden we een andere aanpak nodig hebben
            self.ax.text(0.5, 0.5, "Tabelweergave niet beschikbaar in deze demo", 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.ax.axis('off')
        elif display_type == "Netwerk Diagram":
            # Netwerk diagram zou normaal gesproken een specifieke visualisatie zijn
            self.ax.text(0.5, 0.5, "Netwerk Diagram niet beschikbaar in deze demo", 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.ax.axis('off')
        else:  # Real-time Monitor
            self.ax.plot(x[-20:], y[-20:], 'r-')
            self.ax.set_xlabel("Tijd (s)")
            self.ax.set_ylabel(ylabel)
            self.ax.set_title(f"Realtime {variable}")
            self.ax.grid(True)
        
        # Vernieuw canvas
        self.canvas.draw()
    
    def update_from_controller(self):
        """Update de weergave met data van de controller."""
        # In werkelijkheid zou je hier echte data ophalen van de controller
        
        # Update network status labels
        components = self.controller._simulation_data.get("components", [])
        nodes = sum(1 for comp in components if comp.get("type") == "bus")
        lines = sum(1 for comp in components if comp.get("type") == "line")
        
        self.nodes_label.setText(str(nodes))
        self.lines_label.setText(str(lines))
        
        # Voorbeeldupdate voor andere labels
        self.load_label.setText("24.5 MW")
        self.generation_label.setText("25.0 MW")
        self.frequency_label.setText("50.02 Hz")
        
        if self.controller._is_running:
            if self.controller._is_paused:
                self.status_label.setText("Gepauzeerd")
            else:
                self.status_label.setText("In uitvoering")
        else:
            self.status_label.setText("Gestopt")
        
        # Update plot
        self._update_plot() 