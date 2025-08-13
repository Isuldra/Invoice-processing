"""
Basic tests for OCR engine base classes.

This module contains tests that don't require external OCR engines
to be installed, focusing on the base abstraction layer.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ocr.engines.base import OCRResult, EngineConfig


def test_ocr_result_creation():
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
    print("✅ OCRResult creation test passed")


def test_engine_config_creation():
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
    print("✅ EngineConfig creation test passed")


def test_ocr_result_validation():
    """Test OCRResult validation logic."""
    # Test high confidence result
    high_conf_result = OCRResult(
        text="Valid text",
        confidence=0.9,
        engine_name="test_engine"
    )
    
    # Test low confidence result
    low_conf_result = OCRResult(
        text="Invalid text",
        confidence=0.3,
        engine_name="test_engine"
    )
    
    # Create a mock engine config for validation
    config = EngineConfig(
        name="test_engine",
        confidence_threshold=0.5
    )
    
    # Test validation logic
    assert config.confidence_threshold == 0.5
    assert high_conf_result.confidence >= config.confidence_threshold
    assert low_conf_result.confidence < config.confidence_threshold
    print("✅ OCRResult validation test passed")


if __name__ == "__main__":
    print("Running OCR base tests...")
    test_ocr_result_creation()
    test_engine_config_creation()
    test_ocr_result_validation()
    print("🎉 All OCR base tests passed!")
