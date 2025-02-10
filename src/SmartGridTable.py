##
# @file SmartGridTable.py
#
# @brief The class which connects all the objects together
# SmartGridTable containes multiple sections and the links between them
# At network refresh, all components will be retrieved from all sections and placed in the Simulation 
# When finished the results are loaded back into the sections, which will publish over MQTT
#
# @section libraries_SmartgridTable Libraries/Modules
# - pypsa
# - Timer
#
# @section todo_SmartgridTable TODO
# - Make use of multi-add and multi-remove methods to achieve better performance with a huge number of components.
#
# @section author_SmartgridTable Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

from src.PvPower import PvPower
from src.PhotoVoltaic import PhotoVoltaic
from src.MQTTConfig import MQTTConfig
from src.MQTTConfigManager import MQTTConfigManager
from src.model.calculation.ModelProcessor import ModelProcessor
from src.model.calculation.ModelProcessorInterface import ModelProcessorInterface
from src.Section import Section
from src.SectionLink import SectionLink
from src.ScenarioManager import ScenarioManager
from src.RestrictionsManager import RestrictionsManager
from src.led.LEDDatatype import RBGColor
from src.led.LEDDatatype import RBGAColor
from src.model.Model import Model
from src.model.components.Transformer import Transformer
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Component import Component
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.StorageUnit import StorageUnit
from src.TransformerLink import TransformerLink
from src.Timer import Timer
from src.Section_HV import Section_HV
from src.Section_MV import Section_MV
from src.Section_LV import Section_LV
from src.Section_MV_Ring import Section_MV_Ring
import pandas as pd

from os.path import exists
import json


