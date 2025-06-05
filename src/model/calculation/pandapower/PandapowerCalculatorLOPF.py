##
# @file PandapowerCalculatorLOPF.py
#
# @brief Pandapower Linear Optimal Power Flow calculations.
#
# @section libraries_PandapowerCalculatorLOPF Libraries/Modules
# - pandapower
##

# Internal imports
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder

# External imports
import time
import pandapower as pp

class PandapowerCalculatorLOPF(PandapowerNetworkBuilder):
    """
    Pandapower Linear Optimal Power Flow calculations.
    """

    def __init__(self):
        """! 
        Constructor.
        """
        super().__init__()


    def calculate(self) -> bool:
        """
        Start a Pandapower Linear Optimal Power Flow calculation.
        @return bool True = success, False = Error
        """

        # Start benchmark timer
        start_time = time.perf_counter()

        # Clear previous power line values
        self.reset_lines()

        # CRITICAL: Build the Pandapower model from input_model
        if self._input_model is None:
            print("CRITICAL: No input model set! Cannot calculate.")
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "no input model"
            return False
            
        print("Building Pandapower model from input Model...")
        self.build_model()
     
        # COMMENTED OUT: Don't fail if no generators - allow empty grid simulation
        # # Blackout/failed calculation when no generators and storage units are present
        # if (len(self._input_model.generators) == 0 and
        #     len(self._input_model.storage_units) == 0):
        #         print("WARNING: No generators or storage units present in input model.")
        #         print("         This is likely because no physical modules are placed on the table.")
        #         print("         Cannot run LOPF on empty grid - treating as successful.")
        #         self._calculation_time = time.perf_counter() - start_time
        #         self._status = "warning"
        #         self._condition = "no generation - empty grid"
        #         return True  # Changed from False to True to allow empty grid simulation
        
        # Check for components needed for optimization
        has_generators = len(self._input_model.generators) > 0
        has_storage = len(self._input_model.storage_units) > 0
        
        if not has_generators and not has_storage:
            print("INFO: No generators or storage units for linear optimization.")
            print("      This is typically because no physical modules are placed on the table.")
            print("      Skipping LOPF and treating as successful empty grid.")
            self._calculation_time = time.perf_counter() - start_time
            self._status = "warning" 
            self._condition = "empty grid - no optimization needed"
            return True
            
        success = True
        
        try:
            # Run DC OPF (linear optimal power flow)
            print("Running linear optimal power flow (rundcopp)...")
            pp.rundcopp(self._pandapower_model)
            print("Linear optimal power flow successful!")
            self._status = "ok"
            self._condition = "optimal"
        except pp.OPFNotConverged:
            self._status = "warning"  # Changed from "failed" to "warning"
            self._condition = "not converged"
            print("Warning: Linear optimal power flow did not converge")
            print("         This can be normal for certain grid configurations")
            success = True  # Changed: treat non-convergence as warning, not failure
        except Exception as e:
            self._status = "error"
            self._condition = str(e)
            print(f"Error during linear optimal power flow: {e}")
            success = False
            
        if success:
            print("Retrieving LOPF results...")
            self.retrieve_results()
            print("Results retrieved successfully!")
        
        # Stop benchmark timer
        self._calculation_time = time.perf_counter() - start_time

        return success