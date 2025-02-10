##
# @file Section_LV.py
#
# @brief Objects of this class represents Low Voltage table sections (common street with houses)
# All platforms on this section only accepts LV modules
#
# @section libraries_Section_LV Libraries/Modules
# - 
#
# @section todo_Section_LV TODO
# - None
#
# @section author_Section_LV Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

from src.Section import Section
from src.led.LEDStrip import LEDStrip

class Section_LV (Section):
    """! 
    Instances of this class represents Low Voltage table sections (common street with houses).
    All platforms on this section only accepts LV modules.
    """

    ## Static string which indicates the voltage level of this section (LV, MV or HV).  
    voltage = "LV"

    ## Static int indicating the total number of ledstrips in this table section.
    num_ledstrips  = 16

    ## Static int indicating the total number of buses.
    num_buses      = 16

    ## Nominal voltage of all busses in this section
    v_nom = 0.4

    ##Series reactance, must be non-zero for AC branch in linear power flow.
    x = 0.1

    ## Series resistance, must be non-zero for DC branch in linear power flow.
    r = 0.01

    snom=99999999999999

    linetype="15-AL1/3-ST1A 0.4"
    
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
        self.add_line("line3",  bus0="bus2",  bus1="bus4",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line4",  bus0="bus4",  bus1="bus5",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line5",  bus0="bus4",  bus1="bus6",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line6",  bus0="bus6",  bus1="bus7",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line7",  bus0="bus6",  bus1="bus8",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line8",  bus0="bus8",  bus1="bus9",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line9",  bus0="bus8",  bus1="bus10", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line10", bus0="bus10", bus1="bus11", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line11", bus0="bus10", bus1="bus12", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line12", bus0="bus12", bus1="bus13", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line13", bus0="bus12", bus1="bus14", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line14", bus0="bus14", bus1="bus15", x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)
        self.add_line("line15", bus0="bus14", bus1="bus1",  x=self.x, r=self.r, s_nom=self.snom, type=self.linetype, length=self.length)

        any_component = []
        any_component.append("Generator")
        any_component.append("Load")
        any_component.append("Storage")

        LV_transformer = []
        LV_transformer.append("Transformer")

        # platforms
        self.add_platform("bus13", self.voltage, 0, [12], LV_transformer)
        self.add_platform("bus15", self.voltage, 1, [14], any_component)
        self.add_platform("bus0",  self.voltage, 2, [0],  any_component)
        self.add_platform("bus3",  self.voltage, 3, [2],  any_component)
        self.add_platform("bus5",  self.voltage, 4, [4],  any_component)
        self.add_platform("bus7",  self.voltage, 5, [6],  any_component)
        self.add_platform("bus9",  self.voltage, 6, [8],  any_component)
        self.add_platform("bus11", self.voltage, 7, [10], any_component)

        # bind ledstrips with its respective lines
        prefix = section_name + "_"

        ## Static int indicating critical power level of a power line.
        ## Active power values above this level are considered critical.
        self.threshold_critical = 0.63

        ## Static int indicating high power level of a power line.
        ## Active power values above this level are considered high.
        self.threshold_high = 0.5

        ## Static int indicating normal power level of a power line.
        ## Active power values above this level are considered normal.
        self.threshold_normal = 0.45

        ## Static int indicating low power level of a power line.
        ## Active power values above this level are considered low.
        self.threshold_low = 0.2

        ## Grey = 0x808080
        self.background_color.red = 48
        self.background_color.green = 48
        self.background_color.blue = 48

        for i in range(0, self.num_ledstrips):
            self.ledstrips[i].line = prefix + "line" + str(i)
            self.ledstrips[i].set_ledstrip_id(i)
            self.ledstrips[i].set_background_color(self.background_color)
            self.ledstrips[i].set_background_flashing_time(0)
