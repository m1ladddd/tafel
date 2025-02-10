##
# @file MQTTConfig.py
#
# @brief Class containing MQTT broker address and login data.
#
# @section libraries_MQTTConfig
# - Component
#   - Access to Component class used for inheritance.
#
# @section todo_MQTTConfig TODO
# - None
#
# @section author_MQTTConfig Author(s)
# - Created by Jop Merz on 16/02/2023.
# - Modified by Jop Merz on 17/02/2023.
##

from os.path import exists
import json

# Classes
class MQTTConfig:
    """! 
    Class containing MQTT broker address and login data.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        self.__succes = False

        ## Idenfier of the config data.
        self.__name = ""

        ## Short description.
        self.__description = ""

        ## MQTT broker address.
        self.__address = ""

        ## MQTT broker port to connect to
        self.__port = 1883

        ## Authentication needed for connection (True = authentication needed, False = not needed)
        self.__authentication = False

        ## Username needed for authentication.
        self.__username = ""

        ## Password neededn for authentication.
        self.__password = ""

        ## Filepath of the config file.
        self.__filepath = ""


    def load(self, filepath: str) -> bool:
        """! 
        Take in a filepath to a .JSON file and load all the contents.
        @param filepath (str) Path to .JSON scenario.
        @return Bool (True = succesfull, False = error loading file).
        """

        file_exists = exists(filepath)

        if (not file_exists):
            self.__succes = False
            print("Could not load broker config file -> " + filepath)
            return self.__succes

        with open(filepath) as json_file:
            config_instance = json.load(json_file)
            self.__succes = True

            self.__name = config_instance.get("name")
            self.__description = config_instance.get("description")
            self.__address = config_instance.get("address")
            self.__port = config_instance.get("port")
            self.__base_topic = config_instance.get("base_topic")
            self.__authentication = config_instance.get("authentication")
            self.__username = config_instance.get("user")
            self.__password = config_instance.get("password")
            self.__filepath = filepath

            print("Loaded MQTT config file -> " + self.__filepath)
            print("    Config name  -> " + str(self.get_name()))
            print("    Description  -> " + str(self.get_description()))

            return self.__succes


    def reload(self):
        """! 
        Reload the MQTT config file into this config instance.
        """

        if (not self.__succes):
            return 

        with open(self.__filepath) as json_file:
            broker = json.load(json_file)

            self.__name = broker.get("name")
            self.__description = broker.get("description")
            self.__address = broker.get("address")
            self.__port = broker.get("port")
            self.__authentication = broker.get("authentication")
            self.__username = broker.get("user")
            self.__password = broker.get("password")


    def get_name(self) -> str:
        """! 
        Return the name of this config instance.
        @return config name (str)
        """

        return self.__name
    

    def get_description(self) -> str:
        """! 
        Return the description of this config instance.
        @return config description (str)
        """

        return self.__description
    

    def get_address(self) -> str:
        """! 
        Return the IP or name broker address of this config instance.
        @return broker address (str)
        """

        return self.__address


    def get_port(self) -> int:
        """! 
        Return the broker port of this config instance.
        @return broker port (int)
        """

        return self.__port

    
    def get_auth_mode(self) -> bool:
        """! 
        Return the authentication mode of the broker ("True = authentication, False = no authentication ").
        @return authentication (bool)
        """

        return self.__authentication


    def get_auth_user(self) -> str:
        """! 
        Return the authentication username of the broker.
        @return login username (str)
        """

        return self.__username


    def get_auth_password(self) -> str:
        """! 
        Return the authentication password of the broker.
        @return login password (str)
        """

        return self.__password