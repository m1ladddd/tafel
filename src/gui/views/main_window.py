from PySide6.QtWidgets import (QMainWindow, QDockWidget, QToolBar, QStatusBar, 
                              QMessageBox, QFileDialog, QWidget, QVBoxLayout, 
                              QTextEdit, QInputDialog)
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QAction, QIcon
import os
import json

from .simulation_view import SimulationView
from .config_panel import ConfigPanel
from ..mqtt_client import MqttClientThread
from ..controllers.simulation_controller import SimulationController

class MainWindow(QMainWindow):
    # Signalen voor thread-safe communicatie met de UI
    message_received_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        # Venster eigenschappen instellen
        self.setWindowTitle("Smart Grid Simulatie Controller")
        self.resize(1200, 800)
        
        # Controller en MQTT client instellen
        self.controller = SimulationController()
        self._setup_mqtt()
        self.controller.set_mqtt_client(self.mqtt_thread)
        
        # UI elementen instellen
        self._create_central_widget()
        self._create_dock_widgets()
        self._create_toolbar()
        self._create_statusbar()
        self._create_menu()
        
        # Verbind controller signalen met UI
        self._setup_connections()
        
        # Scan beschikbare scenario's
        self.controller.scan_available_scenarios()
        
        self.statusBar().showMessage("Verbinden met MQTT broker...")
    
    def _setup_mqtt(self):
        """Zet de MQTT client thread op en verbind signalen."""
        self.mqtt_thread = MqttClientThread()
        # Verbind signalen van MQTT thread met slots in deze GUI thread
        self.mqtt_thread.connection_status_signal.connect(self.update_status_label)
        self.mqtt_thread.message_signal.connect(self.handle_incoming_message)
        # Verbind eigen signalen voor UI updates vanuit slots
        self.message_received_signal.connect(self.append_log_message)
        # Start de MQTT thread
        self.mqtt_thread.start()
    
    def _create_central_widget(self):
        """Creëer het centrale widget voor de simulatieweergave."""
        self.simulation_view = SimulationView(self.controller)
        self.setCentralWidget(self.simulation_view)
    
    def _create_dock_widgets(self):
        """Creëer de dock widgets voor configuratie."""
        # Configuratie paneel
        config_dock = QDockWidget("Configuratie", self)
        config_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.config_panel = ConfigPanel(self.controller)
        config_dock.setWidget(self.config_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, config_dock)
        
        # Log paneel
        log_dock = QDockWidget("Log Berichten", self)
        log_dock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        log_layout.addWidget(self.log_output)
        log_dock.setWidget(log_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)
    
    def _create_toolbar(self):
        """Creëer de toolbar met simulatiebesturingsknoppen."""
        toolbar = QToolBar("Simulatie besturing", self)
        self.addToolBar(toolbar)
        
        # Start simulatie
        start_action = QAction("Start", self)
        start_action.triggered.connect(self._on_start_simulation)
        toolbar.addAction(start_action)
        
        # Pauzeer simulatie
        pause_action = QAction("Pauzeer", self)
        pause_action.triggered.connect(self._on_pause_simulation)
        toolbar.addAction(pause_action)
        
        # Stop simulatie
        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self._on_stop_simulation)
        toolbar.addAction(stop_action)
        
        toolbar.addSeparator()
        
        # Vorige snapshot
        prev_action = QAction("Vorige", self)
        prev_action.triggered.connect(self._on_prev_snapshot)
        toolbar.addAction(prev_action)
        
        # Volgende snapshot
        next_action = QAction("Volgende", self)
        next_action.triggered.connect(self._on_next_snapshot)
        toolbar.addAction(next_action)
    
    def _create_statusbar(self):
        """Creëer de statusbalk onderaan het venster."""
        self.setStatusBar(QStatusBar(self))
    
    def _create_menu(self):
        """Creëer het menu van de applicatie."""
        menu_bar = self.menuBar()
        
        # Bestand menu
        file_menu = menu_bar.addMenu("Bestand")
        
        # Scenario laden
        load_scenario_action = QAction("Scenario laden", self)
        load_scenario_action.triggered.connect(self._on_load_scenario)
        file_menu.addAction(load_scenario_action)
        
        # Configuratie laden
        load_config_action = QAction("Configuratie laden", self)
        load_config_action.triggered.connect(self._on_load_config)
        file_menu.addAction(load_config_action)
        
        # Configuratie opslaan
        save_config_action = QAction("Configuratie opslaan", self)
        save_config_action.triggered.connect(self._on_save_config)
        file_menu.addAction(save_config_action)
        
        file_menu.addSeparator()
        
        # Resultaten exporteren
        export_action = QAction("Resultaten exporteren", self)
        export_action.triggered.connect(self._on_export_results)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Afsluiten
        exit_action = QAction("Afsluiten", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Weergave menu
        view_menu = menu_bar.addMenu("Weergave")
        
        # Config paneel tonen/verbergen
        toggle_config_action = QAction("Configuratiepaneel", self)
        toggle_config_action.setCheckable(True)
        toggle_config_action.setChecked(True)
        view_menu.addAction(toggle_config_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # Over
        about_action = QAction("Over...", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _setup_connections(self):
        """Verbind signalen van de controller met slots in het hoofdvenster."""
        self.controller.status_changed.connect(self.update_status_label)
        self.controller.error_occurred.connect(self._on_error)
        self.controller.data_updated.connect(self._on_data_updated)
        self.controller.simulation_finished.connect(self._on_simulation_finished)
    
    @Slot()
    def _on_start_simulation(self):
        """Start of hervat de simulatie."""
        self.controller.start_simulation()
    
    @Slot()
    def _on_pause_simulation(self):
        """Pauzeer de simulatie."""
        self.controller.pause_simulation()
    
    @Slot()
    def _on_stop_simulation(self):
        """Stop de simulatie."""
        self.controller.stop_simulation()
    
    @Slot()
    def _on_prev_snapshot(self):
        """Ga naar de vorige snapshot."""
        self.controller.previous_snapshot()
    
    @Slot()
    def _on_next_snapshot(self):
        """Ga naar de volgende snapshot."""
        self.controller.next_snapshot()
    
    @Slot(str)
    def _on_error(self, error_message):
        """Toon foutmelding."""
        QMessageBox.critical(self, "Fout", error_message)
        self.message_received_signal.emit(f"FOUT: {error_message}")
    
    @Slot()
    def _on_data_updated(self):
        """Reageer op data-updates van de controller."""
        self.simulation_view.update_from_controller()
    
    @Slot()
    def _on_simulation_finished(self):
        """Reageer wanneer simulatie is voltooid."""
        self.statusBar().showMessage("Simulatie voltooid")
        QMessageBox.information(self, "Voltooid", "Simulatie is volledig uitgevoerd")
    
    @Slot()
    def _on_load_scenario(self):
        """Laad een scenario via bestandsdialoog."""
        # Geef beschikbare scenario's weer in een dialoogvenster
        scenarios = self.controller.scan_available_scenarios()
        if not scenarios:
            QMessageBox.warning(self, "Geen scenario's gevonden", 
                               "Er zijn geen scenario bestanden gevonden in de scenarios map.")
            return
        
        # Gebruik QDialog om een scenario te selecteren
        scenario_list = [f"{s['name']} ({s['type']})" for s in scenarios]
        selected_scenario, ok = QInputDialog.getItem(self, "Selecteer Scenario", 
                                                   "Beschikbare scenario's:", 
                                                   scenario_list, 0, False)
        if ok and selected_scenario:
            # Vind het geselecteerde scenario in de lijst
            selected_index = scenario_list.index(selected_scenario)
            scenario_path = scenarios[selected_index]['path']
            
            if self.controller.load_scenario(scenario_path):
                self.statusBar().showMessage(f"Scenario geladen: {selected_scenario}")
            else:
                self.statusBar().showMessage("Kon scenario niet laden")
    
    @Slot()
    def _on_load_config(self):
        """Laad configuratie."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Configuratie laden", "", "JSON bestanden (*.json);;Alle bestanden (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                self.controller.set_configuration(config)
                self.config_panel.update_from_controller()
                self.statusBar().showMessage(f"Configuratie geladen van {file_path}")
                self.message_received_signal.emit(f"Configuratie geladen van {file_path}")
            except Exception as e:
                self._on_error(f"Kon configuratie niet laden: {str(e)}")
    
    @Slot()
    def _on_save_config(self):
        """Sla configuratie op."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Configuratie opslaan", "", "JSON bestanden (*.json);;Alle bestanden (*)"
        )
        if file_path:
            try:
                config = self.controller.get_current_configuration()
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                self.statusBar().showMessage(f"Configuratie opgeslagen naar {file_path}")
                self.message_received_signal.emit(f"Configuratie opgeslagen naar {file_path}")
            except Exception as e:
                self._on_error(f"Kon configuratie niet opslaan: {str(e)}")
    
    @Slot()
    def _on_export_results(self):
        """Exporteer resultaten."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Resultaten exporteren", "", 
            "CSV bestanden (*.csv);;Excel bestanden (*.xlsx);;Alle bestanden (*)"
        )
        if file_path:
            try:
                self.controller.export_results(file_path)
                self.statusBar().showMessage(f"Resultaten geëxporteerd naar {file_path}")
                self.message_received_signal.emit(f"Resultaten geëxporteerd naar {file_path}")
            except Exception as e:
                self._on_error(f"Kon resultaten niet exporteren: {str(e)}")
    
    @Slot()
    def _on_about(self):
        """Toon info over de applicatie."""
        QMessageBox.about(self, "Over Smart Grid Simulatie Controller",
                         "Smart Grid Simulatie Controller\n\n"
                         "Een gebruiksvriendelijke interface voor het aansturen van Smart Grid tafelsimulaties.\n\n"
                         "Gemaakt met PySide6 (Qt voor Python)")
    
    @Slot(str)
    def update_status_label(self, status_message):
        """Update de statusbalk met een nieuw bericht."""
        self.statusBar().showMessage(status_message)
    
    @Slot(str)
    def append_log_message(self, message):
        """Voeg een bericht toe aan het logpaneel."""
        self.log_output.append(message)
    
    @Slot(str, str)
    def handle_incoming_message(self, topic, payload):
        """Verwerk inkomende MQTT berichten."""
        # Log bericht
        log_message = f"MQTT RX | {topic}: {payload}"
        self.message_received_signal.emit(log_message)
        
        # Verwerk bericht op basis van topic
        try:
            if topic.startswith("sgt/status/components"):
                # Update componentlijst
                try:
                    data = json.loads(payload)
                    if isinstance(data, list):
                        # Stuur component data naar controller
                        self.controller._simulation_data["components"] = data
                        self.controller.data_updated.emit()
                except json.JSONDecodeError:
                    self.message_received_signal.emit(f"FOUT: Ongeldige JSON in components bericht")
            
            elif topic.startswith("sgt/result/"):
                # Verwerk simulatieresultaten
                try:
                    data = json.loads(payload)
                    if isinstance(data, dict):
                        # Stuur resultaten naar controller
                        result_type = topic.split('/')[-1]  # Laatste deel van topic
                        self.controller._simulation_data["results"][result_type] = data
                        self.controller.data_updated.emit()
                except json.JSONDecodeError:
                    self.message_received_signal.emit(f"FOUT: Ongeldige JSON in result bericht")
            
            elif topic.startswith("sgt/log/"):
                # Log berichten direct weergeven
                level = topic.split('/')[-1]  # Laatste deel van topic (debug/info/warning/error)
                self.message_received_signal.emit(f"{level.upper()}: {payload}")
            
        except Exception as e:
            self.message_received_signal.emit(f"FOUT bij verwerken MQTT bericht: {str(e)}")
    
    def closeEvent(self, event):
        """Zorg dat de MQTT thread netjes stopt als het venster sluit."""
        print("Hoofdvenster sluiten, MQTT thread stoppen...")
        self.mqtt_thread.stop()
        if not self.mqtt_thread.wait(2000):  # Wacht max 2 seconden
            print("Waarschuwing: MQTT thread stopte niet binnen timeout.")
        event.accept()