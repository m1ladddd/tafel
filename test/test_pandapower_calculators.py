##
# @file debug_import.py
##

import os
import sys

# Voeg de hoofdmap toe aan het pad
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    # Probeer het bestand direct te openen
    path = "src/model/calculation/pandapower/PandapowerNetworkBuilder.py"
    with open(path, 'r') as f:
        print(f"Bestand kon worden geopend: {path}")
        lines = f.readlines()
        print(f"Aantal regels: {len(lines)}")
        print(f"Eerste 5 regels:")
        for i in range(min(5, len(lines))):
            print(f"{i+1}: {lines[i].strip()}")
    
    # Probeer de module te importeren
    from src.model import calculation
    print("Module 'src.model.calculation' geïmporteerd!")
    
    from src.model.calculation import pandapower
    print("Module 'src.model.calculation.pandapower' geïmporteerd!")
    
    # Bekijk wat er in de module zit
    print(f"Inhoud van pandapower module: {dir(pandapower)}")
    
except Exception as e:
    import traceback
    print(f"Fout: {e}")
    traceback.print_exc()