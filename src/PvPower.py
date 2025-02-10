##
# @file PVPower.py
#
# @brief Handles PvLib calculation
#
# @section libraries_main Libraries/Modules
# - PVLib (https://pvlib-python.readthedocs.io/en/stable/)
#   Example used for the calculate_pv(https://pvlib-python.readthedocs.io/en/stable/gallery/bifacial/plot_pvfactors_fixed_tilt.html)
# - Created by Thijs Meidam on 31/04/2023.
##
from pvlib import location
import pvlib
from pvlib.bifacial.pvfactors import pvfactors_timeseries
import pandas as pd
from pvlib import temperature
from pvlib import pvsystem
import matplotlib.pyplot as plt
import warnings

# supressing shapely warnings that occur on import of pvfactors
warnings.filterwarnings(action='ignore', module='pvfactors')
#the PvPower class adds the resticted abillity to use the pvlib to calculate the power of a solar panel at a certain position with certain parameters at a certain time
#uses the dynamic datetime when available and it's initial datetime range when the scenario is static
#modeled using a monoficial fixed tilt model
class PvPower:
    def __init__(self):
        self.startdate='2021-06-21 0:00' 
        self.enddate='2021-06-21 23:00'
        self.freq='H'
        self.timezone='Europe/Amsterdam'
    def calculate_pv(self,photovoltaic,datetime,is_static):
        if(is_static):
            times = pd.date_range(self.startdate, self.enddate, freq=self.freq, tz='Europe/Amsterdam')
            loc = location.Location(latitude=photovoltaic.lat, longitude=photovoltaic.long, tz=self.timezone)
            sp = loc.get_solarposition(times)
            cs = loc.get_clearsky(times)
        else:
            times=datetime
            loc = location.Location(latitude=photovoltaic.lat, longitude=photovoltaic.long, tz=self.timezone)
            sp = loc.get_solarposition(times)
            cs = loc.get_clearsky(times)

        # example array geometry
        gcr = photovoltaic.pvrow_width / photovoltaic.pitch
        irrad = pvfactors_timeseries(
            solar_azimuth=sp['azimuth'],
            solar_zenith=sp['apparent_zenith'],
            surface_azimuth=photovoltaic.surface_azimuth,  # south-facing array
            surface_tilt=photovoltaic.surface_tilt,
            axis_azimuth=photovoltaic.axisazimuth,  # 90 degrees off from surface_azimuth.  270 is ok too
            timestamps=times,
            dni=cs['dni'],
            dhi=cs['dhi'],
            gcr=gcr,
            pvrow_height=photovoltaic.pvrow_height,
            pvrow_width=photovoltaic.pvrow_width,
            albedo=photovoltaic.albedo,
            n_pvrows=photovoltaic.pvrows,
            index_observed_pvrow=1
        )
        # turn into pandas DataFrame
        irrad = pd.concat(irrad, axis=1)

        effirad=irrad['total_abs_front']
        temp_cell = temperature.faiman(effirad, temp_air=photovoltaic.temp_air,
                                    wind_speed=photovoltaic.wind_speed)

        # using the pvwatts_dc model and parameters detailed above,
        # set pdc0 and return DC power for monofacial
        pdc0 = 1
        gamma_pdc = -0.0043
        pdc_mono = pvsystem.pvwatts_dc(effirad,
                                    temp_cell,
                                    pdc0,
                                    gamma_pdc=gamma_pdc
                                    ).fillna(0)
        if(is_static):
            return pdc_mono[12]
        else:  
            return pdc_mono