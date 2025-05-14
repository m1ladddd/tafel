from PySide6.QtCore import QThread, Signal
import time

class MqttClientThread(QThread):
    """Thread voor MQTT communicatie."""
    connection_status_signal = Signal(str)
    message_signal = Signal(str, str)  # topic, payload
    
    def __init__(self, broker="localhost", port=1883):
        super().__init__()
        self.broker = broker
        self.port = port
        self._running = False
        self._connected = False
    
    def run(self):
        """Hoofdloop van de thread."""
        self._running = True
        self.connection_status_signal.emit("MQTT: verbinding maken...")
        
        # Simuleer verbinding
        time.sleep(1)  
        self._connected = True
        self.connection_status_signal.emit("MQTT: verbonden met broker")
        
        # Voer main loop uit
        while self._running:
            time.sleep(0.1)  # Verminder CPU gebruik
        
        self._connected = False
        self.connection_status_signal.emit("MQTT: verbinding verbroken")
    
    def stop(self):
        """Stop de thread."""
        self._running = False
        
    def is_connected(self):
        """Controleer of client verbonden is met de broker."""
        return self._connected
        
    def publish(self, topic, payload, qos=0, retain=False):
        """Publiceer een bericht op een topic."""
        if self._connected:
            print(f"MQTT PUBLISH: {topic} - {payload}")
            return True
        return False 