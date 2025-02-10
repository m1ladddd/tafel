
##
# @file Model.py
#
# @brief Class representing a power grid model
#
# @section author_Model Author(s)
# - Created by Jop Merz on 31/05/2023.
# - Modified by Jop Merz on 11/10/2023.
##

# internal imports
from src.model.components.Bus import  Bus
from src.model.components.Line import Line
from src.model.components.Transformer import Transformer
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.StorageUnit import StorageUnit

# External imports
from dataclasses import dataclass, replace
import time

@dataclass
class BusIndex:
    index: int
    segment: int
    bus_name: str

class Model:
    """! 
    Class representing a basic power grid model.
    This model can contain nodes, power lines, generators, loads, transformers and storage units.
    """
    
    def __init__(self) -> None:
        """! 
        Constructor.
        """

        ## List of all buses/nodes.
        self.buses: list[Bus] = []

        ## List of all lines.
        self.lines: list[Line] = []

        ## List of all transformers.
        self.transformers: list[Transformer] = []

        ## List of all generators.
        self.generators: list[Generator] = []

        ## List of all loads.
        self.loads: list[Load] = []

        ## List of all storage units.
        self.storage_units: list[StorageUnit] = []


    def add_line(self, line: Line) -> None:
        """! 
        Add a line to this model.
        @param line Line
        """
        self.lines.append(line)


    def add_bus(self, bus: Bus) -> None:
        """! 
        Add a bus to this model.
        @param bus Bus
        """
        self.buses.append(bus)


    def add_transformer(self, transformer: Transformer) -> None:
        """! 
        Add a transformer to this model.
        @param transformer Transformer
        """
        self.transformers.append(transformer)


    def add_generator(self, generator: Generator) -> None:
        """! 
        Add a generator to this model.
        @param generator Generator
        """
        self.generators.append(generator)


    def add_load(self, load: Load) -> None:
        """! 
        Add a load to this model.
        @param load Load
        """
        self.loads.append(load)

    def add_storage_unit(self, unit: StorageUnit) -> None:
        """! 
        Add a storage unit to this model.
        @param unit StorageUnit
        """
        self.storage_units.append(unit)
   

    def clear(self) -> None:
        """! 
        Removes every component in this model.
        This included lines, buses, transformers, generators, loads and storage units.
        """
        self.lines.clear()
        self.buses.clear()
        self.transformers.clear()
        self.generators.clear()
        self.loads.clear()
        self.storage_units.clear()


    def reset_changed_components(self) -> None:
        """! 
        Reset the changed flag for every component
        This included lines, buses, transformers, generators, loads and storage units.
        """
        for line in self.lines:
            line.changed = False
        for bus in self.buses:
            bus.changed = False
        for transformer in self.transformers:
            transformer.changed = False
        for generator in self.generators:
            generator.changed = False
        for load in self.loads:
            load.changed = False
        for storage in self.storage_units:
            storage.changed = False


    def compare_model_structure(self, other_model) -> bool:
        """! 
        Return True if a bus or line is removed/added.
        @return bool
        """
        if (not isinstance(other_model, Model)):
            return False
        
        if (len(self.buses) != len(other_model.buses) or
            len(self.lines) != len(other_model.lines)):
            return False

        if (self.buses != other_model.buses or
            self.lines != other_model.lines):
            return False
        return True
    

    def compare_model_components(self, other_model) -> bool:
        """! 
        Return True if a component is removed/added.
        This included generators, loads, storage units and transformers.
        @return bool
        """
        if (not isinstance(other_model, Model)):
            return False
        
        if (len(self.generators) != len(other_model.generators) or
            len(self.loads) != len(other_model.loads) or
            len(self.storage_units) != len(other_model.storage_units) or
            len(self.transformers) != len(other_model.transformers)):
            return False
        
        if (self.generators != other_model.generators or
            self.loads != other_model.loads or
            self.storage_units != other_model.storage_units or
            self.transformers != other_model.transformers):
            return False
        return True
    


