import pandapower as pp
import types

# Bewaar de originele create_line functie
original_create_line = pp.create_line

# Maak een nieuwe functie die altijd een std_type toevoegt als deze niet aanwezig is
def patched_create_line(net, from_bus, to_bus, length_km, *args, **kwargs):
    # Als std_type niet aanwezig is in kwargs, voeg een standaardtype toe
    if 'std_type' not in kwargs:
        kwargs['std_type'] = "NAYY 4x50 SE" # Voegt standaard type toe

    # Roep de originele functie aan met de nieuwe parameters
    return original_create_line(net, from_bus, to_bus, length_km, *args, **kwargs)

# Vervang de originele functie door onze aangepaste versie
pp.create_line = patched_create_line # Monkey patching

print("Pandapower create_line functie is gepatcht!")