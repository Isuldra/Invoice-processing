"""
Base OCR Engine abstraction layer.

This module provides the foundation for implementing multiple OCR engines
with a consistent interface for the Telia PDF processing system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Represents the result of an OCR operation."""
    text: str
    confidence: float
    bounding_box: Optional[Tuple[int, int, int, int]] = None
    engine_name: str = ""
    processing_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EngineConfig:
    """Configuration for an OCR engine."""
    name: str
    enabled: bool = True
    priority: int = 1
    timeout: float = 30.0
    confidence_threshold: float = 0.5
    custom_params: Optional[Dict[str, Any]] = None


class OCREngine(ABC):
    """
    Abstract base class for OCR engines.
    
    This class defines the interface that all OCR engines must implement
    to be compatible with the multi-engine processing pipeline.
    """
    
    def __init__(self, config: EngineConfig):
        """
        Initialize the OCR engine with configuration.
        
        Args:
            config: Engine configuration parameters
        """
        self.config = config
        self.name = config.name
        self.enabled = config.enabled
        self.priority = config.priority
        self.timeout = config.timeout
        self.confidence_threshold = config.confidence_threshold
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the OCR engine.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the OCR engine is available and ready to use.
        
        Returns:
            True if the engine is available, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_text(self, image_path: str) -> List[OCRResult]:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file to process
            
        Returns:
            List of OCRResult objects containing extracted text and metadata
        """
        pass
    
    @abstractmethod
    def extract_text_from_image(self, image) -> List[OCRResult]:
        """
        Extract text from an image object (PIL Image, numpy array, etc.).
        
        Args:
            image: Image object to process
            
        Returns:
            List of OCRResult objects containing extracted text and metadata
        """
        pass
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the OCR engine.
        
        Returns:
            Dictionary containing engine information
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "available": self.is_available(),
            "timeout": self.timeout,
            "confidence_threshold": self.confidence_threshold
        }
    
    def validate_result(self, result: OCRResult) -> bool:
        """
        Validate an OCR result based on confidence threshold.
        
        Args:
            result: OCRResult to validate
            
        Returns:
            True if result meets confidence threshold, False otherwise
        """
        return result.confidence >= self.confidence_threshold
    
    def __str__(self) -> str:
        """String representation of the OCR engine."""
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the OCR engine."""
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled}, priority={self.priority})"
