##
# @file PandapowerCalculatorPF.py
#
# @brief Pandapower model used for Power Flow calculations.
#
# @section libraries_PandapowerCalculatorPF Libraries/Modules
# - pandapower
##

# Internal imports
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder

# External imports
import time
import pandapower as pp

class PandapowerCalculatorPF(PandapowerNetworkBuilder):
    """
    Pandapower Power Flow calculations.
    """

    def __init__(self):
        """! 
        Constructor.
        """
        super().__init__()


    def calculate(self) -> bool:
        """
        Start a Pandapower Power Flow calculation.
        @return bool True = success, False = Error
        """

        self._status = "ok"
        self._condition = "success"

        # Start benchmark timer
        start_time = time.perf_counter()

        # Clear previous power line values
        self.reset_lines()

        # Blackout/failed calculation when no generators and storage units are present
        if (len(self._input_model.generators) == 0 and
            len(self._input_model.storage_units) == 0):
                self._calculation_time = time.perf_counter() - start_time
                self._status = "failed"
                self._condition = "no generation"
                return False
      
        success = True

        try:
            # First run DC power flow as initialization
            pp.rundcpp(self._pandapower_model)
            
            # Then run full AC power flow with Newton-Raphson solver
            pp.runpp(self._pandapower_model, algorithm="nr", init="dc", max_iteration=100)     
        except pp.LoadflowNotConverged:
            print("Warning: Power flow calculation did not converge! Trying with different solver options.")
            try:
                # Second attempt with different settings
                print("Second attempt with different solver settings...")
                pp.runpp(self._pandapower_model, algorithm="bfsw", tolerance_mva=1e-3)
                success = True
            except Exception as e:
                self._status = "warning"
                self._condition = f"failed: {str(e)}"
                success = False
        except Exception as e:
            self._status = "warning"
            self._condition = f"failed: {str(e)}"
            success = False

        # Stop benchmark timer
        self._calculation_time = time.perf_counter() - start_time

        # Retrieve results if successful
        if success:
            self.retrieve_results()

        return success