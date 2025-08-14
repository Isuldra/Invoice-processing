"""
Supplier Management System

This module provides a mappe-basert (folder-based) system for handling different invoice suppliers.
Each supplier gets its own folder with specialized parsers and templates.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type
from abc import ABC, abstractmethod

from .base_supplier import BaseSupplierParser
from .telia import TeliaParser
from .detector import SupplierDetector

logger = logging.getLogger(__name__)

# Registry of available suppliers
SUPPLIER_REGISTRY: Dict[str, Type[BaseSupplierParser]] = {
    "telia": TeliaParser,
    # Add more suppliers here as they are implemented
}

def get_supplier_parser(supplier_name: str) -> Optional[Type[BaseSupplierParser]]:
    """Get a supplier parser by name."""
    return SUPPLIER_REGISTRY.get(supplier_name.lower())

def register_supplier(name: str, parser_class: Type[BaseSupplierParser]) -> None:
    """Register a new supplier parser."""
    SUPPLIER_REGISTRY[name.lower()] = parser_class
    logger.info(f"Registered supplier parser: {name}")

def list_available_suppliers() -> List[str]:
    """List all available suppliers."""
    return list(SUPPLIER_REGISTRY.keys())

def auto_detect_supplier(pdf_content: str) -> Optional[str]:
    """Automatically detect supplier from PDF content."""
    detector = SupplierDetector()
    return detector.detect_supplier(pdf_content)
