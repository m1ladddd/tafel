##
# @file PandapowerCalculatorLPF.py
#
# @brief Pandapower Linear Power Flow calculations.
#
# @section libraries_PandapowerCalculatorLPF Libraries/Modules
# - pandapower
##

# Internal imports
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder

# External imports
import time
import pandapower as pp

class PandapowerCalculatorLPF(PandapowerNetworkBuilder):
    """
    Pandapower Linear Power Flow calculations.
    """

    def __init__(self):
        """! 
        Constructor.
        """        
        super().__init__()


    def calculate(self) -> bool:
        """
        Start a Pandapower Linear Power Flow calculation.
        @return bool True = success, False = Error
        """

        self._status = "ok"
        self._condition = "success"

        # Start benchmark timer
        start_time = time.perf_counter()

        # Clear previous power line values
        self.reset_lines()

        # Blackout/failed calculation when no generators are present
        if len(self._input_model.generators) == 0:
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "no generation"
            return False
      
        success = True

        try:
            # Run DC power flow (linear approximation)
            pp.rundcpp(self._pandapower_model)
        except Exception as e:
            self._status = "warning"
            self._condition = f"failed: {str(e)}"
            success = False

        if success:
            self.retrieve_results()

        # Stop benchmark timer
        self._calculation_time = time.perf_counter() - start_time

        return success