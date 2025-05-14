##
# @file CalculatorThreadManager.py
#
# @brief Manages calculation threads for segmented power grid models using Pandapower.
# This class receives segmented models and assigns them to separate threads
# for parallel calculation using the appropriate Pandapower calculator based on the selected mode.
#
# @section author_Author(s)
# - Created by Jop Merz on 31/05/2023.
# - Modified by [Your Name/Alias] on [Date] to use Pandapower exclusively.
##

# Internal imports
from src.model.Model import Model
# --- Import ONLY Pandapower Calculators ---
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder # Assuming this is needed by calculators
from src.model.calculation.pandapower.PandapowerCalculatorPF import PandapowerCalculatorPF
from src.model.calculation.pandapower.PandapowerCalculatorLPF import PandapowerCalculatorLPF
from src.model.calculation.pandapower.PandapowerCalculatorLOPF import PandapowerCalculatorLOPF
from src.model.calculation.pandapower.PandapowerCalculatorOptimize import PandapowerCalculatorOptimize # If optimize maps to a specific PP calc
# --- PyPSA Imports Removed ---
# from src.model.calculation.pypsa.PyPSANetworkBuilder import PyPSANetworkBuilder
# from src.model.calculation.pypsa.PyPSACalculatorPF import PyPSACalculatorPF
# ... etc for other PyPSA calculators ...

# External imports
from threading import Thread, Lock
from time import perf_counter_ns, sleep
import pandas as pd # Needed for snapshots

