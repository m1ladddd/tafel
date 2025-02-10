# **Firmware update guide**

This guide is made for users of the *Smart Grid Table*, a project created by a group of students from the [HAN](https://www.hanuniversity.com/en/) in Arnhem. The document explains how to run the Smart Grid Table in Standalone or Online mode.

## **Overview**
This document is split into the following sections:
- [**Firmware update guide**](#firmware-update-guide)
  - [**Overview**](#overview)
  - [**Standalone mode**](#standalone-mode)
    - [**Essentials**](#essentials)
    - [**Step by step instructions**](#step-by-step-instructions)
  - [**Online mode**](#online-mode)
    - [**Essentials**](#essentials-1)
    - [**Step by step instructions**](#step-by-step-instructions-1)

## **Standalone mode**
This part is for running the Smart Grid Table in Standalone mode.

### **Essentials**
The next essentials are needed:

- Complete Smart Grid Table set.
- Access point *Tenda2*
- A host PC with:
  - Smart Grid Table simulation program.
  - Mosquitto MQTT broker.

### **Step by step instructions**

1. Power on the *Tenda2* access point.
2. Power on the Smart Grid Table set.
3. Wait until all the LEDs have turned green.
4. Start the host PC.
5. Connect to the *Tenda2* network.
6. Start up a terminal on the host PC.
7. Navigate to the *sgt-simulation* folder.
8. Open *config.json* and make sure the next lines are set:
```
"local_setup": true,
"mqtt_config_name": "local",
```

9. Make sure the Mosquitto broker is running using:
```
service mosquitto status
```

This should output the following status:
```
● mosquitto.service - Mosquitto MQTT Broker
     Loaded: loaded (/lib/systemd/system/mosquitto.service; enabled; vendor preset: enabled)
     Active: active (running)
```

10. Start the Smart Grid Table simulation program with:
```
venv/bin/python3 Application.py
```

11.  Wait until all Smart Grid Table tiles are connected.

   
## **Online mode**
This part is for running the Smart Grid Table in Online mode.

### **Essentials**
The next essentials are needed:

- Complete Smart Grid Table set.
- Access point *Tenda2* with:
  - Internet access.
- A host PC with:
  - Smart Grid Table simulation program.

### **Step by step instructions**

1. Power on the *Tenda2* access point.
2. Power on the Smart Grid Table set.
3. Wait until all the LEDs have turned green.
4. Start the host PC.
5. Connect to the *Tenda2* network.
6. Start up a terminal on the host PC.
7. Navigate to the *sgt-simulation* folder.
8. Open *config.json* and make sure the next lines are set:
```
"local_setup": false,
"mqtt_config_name": "hivemq",
```

9. Start the Smart Grid Table simulation program with:
```
venv/bin/python3 Application.py
```

10. Wait until all Smart Grid Table tiles are connected.

