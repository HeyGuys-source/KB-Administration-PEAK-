import json
import os
from typing import Dict, Any

class BotConfig:
    def __init__(self):
        self.config_file = 'config.json'
        self.default_config = {
            "mod_log_channel": None,
            "default_mute_role": "Muted",
            "max_warnings": 3,
            "auto_ban_on_max_warnings": False,
            "log_all_actions": True,
            "embed_color": 0x2F3136,
            "success_color": 0x00FF00,
            "error_color": 0xFF0000,
            "warning_color": 0xFFFF00
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.default_config.copy()
        else:
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any] = None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
    
    def get_guild_setting(self, guild_id: int, setting: str, default=None):
        """Get guild-specific setting"""
        guild_key = f"guild_{guild_id}"
        if guild_key not in self.config:
            self.config[guild_key] = {}
        
        return self.config[guild_key].get(setting, default)
    
    def set_guild_setting(self, guild_id: int, setting: str, value: Any):
        """Set guild-specific setting"""
        guild_key = f"guild_{guild_id}"
        if guild_key not in self.config:
            self.config[guild_key] = {}
        
        self.config[guild_key][setting] = value
        self.save_config()
