
##
# @file PhotoVoltaic.py
#
# @brief Data container for PhotoVoltaic, inherited from Generator class.
# Most variable values are retrieved from JSON scenario files (static network that is).
# PhotoVoltaic instances are used in Module instances.
# Represented as Generator components towards PyPSA
#
# @section libraries_main Libraries/Modules
# - Generator
#   - Access to Generator class used for inheritance
#
# @section todo_Bus TODO
# - None
#
# @section author_Bus Author(s)
# - Created by Thijs Meidam on 7/05/2023.
##
from pvlib import location
import pvlib
from pvlib.bifacial.pvfactors import pvfactors_timeseries
import pandas as pd
from pvlib import temperature
from pvlib import pvsystem
import matplotlib.pyplot as plt
import warnings
from src.model.components.Generator import Generator

# supressing shapely warnings that occur on import of pvfactors
warnings.filterwarnings(action='ignore', module='pvfactors')

class PhotoVoltaic(Generator):

    def __init__(self):
        """! 
        Intiation of the photovoltaic module. Uses generator as a base class
        """
        Generator.__init__(self)
        self.long=6
        self.lat=52
        self.pvrow_height=1
        self.pvrow_width=1
        self.pitch=1
        self.albedo=0.2
        self.surface_azimuth=180
        self.surface_tilt=20
        self.axisazimuth=self.surface_azimuth-90
        self.pvrows=3
        self.temp_air=25
        self.enable=False
        self.wind_speed=1