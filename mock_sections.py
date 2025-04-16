# This simulates the behavior of the table sections

import json
import random

class MockTableSection:
    """
    A mock version of the table section class that simulates a physical table section.
    """
    def __init__(self, section_id, section_name):
        self.id = section_id
        self.name = section_name
        self.connected = True
        self.modules = []
        self.led_strips = []
        self.rfid_tags = {}
        
        # Add some default LED strips for visualization
        self._init_default_led_strips()
    
    def _init_default_led_strips(self):
        """Initialize default LED strips for visualization"""
        # Number of LED strips depends on the section type
        num_strips = 8
        if self.id == 1:  # High Voltage section
            num_strips = 4
        elif self.id == 2:  # Medium Voltage Ring
            num_strips = 0
        
        # Create mock LED strips
        for i in range(num_strips):
            self.led_strips.append({
                'id': i,
                'flow_color': {'red': 0, 'green': 0, 'blue': 255, 'alpha': 128},
                'flow_direction': 0,
                'flow_speed': 1000,
                'background_color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 0}
            })
    
    def update_leds(self, led_data):
        """Simulate updating the LEDs with provided data"""
        for led in led_data:
            print(f"Section {self.id}: Would update LED {led['id']} with color {led.get('flow_color', {})}")
            # Update our mock representation
            for strip in self.led_strips:
                if strip['id'] == led['id']:
                    if 'flow_color' in led:
                        strip['flow_color'] = led['flow_color']
                    if 'flow_direction' in led:
                        strip['flow_direction'] = led['flow_direction']
                    if 'flow_speed' in led:
                        strip['flow_speed'] = led['flow_speed']
    
    def add_rfid_tag(self, tag_id, uid):
        """Add a simulated RFID tag"""
        self.rfid_tags[tag_id] = uid
        print(f"Section {self.id}: Added RFID tag ID {tag_id} with UID {uid}")
    
    def remove_rfid_tag(self, tag_id):
        """Remove a simulated RFID tag"""
        if tag_id in self.rfid_tags:
            del self.rfid_tags[tag_id]
            print(f"Section {self.id}: Removed RFID tag ID {tag_id}")
    
    def get_all_rfid_tags(self):
        """Return all simulated RFID tags"""
        return self.rfid_tags
    
    def get_modules(self):
        """Return the simulated modules for this section"""
        return self.modules

def create_mock_sections():
    """Create a set of mock table sections"""
    sections = {}
    section_names = ["Table1", "Table2", "Table3", "Table4", "Table5", "Table6"]
    
    for i, name in enumerate(section_names, 1):
        sections[name] = MockTableSection(i, name)
    
    # Add some random modules to each section for demo purposes
    for section in sections.values():
        num_modules = random.randint(1, 5)
        for i in range(num_modules):
            module_id = random.randint(1, 10)
            section.modules.append({
                "id": module_id,
                "type": random.choice(["generation", "load", "storage"]),
                "value": random.uniform(0.5, 10.0)
            })
    
    return sections

def simulate_table_connection():
    """
    This function creates a mock connection to simulate that table sections are connected.
    """
    print("────────────────────────────────────────────────────────────────")
    print("──────── Simulating connection to SmartGridTable sections ──────")
    print("────────────────────────────────────────────────────────────────")
    
    # Return a list of simulated section IDs
    return [1, 2, 3, 4, 5, 6]