##
# @file ScenarioManager.py
#
# @brief Class which search a directory for JSON files and creates Scenario objects respectively
# Only one scenario can be active and is returned with the get_current_scenario() method
# Scenarios can be selected with the set_scenario(name) method 
# A name must be provided with this method, these are stored in the JSON files under "name"
#
# @section libraries_ScenarioManager Libraries/Modules
# - 
#
# @section todo_ScenarioManager TODO
# - None
#
# @section author_ScenarioManager Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

# Internal imports
from src.Scenario import Scenario

# External imports
import glob

class ScenarioManager:
    """! 
    Class which search a directory for JSON files and creates Scenario instances respectively.
    Only one scenario can be active and is returned with the get_current_scenario() method.
    Scenarios can be selected with the set_scenario(name) method.
    """

    def __init__(self, rootpath):
        """! 
        Constructor.
        """

        ## Array of Scenario instances.
        self.scenarios = []

        ## Array of path strings pointing to scenario .JSON files.
        self.scenario_files = []

        ## Root path string of the scenario folder.
        self.scenario_root = rootpath

        ## Current running scenario instance.
        self.current_scenario = None

        # Load all scenario files.
        self.reload_scenarios()


    def reload_scenarios(self):
        """! 
        Search in scenario root folder to all available scenario .JSON files
        and load every scenario into memory.
        """

        path = self.scenario_root + r"*.json"
        scenario_paths = glob.glob(path)
        print("Scenario search succesfull")
        print("    Root  -> " + self.scenario_root)
        print("    Found -> " + str(len(scenario_paths)))

        self.scenarios.clear()

        for scenario_file in scenario_paths:
            scenario = Scenario()
            scenario.load_scenario(scenario_file)
            self.scenarios.append(scenario)

        self.current_scenario = None

        if (self.scenarios[0]):
            self.set_scenario(self.scenarios[0].get_name())


    def set_scenario(self, scenario_name: str) -> bool:
        """! 
        Takes a scenario name and set that scenario as active.
        @return Bool succes (True = succes, False = fail)
        """

        for scenario in self.scenarios:
            if scenario.get_name().lower() == scenario_name.lower():
                self.current_scenario = scenario
                return True
        # no scenario found
        return False


    def print_scenario_list(self):
        """! 
        Print all available scenario names
        """
        for scenario in self.scenarios:
            print(scenario.get_name())

    
    def get_current_scenario(self):
        """! 
        Return the current Scenario instance
        @return current Scenario instance
        """
        return self.current_scenario
    
    def get_referenceless_catalog(self):
        """!
        Returns the catlog without references to csv files from the current scenario.
        @return current scenario catalog.
        """
        return self.current_scenario.referenceless_catalog()
    
    def get_scenario_list(self):
        """!
        Return the list of available scenarios
        @return scenario list
        """        
        scenario_list = []
        for scenario in self.scenarios:
            scenario_list.append(scenario.get_name())

        return scenario_list

    
    def change_catalog(self, catalog):
        self.current_scenario.catalog = catalog