def get_added_buses(bus_list_1: list[Bus], bus_list_2: list[Bus]) -> list[Bus]:
    return set(bus_list_1) - set(bus_list_2)  


def get_removed_buses(bus_list_1: list[Bus], bus_list_2: list[Bus]) -> list[Bus]:
    return set(bus_list_2) - set(bus_list_1)


def get_added_lines(line_list_1: list[Line], line_list_2: list[Line]) -> list[Line]:
    return set(line_list_1) - set(line_list_2)


def get_removed_lines(line_list_1: list[Line], line_list_2: list[Line]) -> list[Line]:
    return set(line_list_2) - set(line_list_1)


def get_added_generators(generator_list_1: list[Generator], generator_list_2: list[Generator]) -> list[Generator]:
    return set(generator_list_1) - set(generator_list_2)


def get_removed_generators(generator_list_1: list[Generator], generator_list_2: list[Generator]) -> list[Generator]:
    return set(generator_list_2) - set(generator_list_1)


def get_added_loads(load_list_1: list[Load], load_list_2: list[Load]) -> list[Load]:
    return set(load_list_1) - set(load_list_2)


def get_removed_loads(load_list_1: list[Load], load_list_2: list[Load]) -> list[Load]:
    return set(load_list_2) - set(load_list_1)


def get_added_storage_units(storage_unit_list_1: list[StorageUnit], storage_unit_list_2: list[StorageUnit]) -> list[StorageUnit]:
    return set(storage_unit_list_1) - set(storage_unit_list_2)


def get_removed_storage_units(storage_unit_list_1: list[StorageUnit], storage_unit_list_2: list[StorageUnit]) -> list[StorageUnit]:
    return set(storage_unit_list_2) - set(storage_unit_list_1)


def get_added_transformers(transformer_list_1: list[Transformer], transformer_list_2: list[Transformer]) -> list[Transformer]:
    return set(transformer_list_1) - set(transformer_list_2)


def get_removed_transformers(transformer_list_1: list[Transformer], transformer_list_2: list[Transformer]) -> list[Transformer]:
    return set(transformer_list_2) - set(transformer_list_1)


def get_added_model_components(model_1: Model, model_2: Model) -> Model:
        
    model: Model = Model()
    added_buses: list[Bus] = get_added_buses(model_1.buses, model_2.buses)
    added_lines: list[Line] = get_added_lines(model_1.lines, model_2.lines)
    added_generators: list[Generator] = get_added_generators(model_1.generators, model_2.generators)
    added_loads: list[Load] = get_added_loads(model_1.loads, model_2.loads)
    added_storage_units: list[StorageUnit] = get_added_storage_units(model_1.storage_units, model_2.storage_units)
    added_transformers: list[Transformer] = get_added_transformers(model_1.transformers, model_2.transformers)

    model.buses = added_buses
    model.lines = added_lines
    model.generators = added_generators
    model.loads = added_loads
    model.storage_units = added_storage_units
    model.transformers = added_transformers

    return model


def get_removed_model_components(model_1: Model, model_2: Model) -> Model:
        
    model: Model = Model()
        
    removed_buses: list[Bus] = get_removed_buses(model_1.buses, model_2.buses)
    removed_lines: list[Line] = get_removed_lines(model_1.lines, model_2.lines)
    removed_generators: list[Generator] = get_removed_generators(model_1.generators, model_2.generators)
    removed_loads: list[Load] = get_removed_loads(model_1.loads, model_2.loads)
    removed_storage_units: list[StorageUnit] = get_removed_storage_units(model_1.storage_units, model_2.storage_units)
    removed_transformers: list[Transformer] = get_removed_transformers(model_1.transformers, model_2.transformers)

    model.buses = removed_buses
    model.lines = removed_lines
    model.generators = removed_generators
    model.loads = removed_loads
    model.storage_units = removed_storage_units
    model.transformers = removed_transformers

    return model