class SmartGridTable:
    """! 
    The class which connects all the objects together.
    SmartGridTable containes multiple sections and the links between them.
    At network refresh, all components will be retrieved from all sections and placed in the Simulation.
    When finished the results are loaded back into the sections, which will publish over MQTT.
    """

    def __init__(self, config: str):
        """!
        Constructor.
        """

        ## Broker config file
        self.__mqtt_config_name: str = ""

        ## Broker config dicrectory
        self.__mqtt_config_folder: str = ""

        ## Enable or disable the UPD broadcasting to indicate whenever
        ## the table sections should run in Offline or Online mode
        self.__local_setup: bool = True

        self.__running=True

        ## Topic of this table set.
        self.__mqtt_base_topic: str = "Unset"

        ## Folder containing all static scenarios
        self.__static_scenario_folder: str = r""

        ## Folder containing all dynamic scenarios
        self.__dynamic_scenario_folder: str = r""

        ## Folder containing all restrictions
        self.__restrictions_folder:str = r""

        ## Config manager instance which handles MQTT connection data  
        self.__MQTT_config_manager: MQTTConfigManager = None

        ## Succesfull table initiation or not
        self.__init_succes: bool = self.table_load_config(config)

        if (not self.__init_succes):
            return

        self.__MQTT_config_manager = MQTTConfigManager(self.__mqtt_config_folder)
        self.__MQTT_config_manager.set_config_instance(self.__mqtt_config_name)

        ## Simulation instance for global PyPSA simulation.
        self.__model_calculator: ModelProcessorInterface = ModelProcessor()

        ## Bool indicating if PyPSA was succesfull.
        ## (True = succes, False = simulation failed).
        self.__simulation_succes: bool = False

        ## Elapsed time since the previous snapshot index change.
        self.__elapsed_time: float = 0

        ## Current PyPSA snapshot
        self.__snapshot_index: int = 0

        ## Bool indicating if the snapshot index has changed.
        self.snapshot_changed: bool  = False

        ## Bool indicating if a network LOPF has been carried out.
        self.simulation_changed: bool = False

        ## Array of all table sections
        self.__table_sections: list[Section] = []

        ## Array of all solid connection points between table sections
        self.__section_links: list[SectionLink]  = []

        ## Array of all dynamic connection points between table sections.
        ## These links will only activate if a Transformer has been placed.
        self.__transformer_links: list[TransformerLink] = []

        ## Scenario manager instance which loads and manages all static scenarios.
        self.__static_scenario_manager: ScenarioManager = ScenarioManager(self.__static_scenario_folder)

        ## Scenario manager instance which loads and manages all dynamic scenarios.
        self.__dynamic_scenario_manager: ScenarioManager = ScenarioManager(self.__dynamic_scenario_folder)

        ## Current active scenario manager (Static or Dynamic).
        self.__current_scenario_manager: ScenarioManager = self.__static_scenario_manager

        ## Restrictions manager instance which loads and manages all static and dynamic restrictions
        self.__restrictions_manager: RestrictionsManager = RestrictionsManager(self.__restrictions_folder)

        #Pvpower class for use it the photovoltaic modules
        self.PowerPv = PvPower()

        ## Bool indicating if the network simulation is set to Static or Dynamic.
        self.__static: bool = True

        ## Bool indicating if an LED update is required
        self.__led_update_flag: bool = False
        self.__static: bool = True

        ## Current active Scenario instance containing all module data (generators, loads, storages and transformers)
        self.__current_scenario: ScenarioManager = self.__static_scenario_manager.get_current_scenario()

        ## Sets initial scenario type.
        self.__restrictions_manager.set_restrictions(isStatic = self.__static)

        # Add table sections
        self.__table_sections.append( Section_HV("Table1") )
        self.__table_sections.append( Section_MV_Ring("Table2") )
        self.__table_sections.append( Section_MV("Table3") )
        self.__table_sections.append( Section_LV("Table4") )
        self.__table_sections.append( Section_LV("Table5") )
        self.__table_sections.append( Section_LV("Table6") )

        # Place static connections between table sections
        self.__section_links.append( SectionLink("Table2", "bus0",  "Table3", "bus0") )
        self.__section_links.append( SectionLink("Table2", "bus4",  "Table3", "bus21") )

        # Place dynamic connections (transformers) between table sections
        self.__transformer_links.append( TransformerLink("Table1", 0, "Table1", "bus5",  "Table2", "bus12") )
        self.__transformer_links.append( TransformerLink("Table1", 3, "Table1", "bus9",  "Table2", "bus15") )
        self.__transformer_links.append( TransformerLink("Table4", 0, "Table3", "bus11", "Table4", "bus13") )
        self.__transformer_links.append( TransformerLink("Table5", 0, "Table2", "bus8", "Table5", "bus13") )
        self.__transformer_links.append( TransformerLink("Table6", 0, "Table2", "bus19", "Table6", "bus13") )

        self.modules_reload()

        MQTT_config_instance = self.__MQTT_config_manager.get_current_config()

        self.mqtt_set_config(MQTT_config_instance)
        self.mqtt_set_base_topic(self.__mqtt_base_topic)

        self.__init_succes = True
        

    def shutdown(self) -> None:
        self.__model_calculator.shutdown()

    #-------------------------------
    # Table sections
    #-------------------------------

    def table_reboot_all(self):
        """!
        Send a reboot command to all table sections.
        """

        for section in self.__table_sections:
            section.reboot_section()


    def table_ping_all(self):
        """!
        Send a ping command to all table sections.
        """

        for section in self.__table_sections:
            section.send_ping()


    def table_update_firmware_all(self):
        """!
        Send a update firmware command to all table secions
        """

        for section in self.__table_sections:
            section.send_firmware_update_command()


    def table_update_config_all(self):
        """!
        Send a update config command to all table secions
        """

        for section in self.__table_sections:
            section.send_config_update_command()


    def table_reboot(self, table_name):
        """!
        Send a reboot command to a specific table section.
        @param table_name (str) Name of the table section.
        """

        found = False

        for section in self.__table_sections:
            if (section.name == table_name):
                section.reboot_section()
                found = True

        if (found == False):
            print("Table not found -> " + table_name)


    def table_shutdown(self, table_name):
        """!
        Send a shutdown command to a specific table section.
        @param table_name (str) Name of the table section.
        """
        found = False

        for section in self.__table_sections:
            if (section.name == table_name):
                section.reboot_section()
                section.mqtt_disconnect()
                found = True

        if (found == False):
            print("Table not found -> " + table_name)


    def table_poweron(self, table_name):
        """!
        Start MQTT connection to the given table section and reboot this section.
        @param table_name (str) Name of the table section.
        """

        found = False

        for section in self.__table_sections:
            if (section.name == table_name):
                section.mqtt_connect()
                section.reboot_section()
                found = True

        if (found == False):
            print("Table not found -> " + table_name)

    def get_generators_information(self):
        pass


    def table_print_list(self):
        """!
        Print all available table sections.
        """
        for section in self.__table_sections:
            print(section.name)


    def table_retrieve_modules(self):
        """!
        Send a command to all table sections to send back all placed modules.
        """

        for section in self.__table_sections:
            section.retrieve_modules()


    def table_is_online(self):
        """!
        Return if all table sections has been connected.
        @return Bool (True = all sections are connected, False = one or more sections are disconnected).
        """
        num = 0
        for section in self.__table_sections:
            if (section.section_is_online() == True):
                num += 1
        if (num == len(self.__table_sections)):
            return True
        return False
    

    def table_is_rfid_online(self):
        """!
        Return if all table sections has been connected.
        @return Bool (True = all sections are connected, False = one or more sections are disconnected).
        """
        num = 0
        for section in self.__table_sections:
            if (section.section_is_rfid_online() == True):
                num += 1
        if (num == len(self.__table_sections)):
            return True
        return False

    
    def table_load_config(self, filepath: str):

        file_exists = exists(filepath)

        if (not file_exists):
            print("Cannot start! config file was NOT found...")
            print("    File -> " + filepath)
            return False

        with open(filepath) as json_file:
            config_file = json.load(json_file)

            self.__mqtt_base_topic = config_file.get("base_topic")
            self.__mqtt_config_name = config_file.get("mqtt_config_name")
            self.__mqtt_config_folder = config_file.get("mqtt_config_folder")
            self.__local_setup = config_file.get("local_setup")
            self.__static_scenario_folder = config_file.get("static_scenario_folder")
            self.__dynamic_scenario_folder = config_file.get("dynamic_scenario_folder")
            self.__restrictions_folder = config_file.get("restrictions_folder")

            print("Loaded config file!")
            print("    Config file -> " + filepath)
            print("    MQTT config -> " + self.__mqtt_config_name)

        return True     


    def table_succes(self):
        return self.__init_succes

    #-------------------------------
    # Modules
    #-------------------------------

    def modules_print_status(self):
        """!
        Print how modules have been placed and how many platforms are available on each table section.
        """

        for section in self.__table_sections:
            section.print_module_status()


    def modules_enable_messages(self, enable):
        """!
        Enable or disable 'Module placed' and 'Module removed' console messages.
        @param enable (Bool) True = enable, False = disable.
        """

        for section in self.__table_sections:
            section.print_module_messages = enable


    def modules_reload(self):
        """!
        Replace all placed Module instances with other Module instanced from another scenario and re-run the simulation.
        Used to switch between scenarios.
        """

        for section in self.__table_sections:
            section.set_scenario(self.__current_scenario)
            section.reload_modules()


    def modules_if_changed(self):
        """!
        Check if a new Module instance has been placed or removed.
        @return Bool (True = new module placed or removed, False = no change).
        """
        for section in self.__table_sections:
            if (section.has_changed()):
                return True
        return False


    def modules_reset_changed(self):
        """!
        Reset the module change flag of each table section.
        Must be done after handing the newly placed/removed modules.
        """
        for section in self.__table_sections:
            section.reset_changed()


    def get_module_changes(self):
        buffer = []

        for i,section in enumerate(self.__table_sections):
            buff = section.get_input_buffer()
            buffer.append({"table_section": i+1, "buffer": buff})

        return buffer
    

    def empty_module_change_buffer(self):
        for section in self.__table_sections:
            section.empty_input_buffer()

    #-------------------------------
    # Scenario
    #-------------------------------

    def scenario_refresh_list(self):
        """!
        Reload every scenario from the .JSON files.
        """
        self.__static_scenario_manager.reload_scenarios()
        self.__dynamic_scenario_manager.reload_scenarios()
        self.__current_scenario_manager = self.__static_scenario_manager
        self.__current_scenario = self.__static_scenario_manager.get_current_scenario()


    def scenario_set(self, scenario_name, static):
        """!
        Switch to a specific scenario.
        @param scenario_name (str) Name of the scenario.
        @param static (Bool) True = static scenario, False = dynamic scenario.
        """
        if (static == True):
            status = self.__static_scenario_manager.set_scenario(scenario_name)
            if (status == True):
                self.__current_scenario_manager = self.__static_scenario_manager
        else:
            status = self.__dynamic_scenario_manager.set_scenario(scenario_name)
            if (status == True):
                self.__current_scenario_manager = self.__dynamic_scenario_manager

        if (status):
            self.__current_scenario = self.__current_scenario_manager.get_current_scenario()
            self.__current_scenario.print_scenario()
            self.__snapshot_index = 0
            self.__elapsed_time = 0
            self.__static = self.__current_scenario.is_static()
            self.modules_reload()
        else:
            print("No scenario found with name -> " + scenario_name)


    def scenario_print_current(self):
        """!
        Print the current active scenario name.
        """
        self.__current_scenario.print_scenario()


    def get_current_scenario(self):
        """!
        Returns the current scenario.
        """
        return self.__current_scenario_manager.get_current_scenario()
    
    def get_referenceless_catalog(self):
        """!
        Returns the catlog without references to csv files from the current scenario.
        @return current scenario catalog.
        """
        return self.__current_scenario_manager.get_referenceless_catalog()
    

    def get_scenario_list(self, isStatic):
        """!
        Returns the list of available scenario's.
        """
        if isStatic:
            return self.__static_scenario_manager.get_scenario_list()
        else:
            return self.__dynamic_scenario_manager.get_scenario_list()
        

    def get_scenario_type(self):
        """!
        Retruns the scenario type.
        True equals static, false equals dynamic.
        """
        return self.__static
    
    
    def change_current_scenario_catalog(self, catalog):
        self.__current_scenario_manager.change_catalog(catalog)


    def scenario_print_list(self):
        """!
        Print every scenario succesfully loaden into program memory.
        """
        self.__static_scenario_manager.print_scenario_list()
        self.__dynamic_scenario_manager.print_scenario_list()

    #-------------------------------
    # Restrictions
    #-------------------------------

    def set_restrictions(self, isStatic):
        """! 
        Wrapper function for setting the restrictions type.
        """
        self.__restrictions_manager.set_restrictions(isStatic)

    
    def get_current_restrictions(self):
        """! 
        Return the current restrictions
        @return current restrictions
        """
        return self.__restrictions_manager.get_current_restrictions()
    

    def change_restrictions(self, changes):
        """!
        Changes current restrictions.
        """
        self.__restrictions_manager.change_restrictions(changes)

    #-------------------------------
    # MQTT
    #-------------------------------

    def mqtt_connect(self):
        """!
        Connect every table section using MQTT.
        """
        for section in self.__table_sections:
            section.mqtt_connect()


    def mqtt_disconnect(self):
        """!
        Reboot all table sections and then closes all connections.
        """
        for section in self.__table_sections:
            section.reboot_section()
            section.mqtt_disconnect()


    def mqtt_selective_publish(self):
        """!
        Update the ;edstrip flow colors of all the table tiles
        """
        for section in self.__table_sections:
            section.mqtt_update_selective_power_flow()
            section.mqtt_update_selective_background()


    def mqtt_force_publish(self):
        """!
        Update the ;edstrip flow colors of all the table tiles
        """
        for section in self.__table_sections:
            section.mqtt_update_force_power_flow()
            section.mqtt_update_force_background()


    def mqtt_set_config(self, config_instance: MQTTConfig):
        """!
        Set the MQTT broker of each table section.
        @param config_instance (MQTTConfig) MQTT broker config instance
        """
        for section in self.__table_sections:
            section.mqtt_set_config(config_instance)


    def mqtt_set_base_topic(self, topic: str):
        """!
        Set the MQTT topic of each table section.
        @param topic (str) address of the broker.
        """
        for section in self.__table_sections:
            section.mqtt_set_base_topic(topic)


    def mqtt_is_connected(self):
        """!
        Check if all MQTT clients has a succesfull connection to the MQTT broker.
        @return (Bool) True = all MQTT clients has succesfully connected, False = one or more could not connect to the broker.
        """
        connected_sections = 0
        for section in self.__table_sections:
            if (section.mqtt_is_connected() == True):
                connected_sections = connected_sections + 1

        if (connected_sections == len(self.__table_sections)):
            return True
        return False

    #-------------------------------
    # Network model
    #-------------------------------  

    def get_model_lines(self) -> list[Line]:
        lines = []
        for section in self.__table_sections:
            section_lines = section.model.lines
            for line in section_lines:
                lines.append(line)
        for link in self.__section_links:
            new_line = Line(name=link.name, bus0=link.bus0, bus1=link.bus1, x=link.x, r=link.r, s_nom=link.s_nom, type="15-AL1/3-ST1A 0.4", length=1)
            lines.append(new_line)
        return lines
    

    def get_table_sections(self) -> list[Section]:
        return self.__table_sections
        

    def set_calculation_method(self, method: str) -> None:
        self.__model_calculator.set_calculation_method(method)
    

    def selective_calculate(self) -> None:
        """!
        Does a selective reload of the model and recalculates.
        Selective reload chacks if components have changed and only recalculates when necessary.
        """
        self.simulation_changed = True
        model = self.get_model()
        self.modules_reset_changed()
        snapshots = self.__current_scenario.index
        self.__model_calculator.set_input_model(model)
        self.__model_calculator.set_snapshots(snapshots)
        self.__model_calculator.selective_calculate()
        model.reset_changed_components()
        if (self.__static):
            self.__snapshot_index = 0
        self.update_ledstrips(self.__snapshot_index)
        self.mqtt_selective_publish()


    def force_calculate(self) -> None:
        """!
        Does a total reload of the model and recalculates.
        """
        self.simulation_changed = True
        model = self.get_model()
        self.modules_reset_changed()
        snapshots = self.__current_scenario.index
        self.__model_calculator.set_input_model(model)
        self.__model_calculator.set_snapshots(snapshots)
        self.__model_calculator.force_calculate()
        model.reset_changed_components()
        if (self.__static):
            self.__snapshot_index = 0
        self.update_ledstrips(self.__snapshot_index)
        self.mqtt_selective_publish()


    def get_sum_section_generation(self, table_name: str) -> pd.Series:
        """!
        Gets the generated power of a specific table section by calling the appropiate simulation function.
        @param tablesection str 
        @return dataframe
        """
        snapshots = self.__current_scenario.index
        model: Model = self.get_section_model(table_name)
        total_generation: list[float] = []

        # Iterate through all snapshots.
        for snapshot_id in range(len(snapshots)):
            # Calculate the generation sum
            sum: float = 0.0
            for generator in model.generators:
                if(generator.output[0]==True):
                    sum += generator.active_power[snapshot_id]
            total_generation.append(sum)

        pd_series: pd.Series = pd.Series(total_generation, snapshots)
        return pd_series

    def get_sum_section_load(self, table_name: str) -> pd.Series:
        """!
        Gets the used power of a specific table section by calling the appropiate simulation function.
        @param table_name str
        @return pd.Series
        """
        snapshots = self.__current_scenario.index   
        model: Model = self.get_section_model(table_name)
        total_load: list[float] = []

        # Iterate through all snapshots.
        for snapshot_id in range(len(snapshots)):
            # Calculate the load sum
            sum: float = 0.0
            for load in model.loads:
                if(load.output[0]==True):
                    sum += load.active_power[snapshot_id]
            total_load.append(sum)

        # Convert to pandas series.
        pd_series: pd.Series = pd.Series(total_load, snapshots)
        return pd_series
    
    def get_sum_section_storage(self, table_name: str) -> pd.Series:
        """!
        Gets the stored power of a specific table section by calling the appropiate simulation function.
        @param table_name str
        @return pd.Series
        """
        snapshots = self.__current_scenario.index   
        model: Model = self.get_section_model(table_name)
        total_storage: list[float] = []

        # Iterate through all snapshots.
        for snapshot_id in range(len(snapshots)):
            # Calculate the storage sum
            sum: float = 0.0
            for storage in model.storage_units:
                if(storage.output[0]==True):
                    sum += storage.active_power[snapshot_id]
            total_storage.append(sum)

        # Convert to pandas series.
        pd_series: pd.Series = pd.Series(total_storage, snapshots)
        return pd_series

    def get_voltage_sum_generation(self, voltage_level: str) -> pd.Series:
        """!
        Gets the generated power of a specific voltage level by using the sum of every appropiate table.
        @param voltage_level str
        @return pd.Series
        """       
        # Create a list of all table section with the same voltage level.
        section_list: list[Section] = []
        for section in self.__table_sections:
            if (section.voltage == voltage_level):
                section_list.append(section)

        snapshots = self.__current_scenario.index        
        total_generation: list[float] = []

        # Iterate through all snapshots.
        for snapshot_id in range(len(snapshots)):
            # Calculate the generation sum
            section_sum: float = 0.0
            for section in section_list:
                section_generation = self.get_sum_section_generation(section.name)
                section_sum += section_generation.iloc[snapshot_id]
            total_generation.append(section_sum)

        pd_series: pd.Series = pd.Series(total_generation, snapshots)
        return pd_series
    def get_sum_generation(self) -> pd.Series:
        """!
        Gets the generated power of the whole table by using the sum of every appropiate table.
        @param voltage_level str
        @return pd.Series
        """       
        # Create a list of all table section with the same voltage level.
        section_list: list[Section] = []
        for section in self.__table_sections:
            section_list.append(section)

        snapshots = self.__current_scenario.index        
        total_generation: list[float] = []

        # Iterate through all snapshots.
        for snapshot_id in range(len(snapshots)):
            # Calculate the generation sum
            section_sum: float = 0.0
            for section in section_list:
                section_generation = self.get_sum_section_generation(section.name)
                section_sum += section_generation.iloc[snapshot_id]
            total_generation.append(section_sum)

        pd_series: pd.Series = pd.Series(total_generation, snapshots)
        return pd_series
    def get_sum_load(self) -> pd.Series:
        """!
        Gets the generated power of the whole table by using the sum of every appropiate table.
        @param voltage_level str
        @return pd.Series
        """       
        # Create a list of all table section with the same voltage level.
        section_list: list[Section] = []
        for section in self.__table_sections:
            section_list.append(section)

        snapshots = self.__current_scenario.index        
        total_load: list[float] = []

        # Iterate through all snapshots.
        for snapshot_id in range(len(snapshots)):
            # Calculate the generation sum
            section_sum: float = 0.0
            for section in section_list:
                section_load = self.get_sum_section_load(section.name)
                section_sum += section_load.iloc[snapshot_id]
            total_load.append(section_sum)

        pd_series: pd.Series = pd.Series(total_load, snapshots)
        return pd_series
    def get_sum_storage(self) -> pd.Series:
        """!
        Gets the generated power of the whole table by using the sum of every appropiate table.
        @param voltage_level str
        @return pd.Series
        """       
        # Create a list of all table section with the same voltage level.
        section_list: list[Section] = []
        for section in self.__table_sections:
            section_list.append(section)

        snapshots = self.__current_scenario.index        
        total_storage: list[float] = []

        # Iterate through all snapshots.
        for snapshot_id in range(len(snapshots)):
            # Calculate the generation sum
            section_sum: float = 0.0
            for section in section_list:
                section_storage = self.get_sum_section_storage(section.name)
                section_sum += section_storage.iloc[snapshot_id]
            total_storage.append(section_sum)

        pd_series: pd.Series = pd.Series(total_storage, snapshots)
        return pd_series
        

    def get_voltage_sum_load(self, voltage_level: str) -> pd.Series:
        """!
        Gets the used power of a specific voltage level by using the sum of every appropiate table. 
        @param voltage str
        @return dataframe
        """
         # Create a list of all table section with the same voltage level.
        section_list: list[Section] = []
        for section in self.__table_sections:
            if (section.voltage == voltage_level):
                section_list.append(section)

        snapshots = self.__current_scenario.index        
        total_load: list[float] = []

        # Iterate through all snapshots.
        for snapshot_id in range(len(snapshots)):
            # Calculate the generation sum
            section_sum: float = 0.0
            for section in section_list:
                section_load = self.get_sum_section_load(section.name)
                section_sum += section_load.iloc[snapshot_id]
            total_load.append(section_sum)

        pd_series: pd.Series = pd.Series(total_load, snapshots)
        return pd_series
        

    def get_voltage_sum(self, voltage_level: str) -> pd.DataFrame:
        """!
        Gets the used power and generated power of a specific voltage level.
        @param voltage str
        @return dataframe
        """
        pd_load:pd.Series=self.get_voltage_sum_load(voltage_level)
        pd_generation:pd.Series=self.get_voltage_sum_generation(voltage_level)
        pd_dataframe:pd.DataFrame=pd.concat([pd_generation,pd_load],axis=1,keys=["Generation","Load"])
        return pd_dataframe
        
    def get_table_section_module_generation(self, table_name: str) -> pd.DataFrame:
        """!
        Gets the generated power of each module on a tablesection
        @param table_name
        @return dataframe
        """
        snapshots = self.__current_scenario.index
        model: Model = self.get_section_model(table_name)
        pd_dataframe=pd.DataFrame(index=snapshots)

        # Iterate through all generators and join them to one dataframe.
        for generators in model.generators:
            if(generators.output[0]==True):
                pd_series=pd.Series(generators.active_power,index=snapshots,name=generators.name)
                pd_dataframe=pd.concat([pd_dataframe,pd_series],axis=1)
        return pd_dataframe
    
    def get_table_section_module_load(self, table_name: str) -> pd.DataFrame:
        """!
        Gets the consumed power of each module on a tablesection
        @param table_name
        @return dataframe
        """
        snapshots = self.__current_scenario.index
        model: Model = self.get_section_model(table_name)
        pd_dataframe=pd.DataFrame(index=snapshots)

        # Iterate through all loads and join them to one dataframe.
        for loads in model.loads:
            if(loads.output[0]==True):
                pd_series=pd.Series(loads.active_power,index=snapshots,name=loads.name)
                pd_dataframe=pd.concat([pd_dataframe,pd_series],axis=1)
        return pd_dataframe
    
    def get_table_section_module_storage(self, table_name: str) -> pd.DataFrame:
        """!
        Gets the stored power of each module on a tablesection
        @param table_name
        @return dataframe
        """
        snapshots = self.__current_scenario.index
        model: Model = self.get_section_model(table_name)
        pd_dataframe=pd.DataFrame(index=snapshots)

        # Iterate through all storage_units and join them to one dataframe.
        for storage_units in model.storage_units:
            if(storage_units.output[0]):
                pd_series=pd.Series(storage_units.active_power,index=snapshots,name=storage_units.name)
                pd_dataframe=pd.concat([pd_dataframe,pd_series],axis=1)
        return pd_dataframe
    
    def get_table_section_module_all(self, table_name: str) -> pd.DataFrame:
        """!
        Gets the all info of each module on a tablesection
        @param table_name
        @return dataframe
        """
        pd_generation=self.get_table_section_module_generation(table_name)
        pd_load=self.get_table_section_module_load(table_name)
        pd_storage=self.get_table_section_module_storage(table_name)
        pdfinal=pd.concat([pd_generation,pd_load,pd_storage])
        return pdfinal



    def get_full_grid_sum_generation_loads_storage(self) -> pd.DataFrame:
        """!
        Gets the generated power, the consumed power and the storage of the whole network
        @return dataframe
        """
        pd_generation=self.get_sum_generation()
        pd_load=self.get_sum_load()
        pd_storage=self.get_sum_storage()
        pdfinal=pd.concat([pd_generation,pd_load,pd_storage],axis=1,keys=["Generation","Load","Storage"])
        return pdfinal

    def get_table_sum(self, table_name: str) -> pd.DataFrame:
        """
        Gets the used and generated power of a specific table section.
        @param tablesection
        @return dataframe
        """
        pd_generation=self.get_sum_section_generation(table_name)
        pd_load=self.get_sum_section_load(table_name)
        pdfinal=pd.concat([pd_generation,pd_load],axis=1,keys=["Generation","Load"])
        return pdfinal
        

    def transformer_capacity(self) -> pd.DataFrame:
        """!
        Returns a dataframe of all transformers with the active p0 power on row 0 and s_nom on row 1
        @return dataframe
        """
        snapshots = self.__current_scenario.index
        pd_power=pd.DataFrame()
        pd_capacity=pd.DataFrame()
        for section in self.__table_sections:
            for transformers in section.model.transformers:
                pd_series=pd.Series(transformers.active_power_0,name=transformers.name)
                pd_power=pd.concat([pd_power,pd_series],axis=1)
                pd_seriescap=pd.Series(transformers.capacity,name=transformers.name)
                pd_capacity=pd.concat([pd_capacity,pd_seriescap],axis=1)
        return pd_power,pd_capacity
        

    def get_snapshot_response_gui(self) -> str:
        transformer_capacity = {}
        power_per_table_Section = {}
        power_per_voltage_level = {}
        power_total = {}

        if self.get_simulation_succes():
            if self.get_scenario_type():
                transformer_df, capacity_df = self.transformer_capacity()

                for col in transformer_df.columns:
                    if(capacity_df[col].tolist()[0]!=0):
                        transformer_capacity[col] = {'Capacity Usage': round(abs(transformer_df[col].tolist()[0] / capacity_df[col].tolist()[0] * 100), 2)}
                    else:
                        transformer_capacity[col] = {'Capacity Usage': round(abs(transformer_df[col].tolist()[0]), 2)}

                for i in range(6):
                    section_df = self.get_table_sum(f'Table{i+1}')
                    power_per_table_Section[f'Table Section {i+1}'] = section_df.to_dict(orient='records')[0]

                for level in ['LV','MV','HV']:
                    level_df = self.get_voltage_sum(level)
                    power_per_voltage_level[level] = level_df.to_dict(orient='records')[0]
                
                power_df = self.get_full_grid_sum_generation_loads_storage()
                power_total['Network'] = power_df.to_dict(orient='records')[0]
                
            else:
                transformer_df, capacity_df = self.transformer_capacity()

                for col in transformer_df.columns:
                    transformer_capacity[col+' Current Power'] = transformer_df[col].tolist()

                for k,v in capacity_df.items():
                    transformer_capacity[k+' Maximum Power'] = [v.tolist()[0]] * len(self.__current_scenario.index)

                for i in range(6):
                    section_df = self.get_table_sum(f'Table{i+1}')
                    section_data = section_df.to_dict(orient='list')

                    for k,v in section_data.items():
                        power_per_table_Section[f'Table Section {i+1} {k}'] = v

                for level in ['LV','MV','HV']:
                    level_df = self.get_voltage_sum(level)

                    level_data = level_df.to_dict(orient='list')

                    for k,v in level_data.items():
                        power_per_voltage_level[f'{level} {k}'] = v
                
                power_df = self.get_full_grid_sum_generation_loads_storage()
                power_data = power_df.to_dict(orient='list')

                for k,v in power_data.items():
                    power_total[f'Network {k}'] = v

        response = {
            'type': 'NETWORK_SNAPSHOTS', 
            'payload': {
                'transformerCapacityGraphs': transformer_capacity,
                'powerPerTableSection': power_per_table_Section,
                'powerPerVoltageLevel': power_per_voltage_level,
                'powerTotal': power_total
            }
        }
        return dict(response)
                 
                                        
    def change_photovoltaic(self,direction,module):
        """!
        Changes the direction for the development pv-special module
        @param direction str
        @param module str
        """
        for section in self.__table_sections:
            for platform in section.platforms:
                if platform.module is not None:
                    if(platform.module.RFID_tag==module):
                       for component in platform.module.components:
                           if(isinstance(component,PhotoVoltaic)):
                                if(direction=="South"):
                                   self.__current_scenario.catalog[module]["photovoltaic"][0]["surface_azimuth"]=180
                                   self.__current_scenario.catalog[module]["photovoltaic"][0]["enable"]=True

                                   self.modules_reload()
                                if(direction=="East"):
                                   self.__current_scenario.catalog[module]["photovoltaic"][0]["surface_azimuth"]=90
                                   self.__current_scenario.catalog[module]["photovoltaic"][0]["enable"]=True

                                   self.modules_reload()
                                if(direction=="West"):
                                   self.__current_scenario.catalog[module]["photovoltaic"][0]["surface_azimuth"]=270
                                   self.__current_scenario.catalog[module]["photovoltaic"][0]["enable"]=True

                                   self.modules_reload()
                                if(direction=="None"):
                                   self.__current_scenario.catalog[module]["photovoltaic"][0]["enable"]=False
                                   self.modules_reload()

   

    def set_calculation_method(self, method: str) -> None:
        self.__model_calculator.set_calculation_method(method)
    
    
    def get_model(self) -> Model:
        """! 
        Return the complete model of this table set.
        """
        model = Model()

        for link in self.__section_links:
            new_line = Line(name=link.name, bus0=link.bus0, bus1=link.bus1, x=link.x, r=link.r, s_nom=link.s_nom, type="15-AL1/3-ST1A 0.4", length=1)
            model.add_line(new_line)

        for section in self.__table_sections:
            section.reload_model()
            for bus in section.model.buses:
                model.add_bus(bus)
            for line in section.model.lines:
                model.add_line(line)
            for generator in section.model.generators:
                model.add_generator(generator)
            for load in section.model.loads:
                model.add_load(load)
            for storage_unit in section.model.storage_units:
                model.add_storage_unit(storage_unit)
            for transformer in section.model.transformers:
                for link in self.__transformer_links:
                    if (link.RFID_table == section.name):
                        for platform in section.platforms:
                            if (platform.RFID_location == link.RFID):
                                if (platform.module != None):
                                    if(link.bus0==transformer.bus0):
                                        transformer.bus1=link.bus1
                                    if(link.bus1==transformer.bus0):
                                        transformer.bus0=link.bus0
                                        transformer.bus1=link.bus1   
                model.add_transformer(transformer)

        return model
    

    def get_section_model(self, table: str) -> Model:
        """! 
        Return the model of one table section.
        """
        section: Section = None

        for section_search in self.__table_sections:
            if (section_search.name == table):
                section = section_search

        if (section == None):
            return None

        return section.model

    #-------------------------------
    # Miscellaneous
    #-------------------------------

    def get_lep_update_flag(self) -> bool:
        
        for table in self.__table_sections:
            if table.get_led_update_flag() == True:
                return True
        return self.__led_update_flag
    
    
    def reset_led_update_flag(self) -> None:
        self.__led_update_flag = False
        for table in self.__table_sections:
            table.reset_led_update_flag()


    def update_ledstrips(self, snapshot_index: int) -> None:
        """!
        Update the ledstrip avtive power value depending on the simulation result.
        """
        for section in self.__table_sections:
            index: int = 0
            for ledstrip in section.ledstrips:
                line = section.model.lines[index]
                active_power = line.active_power[snapshot_index]
                line_output = line.output[snapshot_index]
                absolute_active_power = abs(active_power)

                index += 1

                ledstrip.set_background_color(section.background_color)
                ledstrip.set_background_flashing_time(0)
                ledstrip.set_flow_speed(400)

                if (absolute_active_power > 0.00001):
                    if (active_power >= 0):
                        ledstrip.flow_direction = 0
                    else:
                        ledstrip.flow_direction = 1

                flow_color = RBGAColor(0, 0, 0, 255)
                background_color = RBGColor(0, 0, 0)
                
                # for active power between 0 and threshold_low
                if (absolute_active_power < section.threshold_low):
                    flow_color.red = 0
                    flow_color.green = 128
                    flow_color.blue = 0
                    flow_color.alpha = 255
                    ledstrip.set_flow_color(flow_color)
                    ledstrip.set_flow_speed(300)

                # for active power between threshold_low and threshold_normal
                elif (absolute_active_power < section.threshold_normal):
                    relative_power = absolute_active_power-section.threshold_low
                    relative_limit = section.threshold_normal-section.threshold_low
                    flow_color.red = 0
                    flow_color.green = 128 + (relative_power / relative_limit * 127)
                    flow_color.blue = 0
                    flow_color.alpha = 255
                    ledstrip.set_flow_color(flow_color)
                    ledstrip.set_flow_speed(200)

                # for active power between threshold_normal and threshold_high
                elif (absolute_active_power < section.threshold_high):
                    relative_power = absolute_active_power-section.threshold_normal
                    relative_limit = section.threshold_high-section.threshold_normal
                    flow_color.red = relative_power / relative_limit * 255
                    flow_color.green = 255
                    flow_color.blue = 0
                    flow_color.alpha = 255
                    ledstrip.set_flow_color(flow_color)
                    ledstrip.set_flow_speed(200)

                # for active power between threshold_high and threshold_critical
                elif (absolute_active_power < section.threshold_critical):
                    relative_power = absolute_active_power-section.threshold_high
                    relative_limit = section.threshold_critical-section.threshold_high
                    flow_color.red = 255
                    flow_color.green = 255 - (relative_power / relative_limit * 255)
                    flow_color.blue = 0
                    flow_color.alpha = 255
                    ledstrip.set_flow_color(flow_color)
                    ledstrip.set_flow_speed(100)

                # for active power above threshold_critical
                else:
                    flow_color.red = 255
                    flow_color.green = 0
                    flow_color.blue = 0
                    flow_color.alpha = 255
                    ledstrip.set_flow_color(flow_color)
                    ledstrip.set_flow_speed(100)

                if (absolute_active_power < 0.00001):
                    flow_color.red = 0
                    flow_color.green = 0
                    flow_color.blue = 0
                    flow_color.alpha = 0                
                    ledstrip.set_flow_color(flow_color)

                if (line_output == False):
                    background_color.red = 0
                    background_color.green = 0
                    background_color.blue = 0
                    ledstrip.set_background_color(background_color)

                if (line.active == False):
                    flow_color.red = 0
                    flow_color.green = 0
                    flow_color.blue = 0
                    flow_color.alpha = 0
                    background_color.red = 0
                    background_color.green = 0
                    background_color.blue = 0
                    ledstrip.set_flow_color(flow_color)
                    ledstrip.set_background_color(background_color)
                    ledstrip.set_background_flashing_time(0)

                if (ledstrip.error):
                    flow_color.red = 0
                    flow_color.green = 0
                    flow_color.blue = 0
                    flow_color.alpha = 0
                    background_color.red = 128
                    background_color.green = 0
                    background_color.blue = 0
                    ledstrip.set_flow_color(flow_color)
                    ledstrip.set_background_color(background_color)
                    ledstrip.set_background_flashing_time(75)


    def append_delta_time(self, delta_time):
        """!
        Increment the delta time with given value.
        Needed to time the steps between snapshots in Dynamic network scenarios.
        """
        if (self.__current_scenario.is_static() == False):
            self.__elapsed_time = self.__elapsed_time + delta_time

    def set_index(self,index):
        """!
        Sets the index for the snapshot selection of the network update to index
        """
        self.__snapshot_index=int(index)
        self.update_ledstrips(self.__snapshot_index)
        self.mqtt_selective_publish()

    def stop_running(self):
        """!
        Stops the dynamic running of snapshots, makes sure that the index number does not increase
        """
        self.__running=False

    def start_running(self):
        """!
        Starts the dynamic running of snapshot
        """
        self.__running=True

    def update(self):
        """!
        Only used in Dynamic network scenarios.
        Method will check if elapsed time since last snapshot change has exceeded the 'time per snapshot' value.
        If this is true, increase the snapshot index and send new ledstrip values to the table section.
        """

        if (self.__current_scenario.is_static() == False):
            if(self.__elapsed_time > self.__current_scenario.time_per_snapshot):

                self.__elapsed_time = 0
                self.snapshot_changed = True

                self.update_ledstrips(self.__snapshot_index)
                self.mqtt_selective_publish()
                if(self.__running == True):
                    self.__snapshot_index += 1

                total_snapshots = len(self.__current_scenario.index)

                if (self.__snapshot_index >= total_snapshots):
                    self.__snapshot_index = 0


    def get_simulation_succes(self):
        """!
        Check if PyPSA simulation was succesfull.
        @return Bool (True = succes, False = fail)
        """

        return True
    

    def get_current_snapshot(self):
        """!
        Get the current snapshot index.
        @return int snapshot index.
        """

        index = self.__current_scenario.index
        return index[self.__snapshot_index]


    def get_snapshots(self):
        """!
        Get the current snapshot time data.
        @return list of snapshot data.
        """

        return self.__current_scenario.index

    
    def get_generators_generation(self):
        """!
        Get all Generator power generation
        @return list of power generation
        """
        pass
            

    def get_load_consumption(self):
        """!
        Get all Load power consumption
        @return list of power consumption
        """
        pass
    

    def get_local_setup(self):
        """!
        Get all Load power consumption
        @return list of power consumption
        """
        return self.__local_setup
    

    def table_set_line_status(self, table_id: int, line_id: int, status: bool):
        if (len(self.__table_sections) <= table_id):
            return
        
        line_list: list[Line] = self.__table_sections[table_id].model.lines

        if (len(line_list) <= line_id):
            return
        
        line_list[line_id].active = status
