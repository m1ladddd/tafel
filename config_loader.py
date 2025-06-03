# config_loader.py
"""
Module for centralized configuration loading.
Handles loading of main config and GUI line remapping configurations.
"""

import json
from typing import List, Dict, Any
from src.IndexRemap import IndexRemap


class ConfigLoader:
    """Handles loading and management of all application configurations."""
    
    def __init__(self, main_config_path: str = "config.json"):
        self.main_config_path = main_config_path
        self.main_config = self._load_json(main_config_path)
        self.gui_line_remaps = self._load_gui_line_remaps()
        
    def _load_json(self, path: str) -> Dict[str, Any]:
        """Load and parse a JSON configuration file."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration Error: File not found at {path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Configuration Error: Could not parse JSON in {path}: {e}")
            return {}
        except Exception as e:
            print(f"Configuration Error: Unexpected error loading {path}: {e}")
            return {}
    
    def _load_gui_line_remaps(self) -> List[IndexRemap]:
        """Load all GUI line remapping configurations."""
        remaps = []
        base_path = "configuration/gui_line_remap/"
        
        # Load 6 table remaps (could be made configurable via main_config)
        for i in range(1, 7):
            remap_path = f"{base_path}gui_remap_table{i}.json"
            ir = IndexRemap()
            
            try:
                ir.load(remap_path)
                remaps.append(ir)
                print(f"Loaded GUI remap for table {i}")
            except FileNotFoundError:
                print(f"GUI Remap Warning: File not found {remap_path}")
                remaps.append(ir)  # Add empty remap to maintain indexing
            except Exception as e:
                print(f"GUI Remap Error: Failed to load {remap_path}: {e}")
                remaps.append(ir)  # Add empty remap to maintain indexing
                
        return remaps
    
    def get_main_config(self) -> Dict[str, Any]:
        """Get the main configuration dictionary."""
        return self.main_config
    
    def get_gui_line_remaps(self) -> List[IndexRemap]:
        """Get the GUI line remapping objects."""
        return self.gui_line_remaps
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a specific configuration value with optional default."""
        return self.main_config.get(key, default) 