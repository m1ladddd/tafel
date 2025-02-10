##
# @file CalculatorThreadManager.py
#
# @brief Manager of one or multiple calculation threads.
# CalculatorThreadManager takes a list of power grid models and divedes them over multiple threads.
# Multiple calculation methods are supported: LOPF, LPF and PF.
#
# @section author_Model Author(s)
# - Created by Jop Merz on 31/05/2023.
# - Modified by Jop Merz on 11/10/2023.
##

# Internal imports
from src.model.Model import Model
from src.model.calculation.CalculatorThreadInterface import CalculatorThreadInterface
from src.model.calculation.pypsa.PyPSACalculatorOptimize import PyPSACalculatorOptimize
from src.model.calculation.pypsa.PyPSACalculatorLOPF import PyPSACalculatorLOPF
from src.model.calculation.pypsa.PyPSACalculatorLPF import PyPSACalculatorLPF
from src.model.calculation.pypsa.PyPSACalculatorPF import PyPSACalculatorPF

# External imports
from time import perf_counter
from threading import Thread, Event

"""! 
Dataclass for transferring data between the CalculatorThreadManager instance and its worker threads.
"""
class ThreadData:
    def __init__(self) -> None:

        ## Worker thread instance
        self.calculation_instance: CalculatorThreadInterface = None

        ## Input power grid model
        self.model: Model = None

        ## List of snapshots
        self.snapshots: list[int] = []

        ## Power grid model ID
        self.model_id: int = -1

        ## Start signal for the worker thread
        self.wakeup_event: Event = Event()

        ## Worker thread finished signal for the main thread
        self.finished_event: Event = Event()

        ## Calcualtion time
        self.calculation_time: float = 0.0

        ## Power grid build time
        self.build_time: float = 0.0

        ## Status of the calculation
        self.status: str = "none"

        ## Extra status information of the calculation
        self.status_extended: str = "undefined"