def segment_model(input_model: Model, verbose: bool = True) -> Model:

        bus_list = input_model.buses
        connection_list = []

        # Making a list of all components which can connect 2 buses
        # In this case all lines and transformers

        for connection_line in input_model.lines:
            if connection_line.active:
                connection_list.append(connection_line)

        for connecton_transfomer in input_model.transformers:
            if connecton_transfomer.active:
                connection_list.append(connecton_transfomer)

        start_time = round(time.time_ns())

        # Setting up the temporary bus list containing a segment value
        # This variable is needed for the segmentation process

        bus_index_list = []

        for i in range(len(bus_list)):
            new_bus_index = BusIndex(index=i, segment=-1, bus_name=bus_list[i].name)
            bus_index_list.append(replace(new_bus_index))
        
        iterations = 0
        finished = False
        current_grid_id = -1

        # Main segmentation process

        while not finished:
            finished = True
            current_grid_id += 1

            # Search for the first bus which has no segment ID assigned

            for bus in bus_index_list:
                if bus.segment == -1:
                    bus.segment = current_grid_id
                    break

            # Check if all buses have an allocated segment id
            # If thats the case, the bus segmentation is finished

            for bus in bus_index_list:               
                if bus.segment == -1:
                    finished = False
                    break


            bus_segment_allocated = True

            # Lord have mercy on me for creating this abomination

            while bus_segment_allocated:
                bus_segment_allocated = False
                
                for bus_index in bus_index_list:
                    if bus_index.segment == current_grid_id:
                        for connection in connection_list:
                            if connection.bus0 == bus_index.bus_name:
                                for other_bus in bus_index_list:
                                    iterations += 1
                                    if other_bus.bus_name == connection.bus1:
                                        if other_bus.segment == -1:
                                            other_bus.segment = current_grid_id
                                            bus_segment_allocated = True
                                            break

                            if connection.bus1 == bus_index.bus_name:
                                for other_bus in bus_index_list:
                                    iterations += 1
                                    if other_bus.bus_name == connection.bus0:
                                        if other_bus.segment == -1:
                                            other_bus.segment = current_grid_id    
                                            bus_segment_allocated = True
                                            break

        elapsed_time = round(time.time_ns()) - start_time
        models_found = current_grid_id

        if (verbose):
            print(f"Model segment iterations: {iterations}" )
            print(f"Model segment time: {elapsed_time/1000/1000:.2f} ms")
            print(f"Model segments found: {models_found}")

        start_time = round(time.time_ns())
        iterations: int = 0
        model_list: list[Model] = []

        # After segmenting the buses we need to sort all
        # loads, generators, lines etc into individual models.

        for i in range(models_found):
            model_list.append( Model() )

        for bus_index in bus_index_list:
            for i in range(models_found):
                if bus_index.segment == i:

                    model_list[i].add_bus(bus_list[bus_index.index])

                    for line in input_model.lines:
                        iterations += 1
                        if line.bus0 == bus_index.bus_name and line.active:
                            model_list[i].add_line(line)

                    for transformer in input_model.transformers:
                        iterations += 1
                        if transformer.bus0 == bus_index.bus_name and transformer.active:
                            model_list[i].add_transformer(transformer)

                    for generator in input_model.generators:
                        iterations += 1
                        if generator.bus0 == bus_index.bus_name:
                            model_list[i].add_generator(generator)

                    for load in input_model.loads:
                        iterations += 1
                        if load.bus0 == bus_index.bus_name:
                            model_list[i].add_load(load)

                    for storage_unit in input_model.storage_units:
                        iterations += 1
                        if storage_unit.bus0 == bus_index.bus_name:
                            model_list[i].add_storage_unit(storage_unit)


        elapsed_time = round(time.time_ns()) - start_time

        if (verbose):
            print(f"Model compiler iterations: {iterations}")
            print(f"Model compiler time: {elapsed_time/1000/1000:.2f} ms")

        return model_list