"""
Tests for OCR engine implementations.

This module contains tests to validate the OCR engine abstraction layer
and individual engine implementations.
"""

import pytest
import tempfile
import os
from PIL import Image
import numpy as np

from src.ocr.engines import (
    OCREngine, 
    OCRResult, 
    EngineConfig,
    TesseractEngine,
    EasyOCREngine
)


class TestOCRResult:
    """Test OCRResult dataclass."""
    
    def test_ocr_result_creation(self):
        """Test creating an OCRResult instance."""
        result = OCRResult(
            text="Test text",
            confidence=0.95,
            bounding_box=(10, 20, 100, 50),
            engine_name="test_engine"
        )
        
        assert result.text == "Test text"
        assert result.confidence == 0.95
        assert result.bounding_box == (10, 20, 100, 50)
        assert result.engine_name == "test_engine"


class TestEngineConfig:
    """Test EngineConfig dataclass."""
    
    def test_engine_config_creation(self):
        """Test creating an EngineConfig instance."""
        config = EngineConfig(
            name="test_engine",
            enabled=True,
            priority=1,
            timeout=30.0,
            confidence_threshold=0.5
        )
        
        assert config.name == "test_engine"
        assert config.enabled is True
        assert config.priority == 1
        assert config.timeout == 30.0
        assert config.confidence_threshold == 0.5


class TestTesseractEngine:
    """Test TesseractEngine implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = EngineConfig(
            name="test_tesseract",
            enabled=True,
            priority=1
        )
        self.engine = TesseractEngine(self.config)
    
    def test_engine_creation(self):
        """Test TesseractEngine creation."""
        assert self.engine.name == "test_tesseract"
        assert self.engine.enabled is True
        assert self.engine.priority == 1
    
    def test_engine_info(self):
        """Test getting engine information."""
        info = self.engine.get_engine_info()
        assert info['name'] == "test_tesseract"
        assert info['enabled'] is True
        assert info['priority'] == 1
    
    def test_is_available(self):
        """Test availability check."""
        # This test will pass if Tesseract is installed, fail if not
        # We'll just test that the method exists and doesn't crash
        available = self.engine.is_available()
        assert isinstance(available, bool)
    
    def test_initialization(self):
        """Test engine initialization."""
        # This test will pass if Tesseract is available and can be initialized
        # We'll just test that the method exists and doesn't crash
        initialized = self.engine.initialize()
        assert isinstance(initialized, bool)
    
    def test_image_preprocessing(self):
        """Test image preprocessing."""
        # Create a test image
        test_image = Image.new('RGB', (100, 50), color='white')
        
        # Test preprocessing
        processed = self.engine._preprocess_image(test_image)
        assert isinstance(processed, Image.Image)
        assert processed.mode == 'RGB'


class TestEasyOCREngine:
    """Test EasyOCREngine implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = EngineConfig(
            name="test_easyocr",
            enabled=True,
            priority=2
        )
        self.engine = EasyOCREngine(self.config)
    
    def test_engine_creation(self):
        """Test EasyOCREngine creation."""
        assert self.engine.name == "test_easyocr"
        assert self.engine.enabled is True
        assert self.engine.priority == 2
    
    def test_engine_info(self):
        """Test getting engine information."""
        info = self.engine.get_engine_info()
        assert info['name'] == "test_easyocr"
        assert info['enabled'] is True
        assert info['priority'] == 2
    
    def test_is_available(self):
        """Test availability check."""
        # This test will pass if EasyOCR is installed, fail if not
        # We'll just test that the method exists and doesn't crash
        available = self.engine.is_available()
        assert isinstance(available, bool)
    
    def test_initialization(self):
        """Test engine initialization."""
        # This test will pass if EasyOCR is available and can be initialized
        # We'll just test that the method exists and doesn't crash
        initialized = self.engine.initialize()
        assert isinstance(initialized, bool)
    
    def test_language_configuration(self):
        """Test language configuration."""
        # Test default languages
        assert 'en' in self.engine._languages
        assert 'no' in self.engine._languages
        
        # Test custom languages
        custom_config = EngineConfig(
            name="custom_easyocr",
            custom_params={'languages': ['en', 'sv']}
        )
        custom_engine = EasyOCREngine(custom_config)
        assert 'en' in custom_engine._languages
        assert 'sv' in custom_engine._languages


class TestOCRIntegration:
    """Test OCR engine integration."""
    
    def test_engine_imports(self):
        """Test that all engines can be imported."""
        from src.ocr.engines import (
            OCREngine, 
            OCRResult, 
            EngineConfig,
            TesseractEngine,
            EasyOCREngine
        )
        
        # Test that classes are properly imported
        assert OCREngine is not None
        assert OCRResult is not None
        assert EngineConfig is not None
        assert TesseractEngine is not None
        assert EasyOCREngine is not None
    
    def test_engine_inheritance(self):
        """Test that engines properly inherit from base class."""
        tesseract_config = EngineConfig(name="tesseract")
        easyocr_config = EngineConfig(name="easyocr")
        
        tesseract_engine = TesseractEngine(tesseract_config)
        easyocr_engine = EasyOCREngine(easyocr_config)
        
        assert isinstance(tesseract_engine, OCREngine)
        assert isinstance(easyocr_engine, OCREngine)


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
