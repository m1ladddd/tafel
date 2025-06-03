##
# @file SmartGridTable.py
#
# @brief The class which connects all the objects together
# SmartGridTable containes multiple sections and the links between them
# At network refresh, all components will be retrieved from all sections and placed in the Simulation
# When finished the results are loaded back into the sections, which will publish over MQTT
#
# @section libraries_SmartgridTable Libraries/Modules
# - Timer # Verwijzing naar pypsa hier weggehaald
# - pandas
# - json
#
# @section todo_SmartgridTable TODO
# - Make use of multi-add and multi-remove methods to achieve better performance with a huge number of components.
# - Ensure ModelProcessor and CalculatorThreadManager exclusively use Pandapower.
#
# @section author_SmartgridTable Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
# - Modified by Milad with Pandapower 03/02/2025
##

# === PyPSA Import Verwijderd/Uitgecommentarieerd ===
# import pypsa # <-- DEZE REGEL IS HET PROBLEEM, NU UITGECOMMENTARIEERD
# =============================================

from src.PvPower import PvPower
from src.PhotoVoltaic import PhotoVoltaic
from src.MQTTConfig import MQTTConfig
from src.MQTTConfigManager import MQTTConfigManager
# ModelProcessor importeert de INTERFACE, de implementatie erachter moet Pandapower zijn
from src.model.calculation.ModelProcessorInterface import ModelProcessorInterface
from src.model.calculation.ModelProcessor import ModelProcessor
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
from src.Scenario import Scenario
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

        ## Enable or disable the UPD broadcasting
        self.__local_setup: bool = True

        self.__running=True # Let op: Deze lijkt niet gebruikt te worden binnen deze klasse

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

        ## Simulation instance using the ModelProcessorInterface (should point to Pandapower impl.)
        self.__model_calculator: ModelProcessorInterface = ModelProcessor()

        ## Bool indicating if simulation was succesfull.
        self.__simulation_succes: bool = False # Default to False

        ## Elapsed time since the previous snapshot index change.
        self.__elapsed_time: float = 0

        ## Current simulation snapshot index
        self.__snapshot_index: int = 0

        ## Bool indicating if the snapshot index has changed.
        self.snapshot_changed: bool  = False

        ## Bool indicating if a network calculation has been carried out.
        self.simulation_changed: bool = False

        ## Array of all table sections
        self.__table_sections: list[Section] = []

        ## Array of all solid connection points between table sections
        self.__section_links: list[SectionLink]  = []

        ## Array of all dynamic connection points between table sections.
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
        # self.__static: bool = True # Dubbele toewijzing, verwijderd

        ## Current active Scenario instance containing all module data
        self.__current_scenario: Scenario = self.__static_scenario_manager.get_current_scenario() # Scenario type hint

        ## Sets initial scenario type for restrictions.
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

        self.modules_reload() # Load initial module data based on scenario

        # Laad en zet MQTT configuratie voor alle secties
        MQTT_config_instance = self.__MQTT_config_manager.get_current_config()
        if MQTT_config_instance:
            self.mqtt_set_config(MQTT_config_instance)
            self.mqtt_set_base_topic(self.__mqtt_base_topic)
        else:
            print("Error: Could not load MQTT configuration instance.")
            self.__init_succes = False
            return # Stop init if MQTT config fails

        self.__init_succes = True


    def shutdown(self) -> None:
        """ Gracefully shuts down the model processor """
        print("Shutting down Model Processor...")
        self.__model_calculator.shutdown()
        print("Model Processor shutdown complete.")

    #-------------------------------
    # Table sections
    #-------------------------------

    def table_reboot_all(self):
        """! Send a reboot command to all table sections. """
        for section in self.__table_sections:
            section.reboot_section()

    def table_ping_all(self):
        """! Send a ping command to all table sections. """
        for section in self.__table_sections:
            section.send_ping()

    def table_update_firmware_all(self):
        """! Send a update firmware command to all table secions """
        for section in self.__table_sections:
            section.send_firmware_update_command()

    def table_update_config_all(self):
        """! Send a update config command to all table secions """
        for section in self.__table_sections:
            section.send_config_update_command()

    def table_reboot(self, table_name):
        """! Send a reboot command to a specific table section. """
        section = self._find_section(table_name)
        if section:
            section.reboot_section()
        else:
            print(f"Table not found -> {table_name}")

    def table_shutdown(self, table_name):
        """! Send a shutdown command to a specific table section. """
        section = self._find_section(table_name)
        if section:
            # section.reboot_section() # Rebooten voor shutdown? Lijkt vreemd.
            section.mqtt_disconnect() # Eerst MQTT disconnect
            # TODO: Is er een expliciet shutdown MQTT commando voor de ESP32?
            print(f"MQTT disconnected for {table_name}, physical shutdown needs external action?")
        else:
            print(f"Table not found -> {table_name}")

    def table_poweron(self, table_name):
        """! Start MQTT connection to the given table section and optionally reboot. """
        section = self._find_section(table_name)
        if section:
            section.mqtt_connect()
            # section.reboot_section() # Rebooten bij poweron? Misschien alleen pingen.
            section.send_ping() # Check if it responds after connect
        else:
            print(f"Table not found -> {table_name}")

    def _find_section(self, table_name: str) -> Section | None:
         """ Helper to find a section by name """
         for section in self.__table_sections:
              if section.name.lower() == table_name.lower():
                   return section
         return None

    def get_generators_information(self):
        # TODO: Implement logic to gather generator info
        pass

    def table_print_list(self):
        """! Print all available table sections. """
        print("Available Table Sections:")
        for section in self.__table_sections:
            print(f"- {section.name} ({type(section).__name__})")

    def table_retrieve_modules(self):
        """! Send command to all sections to report placed modules. """
        for section in self.__table_sections:
            section.retrieve_modules()

    def table_is_online(self):
        """! Check if all table sections are considered online (e.g., responding to pings). """
        if not self.__table_sections: return False # Geen secties, dus niet online
        online_count = sum(1 for section in self.__table_sections if section.section_is_online())
        return online_count == len(self.__table_sections)

    def table_is_rfid_online(self):
        """! Check if all RFID readers (if applicable per section type) are online. """
        if not self.__table_sections: return False
        online_count = sum(1 for section in self.__table_sections if section.section_is_rfid_online())
        return online_count == len(self.__table_sections)

    def table_load_config(self, filepath: str) -> bool:
        """! Loads main application configuration from JSON file. """
        if not exists(filepath):
            print(f"CRITICAL ERROR: Config file not found at -> {filepath}")
            return False

        try:
            with open(filepath) as json_file:
                config_file = json.load(json_file)

            # Validate required keys
            required_keys = ["base_topic", "mqtt_config_name", "mqtt_config_folder",
                             "local_setup", "static_scenario_folder",
                             "dynamic_scenario_folder", "restrictions_folder"]
            missing_keys = [key for key in required_keys if key not in config_file]

            if missing_keys:
                 print(f"CRITICAL ERROR: Config file '{filepath}' missing keys: {', '.join(missing_keys)}")
                 return False

            self.__mqtt_base_topic = config_file["base_topic"]
            self.__mqtt_config_name = config_file["mqtt_config_name"]
            self.__mqtt_config_folder = config_file["mqtt_config_folder"]
            self.__local_setup = config_file["local_setup"]
            self.__static_scenario_folder = config_file["static_scenario_folder"]
            self.__dynamic_scenario_folder = config_file["dynamic_scenario_folder"]
            self.__restrictions_folder = config_file["restrictions_folder"]

            print(f"Loaded config file: {filepath}")
            print(f"  MQTT config profile: {self.__mqtt_config_name} (from folder: {self.__mqtt_config_folder})")
            return True

        except json.JSONDecodeError as e:
            print(f"CRITICAL ERROR: Invalid JSON in config file '{filepath}': {e}")
            return False
        except Exception as e:
            print(f"CRITICAL ERROR: Unexpected error loading config file '{filepath}': {e}")
            return False

    def table_succes(self):
        """! Returns if the initialization was successful """
        return self.__init_succes

    #-------------------------------
    # Modules
    #-------------------------------

    def modules_print_status(self):
        """! Print module count and available platforms per section. """
        print("Module Status per Section:")
        for section in self.__table_sections:
            section.print_module_status() # Assumes Section has this method

    def modules_enable_messages(self, enable: bool):
        """! Enable/disable verbose console messages for module placement/removal. """
        for section in self.__table_sections:
            section.print_module_messages = enable # Assumes Section has this attribute

    def modules_reload(self):
        """! Reload module instances in all sections based on the current scenario. """
        # Ensure a scenario is actually loaded
        if not self.__current_scenario:
             print("Error: Cannot reload modules, no current scenario set.")
             return
             
        print(f"Reloading modules for scenario: {self.__current_scenario.get_name()} (Static: {self.__static})")

        for section in self.__table_sections:
            section.set_scenario(self.__current_scenario) # Pass the Scenario object
            section.reload_modules() # Assumes Section has this method
        print("Module reload complete.")

    def modules_if_changed(self) -> bool:
        """! Check if any section reported a module change since last reset. """
        for section in self.__table_sections:
            if section.has_changed(): # Assumes Section has this method
                return True
        return False

    def modules_reset_changed(self):
        """! Reset the change flag for all sections. """
        for section in self.__table_sections:
            section.reset_changed() # Assumes Section has this method

    def get_module_changes(self) -> list:
        """! Collect module change buffer from all sections. """
        buffer = []
        for i, section in enumerate(self.__table_sections):
            # Assuming get_input_buffer returns list of changes (dicts?) for that section
            section_buffer = section.get_input_buffer()
            if section_buffer: # Only add if there are changes
                 buffer.append({"table_section": i + 1, "buffer": section_buffer})
        return buffer

    def empty_module_change_buffer(self):
        """! Empty the change buffer for all sections. """
        for section in self.__table_sections:
            section.empty_input_buffer() # Assumes Section has this method

    #-------------------------------
    # Scenario
    #-------------------------------

    def scenario_refresh_list(self):
        """! Reload scenario lists from disk. """
        print("Reloading scenario lists from disk...")
        self.__static_scenario_manager.reload_scenarios()
        self.__dynamic_scenario_manager.reload_scenarios()
        # Reset current scenario to default static if needed? Or keep current?
        # Let's keep the current one for now, just refresh the lists.
        print("Scenario lists refreshed.")

    def scenario_set(self, scenario_name: str, static: bool):
        """! Switch to a specific scenario by name and type. """
        target_manager = self.__static_scenario_manager if static else self.__dynamic_scenario_manager
        status = target_manager.set_scenario(scenario_name)

        if status:
            self.__current_scenario_manager = target_manager
            self.__current_scenario = self.__current_scenario_manager.get_current_scenario()
            self.__static = self.__current_scenario.is_static() # Update static flag
            print(f"Switched to {'static' if static else 'dynamic'} scenario: {scenario_name}")
            self.__current_scenario.print_scenario() # Print details of new scenario
            self.__snapshot_index = 0 # Reset snapshot index
            self.__elapsed_time = 0 # Reset timer
            self.modules_reload() # Reload modules for the new scenario
            self.set_restrictions(self.__static) # Update restrictions for new type
        else:
            print(f"Error: Scenario '{scenario_name}' ({'static' if static else 'dynamic'}) not found.")

    def scenario_print_current(self):
        """! Print details of the currently active scenario. """
        if self.__current_scenario:
            self.__current_scenario.print_scenario()
        else:
            print("No scenario currently loaded.")

    def get_current_scenario(self):
        """! Returns the current Scenario object. """
        return self.__current_scenario_manager.get_current_scenario()

    def get_referenceless_catalog(self):
        """! Returns the catalog dict from the current scenario. """
        return self.__current_scenario_manager.get_referenceless_catalog()

    def get_scenario_list(self, isStatic: bool) -> list:
        """! Returns the list of available scenario names for the given type. """
        manager = self.__static_scenario_manager if isStatic else self.__dynamic_scenario_manager
        return manager.get_scenario_list()

    def get_scenario_type(self) -> bool:
        """! Returns the type of the current scenario (True=static, False=dynamic). """
        return self.__static

    def change_current_scenario_catalog(self, catalog: dict):
        """! Updates the catalog of the currently loaded scenario instance. """
        # Be careful modifying the loaded scenario directly
        print("Updating current scenario catalog in memory...")
        self.__current_scenario_manager.change_catalog(catalog)
        # Does not automatically save the changes to disk!

    def scenario_print_list(self):
        """! Print all available static and dynamic scenarios. """
        print("--- Static Scenarios ---")
        self.__static_scenario_manager.print_scenario_list()
        print("--- Dynamic Scenarios ---")
        self.__dynamic_scenario_manager.print_scenario_list()

    #-------------------------------
    # Restrictions
    #-------------------------------

    def set_restrictions(self, isStatic: bool):
        """! Sets the restrictions manager to use static or dynamic restrictions. """
        print(f"Setting restrictions type to {'static' if isStatic else 'dynamic'}.")
        self.__restrictions_manager.set_restrictions(isStatic)

    def get_current_restrictions(self):
        """! Returns the currently active restrictions object. """
        return self.__restrictions_manager.get_current_restrictions()

    def change_restrictions(self, changes: list):
        """! Applies changes to the current restrictions object. """
        print(f"Applying {len(changes)} changes to restrictions...")
        self.__restrictions_manager.change_restrictions(changes)

    #-------------------------------
    # MQTT
    #-------------------------------

    def mqtt_connect(self):
        """! Connect all table sections via MQTT. """
        print("Connecting all sections via MQTT...")
        for section in self.__table_sections:
            section.mqtt_connect()

    def mqtt_disconnect(self):
        """! Disconnect all table sections from MQTT (after optional reboot). """
        print("Disconnecting all sections from MQTT...")
        for section in self.__table_sections:
            # section.reboot_section() # Consider if reboot is needed before disconnect
            section.mqtt_disconnect()

    def mqtt_selective_publish(self):
        """! Publish LED updates only for changed values. """
        for section in self.__table_sections:
            section.mqtt_update_selective_power_flow()
            section.mqtt_update_selective_background()

    def mqtt_force_publish(self):
        """! Force publish all LED values. """
        for section in self.__table_sections:
            section.mqtt_update_force_power_flow()
            section.mqtt_update_force_background()

    def mqtt_set_config(self, config_instance: MQTTConfig):
        """! Set MQTT config for all sections. """
        if not config_instance:
             print("Error: Attempted to set None as MQTT config.")
             return
        print(f"Setting MQTT config '{config_instance.get_name()}' for all sections.")
        for section in self.__table_sections:
            section.mqtt_set_config(config_instance)

    def mqtt_set_base_topic(self, topic: str):
        """! Set base MQTT topic for all sections. """
        print(f"Setting base MQTT topic to '{topic}' for all sections.")
        for section in self.__table_sections:
            section.mqtt_set_base_topic(topic)

    def mqtt_is_connected(self) -> bool:
        """! Check if all sections are connected to MQTT. """
        if not self.__table_sections: return False
        connected_count = sum(1 for section in self.__table_sections if section.mqtt_is_connected())
        return connected_count == len(self.__table_sections)

    #-------------------------------
    # Network model & Calculation
    #-------------------------------

    def get_model_lines(self) -> list[Line]:
        """! Get all lines from all sections and links. """
        lines = []
        for section in self.__table_sections:
            if hasattr(section, 'model') and hasattr(section.model, 'lines'):
                 lines.extend(section.model.lines)
            else:
                 print(f"Warning: Section {section.name} has no 'model' or 'model.lines'.")
        for link in self.__section_links:
            # Ensure link attributes exist before creating Line
            if all(hasattr(link, attr) for attr in ['name', 'bus0', 'bus1', 'x', 'r', 's_nom']):
                new_line = Line(name=link.name, bus0=link.bus0, bus1=link.bus1, x=link.x, r=link.r, s_nom=link.s_nom, type="Link", length=1) # Use generic type
                lines.append(new_line)
            else:
                print(f"Warning: SectionLink '{getattr(link, 'name', 'Unknown')}' missing attributes.")
        return lines

    def get_table_sections(self) -> list[Section]:
        """! Return list of table sections. """
        return self.__table_sections

    def set_calculation_method(self, method: str) -> None:
        """! Pass calculation method down to the model calculator. """
        print(f"Setting calculation method to: {method}")
        self.__model_calculator.set_calculation_method(method)

    def _prepare_calculation(self) -> Model | None:
         """ Helper to get model and reset flags """
         model = self.get_model()
         if not model:
              print("Error: Could not build model for calculation.")
              return None
         self.modules_reset_changed()
         self.simulation_changed = True # Mark that a calc is happening
         return model

    def selective_calculate(self) -> None:
        """! Selectively recalculate based on changes. """
        print("Starting selective calculation...")
        model = self._prepare_calculation()
        if not model: return

        # Snapshots depend on current scenario type
        snapshots = self.__current_scenario.index if self.__current_scenario else []
        if not snapshots:
             print("Warning: No snapshots found for current scenario.")
             # Decide how to handle: Use default? Return?
             # snapshots = pd.Index([pd.Timestamp.now()]) # Example: Use current time as single snapshot

        self.__model_calculator.set_input_model(model)
        self.__model_calculator.set_snapshots(snapshots) # Pass possibly adjusted snapshots
        self.__simulation_succes = self.__model_calculator.selective_calculate() # Capture success/fail

        # Post-calculation updates
        model.reset_changed_components()
        if (self.__static): self.__snapshot_index = 0 # Reset index for static
        self.update_ledstrips(self.__snapshot_index)
        self.mqtt_selective_publish()
        print("Selective calculation finished.")

    def force_calculate(self) -> None:
        """! Force recalculation of the entire model. """
        print("Starting forced calculation...")
        model = self._prepare_calculation()
        if not model: return

        snapshots = self.__current_scenario.index if self.__current_scenario else []
        if not snapshots:
             print("Warning: No snapshots found for current scenario.")
             # snapshots = pd.Index([pd.Timestamp.now()])

        self.__model_calculator.set_input_model(model)
        self.__model_calculator.set_snapshots(snapshots)
        self.__simulation_succes = self.__model_calculator.force_calculate() # Capture success/fail

        # Post-calculation updates
        model.reset_changed_components()
        if (self.__static): self.__snapshot_index = 0 # Reset index for static
        self.update_ledstrips(self.__snapshot_index)
        self.mqtt_force_publish() # Force publish LEDs after full recalc
        print("Forced calculation finished.")

    def _get_section_sum(self, table_name: str, component_type: str) -> pd.Series:
        """ Helper to calculate sum for generators, loads, or storage units """
        model = self.get_section_model(table_name)
        snapshots = self.__current_scenario.index if self.__current_scenario else []
        total_power = pd.Series(0.0, index=snapshots, dtype=float) # Initialize with zeros

        if not model or not snapshots:
            return total_power # Return empty/zero series

        components_to_sum = []
        if component_type == "generators":
            components_to_sum = model.generators
        elif component_type == "loads":
            components_to_sum = model.loads
        elif component_type == "storage_units":
            components_to_sum = model.storage_units
        else:
            print(f"Warning: Unknown component_type '{component_type}' in _get_section_sum")
            return total_power

        if not components_to_sum: # Check if the list is empty
            return total_power

        # Ensure components have active_power attribute and it matches snapshots length
        valid_components = []
        for comp in components_to_sum:
             if hasattr(comp, 'active_power') and hasattr(comp, 'output') and \
                isinstance(comp.active_power, (list, pd.Series)) and len(comp.active_power) == len(snapshots):
                  valid_components.append(comp)
             #else:
             #    print(f"Debug: Skipping component {getattr(comp, 'name', 'Unknown')} due to missing/mismatched active_power/output.")


        # Sum using pandas for potentially better performance if active_power is Series
        temp_df = pd.DataFrame(index=snapshots)
        for i, comp in enumerate(valid_components):
            # Only include if output[0] is True (assuming output[0] controls overall status)
             if comp.output and comp.output[0] is True:
                  # Ensure active_power is treated as a Series for alignment
                  temp_df[f'comp_{i}'] = pd.Series(comp.active_power, index=snapshots)

        if not temp_df.empty:
             total_power = temp_df.sum(axis=1)

        return total_power

    def get_sum_section_generation(self, table_name: str) -> pd.Series:
        """! Gets the generated power of a specific table section. """
        return self._get_section_sum(table_name, "generators")

    def get_sum_section_load(self, table_name: str) -> pd.Series:
        """! Gets the used power of a specific table section. """
        return self._get_section_sum(table_name, "loads")

    def get_sum_section_storage(self, table_name: str) -> pd.Series:
        """! Gets the stored/discharged power of storage in a specific table section. """
        return self._get_section_sum(table_name, "storage_units")

    def _get_voltage_level_sum(self, voltage_level: str, component_type: str) -> pd.Series:
         """ Helper to get sum for a voltage level """
         snapshots = self.__current_scenario.index if self.__current_scenario else []
         total_power = pd.Series(0.0, index=snapshots, dtype=float)

         if not snapshots: return total_power

         section_names = [sec.name for sec in self.__table_sections if hasattr(sec, 'voltage') and sec.voltage == voltage_level]

         if not section_names:
              print(f"Warning: No sections found for voltage level '{voltage_level}'")
              return total_power

         # Sum the series from relevant sections
         series_list = [self._get_section_sum(name, component_type) for name in section_names]

         if series_list:
              # Concatenate and sum, fill NaN with 0 before summing
              total_power = pd.concat(series_list, axis=1).fillna(0).sum(axis=1)

         return total_power

    def get_voltage_sum_generation(self, voltage_level: str) -> pd.Series:
        """! Gets the generated power of a specific voltage level. """
        return self._get_voltage_level_sum(voltage_level, "generators")

    def get_voltage_sum_load(self, voltage_level: str) -> pd.Series:
        """! Gets the used power of a specific voltage level. """
        return self._get_voltage_level_sum(voltage_level, "loads")

    def get_voltage_sum_storage(self, voltage_level: str) -> pd.Series: # Added storage sum
        """! Gets the storage power of a specific voltage level. """
        return self._get_voltage_level_sum(voltage_level, "storage_units")

    def get_voltage_sum(self, voltage_level: str) -> pd.DataFrame:
        """! Gets generated, used, and storage power for a specific voltage level. """
        pd_generation = self.get_voltage_sum_generation(voltage_level)
        pd_load = self.get_voltage_sum_load(voltage_level)
        pd_storage = self.get_voltage_sum_storage(voltage_level) # Added
        # Combine into DataFrame
        pd_dataframe = pd.concat([pd_generation, pd_load, pd_storage], axis=1, keys=["Generation", "Load", "Storage"]) # Added Storage
        return pd_dataframe

    def _get_full_grid_sum(self, component_type: str) -> pd.Series:
        """ Helper to get total sum across all sections """
        snapshots = self.__current_scenario.index if self.__current_scenario else []
        total_power = pd.Series(0.0, index=snapshots, dtype=float)

        if not snapshots: return total_power

        series_list = [self._get_section_sum(section.name, component_type) for section in self.__table_sections]

        if series_list:
            total_power = pd.concat(series_list, axis=1).fillna(0).sum(axis=1)

        return total_power

    def get_sum_generation(self) -> pd.Series:
        """! Gets the total generated power of the whole grid. """
        return self._get_full_grid_sum("generators")

    def get_sum_load(self) -> pd.Series:
        """! Gets the total used power of the whole grid. """
        return self._get_full_grid_sum("loads")

    def get_sum_storage(self) -> pd.Series:
        """! Gets the total storage power of the whole grid. """
        return self._get_full_grid_sum("storage_units")

    def get_full_grid_sum_generation_loads_storage(self) -> pd.DataFrame:
        """! Gets the total generated, used, and storage power for the whole grid. """
        pd_generation = self.get_sum_generation()
        pd_load = self.get_sum_load()
        pd_storage = self.get_sum_storage()
        pdfinal = pd.concat([pd_generation, pd_load, pd_storage], axis=1, keys=["Generation", "Load", "Storage"])
        return pdfinal

    def _get_module_dataframe(self, table_name: str, component_type: str) -> pd.DataFrame:
         """ Helper to get DataFrame per module type for a section """
         snapshots = self.__current_scenario.index if self.__current_scenario else []
         model = self.get_section_model(table_name)
         pd_dataframe = pd.DataFrame(index=snapshots)

         if not model or not snapshots: return pd_dataframe

         components_list = []
         if component_type == "generators": components_list = model.generators
         elif component_type == "loads": components_list = model.loads
         elif component_type == "storage_units": components_list = model.storage_units
         else: return pd_dataframe

         for comp in components_list:
              # Check attributes and length consistency
              if hasattr(comp, 'output') and comp.output and comp.output[0] is True and \
                 hasattr(comp, 'active_power') and isinstance(comp.active_power, (list, pd.Series)) and \
                 len(comp.active_power) == len(snapshots) and hasattr(comp, 'name'):
                  pd_series = pd.Series(comp.active_power, index=snapshots, name=comp.name)
                  pd_dataframe = pd.concat([pd_dataframe, pd_series], axis=1)

         return pd_dataframe

    def get_table_section_module_generation(self, table_name: str) -> pd.DataFrame:
        """! Gets the generated power of each active module on a table section. """
        return self._get_module_dataframe(table_name, "generators")

    def get_table_section_module_load(self, table_name: str) -> pd.DataFrame:
        """! Gets the consumed power of each active module on a table section. """
        return self._get_module_dataframe(table_name, "loads")

    def get_table_section_module_storage(self, table_name: str) -> pd.DataFrame:
        """! Gets the stored/discharged power of each active module on a table section. """
        return self._get_module_dataframe(table_name, "storage_units")

    def get_table_section_module_all(self, table_name: str) -> pd.DataFrame:
        """! Gets all module info (gen, load, storage) for a table section. """
        # Note: concat might result in duplicate columns if names overlap.
        pd_generation = self.get_table_section_module_generation(table_name)
        pd_load = self.get_table_section_module_load(table_name)
        pd_storage = self.get_table_section_module_storage(table_name)
        # Use multi-index columns to distinguish types
        all_dfs = {}
        if not pd_generation.empty: all_dfs['Generation'] = pd_generation
        if not pd_load.empty: all_dfs['Load'] = pd_load
        if not pd_storage.empty: all_dfs['Storage'] = pd_storage

        if not all_dfs: return pd.DataFrame() # Return empty if no data

        pdfinal = pd.concat(all_dfs, axis=1)
        return pdfinal

    def get_table_sum(self, table_name: str) -> pd.DataFrame:
        """! Gets the total generated and used power of a specific table section. """
        pd_generation = self.get_sum_section_generation(table_name)
        pd_load = self.get_sum_section_load(table_name)
        pd_storage = self.get_sum_section_storage(table_name) # Added storage
        pdfinal = pd.concat([pd_generation, pd_load, pd_storage], axis=1, keys=["Generation", "Load", "Storage"]) # Added Storage
        return pdfinal

    def transformer_capacity(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """! Returns dataframes for transformer power (p0) and nominal capacity (s_nom). """
        snapshots = self.__current_scenario.index if self.__current_scenario else []
        pd_power = pd.DataFrame(index=snapshots)
        pd_capacity = pd.DataFrame(index=snapshots) # Capacity can vary per snapshot? Unlikely but match index

        if not snapshots: return pd_power, pd_capacity

        for section in self.__table_sections:
            if hasattr(section, 'model') and hasattr(section.model, 'transformers'):
                 for transformer in section.model.transformers:
                      if hasattr(transformer, 'active_power_0') and \
                         isinstance(transformer.active_power_0, (list, pd.Series)) and \
                         len(transformer.active_power_0) == len(snapshots) and hasattr(transformer, 'name'):
                           pd_series = pd.Series(transformer.active_power_0, index=snapshots, name=transformer.name)
                           pd_power = pd.concat([pd_power, pd_series], axis=1)

                      if hasattr(transformer, 'capacity') and hasattr(transformer, 'name'):
                           # Capacity is likely scalar, repeat it for all snapshots
                           capacity_val = transformer.capacity if transformer.capacity is not None else 0.0
                           pd_seriescap = pd.Series(capacity_val, index=snapshots, name=transformer.name)
                           pd_capacity = pd.concat([pd_capacity, pd_seriescap], axis=1)

        return pd_power, pd_capacity

    def get_snapshot_response_gui(self) -> dict:
        """! Creates a structured dictionary response for GUI snapshots. """
        response = {
            'type': 'NETWORK_SNAPSHOTS',
            'payload': {
                'transformerCapacityGraphs': {},
                'powerPerTableSection': {},
                'powerPerVoltageLevel': {},
                'powerTotal': {}
            }
        }

        if not self.get_simulation_succes():
            print("Warning: Cannot generate snapshot response, simulation failed.")
            return response # Return empty structure

        # Assuming static scenario for simplicity here - adapt for dynamic if needed
        # Needs current snapshot index if dynamic
        snap_idx = self.__snapshot_index if not self.__static else 0

        transformer_df, capacity_df = self.transformer_capacity()
        for col in transformer_df.columns:
            capacity = capacity_df[col].iloc[snap_idx] if snap_idx < len(capacity_df) else 0
            power = transformer_df[col].iloc[snap_idx] if snap_idx < len(transformer_df) else 0
            usage_perc = round(abs(power / capacity * 100), 2) if capacity != 0 else 0
            response['payload']['transformerCapacityGraphs'][col] = {'Capacity Usage': usage_perc, 'Power': round(power, 3)}

        for i in range(len(self.__table_sections)):
            section_name = f'Table{i+1}'
            section_df = self.get_table_sum(section_name)
            if snap_idx < len(section_df):
                response['payload']['powerPerTableSection'][section_name] = section_df.iloc[snap_idx].round(3).to_dict()
            else:
                response['payload']['powerPerTableSection'][section_name] = {"Generation": 0, "Load": 0, "Storage": 0}


        for level in ['LV', 'MV', 'HV']:
            level_df = self.get_voltage_sum(level)
            if snap_idx < len(level_df):
                 response['payload']['powerPerVoltageLevel'][level] = level_df.iloc[snap_idx].round(3).to_dict()
            else:
                 response['payload']['powerPerVoltageLevel'][level] = {"Generation": 0, "Load": 0, "Storage": 0}


        power_df = self.get_full_grid_sum_generation_loads_storage()
        if snap_idx < len(power_df):
            response['payload']['powerTotal']['Network'] = power_df.iloc[snap_idx].round(3).to_dict()
        else:
            response['payload']['powerTotal']['Network'] = {"Generation": 0, "Load": 0, "Storage": 0}


        # --- Dynamic Scenario Specific Part (If needed) ---
        # if not self.__static:
        #     # Reformat dataframes to lists per key if GUI expects that for dynamic
        #     # Example for transformers:
        #     transformer_payload_dynamic = {}
        #     transformer_df_dyn, capacity_df_dyn = self.transformer_capacity()
        #     for col in transformer_df_dyn.columns:
        #          transformer_payload_dynamic[f'{col}_Power'] = transformer_df_dyn[col].round(3).tolist()
        #          transformer_payload_dynamic[f'{col}_Capacity'] = capacity_df_dyn[col].round(3).tolist() # Assuming capacity is Series
        #     response['payload']['transformerCapacityGraphs'] = transformer_payload_dynamic
        #     # Similar logic for other categories...

        return response


    def change_photovoltaic(self, direction: str, module_rfid: str):
        """! Changes the direction for a specific PV module via its RFID tag. """
        print(f"Attempting to change PV module '{module_rfid}' direction to '{direction}'...")
        found_module = False
        # Iterate through the catalog in the current scenario
        if not self.__current_scenario or not self.__current_scenario.catalog:
             print("Error: No current scenario or catalog loaded.")
             return

        if module_rfid in self.__current_scenario.catalog:
            module_data = self.__current_scenario.catalog[module_rfid]
            if "photovoltaic" in module_data and isinstance(module_data["photovoltaic"], list) and module_data["photovoltaic"]:
                 pv_component = module_data["photovoltaic"][0] # Assume first PV component
                 azimuth_map = {"South": 180, "East": 90, "West": 270}
                 enable = True

                 if direction in azimuth_map:
                      pv_component["surface_azimuth"] = azimuth_map[direction]
                 elif direction.lower() == "none":
                      enable = False
                 else:
                      print(f"Error: Invalid direction '{direction}'. Use South, East, West, or None.")
                      return

                 pv_component["enable"] = enable
                 found_module = True
                 print(f"PV module '{module_rfid}' updated in catalog: Azimuth={pv_component.get('surface_azimuth', 'N/A')}, Enabled={enable}")
                 # Reload modules to apply changes from catalog to simulation model
                 self.modules_reload()
                 # self.force_calculate() # Force recalc is handled by force_update flag in handler
            else:
                 print(f"Error: Module '{module_rfid}' found but has no valid 'photovoltaic' data.")
        else:
            print(f"Error: Module with RFID tag '{module_rfid}' not found in current scenario catalog.")

        # if found_module:
            # Force recalculation is handled by setting force_update = True in the handler


    def get_model(self) -> Model:
        """! Construct the complete simulation Model object from sections and links. """
        model = Model()
        print("Building full simulation model...")

        # 1. Add components from each section
        for section in self.__table_sections:
            section.reload_model() # Ensure section model is up-to-date with its modules
            if hasattr(section, 'model'):
                 # Add buses first
                 if hasattr(section.model, 'buses'):
                      for bus in section.model.buses: model.add_bus(bus)
                 # Then other components
                 if hasattr(section.model, 'generators'):
                      for generator in section.model.generators: model.add_generator(generator)
                 if hasattr(section.model, 'loads'):
                      for load in section.model.loads: model.add_load(load)
                 if hasattr(section.model, 'storage_units'):
                      for storage_unit in section.model.storage_units: model.add_storage_unit(storage_unit)
                 # Add lines last within section? Order might matter for dependencies
                 if hasattr(section.model, 'lines'):
                      for line in section.model.lines: model.add_line(line)
                 # Add transformers
                 if hasattr(section.model, 'transformers'):
                      for transformer in section.model.transformers:
                          # Find the specific link for this transformer by matching platform/module placement
                          transformer_connected = False
                          
                          # Get the RFID tag from the transformer name (e.g., "Table1_1071746625_Transformer0" -> "1071746625")
                          transformer_rfid = None
                          name_parts = transformer.name.split("_")
                          if len(name_parts) >= 2:
                              transformer_rfid = name_parts[1]  # Extract RFID from name
                          
                          if transformer_rfid:
                              # Find the platform that has this specific transformer module
                              platform_location = None
                              for platform in section.platforms:
                                  if platform.module is not None and hasattr(platform.module, 'RFID_tag'):
                                      if platform.module.RFID_tag == transformer_rfid:
                                          platform_location = platform.RFID_location
                                          break
                              
                              # Now find the matching TransformerLink for this specific platform location
                              if platform_location is not None:
                                  for link in self.__transformer_links:
                                      if link.RFID_table == section.name and link.RFID == platform_location:
                                          # Set transformer bus connections based on this specific TransformerLink
                                          transformer.bus0 = link.bus0  # HV side
                                          transformer.bus1 = link.bus1  # LV side
                                          transformer_connected = True
                                          print(f"DEBUG: Connected transformer {transformer.name} (RFID: {transformer_rfid}, Platform: {platform_location}) - bus0: {transformer.bus0}, bus1: {transformer.bus1}")
                                          break

                          # Only add transformer if it has valid bus connections
                          if transformer_connected and transformer.bus0 and transformer.bus1:
                               model.add_transformer(transformer)
                          else:
                               print(f"DEBUG: Skipping transformer {transformer.name} - no valid connections or module not placed")


            else:
                 print(f"Warning: Section {section.name} has no 'model' attribute.")

        # 2. Add lines representing fixed section links
        print("Adding section link lines...")
        for link in self.__section_links:
            if all(hasattr(link, attr) for attr in ['name', 'bus0', 'bus1', 'x', 'r', 's_nom']):
                new_line = Line(name=link.name, bus0=link.bus0, bus1=link.bus1, x=link.x, r=link.r, s_nom=link.s_nom, type="Link", length=1)
                model.add_line(new_line)
            else:
                print(f"Warning: SectionLink '{getattr(link, 'name', 'Unknown')}' missing attributes.")

        # 3. Add lines representing dynamic transformer links (if module placed)
        print("Adding transformer link lines (if applicable)...")
        for link in self.__transformer_links:
             # Check if the corresponding module is placed
             module_placed = False
             section = self._find_section(link.RFID_table)
             if section:
                  for platform in section.platforms:
                       if platform.RFID_location == link.RFID and platform.module is not None:
                            module_placed = True
                            break
             if module_placed:
                  # Module is placed, add a line representing the transformer connection
                  if all(hasattr(link, attr) for attr in ['bus0', 'bus1']):
                       # Assume transformer link represents a simple line for modeling purposes
                       # Need default line parameters (x, r, s_nom) for these links
                       # TODO: Define default parameters for transformer links or get from catalog
                       default_x = 0.01
                       default_r = 0.001
                       default_s_nom = 1000 # kVA? MVA? Needs context
                       trans_link_name = f"TLink_{link.RFID_table}_{link.RFID}"
                       new_line = Line(name=trans_link_name, bus0=link.bus0, bus1=link.bus1,
                                       x=default_x, r=default_r, s_nom=default_s_nom, type="TransformerLink", length=1)
                       model.add_line(new_line)
                  else:
                       print(f"Warning: TransformerLink for {link.RFID_table}/{link.RFID} missing bus attributes.")


        print(f"Model build complete. Buses: {len(model.buses)}, Lines: {len(model.lines)}, Gens: {len(model.generators)}, Loads: {len(model.loads)}, Storage: {len(model.storage_units)}, Transformers: {len(model.transformers)}")
        return model


    def get_section_model(self, table_name: str) -> Model | None:
        """! Return the model of one specific table section. """
        section = self._find_section(table_name)
        if section and hasattr(section, 'model'):
            return section.model
        print(f"Warning: Could not find model for section '{table_name}'.")
        return None

    #-------------------------------
    # Miscellaneous
    #-------------------------------

    def get_lep_update_flag(self) -> bool:
        """! Check if any section requires an LED update. """
        # Original logic checked self.__led_update_flag, let's stick to checking sections
        for section in self.__table_sections:
            if section.get_led_update_flag(): # Assumes method exists in Section
                return True
        return False


    def reset_led_update_flag(self) -> None:
        """! Resets the LED update flag in all sections. """
        # self.__led_update_flag = False # Reset own flag if used elsewhere
        for section in self.__table_sections:
            section.reset_led_update_flag() # Assumes method exists in Section


    def update_ledstrips(self, snapshot_index: int) -> None:
        """! Update the ledstrip active power values based on simulation results. """
        # Make sure snapshot_index is valid
        if self.__current_scenario and snapshot_index >= len(self.__current_scenario.index):
             print(f"Warning: snapshot_index {snapshot_index} out of bounds for current scenario. Using 0.")
             snapshot_index = 0
        elif not self.__current_scenario:
             print("Warning: No current scenario, cannot update LEDs.")
             return

        for section in self.__table_sections:
            if not hasattr(section, 'ledstrips') or not hasattr(section, 'model') or not hasattr(section.model, 'lines'):
                 continue # Skip sections without necessary attributes

            num_ledstrips = len(section.ledstrips)
            num_lines = len(section.model.lines)

            # Iterate safely, up to the minimum of available ledstrips and lines
            for index in range(min(num_ledstrips, num_lines)):
                ledstrip = section.ledstrips[index]
                line = section.model.lines[index]

                # Check if line has results for the given snapshot
                if not hasattr(line, 'active_power') or not hasattr(line, 'output') or \
                   snapshot_index >= len(line.active_power) or snapshot_index >= len(line.output):
                    # print(f"Debug: Skipping LED update for line {index} in {section.name} - missing data for snapshot {snapshot_index}")
                    # Set LED to off/error state?
                    flow_color = RBGAColor(0, 0, 0, 0)
                    background_color = RBGColor(128, 0, 0) # Error color?
                    ledstrip.set_flow_color(flow_color)
                    ledstrip.set_background_color(background_color)
                    ledstrip.set_background_flashing_time(75)
                    continue

                active_power = line.active_power[snapshot_index]
                line_output_active = line.output[snapshot_index] # Is this line carrying power?
                line_component_active = line.active # Is the line component itself enabled?

                absolute_active_power = abs(active_power)

                # --- Default LED settings ---
                ledstrip.set_background_color(section.background_color) # Use section default bg
                ledstrip.set_background_flashing_time(0)
                ledstrip.set_flow_speed(400) # Default speed

                # Determine flow direction
                if absolute_active_power > 1e-5: # Threshold to avoid near-zero flips
                    ledstrip.flow_direction = 0 if active_power >= 0 else 1
                else:
                     ledstrip.flow_direction = 0 # Or keep previous? Set default.

                # Determine flow color and speed based on power thresholds
                flow_color = RBGAColor(0, 0, 0, 255) # Default to black (off)
                flow_speed = 400 # Default speed

                if absolute_active_power < section.threshold_low:
                    flow_color.green = 128
                    flow_speed = 300
                elif absolute_active_power < section.threshold_normal:
                    relative = (absolute_active_power - section.threshold_low) / (section.threshold_normal - section.threshold_low + 1e-9) # Avoid div by zero
                    flow_color.green = int(128 + relative * 127)
                    flow_speed = 200
                elif absolute_active_power < section.threshold_high:
                    relative = (absolute_active_power - section.threshold_normal) / (section.threshold_high - section.threshold_normal + 1e-9)
                    flow_color.red = int(relative * 255)
                    flow_color.green = 255
                    flow_speed = 200
                elif absolute_active_power < section.threshold_critical:
                    relative = (absolute_active_power - section.threshold_high) / (section.threshold_critical - section.threshold_high + 1e-9)
                    flow_color.red = 255
                    flow_color.green = int(255 - relative * 255)
                    flow_speed = 100
                else: # Above critical
                    flow_color.red = 255
                    flow_color.green = 0
                    flow_speed = 100

                # Handle very low power (set flow alpha to 0)
                if absolute_active_power < 1e-5:
                    flow_color.alpha = 0

                ledstrip.set_flow_color(flow_color)
                ledstrip.set_flow_speed(flow_speed)

                # --- Handle Line Output Status ---
                # If line result shows no output power (output=False), maybe set background?
                # This might conflict with line component status below. Decide priority.
                # if not line_output_active:
                #    # Optional: indicate inactive line result differently, e.g., grey bg
                #    ledstrip.set_background_color(RBGColor(50, 50, 50))
                #    pass

                # --- Handle Line Component Status (active=False) ---
                # If the line component itself is disabled, turn LED off completely
                if not line_component_active:
                    off_flow = RBGAColor(0, 0, 0, 0)
                    off_background = RBGColor(0, 0, 0)
                    ledstrip.set_flow_color(off_flow)
                    ledstrip.set_background_color(off_background)
                    ledstrip.set_background_flashing_time(0)
                    ledstrip.set_flow_speed(0) # Stop flow completely

                # Handle LED strip error state (overrides other states)
                if hasattr(ledstrip, 'error') and ledstrip.error:
                    err_flow = RBGAColor(0, 0, 0, 0)
                    err_background = RBGColor(128, 0, 0) # Flashing Red Background
                    ledstrip.set_flow_color(err_flow)
                    ledstrip.set_background_color(err_background)
                    ledstrip.set_background_flashing_time(75) # Standard flash time


    def append_delta_time(self, delta_time: float):
        """! Increment elapsed time for dynamic scenarios. """
        if not self.__static:
            self.__elapsed_time += delta_time

    def set_index(self, index: int):
        """! Manually sets the snapshot index for dynamic scenarios (or static view). """
        total_snapshots = len(self.__current_scenario.index) if self.__current_scenario else 0
        if 0 <= index < total_snapshots:
             self.__snapshot_index = index
             print(f"Snapshot index manually set to: {index}")
             # Force LED update for the new index
             self.update_ledstrips(self.__snapshot_index)
             self.mqtt_selective_publish() # Send new LED state
             self.snapshot_changed = True # Indicate state changed
        else:
             print(f"Error: Invalid snapshot index {index}. Valid range is 0 to {total_snapshots-1}.")

    def stop_running(self):
        """! Stops automatic index increment for dynamic scenarios. """
        if not self.__static:
             print("Stopping automatic snapshot advancement.")
             self.__running = False # Use internal running flag? Or need separate dynamic running flag?
             # Let's assume the global 'running' flag controls this too for now.

    def start_running(self):
        """! Starts automatic index increment for dynamic scenarios. """
        if not self.__static:
             print("Starting automatic snapshot advancement.")
             self.__running = True # Use internal running flag?

    def update(self):
        """! Handles snapshot advancement for dynamic scenarios. """
        if self.__static: return # Only run for dynamic scenarios

        # Check if automatic advancement is enabled (using __running flag for now)
        # if not self.__running: return

        if not self.__current_scenario or not self.__current_scenario.time_per_snapshot:
             return # Cannot advance without scenario/time info

        if self.__elapsed_time >= self.__current_scenario.time_per_snapshot:
            self.__elapsed_time -= self.__current_scenario.time_per_snapshot # Subtract interval, don't just reset
            total_snapshots = len(self.__current_scenario.index)
            if total_snapshots > 0:
                 self.__snapshot_index = (self.__snapshot_index + 1) % total_snapshots
                 print(f"Advanced to snapshot index: {self.__snapshot_index}")
                 self.snapshot_changed = True
                 # Update LEDs for the new snapshot
                 self.update_ledstrips(self.__snapshot_index)
                 self.mqtt_selective_publish()
                 # Snapshot data should be published AFTER calculation, maybe trigger here?
                 # ui_handler({'type': 'SEND_SNAPSHOTS'}) # Send new snapshot data


    def get_simulation_succes(self) -> bool:
        """! Check if the last simulation calculation was successful. """
        # This should ideally be set by the calculate methods in ModelProcessorInterface
        return self.__simulation_succes

    def get_current_snapshot(self):
        """! Get the timestamp/label of the current snapshot index. """
        if self.__current_scenario and 0 <= self.__snapshot_index < len(self.__current_scenario.index):
            return self.__current_scenario.index[self.__snapshot_index]
        return None # Return None if invalid

    def get_snapshots(self):
        """! Get the list of all snapshot timestamps/labels. """
        return self.__current_scenario.index if self.__current_scenario else []

    def get_generators_generation(self):
        # TODO: Implement based on aggregated model results
        pass

    def get_load_consumption(self):
        # TODO: Implement based on aggregated model results
        pass

    def get_local_setup(self) -> bool:
        """! Returns True if configured for local setup (e.g., enables UDP). """
        return self.__local_setup

    def table_set_line_status(self, table_idx: int, sim_line_id: int, status: bool):
        """! Sets the 'active' status of a specific line in the simulation model. """
        # Needs careful mapping from GUI table/line index to actual model line object/index
        print(f"Attempting to set line status: Table Index={table_idx}, Sim Line ID={sim_line_id}, Status={status}")
        # This requires finding the correct line object within the combined model,
        # which is complex given the current structure.
        # Option 1: Find the line by name/bus connections in the full model?
        # Option 2: Modify the model *within* the specific section *before* get_model() is called?
        # Option 3: Pass the line object reference through the mapping?
        # For now, this function needs a proper implementation based on how lines are identified
        # across sections in the combined model or how sections manage their line states.
        # Placeholder:
        model = self.get_model() # Rebuild model? Risky. Better modify section state.
        section = self.__table_sections[table_idx] if 0 <= table_idx < len(self.__table_sections) else None
        if section and hasattr(section, 'model') and hasattr(section.model, 'lines'):
             # This assumes sim_line_id is the INDEX within that section's lines list
             if 0 <= sim_line_id < len(section.model.lines):
                  section.model.lines[sim_line_id].active = status
                  print(f"Set section {section.name} line index {sim_line_id} active status to {status}")
                  # Mark model as changed?
                  # self.force_calculate() # Triggered by force_update flag set in handler
             else:
                  print(f"Error: Sim line index {sim_line_id} out of bounds for section {section.name}")
        else:
             print(f"Error: Cannot find section or lines for table index {table_idx}")

# --- Einde Klasse SmartGridTable ---