##
# @file test_pandapower_calculators.py
##

import os
import sys

# Voeg de hoofdmap toe aan het pad
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Importeer de benodigde modules direct
    from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder
    print("Module 'PandapowerNetworkBuilder' geïmporteerd!")
    
    # Importeer de calculator modules
    from src.model.calculation.pandapower.PandapowerCalculatorLOPF import PandapowerCalculatorLOPF
    print("Module 'PandapowerCalculatorLOPF' geïmporteerd!")
    
    from src.model.calculation.pandapower.PandapowerCalculatorLPF import PandapowerCalculatorLPF
    print("Module 'PandapowerCalculatorLPF' geïmporteerd!")
    
    from src.model.calculation.pandapower.PandapowerCalculatorPF import PandapowerCalculatorPF
    print("Module 'PandapowerCalculatorPF' geïmporteerd!")
    
    from src.model.calculation.pandapower.PandapowerCalculatorOptimize import PandapowerCalculatorOptimize
    print("Module 'PandapowerCalculatorOptimize' geïmporteerd!")
    
    # Test een instantie van elke calculator
    print("\nCreëren van calculator-instanties:")
    
    builder = PandapowerNetworkBuilder()
    print("PandapowerNetworkBuilder instantie aangemaakt")
    
    lopf = PandapowerCalculatorLOPF()
    print("PandapowerCalculatorLOPF instantie aangemaakt")
    
    lpf = PandapowerCalculatorLPF()
    print("PandapowerCalculatorLPF instantie aangemaakt")
    
    pf = PandapowerCalculatorPF()
    print("PandapowerCalculatorPF instantie aangemaakt")
    
    opt = PandapowerCalculatorOptimize()
    print("PandapowerCalculatorOptimize instantie aangemaakt")
    
    # Controleer beschikbare methoden
    print("\nBeschikbare methoden in PandapowerNetworkBuilder:")
    methods = [method for method in dir(builder) if not method.startswith('_')]
    for method in methods[:10]:  # Toon de eerste 10 methoden
        print(f"- {method}")
    
    print("\n Alle pandapower calculator modules zijn succesvol geïmporteerd en getest!")
    
except Exception as e:
    import traceback
    print(f"Fout: {e}")
    traceback.print_exc()