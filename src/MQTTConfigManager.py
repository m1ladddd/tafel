##
# @file BrokerManager.py
#
# @brief Class which loads a list of brokers from a directory (.JSON files containing broker data).
#  Only one broker can be active at ont time.
#
# @section 
# - 
#
# @section todo_MQTTConfigManager TODO
# - None
#
# @section author_MQTT_ConfigManager Author(s)
# - Created by Jop Merz on 17/02/2023.
# - Modified by Jop Merz on 17/02/2023.
##

from src.MQTTConfig import MQTTConfig
import glob

class MQTTConfigManager:
    """! 
    Class which loads a list of brokers from a directory (.JSON files containing broker data).
    Only one broker can be active at ont time.
    """

    def __init__(self, directory: str):
        """! 
        Constructor.
        """

        ## Succesfull init
        self.__init_succes = False

        ## Array of broker instances.
        self.__config_instances = []

        ## Array of path strings pointing to broker .JSON files.
        self.__config_files = []

        ## Main directory containing the .JSON broker config files.
        self.__directory = directory

        ## Current broker instance.
        self.__current_config = None

        # Reread the broker directory and load in all .JSON broker files.
        self.reload_config_files()

        if (len(self.__config_instances) > 0):
            self.__init_succes = True


    def reload_config_files(self):
        """! 
        Search in MQTT config root folder to all available config .JSON files
        and load every file into memory.
        """

        path = self.__directory + r"*.json"
        self.__config_files = glob.glob(path)
        print("MQTT config search succesfull")
        print("    Directory  -> " + self.__directory)
        print("    Found      -> " + str(len(self.__config_files)))

        self.__config_instances.clear()

        for config_file in self.__config_files:
            config_instance = MQTTConfig()
            config_instance.load(config_file)
            self.__config_instances.append(config_instance)

        self.__current_config = None


    def set_config_instance(self, name: str) -> bool:
        """! 
        Takes a config name and set that config instance as active.
        @return Bool succes (True = succes, False = fail)
        """

        for config_instance in self.__config_instances:
            if config_instance.get_name() == name:
                self.__current_config = config_instance
                return True
        # No config instance found with this name
        return False


    def print_all(self):
        """! 
        Print all available config instance names
        """

        for config_instance in self.__config_instances:
            print(config_instance.get_name())

    
    def get_current_config(self) -> MQTTConfig:
        """! 
        Return the current Scenario instance
        @return current Scenario instance
        """

        return self.__current_config


    def get_succes(self) -> bool:
        """! 
        Return if the manager has succesfully initialized
        @return bool init succes
        """
        return self.__init_succes
