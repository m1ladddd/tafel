##
# @file calculatorThreadInterface.py
#
# @brief Interface for a simulation worker thread.
#
# @section author_Model Author(s)
# - Created by Jop Merz on 31/05/2023.
# - Modified by Jop Merz on 11/10/2023.
##

# Internal imports
from src.model.Model import Model

# External imports
from abc import abstractmethod

"""!
Interface class for a simulation worker thread.
Created to support the strategy design pattern.
"""
class CalculatorThreadInterface:

    @abstractmethod
    def set_input_model(self, input_model: Model) -> None:
        """!
        Interface method.
        Set the input model for this worker thread.
        @param input_model Model
        """
        pass


    @abstractmethod
    def set_snapshots(self, snapshots: list[int]) -> None:
        """! 
        Interface method.
        Set the input snapshots for this worker thread.
        @param snapshots list[int]
        """
        pass


    @abstractmethod
    def calculate(self) -> bool:
        """! 
        Interface method.
        Start calculating and return True if succesful.
        @return bool
        """
        pass


    @abstractmethod
    def get_status(self) -> str:
        """! 
        Interface method.
        Return the status of the calcualtion.
        @return str
        """
        pass


    @abstractmethod
    def get_condition(self) -> str:
        """! 
        Interface method.
        Return the condition of the calcualtion.
        @return str
        """
        pass

    @abstractmethod
    def get_calculation_time(self) -> float:
        """! 
        Interface method.
        Return the time the calculation took
        @return float
        """
        pass


    @abstractmethod
    def get_network_build_time(self) -> float:
        """! 
        Interface method.
        Return the network building time
        @return float
        """
        pass


    @abstractmethod
    def set_calculation_method(self, method: str) -> None:
        """! 
        Interface method.
        Set the calcualtion method.
        @param method str
        """
        pass


    @abstractmethod
    def export_result(self, file_path: str) -> None:
        """! 
        Interface method.
        Export the calculation output to external files.
        @param file_path str
        """
        pass


    @abstractmethod
    def build_model(self) -> None:
        """! 
        Interface method.
        Build the power grid model.
        """
        pass