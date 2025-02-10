
##
# @file GridCalculatorPyPSA.py
#
# @brief Class responible for building and maintaining PyPSA power grid models.
#
# @section libraries_GridCalculatorPyPSA Libraries/Modules
# - pypsa
# - Timer
#
# @section author_PyPSANetworkBuilder Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

# Internal imports
from src.model.calculation.CalculatorThreadInterface import CalculatorThreadInterface
from src.model.Model import Model, get_added_model_components, get_removed_model_components
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.Transformer import Transformer
from src.model.components.StorageUnit import StorageUnit

# External imports
import pypsa
import pandas as pd
import time
from os import path, makedirs
from copy import deepcopy


class PyPSANetworkBuilder (CalculatorThreadInterface):
    """! 
    Class responible for building and maintaining PyPSA power grid models.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        ## Main pypsa network object.
        self._pypsa_model: pypsa.Network = pypsa.Network()

        ## Disable all logging messages from PyPSA
        pypsa.io.logger.disabled = True
        pypsa.pf.logger.disabled = True
        pypsa.opf.logger.disabled = True
        pypsa.linopf.logger.disabled = True

        ## Input model used for the calculation
        self._input_model: Model = None

        ## Model used to remove components from previous PyPSA network
        self.__previous_model: Model = None

        ## Status of the simulation calculation
        self._status: str = ""

        ## Condition of the simulation calculation
        self._condition: str = ""

        ## Time the simulation calculation took
        self._calculation_time: float = 0.0

        ## Time it took to build the PyPSA network
        self._network_build_time: float = 0.0

    def _reset_lines(self) -> None:
        """
        Resets the active power output of all line instances.
        When snapshots are used, the output becomes a list of active power values
        """
        snapshot_count: int = len(self.snapshots)

        # Clear previous line output
        for line in self._input_model.lines:
            line.active_power.clear()
            line.output.clear()
            for i in range(snapshot_count):
                line.active_power.append(0.0)
                line.output.append(False)


    def _retrieve_results(self) -> None:
        """
        Retrieve all power grid output data from the PyPSA model.
        This includes power line, generator, load and transformer active power.
        """
        snapshot_count: int = len(self.snapshots)

        # Set power line active power.
        for line in self._input_model.lines:
            if (line.active):
                line.active_power.clear()
                line.output.clear()
                for i in range(snapshot_count):
                    line.active_power.append(self._pypsa_model.lines_t.p0[line.name][i])
                    line.output.append(True)

        # Set generator active power.
        for generator in self._input_model.generators:
            if (generator.active):
                generator.active_power.clear()
                generator.output.clear()
                for i in range(snapshot_count):
                    generator.active_power.append(self._pypsa_model.generators_t.p[generator.name][i])
                    generator.output.append(True)

        # Set load active power.
        for load in self._input_model.loads:
            if (load.active):
                load.active_power.clear()
                load.output.clear()
                for i in range(snapshot_count):
                    load.active_power.append(self._pypsa_model.loads_t.p[load.name][i])
                    load.output.append(True)

        # Set transformer active power and capacity.
        for transformer in self._input_model.transformers:
            if (transformer.active):
                transformer.active_power_0.clear()
                transformer.output.clear()
                transformer.capacity = self._pypsa_model.transformers.s_nom[transformer.name]
                for i in range(snapshot_count):
                    transformer.active_power_0.append(self._pypsa_model.transformers_t.p0[transformer.name][i])
                    transformer.output.append(True)
        for storage in self._input_model.storage_units:
            if (storage.active):
                storage.active_power.clear()
                storage.output.clear()
                for i in range(snapshot_count):
                    storage.active_power.append(self._pypsa_model.storage_units_t.p[storage.name][i])
                    storage.output.append(True)


    def __add_buses(self, bus_list: list[Bus]) -> None:
        """
        Private method used to add a list of Bus instances to the PyPSA model.
        @param bus_list list[Bus]
        """
        name_list: list[str] = []
        v_nom_list: list[float] = []

        # Only add active buses
        for bus in bus_list:
            if (bus.active):
                name_list.append(bus.name)
                v_nom_list.append(bus.v_nom)

        self._pypsa_model.madd("Bus", 
                                names=name_list,
                                v_nom=v_nom_list)
        

    def __add_lines(self, line_list: list[Line]) -> None:
        """
        Private method used to add a list of Line instances to the PyPSA model.
        @param line_list list[Line]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []
        bus0_list: list[str] = []
        bus1_list: list[str] = []
        r_list: list[float] = []
        x_list: list[float] = []
        s_nom_list: list[float] = []
        s_nom_extendable_list: list[bool] = []

        # Only add active lines
        for line in line_list:
            if (line.active):
                name_list.append(line.name)
                bus0_list.append(line.bus0)
                bus1_list.append(line.bus1)
                r_list.append(line.r)
                x_list.append(line.x)
                s_nom_list.append(line.s_nom)
                s_nom_extendable_list.append(line.s_nom_extendable)

        self._pypsa_model.madd("Line", 
                                names=name_list,
                                bus0=bus0_list,
                                bus1=bus1_list,
                                r=r_list,
                                x=x_list,
                                s_nom=s_nom_list,
                                s_nom_extendable=s_nom_extendable_list)


    def __add_generators(self, generator_list: list[Generator]) -> None:
        """
        Private method used to add a list of Generator instances to the PyPSA model.
        @param generator_list list[Generator]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []
        bus_list: list[str] = []
        p_set_list: list[float] = []
        p_nom_list: list[float] = []
        p_nom_min_list: list[float] = []
        p_nom_max_list: list[float] = []
        p_min_pu_list: list[float] = []
        p_max_pu_df: pd.DataFrame = pd.DataFrame(index=self.snapshots)
        marginal_cost_list: list[float] = []
        p_nom_extendable_list: list[bool] = []
        control_list: list[str] = []

        # Only add active generators
        for generator in generator_list:
            if (generator.active):
                name_list.append(generator.name)
                bus_list.append(generator.bus0)
                p_set_list.append(generator.p_set)
                p_nom_list.append(generator.p_nom)
                p_nom_min_list.append(generator.p_nom_min)
                p_nom_max_list.append(generator.p_nom_max)
                p_min_pu_list.append(generator.p_min_pu)
                p_max_pu_df[generator.name] = generator.p_max_pu
                marginal_cost_list.append(generator.marginal_cost)
                p_nom_extendable_list.append(generator.p_nom_extendable)
                control_list.append("PV")

        self._pypsa_model.madd("Generator",
                          names=name_list,
                          bus=bus_list,
                          p_set=p_set_list,
                          p_nom=p_nom_list,
                          p_nom_min=p_nom_min_list,
                          p_nom_max=p_nom_max_list,
                          p_min_pu=p_min_pu_list,
                          p_max_pu=p_max_pu_df,
                          marginal_cost=marginal_cost_list,
                          p_nom_extendable=p_nom_extendable_list,
                          control=control_list)


    def __add_loads(self, load_list: list[Load]) -> None:
        """
        Private method used to add a list of Load instances to the PyPSA model.
        @param load_list list[Load]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []
        bus_list: list[str] = []
        q_set_list: list[float] = []
        p_set_df: pd.DataFrame = pd.DataFrame(index=self.snapshots)

        # Only add active loads
        for load in load_list:
            if (load.active):
                name_list.append(load.name)
                bus_list.append(load.bus0)
                p_set_df[load.name] = load.p_set
                q_set_list.append(load.q_set)

        self._pypsa_model.madd("Load",
                                names=name_list,
                                bus=bus_list,
                                p_set=p_set_df,
                                q_set=q_set_list)


    def __add_storage_units(self, storage_unit_list: list[StorageUnit]) -> None: 
        """
        Private method used to add a list of StorageUnit instances to the PyPSA model.
        @param storage_unit_list list[StorageUnit]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []
        bus_list: list[str] = []
        p_nom_list: list[float] = []
        p_nom_min_list: list[float] = []
        p_nom_max_list: list[float] = []
        p_nom_extendable_list: list[bool] = []
        marginal_cost_list: list[float] = []
        state_of_charge_initial_list: list[float] = []

        # Only add active storage units
        for storage_unit in storage_unit_list:
            if (storage_unit.active):
                name_list.append(storage_unit.name)
                bus_list.append(storage_unit.bus0)
                p_nom_list.append(storage_unit.p_nom)
                p_nom_min_list.append(storage_unit.p_nom_min)
                p_nom_max_list.append(storage_unit.p_nom_max)
                p_nom_extendable_list.append(storage_unit.p_nom_extendable)
                marginal_cost_list.append(storage_unit.marginal_cost)
                state_of_charge_initial_list.append(storage_unit.state_of_charge_initial)

        self._pypsa_model.madd("StorageUnit",
                                names=name_list,
                                bus=bus_list,
                                p_nom=p_nom_list,
                                p_nom_min=p_nom_min_list,
                                p_nom_max=p_nom_max_list,
                                p_nom_extendable=p_nom_extendable_list,
                                marginal_cost=marginal_cost_list,
                                state_of_charge_initial=state_of_charge_initial_list)

    def __add_transformers(self, transformer_list: list[Transformer]) -> None:
        """
        Private method used to add a list of Transformer instances to the PyPSA model.
        @param transformer_list list[Transformer]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []
        bus0_list: list[str] = []
        bus1_list: list[str] = []
        transformer_type_list: list[str] = []

        # Only add active transformers
        for transformer in transformer_list:
            if (transformer.active):
                name_list.append(transformer.name)
                bus0_list.append(transformer.bus0)
                bus1_list.append(transformer.bus1)
                transformer_type_list.append(transformer.model)

        self._pypsa_model.madd("Transformer",
                                names=name_list,
                                bus0=bus0_list,
                                bus1=bus1_list,
                                type=transformer_type_list)


    def __remove_buses(self, bus_list: list[Bus]) -> None:   
        """
        Private method used to remove Bus instances from the PyPSA model.
        @param bus_list list[Bus]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []

        # Only remove active buses
        for bus in bus_list:
            if (bus.active):
                name_list.append(bus.name)

        self._pypsa_model.mremove("Bus", names=name_list)
        

    def __remove_lines(self, line_list: list[Line]) -> None:   
        """
        Private method used to remove Line instances from the PyPSA model.
        @param line_list list[Line]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []

        # Only remove active power lines
        for line in line_list:
            if (line.active):
                name_list.append(line.name)

        self._pypsa_model.mremove("Line", names=name_list)


    def __remove_generators(self, generator_list: list[Generator]) -> None:   
        """
        Private method used to remove Generator instances from the PyPSA model.
        @param generator_list list[Generator]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []

        # Only remove active generators
        for generator in generator_list:
            if (generator.active):
                name_list.append(generator.name)

        self._pypsa_model.mremove("Generator", names=name_list)


    def __remove_loads(self, load_list: list[Load]) -> None:   
        """
        Private method used to remove Load instances from the PyPSA model.
        @param load_list list[Load]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []

        # Only remove active loads
        for load in load_list:
            if (load.active):
                name_list.append(load.name)

        self._pypsa_model.mremove("Load", names=name_list)


    def __remove_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:   
        """
        Private method used to remove StorageUnit instances from the PyPSA model.
        @param storage_unit_list list[StorageUnit]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []

        # Only remove active storage units
        for storage_unit in storage_unit_list:
            if (storage_unit.active):
                name_list.append(storage_unit.name)

        self._pypsa_model.mremove("StorageUnit", names=name_list)


    def __remove_transformers(self, transformers_list: list[Transformer]) -> None:   
        """
        Private method used to remove Transformer instances from the PyPSA model.
        @param transformers_list list[Transformer]
        """

        # Using lists of values so PyPSA.madd can be used.
        # PyPSA.madd is faster than PyPSA.add when dealing with multiple instances.
        name_list: list[str] = []

        # Only remove active transformers
        for transformer in transformers_list:
            if (transformer.active):
                name_list.append(transformer.name)

        self._pypsa_model.mremove("Transformer", names=name_list)


    def set_input_model(self, input_model: Model) -> None:
        """
        Set the input model.
        @param input_model Model
        """
        self._input_model = input_model


    def set_snapshots(self, snapshots: list[int]):
        """! 
        Set the simulation snapshot list.
        @param snapshots list[int]
        """
        self.snapshots = snapshots


    def calculate(self) -> bool:
        """
        Initate a PyPSA calculation.
        """
        pass
    

    def get_status(self) -> str:
        """
        Return the PyPSA calculation status.
        @return str
        """
        return self._status
    

    def get_condition(self) -> str:
        """
        Return the PyPSA calculation condition.
        @return str
        """
        return self._condition
    

    def get_calculation_time(self) -> float:
        """
        Return the PyPSA calculation time.
        @return float
        """
        return self._calculation_time
    

    def get_network_build_time(self) -> float:
        """
        Return the PyPSA model building time.
        @return float
        """
        return self._network_build_time


    def export_result(self, file_path: str) -> None:
        """
        Export the PyPSA output to external files.
        @param file_path str Directory to export the model values
        """

        # Make sure the directory exists
        if (not path.exists(file_path)):
            makedirs(file_path)

        self._pypsa_model.export_to_csv_folder(file_path)


    def build_model(self) -> None:
        """
        Load the input model into PyPSA.
        """

        # Start benchmark timer for model building
        start_time: float = time.perf_counter()

        # Reload the whole model into PyPSA if snapshots have changed.
        # If not changed, selective build is faster.
        if(len(self.snapshots) != len(self._pypsa_model.snapshots)):
            self._pypsa_model.set_snapshots(self.snapshots)
            self.force_build()
        else:
            self._pypsa_model.set_snapshots(self.snapshots)
            self.selective_build()        

        # Save current model so it can be used in future selective_build calls.
        self.__previous_model = deepcopy(self._input_model)
        self.__previous_model.reset_changed_components()
        self._network_build_time = (time.perf_counter() - start_time)


    def force_build(self):
        """
        Reload every model component into PyPSA.
        """

        # Remove the previous loaded components from PyPSA.
        if (self.__previous_model != None):
            self.__remove_generators(self.__previous_model.generators)
            self.__remove_loads(self.__previous_model.loads)
            self.__remove_storage_units(self.__previous_model.storage_units)
            self.__remove_transformers(self.__previous_model.transformers)
            self.__remove_lines(self.__previous_model.lines)
            self.__remove_buses(self.__previous_model.buses)

        # Add the new components into PyPSA.
        self.__add_buses(self._input_model.buses)
        self.__add_lines(self._input_model.lines)
        self.__add_generators(self._input_model.generators)
        self.__add_loads(self._input_model.loads)
        self.__add_storage_units(self._input_model.storage_units)
        self.__add_transformers(self._input_model.transformers)


    def selective_build(self):
        """
        Only load changed components into the PyPSA model.
        Non changed components are ignored.
        """

        # If previous model exists, remove those components if necessary
        if (self.__previous_model != None):
            model = get_removed_model_components(self._input_model, self.__previous_model)

            if (len(model.transformers) > 0):
                self.__remove_transformers(model.transformers)
            if (len(model.storage_units) > 0):
                self.__remove_storage_units(model.storage_units)
            if (len(model.loads) > 0):
                self.__remove_loads(model.loads)
            if (len(model.generators) > 0):
                self.__remove_generators(model.generators)
            if (len(model.lines) > 0):
                self.__remove_lines(model.lines)
            if (len(model.buses) > 0):
                self.__remove_buses(model.buses)

        # When no previous model is present, add everything.
        model = self._input_model

        # Only load changed components compared to the previous model.
        if (self.__previous_model != None):
            model = get_added_model_components(self._input_model, self.__previous_model)

        if (len(model.buses) > 0):
            self.__add_buses(model.buses)
        if (len(model.lines) > 0):
            self.__add_lines(model.lines)
        if (len(model.generators) > 0):
            self.__add_generators(model.generators)
        if (len(model.loads) > 0):
            self.__add_loads(model.loads)
        if (len(model.storage_units) > 0):
            self.__add_storage_units(model.storage_units)
        if (len(model.transformers) > 0):
            self.__add_transformers(model.transformers)
