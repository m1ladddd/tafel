# 🎯 Smart Grid Table GUI Interface Gids

## 📖 **Overzicht**
Dit Smart Grid Table project heeft **geen Flutter/Dart GUI**, maar gebruikt een **MQTT-gebaseerde architectuur** met verschillende interface opties.

## 🚀 **Beschikbare GUI Opties:**

### **1. 📊 Jupyter Notebook GUI (RECOMMENDED)**
Interactive matplotlib-based GUI met widgets:

```bash
# Start Jupyter notebook
jupyter notebook tools/Matplotlib_gui.ipynb

# Of direct jupyter lab
jupyter lab
```

**Features:**
- ✅ Real-time data visualization
- ✅ Interactive controls (dropdowns, buttons)
- ✅ MQTT data streaming
- ✅ Voltage/current/power plots

### **2. 🗂️ Console Interface**
Command-line interface:

```bash
# Start application in simulation mode
python Application.py --simulation

# Available commands:
help                    # Show all commands
scenario list           # List available scenarios
table list             # Show connected tables
calculate              # Run power flow calculation
mode set pf            # Set calculation mode
```

### **3. 📡 MQTT Dashboard (External)**
Connect external MQTT clients:

```bash
# MQTT Topics:
SmartDemoTable2/GUI/Outgoing     # Data from application
SmartDemoTable2/GUI/Ingoing      # Commands to application
SmartDemoTable2/Jupyter/Outgoing # Jupyter data
SmartDemoTable2/Jupyter/Ingoing  # Jupyter commands

# MQTT Broker: localhost:1883 (in simulation mode)
```

### **4. 🎮 Virtual Table Simulator**
Generates test RFID data:

```bash
python tools/virtual_table.py
```

## **🔧 Setup Instructions:**

### **Dependencies Installation:**
```bash
# Install required packages
pip install seaborn ipywidgets jupyter

# Or update requirements.txt:
echo "seaborn>=0.13.0" >> requirements.txt
echo "ipywidgets>=8.0.0" >> requirements.txt
echo "jupyter>=1.0.0" >> requirements.txt
```

### **Start Complete System:**

1. **Terminal 1 - Backend:**
```bash
python Application.py --simulation
```

2. **Terminal 2 - GUI:**
```bash
jupyter notebook tools/Matplotlib_gui.ipynb
```

3. **Terminal 3 - Data Generator:**
```bash
python tools/virtual_table.py
```

## **📱 MQTT Client Apps (External)**

Voor mobile/web interfaces kun je externe MQTT clients gebruiken:

### **Desktop MQTT Clients:**
- **MQTT Explorer** (Visual MQTT client)
- **mosquitto_pub/sub** (Command line)
- **HiveMQ WebSocket Client** (Web-based)

### **Mobile MQTT Clients:**
- **MyMQTT** (iOS/Android)
- **MQTT Dashboard** (Android)
- **IoT MQTT Panel** (Android)

## **🌐 Web-based Alternatives:**

### **Node-RED Dashboard:**
```bash
# Install Node-RED
npm install -g node-red

# Add dashboard
npm install node-red-dashboard

# Start Node-RED
node-red

# Navigate to: http://localhost:1880
# Add MQTT nodes to connect to SmartDemoTable2 topics
```

### **Grafana + InfluxDB:**
```bash
# For advanced data visualization
# Connect via MQTT -> InfluxDB -> Grafana pipeline
```

## **🎨 Creating Your Own Flutter GUI:**

Als je een Flutter GUI wilt maken:

### **1. Create Flutter Project:**
```bash
flutter create smart_grid_gui
cd smart_grid_gui
```

### **2. Add MQTT Dependency:**
```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  mqtt_client: ^10.0.0
  charts_flutter: ^0.12.0
```

### **3. Basic MQTT Connection:**
```dart
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

class SmartGridMQTT {
  late MqttServerClient client;
  
  Future<void> connect() async {
    client = MqttServerClient('localhost', '');
    client.port = 1883;
    
    await client.connect();
    
    // Subscribe to data
    client.subscribe('SmartDemoTable2/GUI/Outgoing', MqttQos.atMostOnce);
    
    // Listen for data
    client.updates!.listen((List<MqttReceivedMessage<MqttMessage>> c) {
      final MqttPublishMessage message = c[0].payload as MqttPublishMessage;
      final payload = MqttPublishPayload.bytesToStringAsString(message.payload.message);
      
      // Process JSON data
      print('Received: $payload');
    });
  }
  
  void sendCommand(String command) {
    final builder = MqttClientPayloadBuilder();
    builder.addString(command);
    client.publishMessage('SmartDemoTable2/GUI/Ingoing', MqttQos.atMostOnce, builder.payload!);
  }
}
```

## **🎯 Conclusion:**

Het Smart Grid Table project is **niet gebouwd voor Flutter**, maar gebruikt:
- 🐍 **Python Backend** (Smart Grid calculations)
- 📡 **MQTT Communication** (Real-time data)
- 📊 **Jupyter Widgets** (Interactive GUI)
- 🗂️ **Console Interface** (Command line)

Voor een moderne mobile GUI kun je:
1. ✅ **Gebruik Jupyter Notebook** (easiest)
2. ✅ **Build custom Flutter app** met MQTT
3. ✅ **Use Node-RED dashboard** (web-based)
4. ✅ **Connect via external MQTT clients**

🚀 **Recommended: Start met Jupyter Notebook voor immediate visualization!** 