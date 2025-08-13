"""
Custom exceptions for Telia PDF Processing System.

This module defines all custom exceptions used throughout the application
for better error handling and debugging.
"""


class TeliaProcessingError(Exception):
    """Base exception for Telia processing errors."""
    pass


class OCRException(TeliaProcessingError):
    """Exception raised when OCR processing fails."""
    
    def __init__(self, message: str, engine: str = None, confidence: float = None):
        self.message = message
        self.engine = engine
        self.confidence = confidence
        super().__init__(self.message)


class ValidationException(TeliaProcessingError):
    """Exception raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


class TemplateException(TeliaProcessingError):
    """Exception raised when template matching fails."""
    
    def __init__(self, message: str, template: str = None, section: str = None):
        self.message = message
        self.template = template
        self.section = section
        super().__init__(self.message)


class ProcessingException(TeliaProcessingError):
    """Exception raised when document processing fails."""
    
    def __init__(self, message: str, stage: str = None, document: str = None):
        self.message = message
        self.stage = stage
        self.document = document
        super().__init__(self.message)


class ConfigurationException(TeliaProcessingError):
    """Exception raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None):
        self.message = message
        self.config_key = config_key
        super().__init__(self.message)


class FileException(TeliaProcessingError):
    """Exception raised when file operations fail."""
    
    def __init__(self, message: str, file_path: str = None, operation: str = None):
        self.message = message
        self.file_path = file_path
        self.operation = operation
        super().__init__(self.message)


class TimeoutException(TeliaProcessingError):
    """Exception raised when processing times out."""
    
    def __init__(self, message: str, timeout_seconds: int = None):
        self.message = message
        self.timeout_seconds = timeout_seconds
        super().__init__(self.message)
