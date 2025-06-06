# **First time setup - macOS & Windows**

This guide is made for developers of the *Smart Grid Table*, a project created by a group of students from the [HAN](https://www.hanuniversity.com/en/) in Arnhem. The guide explains how to set up a developing and runtime environment for the Smart Grid Table simulation program on macOS and Windows.

## **Overview**
This document is split into the following sections:
- [**First time setup - macOS & Windows**](#first-time-setup---macos--windows)
  - [**Overview**](#overview)
  - [**macOS**](#macos)
    - [**Setting up a Python environment**](#setting-up-a-python-environment)
    - [**Installing Python libraries**](#installing-python-libraries)
    - [**Installing GLPK**](#installing-glpk)
    - [**Installing the MQTT broker**](#installing-the-mqtt-broker)
    - [**Configuring the MQTT broker**](#configuring-the-mqtt-broker)
  - [**Windows**](#windows)
    - [**Setting up a Python environment**](#setting-up-a-python-environment-1)
    - [**Installing Python libraries**](#installing-python-libraries-1)
    - [**Installing GLPK**](#installing-glpk-1)
    - [**Installing mosquitto MQTT broker**](#installing-mosquitto-mqtt-broker)
    - [**Configuring the MQTT broker**](#configuring-the-mqtt-broker-1)

## **macOS**

### **Setting up a Python environment**
Python programs can be run in two manners: global or in a virtual environment. The Smart Grid Table simulation program is run in a virtual environment so we have total control over the Python libraries. We are using python-venv as our virtual environment.

**Prerequisites:**
1. Make sure you have Python 3 installed on your macOS machine. This can be done by running:
```
python3 --version
```
2. Install Homebrew if not already installed:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Creating virtual environment:**
1. Open the Terminal.
2. Go to the sgt-simulation working directory.
3. Enter the following command to create a virtual environment:
```
python3 -m venv ./venv
```

This creates a folder venv containing all virtual environment files.

4. Activate the virtual environment:
```
source venv/bin/activate
```

5. Test the virtual environment was successfully created using the command:
```
python --version
```
This should print the Python version of the virtual environment.

### **Installing Python libraries**
The Smart Grid Table simulation program is dependent on several libraries. These must be installed before running the program.

1. Open the Terminal.
2. Go to the sgt-simulation working directory.
3. Make sure your virtual environment is activated:
```
source venv/bin/activate
```
4. Install the required libraries:
```
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** If you encounter network issues, try:
```
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### **Installing GLPK**
The Smart Grid Table simulation program is dependent on the GLPK package.

1. Open the Terminal.
2. Install GLPK using Homebrew:
```
brew install glpk
```

### **Installing the MQTT broker**
When the Smart Grid Table simulation program is run in Standalone mode, it requires a locally run MQTT broker. This part explains how to install and configure a Mosquitto MQTT broker.

1. Open the Terminal.
2. Install Mosquitto using Homebrew:
```
brew install mosquitto
```

3. Check if Mosquitto is installed:
```
which mosquitto
```

### **Configuring the MQTT broker**
A newly installed MQTT broker won't work with the Smart Grid Table simulation program. We need to configure it first.

1. Open the Terminal.
2. Stop any running Mosquitto services:
```
brew services stop mosquitto
```

3. Locate the Mosquitto configuration file:
```
find /opt/homebrew -name "mosquitto.conf" 2>/dev/null
```
Usually located at: **/opt/homebrew/etc/mosquitto/mosquitto.conf**

4. Edit the Mosquitto configuration file:
```
sudo nano /opt/homebrew/etc/mosquitto/mosquitto.conf
```

5. Add the following lines to the end of the file:
```
listener 1883
allow_anonymous true
```

6. Save the changes (Ctrl+O, then Enter, then Ctrl+X in nano).

7. Start Mosquitto manually to test:
```
mosquitto -p 1883 -v
```

8. In a new terminal window, test if it's running:
```
lsof -i :1883
```

You should see mosquitto listening on port 1883.

9. To stop Mosquitto, press Ctrl+C in the terminal where it's running.

**Alternative: Start as background service**
```
brew services start mosquitto
```

## **Windows**

### **Setting up a Python environment**
Python programs can be run in two manners: global or in a virtual environment. The Smart Grid Table simulation program is run in a virtual environment so we have total control over the Python libraries.

**Prerequisites:**
1. Download and install Python 3 from https://www.python.org/downloads/
2. Make sure to check "Add Python to PATH" during installation
3. Verify installation by opening Command Prompt and running:
```
python --version
```

**Creating virtual environment:**
1. Open Command Prompt or PowerShell.
2. Navigate to the sgt-simulation working directory:
```
cd path\to\your\sgt-simulation
```
3. Create a virtual environment:
```
python -m venv venv
```
4. Activate the virtual environment:
```
venv\Scripts\activate
```
5. Test the virtual environment:
```
python --version
```

### **Installing Python libraries**
The Smart Grid Table simulation program is dependent on several libraries.

1. Open Command Prompt or PowerShell.
2. Navigate to the sgt-simulation working directory.
3. Activate your virtual environment:
```
venv\Scripts\activate
```
4. Install the required libraries:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### **Installing GLPK**
The Smart Grid Table simulation program is dependent on the GLPK package.

**Option 1: Using conda (recommended)**
1. Install Anaconda or Miniconda from https://www.anaconda.com/
2. Open Anaconda Prompt and run:
```
conda install -c conda-forge glpk
```

**Option 2: Manual installation**
1. Download GLPK for Windows from: https://www.gnu.org/software/glpk/
2. Extract and add the bin folder to your Windows PATH environment variable.

### **Installing mosquitto MQTT broker**
When the Smart Grid Table simulation program is run in Standalone mode, it requires a locally run MQTT broker.

1. Download Mosquitto for Windows from: https://mosquitto.org/download/
2. Install the downloaded .exe file.
3. Add the Mosquitto installation directory to your Windows PATH environment variable.
   - Usually: `C:\Program Files\mosquitto`

### **Configuring the MQTT broker**
A newly installed MQTT broker won't work with the Smart Grid Table simulation program.

1. Open Command Prompt as Administrator.
2. Stop the Mosquitto service:
```
net stop mosquitto
```

3. Navigate to the Mosquitto installation directory:
```
cd "C:\Program Files\mosquitto"
```

4. Edit the mosquitto.conf file using Notepad:
```
notepad mosquitto.conf
```

5. Add the following lines to the end of the file:
```
listener 1883
allow_anonymous true
```

6. Save the file.

7. Start Mosquitto manually to test:
```
mosquitto -c mosquitto.conf -v
```

8. In a new Command Prompt window, test if it's running:
```
netstat -an | findstr 1883
```

You should see a line showing that port 1883 is listening.

**Start as Windows service:**
1. Install Mosquitto as a Windows service:
```
mosquitto install
```
2. Start the service:
```
net start mosquitto
```

## **Configuring the base topic for the new table**

Open `config.json` file:
- Change the `"base_topic": "SmartDemoTable1"` to the corresponding table.

Open the `src` folder → open file `GUI_MQTT.py` change line:         
```python
## MQTT base topic.
self.__mqtt_topic = "SmartDemoTable1/GUI"
```
to the corresponding table.

**Example:** `"SmartDemoTable2"` is for the table set 2.

**PS:** The ESP32 flash firmware table set number and the base topic number must be the same. 

**Example:** 
Open `flash-firmware.ino` file:
```c
// Replace with the desired values.
#define TABLE_SET 5

// Change the base topic to: 
// "base_topic": "SmartDemoTable5"
```

## **Running the application**

1. **Start MQTT broker:**
   - **macOS:** `mosquitto -p 1883 -v` or `brew services start mosquitto`
   - **Windows:** `net start mosquitto` or `mosquitto -c mosquitto.conf -v`

2. **Activate virtual environment:**
   - **macOS:** `source venv/bin/activate`
   - **Windows:** `venv\Scripts\activate`

3. **Run the application:**
   ```
   python application.py
   ```

## **Troubleshooting**

### **MQTT Connection Issues**
- Make sure Mosquitto is running on port 1883
- Check firewall settings
- Verify the configuration file has the correct settings

### **Python Import Errors**
- Make sure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python version compatibility

### **GLPK Issues**
- **macOS:** Try `brew reinstall glpk`
- **Windows:** Verify GLPK is in your PATH environment variable 