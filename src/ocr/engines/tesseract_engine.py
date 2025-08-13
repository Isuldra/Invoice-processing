"""
Tesseract OCR Engine implementation.

This module provides an optimized Tesseract OCR engine implementation
with performance improvements and configuration options.
"""

import time
import logging
from typing import List, Optional, Tuple, Any
from pathlib import Path
import os

import pytesseract
from PIL import Image
import numpy as np

from .base import OCREngine, OCRResult, EngineConfig

logger = logging.getLogger(__name__)


class TesseractEngine(OCREngine):
    """
    Optimized Tesseract OCR engine implementation.
    
    This engine includes performance optimizations such as:
    - Reduced DPI processing (200-250 instead of 300)
    - Optimized Tesseract parameters
    - Image preprocessing integration
    - Caching mechanisms
    """
    
    def __init__(self, config: EngineConfig):
        """
        Initialize the Tesseract engine.
        
        Args:
            config: Engine configuration with Tesseract-specific parameters
        """
        super().__init__(config)
        self._initialized = False
        self._tesseract_config = self._get_tesseract_config()
        self._setup_tesseract_path()
        
    def _setup_tesseract_path(self):
        """Set up Tesseract executable path for Windows."""
        # Common Tesseract installation paths on Windows
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', '')),
        ]
        
        # Check if any of the paths exist
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                self.logger.info(f"Found Tesseract at: {path}")
                return
        
        # If not found in common paths, try to use system PATH
        self.logger.warning("Tesseract not found in common paths, trying system PATH")
        
    def _get_tesseract_config(self) -> str:
        """
        Get optimized Tesseract configuration string.
        
        Returns:
            Tesseract configuration string with optimized parameters
        """
        # Optimized configuration for better performance and accuracy
        config = [
            '--oem', '3',  # Use LSTM OCR Engine Mode
            '--psm', '6',  # Assume a uniform block of text
            '-c', 'preserve_interword_spaces=1',
            '-c', 'textord_heavy_nr=1',
            '-c', 'textord_min_linesize=2',
            '-c', 'tessedit_do_invert=0',
            '-c', 'tessedit_pageseg_mode=6',
            '-c', 'tessedit_ocr_engine_mode=3'
        ]
        
        # Add custom parameters if provided
        if self.config.custom_params:
            for key, value in self.config.custom_params.items():
                config.extend(['-c', f'{key}={value}'])
                
        return ' '.join(config)
    
    def initialize(self) -> bool:
        """
        Initialize the Tesseract engine.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Check if Tesseract is available
            if not self.is_available():
                self.logger.error("Tesseract is not available")
                return False
            
            # Test basic functionality
            test_image = Image.new('RGB', (100, 50), color='white')
            pytesseract.image_to_string(test_image, config=self._tesseract_config)
            
            self._initialized = True
            self.logger.info(f"Tesseract engine '{self.name}' initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Tesseract engine: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if Tesseract is available and properly installed.
        
        Returns:
            True if Tesseract is available, False otherwise
        """
        try:
            # Check if pytesseract can find the Tesseract executable
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            self.logger.warning(f"Tesseract not available: {e}")
            return False
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for optimal OCR performance.
        
        Args:
            image: PIL Image to preprocess
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image to reduce DPI (performance optimization)
        # Target DPI: 200-250 instead of 300
        width, height = image.size
        target_dpi = 225  # Middle ground between 200-250
        current_dpi = 300  # Assuming original is 300 DPI
        
        if current_dpi > target_dpi:
            scale_factor = target_dpi / current_dpi
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def extract_text(self, image_path: str) -> List[OCRResult]:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file to process
            
        Returns:
            List of OCRResult objects containing extracted text and metadata
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            image = self._preprocess_image(image)
            
            return self.extract_text_from_image(image)
            
        except Exception as e:
            self.logger.error(f"Error processing image file {image_path}: {e}")
            return []
    
    def extract_text_from_image(self, image) -> List[OCRResult]:
        """
        Extract text from an image object.
        
        Args:
            image: PIL Image object to process
            
        Returns:
            List of OCRResult objects containing extracted text and metadata
        """
        start_time = time.time()
        results = []
        
        try:
            # Ensure image is preprocessed
            if isinstance(image, Image.Image):
                image = self._preprocess_image(image)
            
            # Extract text with detailed data
            data = pytesseract.image_to_data(
                image, 
                config=self._tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Process results
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                confidence = float(data['conf'][i]) / 100.0  # Convert to 0-1 scale
                
                if text and confidence > 0:  # Filter out empty text and very low confidence
                    # Get bounding box
                    bbox = (
                        data['left'][i],
                        data['top'][i], 
                        data['left'][i] + data['width'][i],
                        data['top'][i] + data['height'][i]
                    )
                    
                    result = OCRResult(
                        text=text,
                        confidence=confidence,
                        bounding_box=bbox,
                        engine_name=self.name,
                        processing_time=time.time() - start_time,
                        metadata={
                            'block_num': data['block_num'][i],
                            'par_num': data['par_num'][i],
                            'line_num': data['line_num'][i],
                            'word_num': data['word_num'][i]
                        }
                    )
                    
                    results.append(result)
            
            # Also get full text for overall result
            full_text = pytesseract.image_to_string(image, config=self._tesseract_config)
            if full_text.strip():
                full_result = OCRResult(
                    text=full_text.strip(),
                    confidence=1.0,  # Full text doesn't have confidence score
                    engine_name=self.name,
                    processing_time=time.time() - start_time,
                    metadata={'type': 'full_text'}
                )
                results.append(full_result)
            
            self.logger.debug(f"Tesseract extracted {len(results)} text elements in {time.time() - start_time:.2f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in Tesseract text extraction: {e}")
            return []
    
    def get_engine_info(self) -> dict:
        """
        Get detailed information about the Tesseract engine.
        
        Returns:
            Dictionary containing engine information
        """
        info = super().get_engine_info()
        info.update({
            'tesseract_version': self._get_tesseract_version(),
            'initialized': self._initialized,
            'config': self._tesseract_config,
            'tesseract_path': pytesseract.pytesseract.tesseract_cmd
        })
        return info
    
    def _get_tesseract_version(self) -> str:
        """
        Get Tesseract version information.
        
        Returns:
            Tesseract version string
        """
        try:
            version = pytesseract.get_tesseract_version()
            return str(version)
        except Exception as e:
            self.logger.warning(f"Could not get Tesseract version: {e}")
            return "Unknown"
