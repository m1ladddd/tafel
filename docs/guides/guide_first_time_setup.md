# **First time setup**

This guide is made for developers of the *Smart Grid Table*, a project created by a group of students from the [HAN](https://www.hanuniversity.com/en/) in Arnhem. The guide explanes how to set up a developing and runtime environment for the Smart Grid Table simulation program.

## **Overview**
This document is split into the following sections:
- [**First time setup**](#first-time-setup)
  - [**Overview**](#overview)
  - [**Linux**](#linux)
    - [**Setting up a Python environment**](#setting-up-a-python-environment)
      - [**Installing Python venv**](#installing-python-venv)
    - [**Installing Python libraries**](#installing-python-libraries)
    - [**Installing GLPK**](#installing-glpk)
    - [**Installing the MQTT broker**](#installing-the-mqtt-broker)
    - [**Configuring the MQTT broker**](#configuring-the-mqtt-broker)
  - [**Windows**](#windows)
    - [**Setting up a Python environment**](#setting-up-a-python-environment-1)
    - [**Installing Python libaries**](#installing-python-libaries)
    - [**Installing GLPK**](#installing-glpk-1)
    - [**Installing mosquitto MQTT broker**](#installing-mosquitto-mqtt-broker)

## **Linux**

### **Setting up a Python environment**
Python programs can be run in two manners: global or in a virtual environment. The Smart Grid Table simulation program is run in a virtual environment so we have total controll over the Python libaries. We are using python-venv as or virtual environment.

#### **Installing Python venv**
venv can be installed using Python itself. 

1. Open the terminal.
2. Make sure you have Python 3 installed on your Linux machine. This can be done by running:
```
python3 --version
```
3. Install venv using the following command:
```
sudo apt install python3-venv
```

4. Go the the sgt-simulation working directory.
5. Enter the following command to create a virtual environment:
```
python -m venv ./venv
```

This creates a folder venv containing all virtual environment files.

6. Test the virtual environment was succesfully created using the command:
```
venv/bin/python3 --version
```
This should print the Python version of the virtual environment.

### **Installing Python libraries**
The Smart Grid Table simulation program is dependent on servial libraries. These must be installed before running the program.

1. Open the terminal.
2. Go the the sgt-simulation working directory.
3. Enter the following command:
```
venv/bin/pip install -e ./ 
```
This command sets up the project.

4. Make sure the installation is succesfull.
5. Enter the following command:
```
venv/bin/pip install -r requirements.txt 
```
This command installs all necessary libraries.

6. Make sure the installation is succesfull.
### **Installing GLPK**
The Smart Grid Table simulation program is dependent on the GLPK package.

1. Open the terminal.
2. Enter the following command:
```
sudo apt install glpk-utils
```
This installs the GLPK package.

### **Installing the MQTT broker**
When the Smart Grid Table simulation program is run in Standalone mode, it requires a localy run MQTT broker. This part explans how to install and configure a Mosquitto MQTT broker.

1. Open the terminal.
2. Enter the following command:
```
sudo apt install mosquitto
```

3. Enter the following command:
```
service mosquitto status
```

This displays the status of the MQTT broker which should look like the following:
```
● mosquitto.service - Mosquitto MQTT Broker
     Loaded: loaded (/lib/systemd/system/mosquitto.service; enabled; vendor preset: enabled)
     Active: active (running)
```

### **Configuring the MQTT broker**
A newly installed MQTT broker won't work with the Smart Grid Table simulation program. We need to configure it first.

1. Open the terminal.
2. Stop the MQTT broker using the following command:
```
sudo service mosquitto stop
```

3. Display the status of the broker using:
```
service mosquitto status
```

The output should look like this:
```
○ mosquitto.service - Mosquitto MQTT Broker
     Loaded: loaded (/lib/systemd/system/mosquitto.service; enabled; vendor preset: enabled)
     Active: inactive (dead)
```

4. Locate the  Mosquitto configuration file. for Ubuntu based operating systems this is ussaly located at: **/etc/mosquitto/mosquitto.conf**
5. Open up a text editor with root privileges.
6. Open the Mosquitto configuration file.
7. Append the following values to the file:
```
listener 1883
allow_anonymous true
```

8. Save the changes.
9. Start the Mosquitto broker using:
```
sudo service mosquitto start
```

10. Display the status of the broker using:
```
service mosquitto status
```

The output should look like this:
```
● mosquitto.service - Mosquitto MQTT Broker
     Loaded: loaded (/lib/systemd/system/mosquitto.service; enabled; vendor preset: enabled)
     Active: active (running)
```

## **Configuring the base topic for the new table**

Open conf.json file:
    change the "base_topic": "SmartDemoTable1" to the corresponding table.

Open the src folder --> open file GUI_MQTT.py change line:         
        
        ## MQTT base topic.
        self.__mqtt_topic = "SmartDemoTable1/GUI" to the corresponding table

Example: "SmartDemoTable2" is for the table set 2.

PS: The ESP32 flash firmware table set number and the base topic number must be the same. 

Example: 
        Open flash-firmware.ino file. 

        // Replace with the desired values.
        #define TABLE_SET 5

        // Change the base topic to : 
        The the "base_topic": "SmartDemoTable5"


## **Windows**
### **Setting up a Python environment**
### **Installing Python libaries**
### **Installing GLPK**
### **Installing mosquitto MQTT broker**
