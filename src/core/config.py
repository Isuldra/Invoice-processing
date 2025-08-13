"""
Configuration management for Telia PDF Processing System.

This module handles all configuration settings including OCR engines,
processing parameters, and system settings.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OCRConfig:
    """Configuration for OCR engines."""
    tesseract_path: Optional[str] = None
    tesseract_config: str = "--oem 3 --psm 6"
    easyocr_languages: list = None
    confidence_threshold: float = 0.7
    max_workers: int = 2

    def __post_init__(self):
        if self.easyocr_languages is None:
            self.easyocr_languages = ['en', 'no']


@dataclass
class ProcessingConfig:
    """Configuration for document processing."""
    dpi: int = 250  # Reduced from 300 for performance
    preprocessing_enabled: bool = True
    deskew_enabled: bool = True
    noise_reduction: bool = True
    contrast_enhancement: bool = True
    timeout_seconds: int = 60


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
        self.ocr = OCRConfig()
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
        if 'ocr' in config_data:
            for key, value in config_data['ocr'].items():
                if hasattr(self.ocr, key):
                    setattr(self.ocr, key, value)
        
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
            'ocr': {
                'tesseract_path': None,
                'tesseract_config': '--oem 3 --psm 6',
                'easyocr_languages': ['en', 'no'],
                'confidence_threshold': 0.7,
                'max_workers': 2
            },
            'processing': {
                'dpi': 250,
                'preprocessing_enabled': True,
                'deskew_enabled': True,
                'noise_reduction': True,
                'contrast_enhancement': True,
                'timeout_seconds': 60
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
            'ocr': {
                'tesseract_path': self.ocr.tesseract_path,
                'tesseract_config': self.ocr.tesseract_config,
                'easyocr_languages': self.ocr.easyocr_languages,
                'confidence_threshold': self.ocr.confidence_threshold,
                'max_workers': self.ocr.max_workers
            },
            'processing': {
                'dpi': self.processing.dpi,
                'preprocessing_enabled': self.processing.preprocessing_enabled,
                'deskew_enabled': self.processing.deskew_enabled,
                'noise_reduction': self.processing.noise_reduction,
                'contrast_enhancement': self.processing.contrast_enhancement,
                'timeout_seconds': self.processing.timeout_seconds
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
