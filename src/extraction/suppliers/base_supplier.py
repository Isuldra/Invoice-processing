"""
Base Supplier Parser

This module defines the base class for all supplier parsers.
Each supplier should implement this interface.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class InvoiceLine:
    """Represents a single line item from the invoice."""
    employee_name: str
    phone_number: Optional[str] = None
    amount: float = 0.0
    currency: str = "NOK"
    cost_center: Optional[str] = None
    department: Optional[str] = None
    source_page: int = 0
    confidence: float = 1.0


@dataclass
class InvoiceData:
    """Represents the complete invoice data."""
    supplier: str
    invoice_number: str = ""
    invoice_date: str = ""
    period_from: str = ""
    period_to: str = ""
    currency: str = "NOK"
    grand_total: float = 0.0
    lines: List[InvoiceLine] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.lines is None:
            self.lines = []
    
    def get_totals(self) -> Dict[str, Any]:
        """Calculate totals from the invoice lines."""
        sum_of_lines = sum(line.amount for line in self.lines)
        diff_vs_grand_total = round(self.grand_total - sum_of_lines, 2)
        
        return {
            "lines_count": len(self.lines),
            "sum_of_lines": sum_of_lines,
            "diff_vs_grand_total": diff_vs_grand_total
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        totals = self.get_totals()
        
        return {
            "invoice": {
                "supplier": self.supplier,
                "invoice_number": self.invoice_number,
                "invoice_date": self.invoice_date,
                "period": {
                    "from": self.period_from,
                    "to": self.period_to
                },
                "currency": self.currency,
                "grand_total": self.grand_total,
                "confidence": self.confidence
            },
            "lines": [asdict(line) for line in self.lines],
            "totals": totals
        }


class BaseSupplierParser(ABC):
    """
    Base class for all supplier parsers.
    
    Each supplier should implement this interface to provide:
    - Supplier identification patterns
    - Invoice data extraction logic
    - Validation rules
    - Output formatting
    """
    
    def __init__(self):
        self.supplier_name = self.get_supplier_name()
        self.identification_patterns = self.get_identification_patterns()
        self.logger = logging.getLogger(f"{__name__}.{self.supplier_name}")
    
    @abstractmethod
    def get_supplier_name(self) -> str:
        """Return the supplier name."""
        pass
    
    @abstractmethod
    def get_identification_patterns(self) -> List[str]:
        """Return patterns that identify this supplier's invoices."""
        pass
    
    @abstractmethod
    def can_parse(self, pdf_content: str) -> bool:
        """Check if this parser can handle the given PDF content."""
        pass
    
    @abstractmethod
    def parse_invoice(self, pdf_content: str, pdf_path: Optional[Path] = None) -> InvoiceData:
        """Parse the invoice and return structured data."""
        pass
    
    def validate_invoice(self, invoice_data: InvoiceData) -> Dict[str, Any]:
        """Validate the parsed invoice data."""
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "confidence": invoice_data.confidence
        }
        
        # Basic validation
        if not invoice_data.invoice_number:
            validation_results["errors"].append("Missing invoice number")
            validation_results["is_valid"] = False
        
        if invoice_data.grand_total <= 0:
            validation_results["errors"].append("Invalid grand total")
            validation_results["is_valid"] = False
        
        if not invoice_data.lines:
            validation_results["warnings"].append("No invoice lines found")
        
        # Calculate confidence based on validation results
        if validation_results["errors"]:
            validation_results["confidence"] *= 0.5
        if validation_results["warnings"]:
            validation_results["confidence"] *= 0.9
        
        return validation_results
    
    def get_template_path(self) -> Path:
        """Get the path to this supplier's template configuration."""
        supplier_dir = Path(__file__).parent / self.supplier_name.lower()
        return supplier_dir / "template.yaml"
    
    def get_mapping_path(self) -> Path:
        """Get the path to this supplier's mapping configuration."""
        supplier_dir = Path(__file__).parent / self.supplier_name.lower()
        return supplier_dir / "mapping.yaml"
