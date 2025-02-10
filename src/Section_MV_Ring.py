##
# @file Section_MV_Ring.py
#
# @brief Objects of this class represents the Medium Voltage ring table section.
#
# @section libraries_Section_MV_Ring Libraries/Modules
# - 
#
# @section todo_Section_MV_Ring TODO
# - None
#
# @section author_Section_MV_Ring Author(s)
# - Created by Thijs van Elsacker on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

from src.Section import Section
from src.led.LEDStrip import LEDStrip

class Section_MV_Ring (Section):
    """! 
    Instances of this class represents the Medium Voltage ring table section
    """

    ## Static string which indicates the voltage level of this section (LV, MV or HV).
    voltage = "MV"

    ## Static int indicating the total number of ledstrips in this table section.
    num_ledstrips = 22

    ## Static int indicating the total number of buses.
    num_buses = 22

    ## Nominal voltage of all busses in this section
    v_nom = 10

    ##Series reactance, must be non-zero for AC branch in linear power flow.
    x = 0.1

    ## Series resistance, must be non-zero for DC branch in linear power flow.
    r = 0.01
    
    snom=99999999999999
    linetype="149-AL1/24-ST1A 10.0"
    length=1

    def __init__(self, section_name):
        """! 
        Constructor.
        @param section_name (str) Unique name of this stable section (for example "Table1").
        """

        Section.__init__(self, section_name)

        # ledstrips
        for i in range(self.num_ledstrips):
            self.ledstrips.append(LEDStrip())
            self._previous_ledstrips.append(LEDStrip())

        # buses
        for i in range(0, self.num_buses):
            bus_name = "bus" + str(i)
            self.add_bus(bus_name, self.v_nom)

        # lines
        self.add_line("line0",  bus0="bus0",  bus1="bus1",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line1",  bus0="bus1",  bus1="bus2",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line2",  bus0="bus2",  bus1="bus3",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line3",  bus0="bus3",  bus1="bus4",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line4",  bus0="bus3",  bus1="bus5",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line5",  bus0="bus5",  bus1="bus6",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line6",  bus0="bus6",  bus1="bus7",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line7",  bus0="bus7",  bus1="bus8",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line8",  bus0="bus7",  bus1="bus9",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line9",  bus0="bus9",  bus1="bus10", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line10", bus0="bus10", bus1="bus11", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line11", bus0="bus11", bus1="bus12", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line12", bus0="bus11", bus1="bus13", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line13", bus0="bus13", bus1="bus14", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line14", bus0="bus14", bus1="bus15", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line15", bus0="bus14", bus1="bus16", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line16", bus0="bus16", bus1="bus17", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line17", bus0="bus17", bus1="bus18", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line18", bus0="bus18", bus1="bus19", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line19", bus0="bus18", bus1="bus20", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line20", bus0="bus20", bus1="bus21", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line21", bus0="bus21", bus1="bus1",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        # bind ledstrips with its respective lines
        prefix = section_name + "_"

        ## Static int indicating critical power level of a power line.
        ## Active power values above this level are considered critical.
        self.threshold_critical = 30

        ## Static int indicating high power level of a power line.
        ## Active power values above this level are considered high.
        self.threshold_high = 25

        ## Static int indicating normal power level of a power line.
        ## Active power values above this level are considered normal.
        self.threshold_normal = 20

        ## Static int indicating low power level of a power line.
        ## Active power values above this level are considered low.
        self.threshold_low = 10

        ## Magenta = 0xFF00FF
        self.background_color.red = 48
        self.background_color.green = 0
        self.background_color.blue = 48

        for i in range(0, self.num_ledstrips):
            self.ledstrips[i].line = prefix + "line" + str(i)
            self.ledstrips[i].set_ledstrip_id(i)
            self.ledstrips[i].set_background_color(self.background_color)
            self.ledstrips[i].set_background_flashing_time(0)
