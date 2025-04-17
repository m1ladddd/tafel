# test/test_pandapower_implementation.py
#!/usr/bin/env python3
"""
Vereenvoudigd testscript voor de Pandapower implementatie.
Focust alleen op de componenten die werkelijk beschikbaar zijn.
"""

import os
import sys
import time
import unittest  # Import unittest

# Voeg de hoofdmap toe aan het pad voor imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Model en component imports
from src.model.Model import Model
from src.model.components.Bus import Bus

# Pandapower calculator imports
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder
import pandapower as pp
import pandas as pd # Import pandas for checking DataFrame types

# Create a test class inheriting from unittest.TestCase
class TestPandapowerImplementation(unittest.TestCase):

    def test_pandapower_builder(self):
        """Test de basis functionaliteit van PandapowerNetworkBuilder."""
        print("\n=== Test PandapowerNetworkBuilder ===")

        # Maak een leeg model
        model = Model()

        # Voeg handmatig een bus toe
        bus = Bus("testbus", 110.0)
        # Mark this bus as the reference bus for Pandapower
        # Add is_ref attribute dynamically for the test or ensure Bus class has it
        setattr(bus, 'is_ref', True)
        model.buses.append(bus)

        print(f"Model gemaakt met 1 bus: {model.buses[0]}")

        # Maak de PandapowerNetworkBuilder aan
        builder = PandapowerNetworkBuilder()
        self.assertIsNotNone(builder, "Builder should be created") # Use assert
        print(f"Builder aangemaakt: {builder}")

        # Set input model
        builder.set_input_model(model)

        # Set snapshots
        builder.set_snapshots([0])

        try:
            # Bouw het model
            print("Model bouwen...")
            builder.build_model()
            print("Model gebouwd!")

            # Bekijk het resulterende pandapower model
            pp_model = builder._pandapower_model
            self.assertIsNotNone(pp_model, "Pandapower model should exist")
            self.assertIsInstance(pp_model, dict, "Pandapower model should be a dict") # Check type

            bus_table = pp_model.get('bus', None)
            self.assertIsNotNone(bus_table, "Bus table should exist in pp_model")
            self.assertIsInstance(bus_table, pd.DataFrame, "Bus table should be a DataFrame") # Check type
            if bus_table is not None:
                 print(f"Pandapower model heeft {len(bus_table)} bussen")
                 print(f"Bus details: {bus_table}")
                 self.assertEqual(len(bus_table), 1, "Should have 1 bus in pp_model") # Assert count

            # Check if external grid was added (since bus was marked as is_ref)
            ext_grid_table = pp_model.get('ext_grid', None)
            self.assertIsNotNone(ext_grid_table, "External grid table should exist")
            self.assertIsInstance(ext_grid_table, pd.DataFrame, "Ext grid table should be a DataFrame") # Check type
            if ext_grid_table is not None:
                 self.assertEqual(len(ext_grid_table), 1, "Should have 1 external grid")


        except Exception as e:
            self.fail(f"Fout tijdens het bouwen van het model: {e}") # Fail test on exception


    def test_direct_pandapower(self):
        """Test direct pandapower functionaliteit zonder de model laag."""
        print("\n=== Test Direct Pandapower ===")

        try:
            # Maak een leeg pandapower netwerk
            net = pp.create_empty_network()
            self.assertIsNotNone(net, "Pandapower network should be created")
            self.assertIsInstance(net, dict, "Pandapower network should be a dict")

            # Voeg handmatig elementen toe
            bus1_idx = pp.create_bus(net, vn_kv=110, name="bus1")
            bus2_idx = pp.create_bus(net, vn_kv=110, name="bus2")
            # Use assertEqual for checks
            self.assertEqual(len(net.get('bus', pd.DataFrame())), 2, "Should have 2 buses")

            # Voeg een lijn toe - Use a known standard type or parameters
            try:
                 # Try a common HV type first
                 pp.create_line(net, from_bus=bus1_idx, to_bus=bus2_idx, length_km=1.0,
                                std_type="149-AL1/24-ST1A 110.0")
            except:
                 print("HV Line type not found, trying LV type.")
                 try:
                     pp.create_line(net, from_bus=bus1_idx, to_bus=bus2_idx, length_km=1.0,
                                     std_type="NAYY 4x50 SE") # Example LV type
                 except Exception as e_line:
                     print(f"Standard line types not found, using parameters as fallback. Error: {e_line}")
                     pp.create_line_from_parameters(net, from_bus=bus1_idx, to_bus=bus2_idx, length_km=1.0,
                                                    r_ohm_per_km=0.1, x_ohm_per_km=0.1, c_nf_per_km=10, max_i_ka=1.0)
            self.assertEqual(len(net.get('line', pd.DataFrame())), 1, "Should have 1 line")

            # Voeg een externe grid (slack bus) toe
            pp.create_ext_grid(net, bus=bus1_idx, vm_pu=1.0)
            self.assertEqual(len(net.get('ext_grid', pd.DataFrame())), 1, "Should have 1 external grid")

            # Voeg een load toe
            pp.create_load(net, bus=bus2_idx, p_mw=100)
            self.assertEqual(len(net.get('load', pd.DataFrame())), 1, "Should have 1 load")

            # Voer een power flow berekening uit
            print("Power flow uitvoeren...")
            pp.runpp(net, numba=False) # Disable numba for broader compatibility
            print("Power flow succesvol uitgevoerd!")

            # Bekijk resultaten - Use .get() for safe access
            res_bus_table = net.get('res_bus', pd.DataFrame())
            res_line_table = net.get('res_line', pd.DataFrame())

            self.assertFalse(res_bus_table.empty, "Bus results should exist and be non-empty")
            self.assertFalse(res_line_table.empty, "Line results should exist and be non-empty")

            print(f"Bus resultaten: {res_bus_table}")
            print(f"Line resultaten: {res_line_table}")

            # Example assertion on results
            if not res_bus_table.empty and 'vm_pu' in res_bus_table.columns:
                 # Access result using the actual index (bus2_idx)
                 self.assertAlmostEqual(res_bus_table.vm_pu.loc[bus2_idx], 1.0, delta=0.1, msg="Voltage at bus2 should be close to 1.0 pu")

        except Exception as e:
            # Use self.fail to indicate test failure on exception
            self.fail(f"Fout tijdens directe pandapower test: {e}")

# This part is usually handled by the test runner (like pytest or unittest discovery)
# If running the script directly, use unittest's main function
if __name__ == "__main__":
     print("Starting Pandapower Implementation Tests...")
     # Create a test suite
     suite = unittest.TestSuite()
     # Load tests from the class
     suite.addTest(unittest.makeSuite(TestPandapowerImplementation))

     # Run the tests
     runner = unittest.TextTestRunner(verbosity=2)
     result = runner.run(suite)
     print("\n=== Tests Voltooid ===")
     # Optionally, exit with non-zero code if tests failed
     # if not result.wasSuccessful():
     #     sys.exit(1)