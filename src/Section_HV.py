##
# @file Section_HV.py
#
# @brief Objects of this class represents High Voltage table sections (heavy power generators).
# All platforms on this section only accepts HV modules.
#
# @section libraries_Section_HV Libraries/Modules
# - 
#
# @section todo_Section_HV TODO
# - None
#
# @section author_Section_HV Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

from src.Section import Section
from src.led.LEDStrip import LEDStrip

class Section_HV (Section):
    """! 
    Instances of this class represents High Voltage table sections (heavy power generators).
    All platforms on this section only accepts HV modules.
    """

    ## Static string which indicates the voltage level of this section (LV, MV or HV).
    voltage = "HV"

    ## Static int indicating the total number of ledstrips in this table section.
    num_ledstrips = 12

    ## Static int indicating the total number of buses.
    num_buses = 13

    ## Nominal voltage of all busses in this section
    v_nom = 110

    ##Series reactance, must be non-zero for AC branch in linear power flow.
    x = 0.1

    ## Series resistance, must be non-zero for DC branch in linear power flow.
    r = 0.01
    
    s_nom=99999999999999
    linetype="149-AL1/24-ST1A 110.0"
    length=10
    
    def __init__(self, section_name):
        """! 
        Constructor.
        @param section_name (str) Unique name of this stable section (for example "Table1").
        """

        Section.__init__(self, section_name)
        s_nom=70
        
        # ledstrips
        for i in range(self.num_ledstrips):
            self.ledstrips.append(LEDStrip())
            self._previous_ledstrips.append(LEDStrip())

        # buses
        for i in range(0, self.num_buses):
            bus_name = "bus" + str(i)
            self.add_bus(bus_name, self.v_nom)

        # lines
        self.add_line("line0",  bus0="bus0", bus1="bus1",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line1",  bus0="bus1", bus1="bus2",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line2",  bus0="bus1", bus1="bus3",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line3",  bus0="bus3", bus1="bus4",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line4",  bus0="bus4", bus1="bus5",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line5",  bus0="bus3", bus1="bus6",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line6",  bus0="bus6", bus1="bus7",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line7",  bus0="bus7", bus1="bus8",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line8",  bus0="bus8", bus1="bus9",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line9",  bus0="bus7", bus1="bus10",  x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line10", bus0="bus10", bus1="bus11", x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)
        self.add_line("line11", bus0="bus10", bus1="bus12", x=self.x, r=self.r, s_nom=self. s_nom, type=self.linetype, length=self.length)

        any_component = []
        any_component.append("Generator")
        any_component.append("Load")
        any_component.append("Storage")

        HV_transformers = []
        HV_transformers.append("Transformer")

        # platforms
        self.add_platform("bus0",  self.voltage, 5, [0],    any_component)
        self.add_platform("bus5",  self.voltage, 0, [3, 4], HV_transformers)
        self.add_platform("bus9",  self.voltage, 3, [7, 8], HV_transformers)
        self.add_platform("bus11", self.voltage, 1, [10],   any_component)

        # bind ledstrips with its respective lines
        prefix = section_name + "_"

        ## Static int indicating critical power level of a power line.
        ## Active power values above this level are considered critical.
        self.threshold_critical = 35

        ## Static int indicating high power level of a power line.
        ## Active power values above this level are considered high.
        self.threshold_high = 30

        ## Static int indicating normal power level of a power line.
        ## Active power values above this level are considered normal.
        self.threshold_normal = 20

        ## Static int indicating low power level of a power line.
        ## Active power values above this level are considered low.
        self.threshold_low = 10

        ## Darkblue = 0x00008B
        self.background_color.red = 0
        self.background_color.green = 0
        self.background_color.blue = 48

        for i in range(0, self.num_ledstrips):
            self.ledstrips[i].line = prefix + "line" + str(i)
            self.ledstrips[i].set_ledstrip_id(i)
            self.ledstrips[i].set_background_color(self.background_color)
            self.ledstrips[i].set_background_flashing_time(0)
