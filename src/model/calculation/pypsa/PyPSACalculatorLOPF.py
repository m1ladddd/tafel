##
# @file PyPSACalculatorLOPF.py
#
# @brief PyPSA Linear Optimal Power Flow calculations.
#
# @section libraries_PyPSACalculatorLPF Libraries/Modules
# - pypsa
##

# Internal imports
from src.model.calculation.pypsa.PyPSANetworkBuilder import PyPSANetworkBuilder

# External imports
import time

class PyPSACalculatorLOPF (PyPSANetworkBuilder):
    """
    PyPSA Linear Optimal Power Flow calculations.
    """

    def __init__(self):
        """! 
        Constructor.
        """
        super().__init__()


    def calculate(self) -> bool:
        """
        Start a PyPSA Linear Optimal Power Flow calculation.
        @return bool True = succes, False = Error
        """

        # Start benchmark timer
        start_time: float = time.perf_counter()

        # Clear previous power line values
        self._reset_lines()
     
        # Blackout/failed calculation when no generators and storage units are present
        if (len(self._input_model.generators) == 0 and
            len(self._input_model.storage_units) == 0):
                self._calculation_time = time.perf_counter() - start_time
                self._status = "failed"
                self._condition = "no generation"
                return False
        
        succes: bool = True
        status = self._pypsa_model.lopf()

        self._status = status[0]
        self._condition = status[1]

        if (self._status == "ok" and self._condition == "optimal"):
            self._retrieve_results()
            succes = True
        else:
            succes = False            
        
        # Stop benchmark timer
        self._calculation_time = time.perf_counter() - start_time

        return succes