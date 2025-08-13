"""
OCR Engines module.

This module provides multiple OCR engine implementations for the
Telia PDF processing system, enabling improved accuracy through
multi-engine consensus.
"""

from .base import OCREngine, OCRResult, EngineConfig

# Import engines with graceful fallback for missing dependencies
try:
    from .tesseract_engine import TesseractEngine
    TESSERACT_AVAILABLE = True
except ImportError:
    TesseractEngine = None
    TESSERACT_AVAILABLE = False

try:
    from .easyocr_engine import EasyOCREngine
    EASYOCR_AVAILABLE = True
except ImportError:
    EasyOCREngine = None
    EASYOCR_AVAILABLE = False

__all__ = [
    'OCREngine',
    'OCRResult', 
    'EngineConfig',
    'TesseractEngine',
    'EasyOCREngine',
    'TESSERACT_AVAILABLE',
    'EASYOCR_AVAILABLE'
]
