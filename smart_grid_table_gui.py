#!/usr/bin/env python3
"""
Smart Grid Table GUI - Visual representation of the physical table
Shows real-time status of all modules, power flows, and calculations
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import math
import sys
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Add src to path for imports
sys.path.append('src')
sys.path.append('.')

from main_controller import MainApplicationController
from app_state import AppState

class SmartGridTableGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Smart Grid Table - Live View")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#1a1a1a')
        
        # Initialize app controller
        self.app_controller = None
        self.table = None
        self.running = False
        
        # Colors based on voltage levels
        self.colors = {
            'HV': '#0000B0',      # Dark Blue (110kV)
            'MV': '#B000B0',      # Magenta (10kV) 
            'LV': '#606060',      # Grey (0.4kV)
            'bg': '#1a1a1a',      # Dark background
            'line': '#404040',    # Line color
            'bus': '#808080',     # Bus color
            'module_empty': '#2a2a2a',  # Empty platform
            'module_gen': '#00aa00',     # Generator (green)
            'module_load': '#aa0000',    # Load (red)
            'module_tf': '#ffaa00',      # Transformer (orange)
            'module_storage': '#0088aa', # Storage (cyan)
            'text': '#ffffff',           # White text
            'power_high': '#ff4444',     # High power flow
            'power_med': '#ffaa44',      # Medium power flow
            'power_low': '#44aa44'       # Low power flow
        }
        
        # Table layout configuration
        self.table_config = {
            'Table1': {
                'type': 'HV', 'pos': (100, 100), 'size': (280, 160),
                'platforms': {0: (40, 40), 1: (200, 40), 3: (200, 120), 5: (40, 120)}
            },
            'Table2': {
                'type': 'MV', 'pos': (450, 50), 'size': (400, 260),
                'platforms': {}  # Ring layout - no visible platforms
            },
            'Table3': {
                'type': 'MV', 'pos': (900, 100), 'size': (280, 300),
                'platforms': {0: (40, 40), 1: (120, 40), 2: (200, 40), 3: (240, 120),
                             4: (200, 200), 5: (120, 200), 6: (40, 200), 7: (0, 120)}
            },
            'Table4': {
                'type': 'LV', 'pos': (100, 400), 'size': (280, 300),
                'platforms': {0: (40, 40), 1: (120, 40), 2: (200, 40), 3: (240, 120),
                             4: (200, 200), 5: (120, 200), 6: (40, 200), 7: (0, 120)}
            },
            'Table5': {
                'type': 'LV', 'pos': (450, 400), 'size': (280, 300),
                'platforms': {0: (40, 40), 1: (120, 40), 2: (200, 40), 3: (240, 120),
                             4: (200, 200), 5: (120, 200), 6: (40, 200), 7: (0, 120)}
            },
            'Table6': {
                'type': 'LV', 'pos': (800, 400), 'size': (280, 300),
                'platforms': {0: (40, 40), 1: (120, 40), 2: (200, 40), 3: (240, 120),
                             4: (200, 200), 5: (120, 200), 6: (40, 200), 7: (0, 120)}
            }
        }
        
        # Transformer connections (based on SmartGridTable.py)
        self.transformer_links = [
            {'from': 'Table1', 'pos': 0, 'to': 'Table2', 'color': '#ffaa00'},
            {'from': 'Table1', 'pos': 3, 'to': 'Table2', 'color': '#ffaa00'}, 
            {'from': 'Table2', 'to': 'Table3', 'color': '#ff8800'},
            {'from': 'Table3', 'to': 'Table4', 'color': '#ff6600'},
            {'from': 'Table2', 'to': 'Table5', 'color': '#ff6600'},
            {'from': 'Table2', 'to': 'Table6', 'color': '#ff6600'}
        ]
        
        self.create_widgets()
        self.update_thread = None
        
    def create_widgets(self):
        """Create the GUI layout"""
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Smart Grid Table - Live Monitoring", 
                              font=('Arial', 24, 'bold'), fg=self.colors['text'], bg=self.colors['bg'])
        title_label.pack(pady=(0, 10))
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        control_frame = tk.Frame(status_frame, bg=self.colors['bg'])
        control_frame.pack(side=tk.LEFT)
        
        self.start_btn = tk.Button(control_frame, text="Start System", command=self.start_system,
                                  bg='#006600', fg='white', font=('Arial', 12, 'bold'))
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.calc_btn = tk.Button(control_frame, text="Force Calculate", command=self.force_calculate,
                                 bg='#0066aa', fg='white', font=('Arial', 12, 'bold'))
        self.calc_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.sim_btn = tk.Button(control_frame, text="Simulate Quick", command=self.simulate_quick,
                                bg='#aa6600', fg='white', font=('Arial', 12, 'bold'))
        self.sim_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status labels
        self.status_label = tk.Label(status_frame, text="Status: Ready", 
                                    font=('Arial', 12), fg=self.colors['text'], bg=self.colors['bg'])
        self.status_label.pack(side=tk.RIGHT)
        
        # Main canvas for the table layout
        canvas_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg=self.colors['bg'], highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Info panel
        info_frame = tk.Frame(canvas_frame, bg=self.colors['bg'], width=300)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        info_frame.pack_propagate(False)
        
        info_title = tk.Label(info_frame, text="System Information", 
                             font=('Arial', 14, 'bold'), fg=self.colors['text'], bg=self.colors['bg'])
        info_title.pack(pady=(0, 10))
        
        # Legend
        legend_frame = tk.LabelFrame(info_frame, text="Legend", fg=self.colors['text'], 
                                    bg=self.colors['bg'], font=('Arial', 12, 'bold'))
        legend_frame.pack(fill=tk.X, pady=(0, 10))
        
        legend_items = [
            ("🔵 HV Section (110kV)", self.colors['HV']),
            ("🟣 MV Section (10kV)", self.colors['MV']),
            ("⚫ LV Section (0.4kV)", self.colors['LV']),
            ("🟢 Generator", self.colors['module_gen']),
            ("🔴 Load", self.colors['module_load']),
            ("🟡 Transformer", self.colors['module_tf']),
            ("🔵 Storage", self.colors['module_storage'])
        ]
        
        for text, color in legend_items:
            label = tk.Label(legend_frame, text=text, fg=color, bg=self.colors['bg'], 
                           font=('Arial', 10), anchor='w')
            label.pack(fill=tk.X, padx=5, pady=2)
        
        # Live stats
        self.stats_frame = tk.LabelFrame(info_frame, text="Live Statistics", 
                                        fg=self.colors['text'], bg=self.colors['bg'], 
                                        font=('Arial', 12, 'bold'))
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.modules_label = tk.Label(self.stats_frame, text="Modules: 0", 
                                     fg=self.colors['text'], bg=self.colors['bg'], anchor='w')
        self.modules_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.calc_status_label = tk.Label(self.stats_frame, text="Calculation: Not started", 
                                         fg=self.colors['text'], bg=self.colors['bg'], anchor='w')
        self.calc_status_label.pack(fill=tk.X, padx=5, pady=2)
        
        self.power_label = tk.Label(self.stats_frame, text="Total Generation: 0 MW", 
                                   fg=self.colors['text'], bg=self.colors['bg'], anchor='w')
        self.power_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Module details
        self.details_frame = tk.LabelFrame(info_frame, text="Module Details", 
                                          fg=self.colors['text'], bg=self.colors['bg'], 
                                          font=('Arial', 12, 'bold'))
        self.details_frame.pack(fill=tk.BOTH, expand=True)
        
        self.details_text = tk.Text(self.details_frame, bg='#2a2a2a', fg=self.colors['text'],
                                   font=('Courier', 9), wrap=tk.WORD)
        details_scroll = tk.Scrollbar(self.details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind canvas click
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # Initial draw
        self.draw_table_layout()
        
    def draw_table_layout(self):
        """Draw the complete table layout"""
        self.canvas.delete("all")
        
        # Draw sections
        for table_name, config in self.table_config.items():
            self.draw_section(table_name, config)
            
        # Draw transformer connections
        self.draw_connections()
        
    def draw_section(self, table_name, config):
        """Draw a table section with its platforms"""
        x, y = config['pos']
        w, h = config['size']
        section_type = config['type']
        
        # Section background
        self.canvas.create_rectangle(x, y, x+w, y+h, 
                                   outline=self.colors[section_type], 
                                   fill=self.colors[section_type], 
                                   width=3, stipple='gray25',
                                   tags=f"section_{table_name}")
        
        # Section label
        self.canvas.create_text(x+w//2, y+15, text=f"{table_name} ({section_type})", 
                              fill=self.colors['text'], font=('Arial', 12, 'bold'),
                              tags=f"section_{table_name}")
        
        # Voltage label
        voltage_map = {'HV': '110kV', 'MV': '10kV', 'LV': '0.4kV'}
        self.canvas.create_text(x+w//2, y+h-15, text=voltage_map[section_type], 
                              fill=self.colors['text'], font=('Arial', 10),
                              tags=f"section_{table_name}")
        
        # Draw platforms
        for platform_id, (px, py) in config['platforms'].items():
            self.draw_platform(table_name, platform_id, x+px, y+py+25)
            
    def draw_platform(self, table_name, platform_id, x, y):
        """Draw a platform with its module (if any)"""
        platform_size = 35
        
        # Get module info if system is running
        module_info = self.get_module_info(table_name, platform_id)
        
        if module_info:
            module_type = module_info.get('type', 'unknown')
            module_name = module_info.get('name', 'Unknown')
            
            # Determine color based on module type
            if 'generator' in module_type.lower() or 'powerplant' in module_name.lower() or 'solar' in module_name.lower() or 'wind' in module_name.lower():
                color = self.colors['module_gen']
                symbol = "⚡"
            elif 'transformer' in module_type.lower():
                color = self.colors['module_tf'] 
                symbol = "🔄"
            elif 'load' in module_type.lower() or 'factory' in module_name.lower() or 'house' in module_name.lower():
                color = self.colors['module_load']
                symbol = "🏭"
            elif 'storage' in module_type.lower():
                color = self.colors['module_storage']
                symbol = "🔋"
            else:
                color = self.colors['module_empty']
                symbol = "?"
        else:
            color = self.colors['module_empty']
            symbol = "⬜"
            module_name = "Empty"
        
        # Draw platform
        self.canvas.create_rectangle(x-platform_size//2, y-platform_size//2, 
                                   x+platform_size//2, y+platform_size//2,
                                   outline='white', fill=color, width=2,
                                   tags=f"platform_{table_name}_{platform_id}")
        
        # Platform symbol/label
        self.canvas.create_text(x, y-8, text=symbol, fill='white', 
                              font=('Arial', 12), tags=f"platform_{table_name}_{platform_id}")
        
        # Position number
        self.canvas.create_text(x, y+8, text=str(platform_id), fill='white', 
                              font=('Arial', 8), tags=f"platform_{table_name}_{platform_id}")
        
    def draw_connections(self):
        """Draw transformer connections between sections"""
        for link in self.transformer_links:
            from_table = link['from']
            to_table = link['to']
            
            from_config = self.table_config[from_table]
            to_config = self.table_config[to_table]
            
            # Calculate connection points
            if 'pos' in link:
                # Specific platform connection
                platform_pos = link['pos']
                if platform_pos in from_config['platforms']:
                    px, py = from_config['platforms'][platform_pos]
                    from_x = from_config['pos'][0] + px
                    from_y = from_config['pos'][1] + py + 25
                else:
                    from_x = from_config['pos'][0] + from_config['size'][0] // 2
                    from_y = from_config['pos'][1] + from_config['size'][1] // 2
            else:
                # Center connection
                from_x = from_config['pos'][0] + from_config['size'][0] // 2
                from_y = from_config['pos'][1] + from_config['size'][1] // 2
                
            to_x = to_config['pos'][0] + to_config['size'][0] // 2
            to_y = to_config['pos'][1] + to_config['size'][1] // 2
            
            # Draw connection line
            self.canvas.create_line(from_x, from_y, to_x, to_y, 
                                  fill=link['color'], width=4, 
                                  tags="connection")
    
    def get_module_info(self, table_name, platform_id):
        """Get information about a module on a specific platform"""
        if not self.table:
            return None
            
        try:
            # Find the section
            for section in self.table._SmartGridTable__table_sections:
                if section.name == table_name:
                    # Find the platform
                    for platform in section.platforms:
                        if platform.RFID_location == platform_id:
                            if platform.module:
                                return {
                                    'name': platform.module.name,
                                    'type': getattr(platform.module, 'type', 'unknown'),
                                    'rfid': platform.module.RFID_tag,
                                    'active': getattr(platform.module, 'active', True)
                                }
                            return None
        except:
            pass
        return None
    
    def on_canvas_click(self, event):
        """Handle canvas click events"""
        # Find clicked item
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        
        for tag in tags:
            if tag.startswith("platform_"):
                parts = tag.split("_")
                if len(parts) >= 3:
                    table_name = parts[1]
                    platform_id = int(parts[2])
                    self.show_platform_details(table_name, platform_id)
                break
    
    def show_platform_details(self, table_name, platform_id):
        """Show detailed information about a platform"""
        module_info = self.get_module_info(table_name, platform_id)
        
        details = f"=== {table_name} Platform {platform_id} ===\n\n"
        
        if module_info:
            details += f"Module: {module_info['name']}\n"
            details += f"RFID: {module_info['rfid']}\n"
            details += f"Type: {module_info['type']}\n"
            details += f"Active: {module_info['active']}\n"
            
            # Try to get power information
            if self.table:
                try:
                    for section in self.table._SmartGridTable__table_sections:
                        if section.name == table_name:
                            for platform in section.platforms:
                                if platform.RFID_location == platform_id and platform.module:
                                    for component in platform.components:
                                        if hasattr(component, 'active_power') and component.active_power:
                                            power = component.active_power[0] if component.active_power else 0
                                            details += f"Power: {power:.2f} MW\n"
                                        break
                except:
                    pass
        else:
            details += "No module placed\n"
            
        details += f"\nClick 'Simulate Quick' to place modules\n"
        details += f"or use command: simulate place <RFID> {table_name} {platform_id}"
        
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
    
    def start_system(self):
        """Start the Smart Grid Table system"""
        if self.app_controller:
            return
            
        try:
            self.status_label.config(text="Status: Starting system...")
            self.root.update()
            
            # Initialize with simulation mode
            sys.argv = ['smart_grid_table_gui.py', '--simulation']
            
            # Create app controller
            self.app_controller = MainApplicationController()
            self.app_controller._initialize_system()
            
            self.table = self.app_controller.table
            self.running = True
            
            self.status_label.config(text="Status: System running")
            self.start_btn.config(state='disabled')
            
            # Start update thread
            self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
            self.update_thread.start()
            
            messagebox.showinfo("Success", "Smart Grid Table system started successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start system: {e}")
            self.status_label.config(text="Status: Failed to start")
    
    def force_calculate(self):
        """Force a power flow calculation"""
        if not self.table:
            messagebox.showwarning("Warning", "System not started yet")
            return
            
        try:
            self.status_label.config(text="Status: Calculating...")
            self.root.update()
            
            success = self.table.force_calculate()
            
            if success:
                self.status_label.config(text="Status: Calculation successful")
                messagebox.showinfo("Success", "Power flow calculation completed successfully!")
            else:
                self.status_label.config(text="Status: Calculation failed")
                messagebox.showwarning("Warning", "Power flow calculation failed")
                
        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {e}")
            self.status_label.config(text="Status: Calculation error")
    
    def simulate_quick(self):
        """Place modules via quick simulation"""
        if not self.app_controller:
            messagebox.showwarning("Warning", "System not started yet")
            return
            
        try:
            self.status_label.config(text="Status: Placing modules...")
            self.root.update()
            
            # Use command dispatcher to place modules
            self.app_controller.command_dispatcher._simulate_quick_setup()
            
            self.status_label.config(text="Status: Modules placed")
            messagebox.showinfo("Success", "Quick simulation modules placed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Simulation error: {e}")
            self.status_label.config(text="Status: Simulation error")
    
    def update_loop(self):
        """Background update loop"""
        while self.running:
            try:
                self.update_display()
                time.sleep(1.0)  # Update every second
            except:
                break
    
    def update_display(self):
        """Update the visual display"""
        if not self.table:
            return
            
        # Update canvas
        self.root.after(0, self.draw_table_layout)
        
        # Update statistics
        try:
            total_modules = 0
            total_generation = 0
            total_load = 0
            
            for section in self.table._SmartGridTable__table_sections:
                for platform in section.platforms:
                    if platform.module:
                        total_modules += 1
                        
                        # Try to get power info
                        for component in platform.components:
                            if hasattr(component, 'active_power') and component.active_power:
                                power = component.active_power[0] if component.active_power else 0
                                if power > 0:
                                    total_generation += power
                                else:
                                    total_load += abs(power)
            
            calc_success = self.table.get_simulation_succes()
            calc_status = "Success" if calc_success else "Failed/Not run"
            
            # Update labels
            self.root.after(0, lambda: self.modules_label.config(text=f"Modules: {total_modules}"))
            self.root.after(0, lambda: self.calc_status_label.config(text=f"Calculation: {calc_status}"))
            self.root.after(0, lambda: self.power_label.config(text=f"Generation: {total_generation:.1f} MW"))
            
        except:
            pass
    
    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        finally:
            self.running = False
            if self.app_controller:
                try:
                    self.app_controller.app_state.request_shutdown()
                    self.app_controller._shutdown_system()
                except:
                    pass

def main():
    """Main function"""
    print("🔌 Smart Grid Table GUI Starting...")
    print("📊 This GUI shows a visual representation of your physical Smart Grid Table")
    print("🎮 Controls:")
    print("   • Start System: Initialize the simulation backend")
    print("   • Force Calculate: Run power flow calculations")
    print("   • Simulate Quick: Place a balanced set of modules")
    print("   • Click platforms: View detailed module information")
    print()
    
    gui = SmartGridTableGUI()
    gui.run()

if __name__ == "__main__":
    main() 