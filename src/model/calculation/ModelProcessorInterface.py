##
# @file ModelProcessorInterface.py
#
# @brief Interface for a raw power grid model processor.
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
Interface for a raw power grid model processor.
Created to support the strategy design pattern.
"""
class ModelProcessorInterface:

    @abstractmethod
    def set_input_model(self, model: Model) -> None:
        """!
        Interface method.
        Set the input power grid model.
        @param input_model Model
        """
        pass

    @abstractmethod
    def set_snapshots(self, snapshots: list[int]) -> None:
        """! 
        Interface method.
        Set the snapshots.
        @param snapshots list[int]
        """
        pass

    @abstractmethod
    def get_output_model(self) -> Model:
        """!
        Interface method.
        Return the output power grid model.
        @return Model
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
    def force_calculate(self) -> None:
        """! 
        Interface method.
        Recalcualtes every power grid model.
        """
        pass

    @abstractmethod
    def selective_calculate(self) -> None:
        """! 
        Interface method.
        Only recalcualtes the power grid models which have changed.
        """
        pass
    