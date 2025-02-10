##
# @file PyPSACalculatorPF.py
#
# @brief PyPSA model used for Power Flow calculations.
#
# @section libraries_PyPSACalculatorPF Libraries/Modules
# - pypsa
##

# Internal imports
from src.model.calculation.pypsa.PyPSANetworkBuilder import PyPSANetworkBuilder

# External imports
import time

class PyPSACalculatorPF (PyPSANetworkBuilder):
    """
    PyPSA Power Flow calculations.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        super().__init__()


    def calculate(self) -> bool:
        """
        Start a PyPSA Power Flow calculation.
        @return bool True = succes, False = Error
        """

        self._status = "ok"
        self._condition = "succes"

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

        try:
            self._pypsa_model.lpf()
            self._pypsa_model.pf(use_seed=True)     
        except:
            self._status = "warning"
            self._condition = "failed"
            succes = False

        # Stop benchmark timer
        self._calculation_time = time.perf_counter() - start_time

        ## Clear previous line output
        if (succes):
            self._retrieve_results()

        return succes