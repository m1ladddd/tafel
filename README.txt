SmartGridTable-2022 software requires additional libraries to operate
Installiation of these libaries depents on your python environment

---------------------
------paho-mqtt------
---------------------
for Conda environment:
conda install paho-mqtt
or
conda install -c conda-forge paho-mqtt

for native python with pip:
pip install paho-mqtt

---------------------
--------pypsa--------
---------------------
for Conda environment:
conda install pypsa
or
conda install -c conda-forge pypsa

for native python with pip:
pip install pypsa

---------------------
--------glpk---------
---------------------
for Conda environment:
conda install glpk
or
conda install -c conda-forge glpk

for native python with pip:
pip install glpk

----------------------
-Before starting the program-
----------------------

Open conf.json file change the "base_topic": "SmartDemoTable1" to the corresponding table.
Open the src folder --> open file GUI_MQTT.py change line:         
        ## MQTT base topic.
        self.__mqtt_topic = "SmartDemoTable1/GUI" to the corresponding table
Example: "SmartDemoTable2" is for the table set 2.


----------------------
-starting the program-
----------------------
To start the SmartGridTable-2022 program:
- Start either a normal or a Conda terminal
- Navigate to the SmartGridTable-2022 directory
- Run the Application.py file (either "python Application.py" or "py Application.py")
- Type "shutdown" to exit the program

--------------------
--program commands--
--------------------
SmartGridTable-2022 has multiple interaction commands:
type help for a full list of commands
