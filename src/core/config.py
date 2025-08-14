"""
Configuration management for Invoice Processing System.

This module handles all configuration settings for text-based processing,
processing parameters, and system settings.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ProcessingConfig:
    """Configuration for document processing."""
    timeout_seconds: int = 60
    max_workers: int = 2


@dataclass
class ValidationConfig:
    """Configuration for data validation."""
    name_confidence_threshold: float = 0.8
    phone_confidence_threshold: float = 0.9
    cost_confidence_threshold: float = 0.95
    fuzzy_match_threshold: float = 0.8


class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.processing = ProcessingConfig()
        self.validation = ValidationConfig()
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        return str(Path(__file__).parent.parent.parent / "config" / "config.yaml")
    
    def _load_config(self):
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    self._update_from_dict(config_data)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _update_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration from dictionary."""
        if 'processing' in config_data:
            for key, value in config_data['processing'].items():
                if hasattr(self.processing, key):
                    setattr(self.processing, key, value)
        
        if 'validation' in config_data:
            for key, value in config_data['validation'].items():
                if hasattr(self.validation, key):
                    setattr(self.validation, key, value)
    
    def _create_default_config(self):
        """Create default configuration file."""
        config_data = {
            'processing': {
                'timeout_seconds': 60,
                'max_workers': 2
            },
            'validation': {
                'name_confidence_threshold': 0.8,
                'phone_confidence_threshold': 0.9,
                'cost_confidence_threshold': 0.95,
                'fuzzy_match_threshold': 0.8
            }
        }
        
        # Ensure config directory exists
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not create config file: {e}")
    
    def save(self):
        """Save current configuration to file."""
        config_data = {
            'processing': {
                'timeout_seconds': self.processing.timeout_seconds,
                'max_workers': self.processing.max_workers
            },
            'validation': {
                'name_confidence_threshold': self.validation.name_confidence_threshold,
                'phone_confidence_threshold': self.validation.phone_confidence_threshold,
                'cost_confidence_threshold': self.validation.cost_confidence_threshold,
                'fuzzy_match_threshold': self.validation.fuzzy_match_threshold
            }
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")


# Global configuration instance
config = Config()
