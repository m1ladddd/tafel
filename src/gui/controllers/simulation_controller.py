from PySide6.QtCore import QObject, Signal, Slot, QTimer
import json
import os
import sys

class SimulationController(QObject):
    """Controller voor het beheren van de simulatie."""
    
    # Signalen voor communicatie met de UI
    status_changed = Signal(str)
    data_updated = Signal()
    simulation_finished = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, mqtt_client=None):
        super().__init__()
        self._is_running = False
        self._is_paused = False
        self._config = self.get_default_configuration()
        self._simulation_data = {}
        self._mqtt_client = mqtt_client
        
        # Huidige scenario en snapshot info
        self._current_scenario = None
        self._current_snapshot_index = 0
        self._available_scenarios = []
        
        # Timer voor simulatieupdates
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_simulation)
        self._timer.setInterval(1000)  # Update elke seconde standaard
        
        # Initialiseer simulatiedata
        self._initialize_simulation_data()
    
    def _initialize_simulation_data(self):
        """Initialiseer de simulatiedata."""
        # Basisstructuur voor simulatiegegevens
        self._simulation_data = {
            "time": 0.0,
            "step": 0,
            "components": [],
            "snapshots": [],
            "results": {}
        }
    
    def get_default_configuration(self):
        """Geef de standaardconfiguratie terug."""
        return {
            "general": {
                "name": "Nieuwe Simulatie",
                "type": "Smart Grid",
                "description": "Smart Grid tafelsimulatie",
                "log_level": "info"
            },
            "simulation": {
                "timestep": 1.0,  # Seconden per snapshot
                "max_time": 60.0,  # Totale simulatietijd
                "auto_advance": True  # Automatisch naar volgende snapshot
            },
            "visualization": {
                "framerate": 30,
                "colorscheme": "Smart Grid",
                "background_color": "Zwart",
                "show_grid": True,
                "animation_speed": 1.0
            }
        }
    
    def set_mqtt_client(self, mqtt_client):
        """Stel de MQTT client in voor communicatie met de backend."""
        self._mqtt_client = mqtt_client
    
    def set_configuration(self, config):
        """Update de configuratie."""
        self._config.update(config)
        
        # Update afhankelijke instellingen
        if "simulation" in config and "timestep" in config["simulation"]:
            self._timer.setInterval(int(config["simulation"]["timestep"] * 1000))
        
        # Als verbonden met MQTT, stuur configuratie update
        if self._mqtt_client and self._mqtt_client.is_connected():
            try:
                payload = json.dumps({"config": self._config})
                self._mqtt_client.publish("sgt/command/config/update", payload)
                return True
            except Exception as e:
                self.error_occurred.emit(f"Fout bij versturen configuratie via MQTT: {e}")
                return False
        return True
    
    def get_current_configuration(self):
        """Geef de huidige configuratie terug."""
        return self._config
    
    def scan_available_scenarios(self):
        """Scan voor beschikbare scenario's in de scenario mappen."""
        try:
            # Project root bepalen (2 niveaus omhoog van src/gui/controllers)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            scenarios_static_dir = os.path.join(project_root, 'scenarios', 'static')
            scenarios_dynamic_dir = os.path.join(project_root, 'scenarios', 'dynamic')
            
            # Lijst van scenario's
            scenarios = []
            
            # Statische scenario's doorzoeken
            if os.path.exists(scenarios_static_dir):
                for filename in os.listdir(scenarios_static_dir):
                    if filename.endswith('.json'):
                        scenarios.append({
                            'name': filename.replace('.json', ''),
                            'path': os.path.join(scenarios_static_dir, filename),
                            'type': 'static'
                        })
            
            # Dynamische scenario's doorzoeken
            if os.path.exists(scenarios_dynamic_dir):
                for filename in os.listdir(scenarios_dynamic_dir):
                    if filename.endswith('.json'):
                        scenarios.append({
                            'name': filename.replace('.json', ''),
                            'path': os.path.join(scenarios_dynamic_dir, filename),
                            'type': 'dynamic'
                        })
            
            self._available_scenarios = scenarios
            return scenarios
            
        except Exception as e:
            self.error_occurred.emit(f"Fout bij scannen scenario's: {e}")
            return []
    
    def load_scenario(self, scenario_path):
        """Laad een scenario via MQTT."""
        if not self._mqtt_client or not self._mqtt_client.is_connected():
            self.error_occurred.emit("Geen MQTT verbinding voor het laden van scenario")
            return False
        
        try:
            # Stuur opdracht naar backend om scenario te laden
            payload = json.dumps({"scenario_file": scenario_path})
            self._mqtt_client.publish("sgt/command/scenario/load", payload)
            self._current_scenario = scenario_path
            self.status_changed.emit(f"Scenario laden verzonden: {os.path.basename(scenario_path)}")
            return True
        except Exception as e:
            self.error_occurred.emit(f"Fout bij laden scenario: {e}")
            return False
    
    def start_simulation(self):
        """Start de simulatie."""
        if self._is_running and not self._is_paused:
            return False  # Al actief
        
        if self._is_paused:
            # Hervat simulatie
            self._is_paused = False
            if self._config["simulation"]["auto_advance"]:
                self._timer.start()
            self.status_changed.emit("Simulatie hervat")
        else:
            # Start nieuwe simulatie
            self._is_running = True
            if self._config["simulation"]["auto_advance"]:
                self._timer.start()
            
            # Stuur start commando via MQTT
            if self._mqtt_client and self._mqtt_client.is_connected():
                self._mqtt_client.publish("sgt/command/simulation/start", "{}")
            
            self.status_changed.emit("Simulatie gestart")
        
        return True
    
    def pause_simulation(self):
        """Pauzeer de simulatie."""
        if not self._is_running or self._is_paused:
            return False
        
        self._is_paused = True
        self._timer.stop()
        
        # Stuur pauzeer commando via MQTT
        if self._mqtt_client and self._mqtt_client.is_connected():
            self._mqtt_client.publish("sgt/command/simulation/pause", "{}")
        
        self.status_changed.emit("Simulatie gepauzeerd")
        return True
    
    def stop_simulation(self):
        """Stop de simulatie."""
        if not self._is_running:
            return False
        
        self._is_running = False
        self._is_paused = False
        self._timer.stop()
        
        # Stuur stop commando via MQTT
        if self._mqtt_client and self._mqtt_client.is_connected():
            self._mqtt_client.publish("sgt/command/simulation/stop", "{}")
        
        self.status_changed.emit("Simulatie gestopt")
        return True
    
    def set_snapshot_index(self, index):
        """Stel de snapshot index in."""
        if not self._is_running:
            return False
        
        # Valideer index
        if index < 0:
            index = 0
        
        self._current_snapshot_index = index
        
        # Stuur index update via MQTT
        if self._mqtt_client and self._mqtt_client.is_connected():
            payload = json.dumps({"index": index})
            self._mqtt_client.publish("sgt/command/simulation/set_index", payload)
        
        self.status_changed.emit(f"Snapshot index gezet: {index}")
        self.data_updated.emit()
        return True
    
    def next_snapshot(self):
        """Ga naar de volgende snapshot."""
        return self.set_snapshot_index(self._current_snapshot_index + 1)
    
    def previous_snapshot(self):
        """Ga naar de vorige snapshot."""
        return self.set_snapshot_index(self._current_snapshot_index - 1)
    
    def set_line_status(self, table_idx, line_id, status):
        """Stel de status van een lijn in."""
        if not self._mqtt_client or not self._mqtt_client.is_connected():
            self.error_occurred.emit("Geen MQTT verbinding voor het instellen van lijnstatus")
            return False
        
        try:
            payload = json.dumps({
                "table_idx": table_idx,
                "line_id": line_id,
                "status": status
            })
            self._mqtt_client.publish("sgt/command/line/set_status", payload)
            self.status_changed.emit(f"Lijnstatus update verzonden: Tabel {table_idx}, Lijn {line_id}, Status {status}")
            return True
        except Exception as e:
            self.error_occurred.emit(f"Fout bij instellen lijnstatus: {e}")
            return False
    
    def _update_simulation(self):
        """Update de simulatie (timer callback)."""
        if not self._is_running or self._is_paused:
            return
        
        # In dit voorbeeld gaan we simpelweg naar de volgende snapshot
        self.next_snapshot() 