"""
CalculatorThreadManager takes a list of power grid models and divedes them over multiple threads.
Multiple calculation methods are supported: LOPF, LPF and PF.
"""
class CalculatorThreadManager:
    def __init__(self) -> None:
        """! 
        Constructor.
        """

        ## The input list of Model instances. Each Model will get its own worker thread assigned.
        self.__model_list: list[Model] = []

        ## List of Python Thread instances.
        self.__worker_thread_instances: list[Thread] = []

        ## List of shared data between the CalculatorThreadManager instance and the worker threads.
        self.__worker_threads: list[ThreadData] = []

        ## Input calculation method (lopf, optimize, lpf or pf)
        self.__calculation_method = "optimize"

        ## Flag signaling all worker threads to shutdown
        self.__shutdown: bool = False

        ## A list of all snapshots (for dynamic calculations)
        self.__snapshots: list[int] = [0]

        # Create and init 5 worker threads
        for i in range(5):
            thread: ThreadData = ThreadData()
            thread.calculation_instance = self.__create_calculation_instance(self.__calculation_method)
            thread.model = None
            thread.snapshots = self.__snapshots
            thread.model_id = i
            thread.status = "ok"
            thread.status_extended = "booting"
            self.__add_thread(thread_data=thread)


    def __create_calculation_instance(self, method: str) -> CalculatorThreadInterface:
        """
        Create and return a calculation instance depending on the input string.
        @param method str Input string (lopf, lpf or pf).
        @return instance with a CalculatorThreadInterface interface
        """
        if (method == "optimize"):
            return PyPSACalculatorOptimize()
        if (method == "lopf"):
            return PyPSACalculatorLOPF()
        if (method == "lpf"):
            return PyPSACalculatorLPF()
        if (method == "pf"):
            return PyPSACalculatorPF()
        return None


    def set_calculation_method(self, method: str) -> None:
        """
        Set the calculation method of this CalculationThreadManager.
        @param method str Calculation method (lopf, lpf or pf).
        """
        ## Create the corresponding calculation instances for each worker thread
        if (self.__calculation_method != method):
            for thread_data in self.__worker_threads:
                thread_data.calculation_instance = self.__create_calculation_instance(method)

        self.__calculation_method = method


    def set_snapshots(self, snapshots: list[int]):
        """
        Set the snapshots.
        @param snapshots list[int] 
        """
        for thread_data in self.__worker_threads:
            thread_data.snapshots  = snapshots

        self.__snapshots = snapshots

    
    def calculate(self, model_list: list[Model]) -> None:
        """
        Start the calculation on the provided list of models.
        @param model_list list[Model] Input model list
        """

        # Start benchmark timer
        start_time: float = perf_counter()

        self.__model_list = model_list

        model_count: int = len(model_list)
        worker_thread_count: int = len(self.__worker_thread_instances)

        # Spawn more worker threads if needed
        if (model_count > worker_thread_count):
            for i in range(worker_thread_count, model_count):
                thread: ThreadData = ThreadData()
                thread.calculation_instance = self.__create_calculation_instance(self.__calculation_method)
                thread.model = self.__model_list[i]
                thread.model_id = i
                thread.snapshots = self.__snapshots
                thread.status = "ok"
                thread.status_extended = "booting"
                self.__add_thread(thread_data=thread)
                print(f"Adding new calculation worker thread with ID: {i}")

        # Send the start signal to all worker threads
        for i in range(model_count):
            self.__worker_threads[i].model = self.__model_list[i]
            self.__worker_threads[i].wakeup_event.set()

        # Wait until all worker threads are finished
        for i in range(model_count):
            self.__worker_threads[i].finished_event.wait()
            self.__worker_threads[i].finished_event.clear()

        # Stop benchmark timer
        elapsed_time = perf_counter() - start_time

        # Print results
        for i in range(model_count):
            thread = self.__worker_threads[i]
            total_time: float = thread.build_time + thread.calculation_time
            print(f"Model: {thread.model_id+1}")
            print(f"    Method: {self.__calculation_method}")
            print(f"    Status: [{thread.status}, {thread.status_extended}]")
            print(f"    Build time: {thread.build_time:.3f} s")
            print(f"    Solver time: {thread.calculation_time:.3f} s")      
            print(f"    Total time: {total_time:.3f} s")
        print(f"All model calculations finished in {elapsed_time:.3f} s")


    def shutdown(self) -> None:
        """
        Destroy this CalculatorThreadManager.
        This must be called before closing the simulation server.
        """
        # Set global shutdown flag
        self.__shutdown = True

        # Signal all worker threads to wake up
        for thread in self.__worker_threads:
            thread.wakeup_event.set()

        # Close all worker threads
        for thread in self.__worker_thread_instances:
            thread.join()


    def __calculate_thread(self, thread: ThreadData):
        """
        Main program flow of a worker thread.
        This method never exits until the shutdown flag is set.
        @param thread ThreadData
        """

        # Keep looping until the shutdown flag is set
        while (self.__shutdown == False):

            model_id: int = thread.model_id + 1
            export_path: str = "export/model_" + str(model_id)
            wakeup_event: Event = thread.wakeup_event
            finished_event: Event = thread.finished_event

            # Wait until the wakeup/start signal is given
            wakeup_event.wait()
            wakeup_event.clear()

            # Exit if the shutdown flag is set
            if (self.__shutdown):
                return

            # Provide model and snapshot to the calculating instance and start the calculation
            thread.calculation_instance.set_snapshots(thread.snapshots)
            thread.calculation_instance.set_input_model(thread.model)
            thread.calculation_instance.build_model()
            thread.calculation_instance.calculate()

            # Retrieve benchmarks from the calculating instance
            thread.build_time: float = thread.calculation_instance.get_network_build_time()
            thread.calculation_time: float = thread.calculation_instance.get_calculation_time()
            thread.status: str = thread.calculation_instance.get_status()
            thread.status_extended: str = thread.calculation_instance.get_condition()  

            # Set the finished flag
            finished_event.set()

            # Export the results to external files
            thread.calculation_instance.export_result(export_path)
            
        return
    
    
    def __add_thread(self, thread_data: ThreadData) -> None:
            """
            Create a new worker thread.
            @param thread_data ThreadData
            """
            self.__worker_threads.append(thread_data)
            self.__worker_thread_instances.append(Thread(target=self.__calculate_thread, args=(thread_data, )))
            self.__worker_thread_instances[-1].start()