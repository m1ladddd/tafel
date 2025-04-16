# setup.py
from setuptools import setup, find_packages
import os # Nodig om requirements.txt te lezen

# Functie om dependencies uit requirements.txt te lezen (optioneel, maar handig)
def parse_requirements(filename):
    """Lees requirements uit een requirements bestand."""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

# Lees de requirements - je kunt ook de belangrijkste hier hardcoderen
# install_reqs = parse_requirements("requirements.txt")
# OF definieer de belangrijkste direct:
install_reqs = [
    "pandapower", # Zeker nodig
    "pandas",     # Geïmporteerd in PandapowerNetworkBuilder
    "numpy",      # Geïmporteerd in PandapowerNetworkBuilder
    # Voeg hier andere *essentiële* runtime dependencies toe
    # Test dependencies zoals pytest horen hier NIET, die installeer je apart in CI
]

setup(
    # 1. Project Naam: Gebruik de naam van je applicatie/library
    name="tafel",

    # 2. Versie: Pas aan wanneer je wijzigingen maakt
    version="0.1.0",

    # 3. Korte beschrijving
    description="TAFEL project voor netwerk simulatie en analyse.",

    # 4. Waar bevinden de packages zich? Cruciaal voor src-layout!
    #    Dit zegt: de 'root' package ('') zit in de map 'src'
    package_dir={"": "src"},

    # 5. Welke packages moeten worden meegenomen? Cruciaal voor src-layout!
    #    Zoek naar alle packages (mappen met __init__.py) binnen de 'src' map
    packages=find_packages(where="src"),

    # 6. Welke Python versie is minimaal nodig?
    python_requires='>=3.9', # Match je CI omgeving

    # 7. Welke andere packages zijn nodig om dit project te draaien?
    #    Deze worden automatisch meegeïnstalleerd.
    install_requires=install_reqs,

    # 8. (Optioneel maar aanbevolen) Metadata
    author="Jouw Naam / Team",
    author_email="jouw.email@example.nl",
    url="https://github.com/jouw-username/tafel", # Link naar je repo

    # 9. (Optioneel) Classifiers voor PyPI (Python Package Index)
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        # Voeg meer classifiers toe indien relevant
    ],
)