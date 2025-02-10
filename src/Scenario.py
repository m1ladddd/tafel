##
# @file Scenario.py
#
# @brief Class which represents a scenario, scenarios are loaded from JSON files (for static) and saved here.
# Specific Components can be retrieved using the get_modules(RFID) method where you need to provide a RFID id.
#
# @section libraries_Scenario Libraries/Modules
# - 
#
# @section todo_Scenario TODO
# - None
#
# @section author_Scenario Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

# Internal imports
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.StorageUnit import StorageUnit
from src.model.components.Transformer import Transformer
from src.PhotoVoltaic import PhotoVoltaic
from src.PvPower import PvPower
from src.Module import Module

# External imports
from os.path import exists
import pandas as pd
import numpy as np
import json

class Scenario:
    """! 
    Class which represents a scenario, scenarios are loaded from JSON files (for static) and saved here.
    Specific Components can be retrieved using the get_modules(RFID) method where you need to provide a RFID id.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        ## Dictonary containing all 3D objects with PyPSA component data.
        self.catalog = {}

        ## Bool indicating if this scenario is static or not (True = static, False = Dynamic).
        self.static = False

        ## Bool indicating if scenario load was succesfull.
        self.succes = False
        
        self.PvPow=PvPower()

        ## Snapshot for Dynamic scenario. For static scenarios this is always 0.
        self.index = [0]

        ## Amount of seconds between snapshot iterations
        self.time_per_snapshot = 1

        ## Path of scenario .JSON
        self.filepath = ""

    def referenceless_catalog(self):
        """!
        Replaces all references to CSV files by their contents.
        @return Dict catalog.
        """
        copy_catalog = self.catalog
        for key,value in self.catalog.items():
            if type(value) == dict:
                if 'generators' in value.keys():
                    for i in range(len(value['generators'])):
                        for k,v in value['generators'][i].items():
                            val = self.__derefrence_component_value_series(v)

                            if isinstance(val, pd.Series):
                                val = val.to_list()
                            
                            copy_catalog[key]['generators'][i][k] = val

                if 'storages' in value.keys():
                    for i in range(len(value['storages'])):
                        for k,v in value['storages'][i].items():
                            val = self.__derefrence_component_value_series(v)

                            if isinstance(val, pd.Series):
                                val = val.to_list()

                            copy_catalog[key]['storages'][i][k] = val

                if 'transformers' in value.keys():
                    for i in range(len(value['transformers'])):
                        for k,v in value['transformers'][i].items():
                            val = self.__derefrence_component_value_series(v)

                            if isinstance(val, pd.Series):
                                val = val.to_list()

                            copy_catalog[key]['transformers'][i][k] = val

                if 'loads' in value.keys():
                    for i in range(len(value['loads'])):
                        for k,v in value['loads'][i].items():
                            val = self.__derefrence_component_value_series(v)

                            if isinstance(val, pd.Series):
                                val = val.to_list()

                            copy_catalog[key]['loads'][i][k] = val

        return copy_catalog
    
    def __derefrence_component_value_list(self, value):
        """! 
        Taks a value or CSV filepath and returns a value or pandas Series read from he CSV file.
        This is used to load in CSV references in the JSON files.
        @param value Int value or str filepath.
        @return Int value or pandas Series read from the CSV file.
        """
        if (type(value) == str):
            # Check if value is a reference to a CSV file
            if (value[-4:] == ".csv"):
                pd_csv = pd.read_csv(value)
                pd_csv.fillna(method="ffill",inplace=True)
                value_list = pd_csv.value.tolist()
                return value_list
        # No csv file
        return value


    def __derefrence_component_value_series(self, value):
        """! 
        Taks a value or CSV filepath and returns a value or pandas Series read from he CSV file.
        This is used to load in CSV references in the JSON files.
        @param value Int value or str filepath.
        @return Int value or pandas Series read from the CSV file.
        """
        if (type(value) == str):
            # Check if value is a reference to a CSV file
            if (value[-4:] == ".csv"):
                pd_csv = pd.read_csv(value)
                pd_df=pd.DataFrame()
                pd_df["index"]=self.index
                pd_df["values"]=pd_csv
                pd_df.fillna(method="ffill",inplace=True)
                pd_df.set_index(pd_df["index"],inplace=True)
                pd_series=pd_df["values"].squeeze()
                return pd_series
        # No csv file
        return value


    def load_scenario(self, filepath):
        """! 
        Take in a filepath to a .JSON file and load all the contents.
        @param filepath (str) Path to .JSON scenario.
        @return Bool (True = succesfull, False = error loading file).
        """
        file_exists = exists(filepath)

        if (file_exists):
            with open(filepath) as json_file:
                self.catalog = json.load(json_file)
                self.succes = True
                self.filepath = filepath
                self.static = self.is_static()
                print("Loaded scenario -> " + filepath)
                print("    Scenario name     -> " + str(self.get_name()))

                if (self.is_static()):
                    print("    Scenario type     -> Static")
                    self.index=["now"]
                else:
                    self.index = pd.date_range(self.get_begin_date(), self.get_end_date(), freq=self.get_frequency())
                    self.time_per_snapshot = self.catalog.get("time_per_snapshot")

                    print("    Scenario type     -> Dynamic")
                    print("    Total snapshots   -> " + str(len(self.index)))
                    print("    Time per snapshot -> " + str(self.time_per_snapshot))
        else:
            self.succes = False
            print("Could not load scenario -> " + filepath)
        return self.succes


    def print_scenario(self):
        """! 
        Print the current scenario parameters.
        """
        print("Current scenario...")
        print("    Name    -> " + str(self.get_name()))        
        if (self.is_static()):
            print("    Type    -> Static")
        else:
            print("    Type    -> Dynamic")


    def is_static(self):
        """! 
        Return if current scenario is static.
        @return Bool (True = static scenario, False = dynamic scenario).
        """
        if str(self.catalog.get("simulation_type")):
            if(self.catalog.get("simulation_type") == "Static"):
                return True
            else:
                return False


    def get_begin_date(self):
        """! 
        Return the begin date of the dynamic scenario.
        @return Start date of scenario.
        """
        return self.catalog.get("begin_date")


    def get_end_date(self):
        """! 
        Return the end date of the dynamic scenario.
        @return End date of scenario.
        """
        return self.catalog.get("end_date")


    def get_frequency(self):
        """! 
        Return the format of time unit (H = hours, etc).
        @return Time unit in string format.
        """
        return self.catalog.get("frequency")


    def get_name(self) -> str:
        """! 
        Return the name of the scenario in string format.
        @return Scenario name in string format.
        """
        return self.catalog.get("name")


    def get_module(self, RFID_tag):
        """! 
        Takes a RFID tag and returns the corresponding Module instance.
        If the RFID is invalid, return None.
        @return Module instance connected to the RFID tag.
        """
        if (self.succes == False):
            return None
        module = Module()
        module_dict = self.catalog.get(RFID_tag)        

        if (module_dict == None):
            return None
        name = module_dict.get("name")
        voltage = module_dict.get("voltage")

        if (name == None):
            print("    No name in module")
            return None

        if (voltage == None):
            print("    No voltage in module...")
            return None

        generators_list = module_dict.get("generators")
        loads_list = module_dict.get("loads")
        storages_list = module_dict.get("storages")
        transformers_list = module_dict.get("transformer")
        photovoltaic_list = module_dict.get("photovoltaic")

        if (generators_list == None and 
            loads_list == None and 
            storages_list == None and 
            transformers_list == None and 
            photovoltaic_list == None):
            print("    No componments found in module...")
            return None

        module.name = name
        module.voltage = voltage
        module.RFID_tag = RFID_tag
        if (generators_list != None):
            generator_index = 0
            for generator_dict in generators_list:
                generator = Generator()
                generator.changed = True
                generator.name = str(RFID_tag) + "_Gen" + str(generator_index)
                generator.type = "Generator"
                generator.p_nom = generator_dict.get("p_nom") or generator.p_nom
                generator.p_set = generator_dict.get("p_set") or generator.p_set                
                generator.p_max_pu = generator_dict.get("p_max_pu") or generator.p_max_pu
                generator.p_min_pu = generator_dict.get("p_min_pu") or generator.p_min_pu
                generator.p_nom_min = generator_dict.get("p_nom_min") or generator.p_nom_min
                generator.p_nom_max = generator_dict.get("p_nom_max") or generator.p_nom_max
                generator.marginal_cost = generator_dict.get("marginal_cost") or generator.marginal_cost
                generator.p_nom_extendable = generator_dict.get("p_nom_extendable") or generator.p_nom_extendable
                pd_p_max_pu = self.__derefrence_component_value_series(generator.p_max_pu)
                generator.p_max_pu = pd_p_max_pu
                module.add_component(generator)
                generator_index += 1

        if(photovoltaic_list != None):
            photovoltaic_index=0
            for photovoltaic_dict in photovoltaic_list:
                photovoltaic=PhotoVoltaic()
                photovoltaic.changed = True
                photovoltaic.name= str(RFID_tag) + "_PV" + str(photovoltaic_index)       
                photovoltaic.type="Generator"
                photovoltaic.p_nom=photovoltaic_dict.get("p_nom") or photovoltaic.p_nom
                photovoltaic.p_set=photovoltaic_dict.get("p_set") or photovoltaic.p_set
                photovoltaic.p_max_pu=photovoltaic_dict.get("p_max_pu") or photovoltaic.p_max_pu
                photovoltaic.p_min_pu=photovoltaic_dict.get("p_min_pu") or photovoltaic.p_min_pu
                photovoltaic.p_nom_min=photovoltaic_dict.get("p_nom_min") or photovoltaic.p_nom_min
                photovoltaic.p_nom_max=photovoltaic_dict.get("p_nom_max") or photovoltaic.p_nom_max
                photovoltaic.marginal_cost=photovoltaic_dict.get("marginal_cost") or photovoltaic.marginal_cost
                photovoltaic.p_nom_extendable=photovoltaic_dict.get("p_nom_extendable") or photovoltaic.p_nom_extendable
                photovoltaic.long=photovoltaic_dict.get("long") or photovoltaic.long
                photovoltaic.lat=photovoltaic_dict.get("lat") or photovoltaic.lat
                photovoltaic.pitch=photovoltaic_dict.get("pitch") or photovoltaic.pitch
                photovoltaic.axisazimuth=photovoltaic_dict.get("axisazimuth") or photovoltaic.axisazimuth
                photovoltaic.albedo=photovoltaic_dict.get("albedo") or photovoltaic.albedo
                photovoltaic.surface_azimuth=photovoltaic_dict.get("surface_azimuth") or photovoltaic.surface_azimuth
                photovoltaic.surface_tilt=photovoltaic_dict.get("surface_tilt") or photovoltaic.surface_tilt
                photovoltaic.pvrows=photovoltaic_dict.get("pvrows") or photovoltaic.pvrows
                photovoltaic.temp_air=photovoltaic_dict.get("temp_air") or photovoltaic.temp_air
                photovoltaic.wind_speed=photovoltaic_dict.get("wind_speed") or photovoltaic.wind_speed
                photovoltaic.enable=photovoltaic_dict.get("enable") or photovoltaic.enable
                if(photovoltaic.enable is False):
                    photovoltaic.p_max_pu=0
                else:
                    photovoltaic.p_max_pu=self.PvPow.calculate_pv(photovoltaic,self.index,self.is_static())
                module.add_component(photovoltaic)
                photovoltaic_index+=1                

        if (loads_list != None):
            load_index = 0
            for load_dict in loads_list:                
                load = Load()
                load.changed = True
                load.name = str(RFID_tag) + "_Load" + str(load_index)
                load.type = "Load"
                load.carrier = load_dict.get("carrier") or load.carrier
                load.p_set = load_dict.get("p_set") or load.p_set
                load.q_set = load_dict.get("q_set") or load.q_set
                pd_p_set = self.__derefrence_component_value_series(load.p_set)
                load.p_set = pd_p_set
                module.add_component(load)
                load_index += 1

        if (storages_list != None):
            storage_index = 0
            for storage_dict in storages_list:
                storage = StorageUnit()
                storage.changed = True
                storage.name = str(RFID_tag) + "_Storage" + str(storage_index)
                storage.type = "Storage"
                storage.p_nom = storage_dict.get("p_nom") or storage.p_nom
                storage.p_nom_min = storage_dict.get("p_nom_min") or storage.p_nom_min
                storage.p_nom_max = storage_dict.get("p_nom_max") or storage.p_nom_max
                storage.p_nom_extendable = storage_dict.get("p_nom_extendable") or storage.p_nom_extendable
                storage.marginal_cost = storage_dict.get("marginal_cost") or storage.marginal_cost
                storage.state_of_charge_initial = storage_dict.get("state_of_charge_initial") or storage.state_of_charge_initial
                module.add_component(storage)
                storage_index += 1

        if (transformers_list != None):
            transformer_index = 0
            for transformer_dict in transformers_list:
                transformer = Transformer()
                transformer.changed = True
                transformer.name = str(RFID_tag) + "_Transformer" + str(transformer_index)
                transformer.type = "Transformer"
                transformer.model = transformer_dict.get("type") or transformer.model
                module.add_component(transformer)
                transformer_index += 1

        return module

