from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
                              QDoubleSpinBox, QSpinBox, QComboBox, QPushButton,
                              QGroupBox, QCheckBox, QSlider, QScrollArea)
from PySide6.QtCore import Qt, Slot, Signal

class ConfigPanel(QWidget):
    """Widget voor het configureren van de simulatie."""
    
    config_changed = Signal(dict)  # Signaal wanneer configuratie is gewijzigd
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        # Maak een scrollgebied voor als er veel configuratie-opties zijn
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Maak een container voor alle configuratie-opties
        config_container = QWidget()
        main_layout = QVBoxLayout(config_container)
        
        # Voeg configuratie groepen toe
        main_layout.addWidget(self._create_general_config_group())
        main_layout.addWidget(self._create_simulation_params_group())
        main_layout.addWidget(self._create_visualization_params_group())
        
        # Knoppen onderaan
        buttons_layout = QVBoxLayout()
        apply_button = QPushButton("Toepassen")
        apply_button.clicked.connect(self._on_apply)
        reset_button = QPushButton("Reset naar standaardwaarden")
        reset_button.clicked.connect(self._on_reset_defaults)
        
        buttons_layout.addWidget(apply_button)
        buttons_layout.addWidget(reset_button)
        main_layout.addLayout(buttons_layout)
        
        # Voeg ruimte toe aan het einde
        main_layout.addStretch()
        
        # Stel de container in als het widget van het scrollgebied
        scroll_area.setWidget(config_container)
        
        # Maak een hoofdlayout voor dit widget
        layout = QVBoxLayout(self)
        layout.addWidget(scroll_area)
        
        # Initialiseer configuratiewaarden
        self.update_from_controller()
    
    def _create_general_config_group(self):
        """Maak een groep voor algemene configuratie."""
        group = QGroupBox("Algemene Instellingen")
        layout = QFormLayout(group)
        
        # Simulatienaam
        self.sim_name_edit = QLineEdit()
        layout.addRow("Simulatie Naam:", self.sim_name_edit)
        
        # Simulatietype
        self.sim_type_combo = QComboBox()
        self.sim_type_combo.addItems(["Power Flow", "Dynamisch", "Fault Analysis", "Harmonics"])
        layout.addRow("Simulatie Type:", self.sim_type_combo)
        
        # Beschrijving
        self.description_edit = QLineEdit()
        layout.addRow("Beschrijving:", self.description_edit)
        
        # Log niveau
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        layout.addRow("Log Niveau:", self.log_level_combo)
        
        # Random seed
        self.random_seed_spin = QSpinBox()
        self.random_seed_spin.setMinimum(0)
        self.random_seed_spin.setMaximum(999999)
        layout.addRow("Random Seed:", self.random_seed_spin)
        
        return group
    
    def _create_simulation_params_group(self):
        """Maak een groep voor simulatieparameters."""
        group = QGroupBox("Simulatie Parameters")
        layout = QFormLayout(group)
        
        # Tijdstap
        self.timestep_spin = QDoubleSpinBox()
        self.timestep_spin.setMinimum(0.001)
        self.timestep_spin.setMaximum(10.0)
        self.timestep_spin.setSingleStep(0.01)
        self.timestep_spin.setValue(1.0)
        self.timestep_spin.setSuffix(" s")
        layout.addRow("Tijdstap:", self.timestep_spin)
        
        # Simulatietijd
        self.sim_time_spin = QDoubleSpinBox()
        self.sim_time_spin.setMinimum(1.0)
        self.sim_time_spin.setMaximum(3600.0)
        self.sim_time_spin.setSingleStep(1.0)
        self.sim_time_spin.setValue(60.0)
        self.sim_time_spin.setSuffix(" s")
        layout.addRow("Simulatietijd:", self.sim_time_spin)
        
        # Aantal agents
        self.num_agents_spin = QSpinBox()
        self.num_agents_spin.setMinimum(1)
        self.num_agents_spin.setMaximum(10000)
        self.num_agents_spin.setValue(10)
        layout.addRow("Aantal agents:", self.num_agents_spin)
        
        # Ruimtelijke afmetingen
        self.space_x_spin = QDoubleSpinBox()
        self.space_x_spin.setMinimum(1.0)
        self.space_x_spin.setMaximum(1000.0)
        self.space_x_spin.setValue(100.0)
        layout.addRow("Ruimte X:", self.space_x_spin)
        
        self.space_y_spin = QDoubleSpinBox()
        self.space_y_spin.setMinimum(1.0)
        self.space_y_spin.setMaximum(1000.0)
        self.space_y_spin.setValue(100.0)
        layout.addRow("Ruimte Y:", self.space_y_spin)
        
        # Temperatuur
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setMinimum(0.0)
        self.temp_spin.setMaximum(1000.0)
        self.temp_spin.setValue(300.0)
        self.temp_spin.setSuffix(" K")
        layout.addRow("Temperatuur:", self.temp_spin)
        
        # Zwaartekracht aan/uit
        self.gravity_check = QCheckBox()
        layout.addRow("Zwaartekracht:", self.gravity_check)
        
        # Botsingen aan/uit
        self.collisions_check = QCheckBox()
        layout.addRow("Botsingen:", self.collisions_check)
        
        # Automatisch vooruit aan/uit
        self.auto_advance_check = QCheckBox()
        self.auto_advance_check.setChecked(True)  # standaard aan
        layout.addRow("Automatisch vooruit:", self.auto_advance_check)
        
        return group
    
    def _create_visualization_params_group(self):
        """Maak een groep voor visualisatieparameters."""
        group = QGroupBox("Visualisatie Parameters")
        layout = QFormLayout(group)
        
        # Framerate
        self.framerate_spin = QSpinBox()
        self.framerate_spin.setMinimum(1)
        self.framerate_spin.setMaximum(120)
        self.framerate_spin.setValue(30)
        self.framerate_spin.setSuffix(" fps")
        layout.addRow("Framerate:", self.framerate_spin)
        
        # Kleurenschema
        self.colorscheme_combo = QComboBox()
        self.colorscheme_combo.addItems(["Viridis", "Plasma", "Inferno", "Magma", "Cividis"])
        layout.addRow("Kleurenschema:", self.colorscheme_combo)
        
        # Deeltjesgrootte
        self.particle_size_slider = QSlider(Qt.Horizontal)
        self.particle_size_slider.setMinimum(1)
        self.particle_size_slider.setMaximum(20)
        self.particle_size_slider.setValue(5)
        layout.addRow("Deeltjesgrootte:", self.particle_size_slider)
        
        # Lijndikte
        self.line_width_slider = QSlider(Qt.Horizontal)
        self.line_width_slider.setMinimum(1)
        self.line_width_slider.setMaximum(10)
        self.line_width_slider.setValue(2)
        layout.addRow("Lijndikte:", self.line_width_slider)
        
        # Achtergrondkleur
        self.bg_color_combo = QComboBox()
        self.bg_color_combo.addItems(["Zwart", "Wit", "Grijs", "Blauw", "Groen"])
        layout.addRow("Achtergrondkleur:", self.bg_color_combo)
        
        return group
    
    @Slot()
    def _on_apply(self):
        """Pas de configuratie toe."""
        # Verzamel alle configuratiewaarden
        config = {
            "general": {
                "name": self.sim_name_edit.text(),
                "type": self.sim_type_combo.currentText(),
                "description": self.description_edit.text(),
                "log_level": self.log_level_combo.currentText().lower(),
                "random_seed": self.random_seed_spin.value()
            },
            "simulation": {
                "timestep": self.timestep_spin.value(),
                "max_time": self.sim_time_spin.value(),
                "num_agents": self.num_agents_spin.value(),
                "space_x": self.space_x_spin.value(),
                "space_y": self.space_y_spin.value(),
                "temperature": self.temp_spin.value(),
                "gravity": self.gravity_check.isChecked(),
                "collisions": self.collisions_check.isChecked(),
                "auto_advance": self.auto_advance_check.isChecked()
            },
            "visualization": {
                "framerate": self.framerate_spin.value(),
                "colorscheme": self.colorscheme_combo.currentText(),
                "particle_size": self.particle_size_slider.value(),
                "line_width": self.line_width_slider.value(),
                "background_color": self.bg_color_combo.currentText()
            }
        }
        
        # Stuur de configuratie naar de controller
        self.controller.set_configuration(config)
        
        # Emit signaal dat configuratie is gewijzigd
        self.config_changed.emit(config)
    
    @Slot()
    def _on_reset_defaults(self):
        """Reset naar standaardwaarden."""
        config = self.controller.get_default_configuration()
        self.update_from_config(config)
    
    def update_from_controller(self):
        """Update UI op basis van controller data."""
        # Vraag huidige configuratie op van controller
        config = self.controller.get_current_configuration()
        
        # Update UI met deze configuratie
        self.update_from_config(config)
    
    def update_from_config(self, config):
        """Update UI met gegeven configuratie."""
        # Algemene instellingen
        general = config.get("general", {})
        self.sim_name_edit.setText(general.get("name", "Nieuwe Simulatie"))
        self.sim_type_combo.setCurrentText(general.get("type", "Power Flow"))
        self.description_edit.setText(general.get("description", ""))
        self.log_level_combo.setCurrentText(general.get("log_level", "info").capitalize())
        self.random_seed_spin.setValue(general.get("random_seed", 42))
        
        # Simulatie parameters
        sim = config.get("simulation", {})
        self.timestep_spin.setValue(sim.get("timestep", 1.0))
        self.sim_time_spin.setValue(sim.get("max_time", 60.0))
        self.num_agents_spin.setValue(sim.get("num_agents", 10))
        self.space_x_spin.setValue(sim.get("space_x", 100.0))
        self.space_y_spin.setValue(sim.get("space_y", 100.0))
        self.temp_spin.setValue(sim.get("temperature", 300.0))
        self.gravity_check.setChecked(sim.get("gravity", False))
        self.collisions_check.setChecked(sim.get("collisions", False))
        self.auto_advance_check.setChecked(sim.get("auto_advance", True))
        
        # Visualisatie parameters
        vis = config.get("visualization", {})
        self.framerate_spin.setValue(vis.get("framerate", 30))
        self.colorscheme_combo.setCurrentText(vis.get("colorscheme", "Viridis"))
        self.particle_size_slider.setValue(vis.get("particle_size", 5))
        self.line_width_slider.setValue(vis.get("line_width", 2))
        self.bg_color_combo.setCurrentText(vis.get("background_color", "Zwart")) 