##
# @file model_segmentation_test.py
#
# @brief Unit test for power grid model segmentation.
#
# Created by Jop Merz on 01/11/2023.
##

# Internal imports
from src.model.Model import Model, segment_model
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.StorageUnit import StorageUnit

# External imports
import unittest

class ModelSegmentationTest(unittest.TestCase):
    """
    Unit test for power grid model segmentation.
    """

    def setUp(self) -> None:
        """
        Construct a small model containing one generator, load and storage unit.
        """
        self.model: Model = Model()
        self.model.add_bus(Bus("bus_0", 110))
        self.model.add_bus(Bus("bus_1", 110))
        self.model.add_bus(Bus("bus_2", 110))
        self.model.add_bus(Bus("bus_3", 110))
        self.model.add_bus(Bus("bus_4", 110))
        self.model.add_bus(Bus("bus_5", 110))
        self.model.add_bus(Bus("bus_6", 110))
        self.model.add_bus(Bus("bus_7", 110))

        self.model.add_line(Line("line_0", "bus_0", "bus_1", 0.2, 0.1, 5000, None, 10))
        self.model.add_line(Line("line_1", "bus_1", "bus_2", 0.2, 0.1, 5000, None, 10))
        self.model.add_line(Line("line_2", "bus_2", "bus_3", 0.2, 0.1, 5000, None, 10))
        self.model.add_line(Line("line_3", "bus_3", "bus_0", 0.2, 0.1, 5000, None, 10))
        self.model.add_line(Line("line_4", "bus_3", "bus_4", 0.2, 0.1, 5000, None, 10))
        self.model.add_line(Line("line_5", "bus_4", "bus_5", 0.2, 0.1, 5000, None, 10))
        self.model.add_line(Line("line_6", "bus_5", "bus_6", 0.2, 0.1, 5000, None, 10))
        self.model.add_line(Line("line_7", "bus_6", "bus_7", 0.2, 0.1, 5000, None, 10))
        self.model.add_line(Line("line_8", "bus_7", "bus_4", 0.2, 0.1, 5000, None, 10))

        generator: Generator = Generator()
        generator.name = "gen_0"
        generator.bus0 = "bus_0"
        self.model.add_generator(generator)

        load: Load = Load()
        load.name = "load_0"
        load.bus0 = "bus_6"
        self.model.add_load(load)

        storage: StorageUnit = StorageUnit()
        storage.name = "storage_0"
        storage.bus0 = "bus_2"
        self.model.add_storage_unit(storage)


    def test_complete_network_buses(self):
        """
        Test if all buses are present in model 1.
        """
        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output buses
        self.assertTrue(len(output_models) == 1)
        self.assertTrue(len(output_models[0].buses) == 8)

        # Test if the model contains all correct buses
        for bus in output_models[0].buses:
            self.assertTrue(bus.name == "bus_0" or 
                            bus.name == "bus_1" or 
                            bus.name == "bus_2" or 
                            bus.name == "bus_3" or 
                            bus.name == "bus_4" or 
                            bus.name == "bus_5" or 
                            bus.name == "bus_6" or 
                            bus.name == "bus_7")


    def test_complete_network_lines(self):
        """
        Test if all lines are present in model 1.
        """
        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output buses
        self.assertTrue(len(output_models) == 1)
        self.assertTrue(len(output_models[0].lines) == 9)

        # Test if the model contains all correct buses
        for line in output_models[0].lines:
            self.assertTrue(line.name == "line_0" or 
                            line.name == "line_1" or 
                            line.name == "line_2" or 
                            line.name == "line_3" or 
                            line.name == "line_4" or 
                            line.name == "line_5" or 
                            line.name == "line_6" or 
                            line.name == "line_7" or
                            line.name == "line_8")
            

    def test_complete_network_generators(self):
        """
        Test if the generator is present in model 1.
        """
        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output buses
        self.assertTrue(len(output_models) == 1)
        self.assertTrue(len(output_models[0].generators) == 1)

        # Test if the model contains all correct buses
        for generator in output_models[0].generators:
            self.assertTrue(generator.name == "gen_0")


    def test_complete_network_loads(self):
        """
        Test if the load is present in model 1.
        """
        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output buses
        self.assertTrue(len(output_models) == 1)
        self.assertTrue(len(output_models[0].loads) == 1)

        # Test if the model contains all correct buses
        for load in output_models[0].loads:
            self.assertTrue(load.name == "load_0")


    def test_complete_network_storage_units(self):
        """
        Test if the storage unit is present in model 1.
        """
        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output buses
        self.assertTrue(len(output_models) == 1)
        self.assertTrue(len(output_models[0].storage_units) == 1)

        # Test if the model contains all correct buses
        for storage in output_models[0].storage_units:
            self.assertTrue(storage.name == "storage_0")


    def test_split_network_buses(self):
        """
        Test if the buses are split correctly.
        """
        # Split the network into 2 
        self.model.lines[4].active = False

        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output buses
        self.assertTrue(len(output_models) == 2)
        self.assertTrue(len(output_models[0].buses) == 4)
        self.assertTrue(len(output_models[1].buses) == 4)

        # Test if the model contains all correct buses
        for bus in output_models[0].buses:
            self.assertTrue(bus.name == "bus_0" or 
                            bus.name == "bus_1" or 
                            bus.name == "bus_2" or 
                            bus.name == "bus_3")
            
        # Test if the model contains all correct buses
        for bus in output_models[1].buses:
            self.assertTrue(bus.name == "bus_4" or 
                            bus.name == "bus_5" or 
                            bus.name == "bus_6" or 
                            bus.name == "bus_7")


    def test_split_network_lines(self):
        """
        Test if the lines are split correctly.
        """
        # Split the network into 2 
        self.model.lines[4].active = False

        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output buses
        self.assertTrue(len(output_models) == 2)
        self.assertTrue(len(output_models[0].lines) == 4)
        self.assertTrue(len(output_models[1].lines) == 4)

        # Test if model 1 contains all correct lines
        for line in output_models[0].lines:
            self.assertTrue(line.name == "line_0" or 
                            line.name == "line_1" or 
                            line.name == "line_2" or 
                            line.name == "line_3")

        # Test if model 2 contains all correct lines
        for line in output_models[1].lines:
            self.assertTrue(line.name == "line_5" or 
                            line.name == "line_6" or 
                            line.name == "line_7" or 
                            line.name == "line_8")


    def test_split_network_generators(self):
        """
        Test if the generators are split correctly.
        """
        # Split the network into 2 
        self.model.lines[4].active = False

        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output generators
        self.assertTrue(len(output_models) == 2)
        self.assertTrue(len(output_models[0].generators) == 1)
        self.assertTrue(len(output_models[1].generators) == 0)

        # Test if model 1 has the generator
        for generator in output_models[0].generators:
            self.assertTrue(generator.name == "gen_0")


    def test_split_network_loads(self):
        """
        Test if the loads are split correctly.
        """
        # Split the network into 2 
        self.model.lines[4].active = False
        
        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output loads
        self.assertTrue(len(output_models) == 2)
        self.assertTrue(len(output_models[0].loads) == 0)
        self.assertTrue(len(output_models[1].loads) == 1)

        # Test if model 2 has the load
        for load in output_models[1].loads:
            self.assertTrue(load.name == "load_0")


    def test_split_network_storage_units(self):
        """
        Test if the storage units are split correctly.
        """
        # Split the network into 2 
        self.model.lines[4].active = False
        
        output_models: list[Model] = segment_model(self.model, False)

        # Test the corect number of output models and output storage units
        self.assertTrue(len(output_models) == 2)
        self.assertTrue(len(output_models[0].storage_units) == 1)
        self.assertTrue(len(output_models[1].storage_units) == 0)

        # Test if model 1 has the storage unit
        for storage in output_models[0].storage_units:
            self.assertTrue(storage.name == "storage_0")

if __name__ == '__main__':
    unittest.main()