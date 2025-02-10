##
# @file RestrictionsManager.py
#
# @brief Class which searches for module restrictions in a directory to store and manage these object
# Only one set of restrictions can be active and is returned with the get_current_restrictions() method
# Restricitons can be selected with the set_restrictions(isStatic) method 
# A bool indicating the type of restrictions must be provided with this method.
#
# @section libraries_ModuleConfigManager Libraries/Modules
# - 
#
# @section todo_RestrictionsManager TODO
# - None
#
# @section author_RestrictionsManager Author(s)
# - Created by Jens Reinders on 12/04/2023.
# - Modified by Jens Reinders on 12/04/2023.
##

import glob
import json

class RestrictionsManager:
    """! 
    Class which searches for module restrictions in a directory to store and manage these object
    Only one set of restrictions can be active and is returned with the get_current_restrictions() method
    Restricitons can be selected with the set_restrictions(isStatic) method 
    A bool indicating the type of restrictions must be provided with this method.
    """

    def __init__(self, rootpath):
        """! 
        Constructor.
        """

        ## Dict containing all module restrictions for static scenarios.
        self.static_restrictions = {}

        ## Dict containing all module restrictions for dynamic scenarios.
        self.dynamic_restrictions = {}

        ## Root path string of the restrictions folder.
        self.restrictions_root = rootpath

        ## Current running scenario instance.
        self.current_restrictions = None

        # Load all scenario files.
        self.reload_restrictions()


    def reload_restrictions(self):
        """! 
        Search in restrictions root folder for specific config 
        files and load every scenario into memory.
        """

        path = self.restrictions_root + r"*.json"
        scenario_paths = glob.glob(path)
        print("Scenario search succesfull")
        print("    Root  -> " + self.restrictions_root)
        print("    Found -> " + str(len(scenario_paths)))

        with open(self.restrictions_root + 'static_module_config.json') as f:
            self.static_restrictions = json.load(f)

        with open(self.restrictions_root + 'dynamic_module_config.json') as f:
            self.dynamic_restrictions = json.load(f)

        self.current_restrictions = None


    def set_restrictions(self, isStatic):
        """! 
        Takes a boolean and sets that type of restrictions active.
        """

        if isStatic:
            self.current_restrictions = self.static_restrictions
        else:
            self.current_restrictions = self.dynamic_restrictions
    
    def get_current_restrictions(self):
        """! 
        Return the current restrictions
        @return current restrictions
        """

        return self.current_restrictions
    
    def change_restrictions(self, changes):
        """!
        Changes current restrictions.
        """

        for change in changes:
            restrict_type = change['restrictionField']
            mainField =  change['mainField']
            subField = change['subField']
            value = change['value']

            if subField == None:
                self.current_restrictions[restrict_type][mainField] = value
            else:
                self.current_restrictions[restrict_type][mainField][subField] = value
