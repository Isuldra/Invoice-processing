"""
Logging configuration for Telia PDF Processing System.

This module sets up structured logging with different levels and handlers
for debugging, monitoring, and audit purposes.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        console_output: Whether to output to console
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('telia_processor')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    colored_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(colored_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (optional)
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'telia_processor.{name}')
    return logging.getLogger('telia_processor')


class ProcessingLogger:
    """Specialized logger for processing operations."""
    
    def __init__(self, operation: str):
        self.logger = get_logger(f'processing.{operation}')
        self.operation = operation
        self.start_time = None
    
    def start_operation(self, details: str = None):
        """Log the start of an operation."""
        self.start_time = datetime.now()
        message = f"Starting {self.operation}"
        if details:
            message += f": {details}"
        self.logger.info(message)
    
    def end_operation(self, success: bool = True, details: str = None):
        """Log the end of an operation."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            status = "completed successfully" if success else "failed"
            message = f"{self.operation} {status} in {duration.total_seconds():.2f}s"
            if details:
                message += f": {details}"
            
            if success:
                self.logger.info(message)
            else:
                self.logger.error(message)
    
    def log_progress(self, stage: str, progress: float):
        """Log processing progress."""
        percentage = progress * 100
        self.logger.info(f"{self.operation} - {stage}: {percentage:.1f}%")
    
    def log_error(self, error: Exception, context: str = None):
        """Log an error with context."""
        message = f"Error in {self.operation}"
        if context:
            message += f" ({context})"
        message += f": {str(error)}"
        self.logger.error(message, exc_info=True)
    
    def log_warning(self, message: str, context: str = None):
        """Log a warning."""
        full_message = f"{self.operation}"
        if context:
            full_message += f" ({context})"
        full_message += f": {message}"
        self.logger.warning(full_message)


# Initialize default logging
default_logger = setup_logging()
