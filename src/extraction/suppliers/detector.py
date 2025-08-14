"""
Supplier Detector - Cost-free pattern learning system
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SupplierDetector:
    """Cost-free supplier detector using pattern matching and examples."""
    
    def __init__(self):
        self.supplier_patterns = {
            "telia": [
                r"telia norge as",  # Telia Norge AS - primary identifier
                r"fakturanummer\s*:",  # Invoice number
                r"fakturadato\s*:",  # Invoice date
                r"kundenummer",  # Customer number
                r"tjenestespesifikasjon",  # Service specification
                r"sum denne periode",  # Sum this period
                r"sergel norge as",  # Sergel Norge AS (invoice processor)
                r"samlefaktura",  # Summary invoice
                r"retur:"  # Return address
            ]
        }
        self.example_signatures = self._load_examples()
        self.confidence_threshold = 0.25  # Lower threshold for better detection
    
    def _load_examples(self) -> Dict[str, List[str]]:
        """Load example signatures from stored files."""
        signatures = {}
        examples_dir = Path(__file__).parent / "examples"
        
        if examples_dir.exists():
            for supplier_dir in examples_dir.iterdir():
                if supplier_dir.is_dir():
                    supplier_name = supplier_dir.name
                    signatures[supplier_name] = []
                    
                    for example_file in supplier_dir.glob("*.txt"):
                        try:
                            with open(example_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                signature = self._extract_signature(content)
                                signatures[supplier_name].append(signature)
                        except Exception as e:
                            logger.warning(f"Failed to load {example_file}: {e}")
        
        return signatures
    
    def _extract_signature(self, content: str) -> str:
        """Extract signature from invoice content."""
        content = content.lower()
        parts = []
        
        # Invoice structure
        if "fakturanummer" in content:
            parts.append("has_invoice_number")
        if "fakturadato" in content:
            parts.append("has_invoice_date")
        if "kundenummer" in content:
            parts.append("has_customer_number")
        if "tjenestespesifikasjon" in content:
            parts.append("has_service_spec")
        if "sum denne periode" in content:
            parts.append("has_period_totals")
        if "å betale" in content:
            parts.append("has_payment_section")
        
        # Company identification
        if "telia norge as" in content:
            parts.append("telia_norge_as")
        elif "telia" in content:
            parts.append("telia_general")
        
        # Telia Norge specific patterns
        if "sergel norge as" in content:
            parts.append("sergel_norge_as")
        if "samlefaktura" in content:
            parts.append("samlefaktura")
        if "retur:" in content:
            parts.append("retur_address")
        
        return "|".join(sorted(parts))
    
    def detect_supplier(self, pdf_content: str) -> Optional[str]:
        """Detect supplier using patterns and examples."""
        content_lower = pdf_content.lower()
        
        # Pattern matching
        pattern_scores = {}
        for supplier, patterns in self.supplier_patterns.items():
            matches = sum(1 for pattern in patterns 
                         if re.search(pattern, content_lower))
            pattern_scores[supplier] = matches / len(patterns)
        
        # Signature matching
        signature_scores = {}
        current_sig = self._extract_signature(pdf_content)
        
        for supplier, signatures in self.example_signatures.items():
            if signatures:
                similarities = [SequenceMatcher(None, current_sig, sig).ratio() 
                              for sig in signatures]
                signature_scores[supplier] = max(similarities)
        
        # Combine scores
        combined = {}
        all_suppliers = set(pattern_scores.keys()) | set(signature_scores.keys())
        
        for supplier in all_suppliers:
            pattern_score = pattern_scores.get(supplier, 0.0)
            signature_score = signature_scores.get(supplier, 0.0)
            combined[supplier] = (pattern_score * 0.7) + (signature_score * 0.3)
        
        # Special handling for Telia Norge AS
        # Check for specific company name first - this is the most reliable indicator
        if "telia norge as" in content_lower:
            return "telia"  # If we see "Telia Norge AS", it's definitely a Telia invoice
        
        # Return best match
        if combined:
            best_supplier, best_score = max(combined.items(), key=lambda x: x[1])
            if best_score >= self.confidence_threshold:
                return best_supplier
        
        return None
    
    def add_example(self, supplier: str, content: str) -> None:
        """Add new example to improve detection."""
        signature = self._extract_signature(content)
        
        if supplier not in self.example_signatures:
            self.example_signatures[supplier] = []
        
        self.example_signatures[supplier].append(signature)
        logger.info(f"Added example for {supplier}")
