# test/test_pandapower_implementation.py
#!/usr/bin/env python3
"""
Vereenvoudigd testscript voor de Pandapower implementatie.
Focust alleen op de componenten die werkelijk beschikbaar zijn.
"""

import os
import sys
import time
import unittest

# Voeg de hoofdmap toe aan het pad voor imports
# Pas eventueel aan als je tests vanuit een andere map draait
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)


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
        model = Model()
        bus = Bus("testbus", 110.0)
        # setattr(bus, 'is_ref', True) # Attribuut niet meer nodig/gebruikt door builder
        bus.active = True # Zorg dat de bus actief is
        model.buses.append(bus)
        print(f"Model gemaakt met 1 bus: {model.buses[0]}")

        builder = PandapowerNetworkBuilder()
        self.assertIsNotNone(builder, "Builder should be created")
        print(f"Builder aangemaakt: {builder}")

        builder.set_input_model(model)
        builder.set_snapshots([0]) # Nodig voor interface, niet voor build zelf

        try:
            print("Model bouwen...")
            builder.build_model()
            print("Model gebouwd!")

            pp_model = builder._pandapower_model
            self.assertIsNotNone(pp_model, "Pandapower model should exist")
            self.assertIsInstance(pp_model, dict, "Pandapower model should be a dict")

            bus_table = pp_model.get('bus', pd.DataFrame()) # Gebruik .get met default
            self.assertIsNotNone(bus_table, "Bus table should exist in pp_model")
            self.assertIsInstance(bus_table, pd.DataFrame, "Bus table should be a DataFrame")
            if bus_table is not None and not bus_table.empty: # Check ook of het niet leeg is
                 print(f"Pandapower model heeft {len(bus_table)} bussen")
                 print(f"Bus details:\n{bus_table}")
                 self.assertEqual(len(bus_table), 1, "Should have 1 bus in pp_model")
                 # Check name and voltage
                 self.assertEqual(bus_table.name.iloc[0], "testbus")
                 self.assertEqual(bus_table.vn_kv.iloc[0], 110.0)

            # CORRECTION: De builder voegt nu WEL automatisch een ext_grid toe voor stabiliteit
            ext_grid_table = pp_model.get('ext_grid', pd.DataFrame())
            self.assertFalse(ext_grid_table.empty, "Builder should automatically add ext_grid for stability")
            if not ext_grid_table.empty:
                print(f"Ext_grid details:\n{ext_grid_table}")

            print("PASSED: Pandapower Builder test geslaagd (builder voegt automatisch ext_grid toe).")

        except Exception as e:
            self.fail(f"Fout tijdens het bouwen van het model: {e}")


    def test_direct_pandapower(self):
       """Test direct pandapower functionaliteit zonder de model laag."""
       # Let op: deze test is onafhankelijk van de builder en Model class
       print("\n=== Test Direct Pandapower ===")
       try:
           net = pp.create_empty_network() # Deze zou nu moeten werken!
           self.assertIsNotNone(net, "Pandapower network should be created")

           # Voeg handmatig elementen toe
           bus1_idx = pp.create_bus(net, vn_kv=110, name="bus1")
           bus2_idx = pp.create_bus(net, vn_kv=110, name="bus2")
           self.assertEqual(len(net.get('bus', pd.DataFrame())), 2, "Should have 2 buses")

           # Voeg lijn toe (met fallback)
           try:
                pp.create_line(net, from_bus=bus1_idx, to_bus=bus2_idx, length_km=1.0,
                               std_type="149-AL1/24-ST1A 110.0") # Voorbeeld HV type
           except:
                print("Info: Standaard lijn type niet gevonden, gebruik parameters.")
                pp.create_line_from_parameters(net, from_bus=bus1_idx, to_bus=bus2_idx, length_km=1.0,
                                                   r_ohm_per_km=0.1, x_ohm_per_km=0.1, c_nf_per_km=10, max_i_ka=1.0)
           self.assertEqual(len(net.get('line', pd.DataFrame())), 1, "Should have 1 line")

           # Voeg ext_grid en load toe
           pp.create_ext_grid(net, bus=bus1_idx, vm_pu=1.0)
           self.assertEqual(len(net.get('ext_grid', pd.DataFrame())), 1, "Should have 1 external grid")
           pp.create_load(net, bus=bus2_idx, p_mw=100)
           self.assertEqual(len(net.get('load', pd.DataFrame())), 1, "Should have 1 load")

           print("Power flow uitvoeren...")
           # Verwijder numba=False nu de shadowing is opgelost, laat pandapower proberen Numba te gebruiken
           pp.runpp(net)
           print("Power flow succesvol uitgevoerd!")

           # Asserts op resultaten
           res_bus_table = net.get('res_bus', pd.DataFrame())
           self.assertFalse(res_bus_table.empty, "Bus results should exist and be non-empty")
           if not res_bus_table.empty and 'vm_pu' in res_bus_table.columns:
                self.assertAlmostEqual(res_bus_table.vm_pu.loc[bus2_idx], 1.0, delta=0.1, msg="Voltage at bus2 should be close to 1.0 pu")

           print("PASSED: Directe Pandapower test geslaagd.")

       except Exception as e:
            self.fail(f"Fout tijdens directe pandapower test: {e}")


# Run tests if script is executed directly
if __name__ == "__main__":
     print("Starting Pandapower Implementation Tests...")
     suite = unittest.TestSuite()
     suite.addTest(unittest.makeSuite(TestPandapowerImplementation))
     runner = unittest.TextTestRunner(verbosity=2)
     result = runner.run(suite)
     print("\n=== Tests Voltooid ===")
     # if not result.wasSuccessful():
     #     sys.exit(1) # Optional: exit with error code if tests fail