# --- CalculatorThread Class (Assuming it's generic enough or defined elsewhere) ---
# If CalculatorThread itself imported PyPSA, it needs fixing too.
# For now, assume it takes a calculator instance and calls its methods.
# If it's defined here, ensure it doesn't import PyPSA.
# Example structure (adjust if CalculatorThread is imported):
class CalculatorThread (Thread):
    """
    Thread responsible for running a calculation on a single model segment.
    """
    def __init__(self, model: Model, calculator_instance, snapshots: pd.Index | None):
        Thread.__init__(self)
        self.model = model
        self.calculator = calculator_instance # Expects a Pandapower calculator instance
        self.snapshots = snapshots
        self.succes = False
        self.elapsed_time = 0.0

    def run(self):
        start_time = perf_counter_ns()
        try:
            # Assume calculator instances have a 'calculate' method
            if self.calculator:
                 print(f"Thread starting calculation for model segment (Buses: {[b.name for b in self.model.buses]}) using {type(self.calculator).__name__}")
                 # Pass model and snapshots to the Pandapower calculator instance
                 self.calculator.set_input_model(self.model)
                 self.calculator.set_snapshots(self.snapshots)
                 self.succes = self.calculator.calculate() # Execute calculation
            else:
                 print("Error: No calculator instance provided to thread.")
                 self.succes = False

        except Exception as e:
            print(f"Error during calculation in thread: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
            self.succes = False
        finally:
            self.elapsed_time = (perf_counter_ns() - start_time) / 1000 / 1000 / 1000 # seconds
            print(f"Thread finished calculation. Success: {self.succes}, Time: {self.elapsed_time:.4f} s")

# --- CalculatorThreadManager Class ---
class CalculatorThreadManager:
    """
    Manages multiple CalculatorThreads for parallel processing of segmented models
    using the selected Pandapower calculation method.
    """
    def __init__(self):
        """ Constructor. """
        ## List of active calculation threads.
        self.__threads: list[CalculatorThread] = []
        ## Lock for managing thread list access (optional but good practice).
        self.__thread_lock: Lock = Lock()
        ## Selected calculation method name ('pf', 'lpf', 'lopf', 'optimize').
        self.__calculation_method: str = "pf" # Default to Power Flow
        ## Snapshots to be used for the calculations.
        self.__snapshots: pd.Index | None = None

    def set_calculation_method(self, method: str) -> None:
        """ Set the desired calculation method (maps to Pandapower calculators). """
        valid_methods = ["pf", "lpf", "lopf", "optimize"]
        if method.lower() in valid_methods:
            self.__calculation_method = method.lower()
            print(f"CalculatorThreadManager: Calculation method set to {self.__calculation_method.upper()} (Pandapower)")
        else:
            print(f"Warning: Invalid calculation method '{method}'. Using default '{self.__calculation_method}'.")

    def set_snapshots(self, snapshots: pd.Index | list | None) -> None:
        """ Set the snapshots for the calculations. """
        if snapshots is None:
            self.__snapshots = None
        elif isinstance(snapshots, list):
             # Convert list to pandas Index if needed by calculators
             try:
                 self.__snapshots = pd.Index(snapshots)
                 print(f"CalculatorThreadManager: Snapshots set (converted from list). Count: {len(self.__snapshots)}")
             except Exception as e:
                 print(f"Error converting snapshots list to pd.Index: {e}")
                 self.__snapshots = None # Reset on error
        elif isinstance(snapshots, pd.Index):
             self.__snapshots = snapshots
             print(f"CalculatorThreadManager: Snapshots set. Count: {len(self.__snapshots)}")
        else:
             print(f"Warning: Invalid type for snapshots: {type(snapshots)}. Expected list, pd.Index, or None.")
             self.__snapshots = None


    def _get_calculator_instance(self) -> object | None:
        """ Creates an instance of the appropriate Pandapower calculator based on the selected method. """
        method = self.__calculation_method
        print(f"Creating Pandapower calculator instance for method: {method.upper()}")
        if method == "pf":
            return PandapowerCalculatorPF()
        elif method == "lpf":
            return PandapowerCalculatorLPF()
        elif method == "lopf":
            return PandapowerCalculatorLOPF()
        elif method == "optimize":
            # Determine which calculator 'optimize' maps to in Pandapower context
            # Often OPF (Optimal Power Flow) is used. LOPF is linear.
            # If PandapowerCalculatorOptimize exists and handles non-linear OPF, use that.
            # Otherwise, map to LOPF or raise an error if not implemented.
            # return PandapowerCalculatorOptimize() # If this class exists and does OPF
            print("Mapping 'optimize' mode to LOPF for Pandapower.")
            return PandapowerCalculatorLOPF() # Defaulting optimize to LOPF for now
        else:
            print(f"Error: Unknown calculation method '{method}' requested.")
            return None

    def calculate(self, model_list: list[Model]) -> bool:
        """
        Starts calculation threads for each model in the list using the selected Pandapower method.
        Waits for all threads to complete.
        Returns True if all calculations were successful, False otherwise.
        """
        if not model_list:
            print("CalculatorThreadManager: No models provided for calculation.")
            return True # No work to do, technically successful

        # Clear previous threads
        self.shutdown() # Ensure no old threads are lingering

        print(f"CalculatorThreadManager: Starting calculation for {len(model_list)} model segments using {self.__calculation_method.upper()}...")
        start_time_total = perf_counter_ns()

        with self.__thread_lock:
            self.__threads = []
            for model_segment in model_list:
                calculator_instance = self._get_calculator_instance()
                if calculator_instance:
                    thread = CalculatorThread(model_segment, calculator_instance, self.__snapshots)
                    self.__threads.append(thread)
                    thread.start()
                else:
                    print(f"Error: Could not create calculator for method {self.__calculation_method}. Skipping segment.")
                    # Decide how to handle failure - stop all? Continue? Mark as failed?
                    # For now, we skip, which will likely lead to overall failure state.

            if not self.__threads:
                 print("Error: No calculation threads were started.")
                 return False # Failed if no threads could be started

        # Wait for all started threads to complete
        print(f"CalculatorThreadManager: Waiting for {len(self.__threads)} threads to finish...")
        all_successful = True
        for thread in self.__threads:
            thread.join() # Wait for this thread to finish
            if not thread.succes:
                all_successful = False
                # Optionally log which segment failed
                # bus_names = [b.name for b in thread.model.buses] if thread.model and thread.model.buses else "Unknown"
                # print(f"Calculation FAILED for segment with buses: {bus_names}")

        elapsed_time_total = (perf_counter_ns() - start_time_total) / 1000 / 1000 / 1000 # seconds
        print(f"CalculatorThreadManager: All threads finished. Overall Success: {all_successful}. Total Time: {elapsed_time_total:.4f} s")

        # Optionally clear threads list after joining
        # with self.__thread_lock:
        #     self.__threads = []

        return all_successful

    def shutdown(self) -> None:
        """
        Ensures all active threads are properly joined (waited for).
        Call this before exiting the application or starting a new batch calculation.
        """
        with self.__thread_lock:
            if not self.__threads:
                return # No threads to shut down

            print(f"CalculatorThreadManager: Shutting down - joining {len(self.__threads)} active threads...")
            active_threads = list(self.__threads) # Create copy to iterate over
            self.__threads = [] # Clear the main list

        # Join threads outside the lock
        for thread in active_threads:
            if thread.is_alive():
                print(f"Waiting for thread {thread.name} to complete...")
                thread.join(timeout=5.0) # Add a timeout
                if thread.is_alive():
                     print(f"Warning: Thread {thread.name} did not finish within timeout during shutdown.")
            # else:
            #    print(f"Thread {thread.name} already finished.")

        print("CalculatorThreadManager: Shutdown complete.")

