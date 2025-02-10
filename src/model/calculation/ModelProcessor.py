##
# @file ModelProcessor.py
#
# @brief Main processing of one unsegmented model.
# ModelProcessor splits the provided model into multiple models depending on line connectivity.
#
# @section author_Model Author(s)
# - Created by Jop Merz on 31/05/2023.
# - Modified by Jop Merz on 11/10/2023.
##

# Internal imports
from src.model.calculation.ModelProcessorInterface import ModelProcessorInterface
from src.model.calculation.CalculatorThreadManager import CalculatorThreadManager
from src.model.Model import Model, segment_model

# External imports
from copy import deepcopy
from time import perf_counter_ns

"""
ModelProcessor splits the provided model into multiple models depending on line connectivity.
It then provides the power grid models to the CalculatorThreadManager.
"""
class ModelProcessor (ModelProcessorInterface):

    def __init__(self):
        """
        Constructor.
        """
       
        ## Input raw power grid model.
        self.__input_model: Model = None

        ## List of segmented models.
        self.__segmented_model_list: list[Model] = []

        ## Previous list of segmented models.
        ## Needed to compare which models have changed and need a recalcualtion
        self.__previous_segmented_model_list: list[Model] = []

        ## CalculatorThreadManager instance to handle the calculation per segmented model
        self.__calculation_thread_manager: CalculatorThreadManager = CalculatorThreadManager()


    def set_input_model(self, model: Model) -> None:
        """
        Sets the raw input power grid model.
        #param model Model
        """
        self.__input_model = model


    def set_calculation_method(self, method: str) -> None:
        """
        Set the calculation method.
        #param method str (lopf, lpf or pf)
        """
        self.__calculation_thread_manager.set_calculation_method(method=method)

    
    def set_snapshots(self, snapshots: list[int]) -> None:
        """
        Set the list of snapshots.
        @param snapshots list[int]
        """
        self.__calculation_thread_manager.set_snapshots(snapshots)


    def get_output_model(self) -> Model:
        """
        Return the output model with calculated values.
        @return Model
        """
        return self.__input_model


    def selective_calculate(self) -> None:
        """
        Segment the raw input model into multiple models.
        Compares the models with the previous calculated ones to check which need a recalculation.
        """

        # Network segmentation.
        self.__segmented_model_list = segment_model(self.__input_model)

        model_list: list[Model] = []

        # Start benchmark timer.
        start_time: float = perf_counter_ns()

        # Skip the models which hasn't changed since last calculation.
        if (self.__previous_segmented_model_list != None):
            for model in self.__segmented_model_list:
                add = True
                for existing_model in self.__previous_segmented_model_list:
                    if (model.compare_model_components(existing_model) and
                        model.compare_model_structure(existing_model)):
                        add = False
                if (add):
                    model_list.append(model)

        # Save copy so it can be compared next time.
        self.__previous_segmented_model_list = deepcopy(self.__segmented_model_list)

        # Stop benchmark timer.
        elapsed_time: float = (perf_counter_ns() - start_time) / 1000 / 1000

        # Calculate all models no previous model is present.
        if (self.__previous_segmented_model_list == None):
            model_list = self.__segmented_model_list

        print(f"Selective model preprocessor")
        print(f"Model preprocessor time: {elapsed_time:.3f} ms")
        print(f"Models to calculate: {len(model_list)}")

        # Start multithreaded model calculation.
        self.__calculation_thread_manager.calculate(model_list)


    def force_calculate(self) -> None:
        """
        Segments the raw input model into multiple models.
        Start the calcualtion for each segmented model.
        """

        ## Network segmentation.
        self.__segmented_model_list = segment_model(self.__input_model)

        print(f"Forced model preprocessor")
        print(f"Models to calculate: {len(self.__segmented_model_list)}")

        ## Start multithreaded model calculation.
        self.__calculation_thread_manager.calculate(self.__segmented_model_list)

        ## Save a copy so it can be compared next time.
        self.__previous_segmented_model_list = deepcopy(self.__segmented_model_list)


    def shutdown(self) -> None:
        """
        Closes the CalculatorThreadManager instance.
        """
        self.__calculation_thread_manager.shutdown()
