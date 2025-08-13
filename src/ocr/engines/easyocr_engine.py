"""
EasyOCR Engine implementation.

This module provides an EasyOCR engine implementation as a secondary
OCR engine for the multi-engine processing pipeline.
"""

import time
import logging
from typing import List, Optional, Tuple, Any

import easyocr
from PIL import Image
import numpy as np

from .base import OCREngine, OCRResult, EngineConfig

logger = logging.getLogger(__name__)


class EasyOCREngine(OCREngine):
    """
    EasyOCR engine implementation.
    
    This engine serves as a secondary OCR engine to complement Tesseract
    and provide improved accuracy through consensus algorithms.
    """
    
    def __init__(self, config: EngineConfig):
        """
        Initialize the EasyOCR engine.
        
        Args:
            config: Engine configuration with EasyOCR-specific parameters
        """
        super().__init__(config)
        self._initialized = False
        self._reader = None
        self._languages = self._get_languages()
        
    def _get_languages(self) -> List[str]:
        """
        Get languages for EasyOCR processing.
        
        Returns:
            List of language codes for EasyOCR
        """
        # Default to English and Norwegian for Telia documents
        languages = ['en', 'no']
        
        # Add custom languages if specified
        if self.config.custom_params and 'languages' in self.config.custom_params:
            custom_langs = self.config.custom_params['languages']
            if isinstance(custom_langs, str):
                languages = custom_langs.split(',')
            elif isinstance(custom_langs, list):
                languages = custom_langs
        
        return languages
    
    def initialize(self) -> bool:
        """
        Initialize the EasyOCR engine.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Check if EasyOCR is available
            if not self.is_available():
                self.logger.error("EasyOCR is not available")
                return False
            
            # Initialize EasyOCR reader
            self._reader = easyocr.Reader(
                self._languages,
                gpu=False,  # Use CPU for compatibility
                model_storage_directory=None,  # Use default
                download_enabled=True,
                recog_network='standard'  # Use standard recognition network
            )
            
            self._initialized = True
            self.logger.info(f"EasyOCR engine '{self.name}' initialized successfully with languages: {self._languages}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize EasyOCR engine: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if EasyOCR is available and properly installed.
        
        Returns:
            True if EasyOCR is available, False otherwise
        """
        try:
            # Try to import easyocr
            import easyocr
            return True
        except ImportError:
            self.logger.warning("EasyOCR not available - not installed")
            return False
        except Exception as e:
            self.logger.warning(f"EasyOCR not available: {e}")
            return False
    
    def _preprocess_image(self, image) -> np.ndarray:
        """
        Preprocess image for EasyOCR processing.
        
        Args:
            image: PIL Image or numpy array to preprocess
            
        Returns:
            Preprocessed numpy array
        """
        # Convert PIL Image to numpy array if necessary
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        # Ensure image is in the correct format
        if len(image.shape) == 3 and image.shape[2] == 3:
            # RGB image - EasyOCR expects BGR
            image = image[:, :, ::-1]  # Convert RGB to BGR
        elif len(image.shape) == 2:
            # Grayscale image - convert to BGR
            image = np.stack([image] * 3, axis=-1)
        
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
            # Load image
            image = Image.open(image_path)
            return self.extract_text_from_image(image)
            
        except Exception as e:
            self.logger.error(f"Error processing image file {image_path}: {e}")
            return []
    
    def extract_text_from_image(self, image) -> List[OCRResult]:
        """
        Extract text from an image object.
        
        Args:
            image: PIL Image or numpy array to process
            
        Returns:
            List of OCRResult objects containing extracted text and metadata
        """
        start_time = time.time()
        results = []
        
        try:
            if not self._initialized or self._reader is None:
                self.logger.error("EasyOCR engine not initialized")
                return []
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Extract text with EasyOCR
            ocr_results = self._reader.readtext(processed_image)
            
            # Process results
            for bbox, text, confidence in ocr_results:
                if text.strip() and confidence > 0:
                    # Convert bounding box format
                    # EasyOCR returns: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
                    # We need: (x1, y1, x2, y2)
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    bbox_tuple = (
                        int(min(x_coords)),
                        int(min(y_coords)),
                        int(max(x_coords)),
                        int(max(y_coords))
                    )
                    
                    result = OCRResult(
                        text=text.strip(),
                        confidence=confidence,
                        bounding_box=bbox_tuple,
                        engine_name=self.name,
                        processing_time=time.time() - start_time,
                        metadata={
                            'bbox_original': bbox,
                            'languages': self._languages
                        }
                    )
                    
                    results.append(result)
            
            # Also create a full text result
            full_text = ' '.join([result.text for result in results])
            if full_text.strip():
                full_result = OCRResult(
                    text=full_text.strip(),
                    confidence=1.0,  # Full text doesn't have confidence score
                    engine_name=self.name,
                    processing_time=time.time() - start_time,
                    metadata={'type': 'full_text', 'languages': self._languages}
                )
                results.append(full_result)
            
            self.logger.debug(f"EasyOCR extracted {len(results)} text elements in {time.time() - start_time:.2f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in EasyOCR text extraction: {e}")
            return []
    
    def get_engine_info(self) -> dict:
        """
        Get detailed information about the EasyOCR engine.
        
        Returns:
            Dictionary containing engine information
        """
        info = super().get_engine_info()
        info.update({
            'initialized': self._initialized,
            'languages': self._languages,
            'reader_available': self._reader is not None
        })
        return info
    
    def set_languages(self, languages: List[str]) -> bool:
        """
        Update the languages used by EasyOCR.
        
        Args:
            languages: List of language codes
            
        Returns:
            True if languages were updated successfully, False otherwise
        """
        try:
            self._languages = languages
            if self._initialized:
                # Reinitialize with new languages
                return self.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Failed to update languages: {e}")
            return False
