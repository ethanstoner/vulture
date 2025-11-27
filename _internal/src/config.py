#!/usr/bin/env python3
"""
Vulture - Configuration Manager
Manages configuration settings for Vulture
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any


class Config:
    """Manages Vulture configuration."""
    
    DEFAULT_CONFIG = {
        'default_mc_version': '1.8.9',
        'default_decompiler': 'cfr',
        'auto_download_tools': True,
        'auto_download_mappings': True,
        'auto_detect_version': True,
        'use_specialsource': True,
        'tools_dir': None,  # Auto-detect
        'mappings_dir': None,  # Auto-detect
        'output_dir': None,  # Auto-detect
    }
    
    def __init__(self, config_file: Optional[str] = None):
        if config_file is None:
            # Try Docker path first, then local
            self.config_file = Path("/workspace/.vulture_config.json")
            if not self.config_file.exists():
                self.config_file = Path.home() / ".vulture_config.json"
        else:
            self.config_file = Path(config_file)
        
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(user_config)
                    return config
            except Exception as e:
                print(f"⚠ Error loading config: {e}, using defaults")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
    
    def get_tools_dir(self) -> Path:
        """Get tools directory path."""
        tools_dir = self.config.get('tools_dir')
        if tools_dir:
            return Path(tools_dir)
        
        # Auto-detect
        tools_dir = Path("/workspace/tools")
        if not tools_dir.exists():
            tools_dir = Path("tools")
        return tools_dir
    
    def get_mappings_dir(self) -> Path:
        """Get mappings directory path."""
        mappings_dir = self.config.get('mappings_dir')
        if mappings_dir:
            return Path(mappings_dir)
        
        # Auto-detect
        mappings_dir = Path("/workspace/mappings")
        if not mappings_dir.exists():
            mappings_dir = Path("mappings")
        return mappings_dir


def main():
    """CLI for configuration management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vulture Configuration Manager")
    parser.add_argument('--get', type=str, help='Get configuration value')
    parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), help='Set configuration value')
    parser.add_argument('--list', action='store_true', help='List all configuration values')
    parser.add_argument('--config-file', type=str, help='Configuration file path')
    
    args = parser.parse_args()
    
    config = Config(args.config_file)
    
    if args.get:
        value = config.get(args.get)
        print(value)
    elif args.set:
        key, value = args.set
        # Try to parse value as JSON
        try:
            value = json.loads(value)
        except:
            # Keep as string
            pass
        config.set(key, value)
        config.save()
        print(f"✓ Set {key} = {value}")
    elif args.list:
        for key, value in config.config.items():
            print(f"{key} = {value}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
