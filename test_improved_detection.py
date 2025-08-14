#!/usr/bin/env python3
"""
Test improved supplier detection with separate Telia companies
"""

import sys
import os
from pathlib import Path
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from extraction.suppliers.detector import SupplierDetector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_improved_detection():
    """Test the improved supplier detection."""
    
    print("=== IMPROVED SUPPLIER DETECTION TEST ===\n")
    
    detector = SupplierDetector()
    
    # Test cases
    test_cases = [
        # Telia Norge AS tests
        ("Telia Norge AS - Strong", """Retur:
Sergel Norge AS FAKTURA
Postboks 177
3201 Sandefjord
Fakturadato: 06.07.25
Fakturanummer: INV0214068709
Kundenummer/KID: 3106374

Telia Norge AS
Tjenestespesifikasjon for
SUM DENNE PERIODE""", "telia"),
        
        ("Telia Norge AS - Partial", """Telia Norge AS
Fakturanummer: INV123
Some other content""", "telia"),
        
        ("Telia Norge AS - Weak", """Telia Norge AS
Some other content""", "telia"),
        
        # Non-Telia tests
        ("Non-Telia content", """Invoice from Other Company
Invoice Number: INV789
Date: 2025-01-15""", None),
        
        ("Telia Company AB (should be None)", """Telia Company AB
Invoice Number: INV456""", None),
        
        ("Empty content", "", None)
    ]
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    for name, content, expected in test_cases:
        result = detector.detect_supplier(content)
        success = result == expected
        
        if success:
            successful_tests += 1
        
        print(f"{name}:")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        print(f"  Success: {'✓' if success else '✗'}")
        
        # Show pattern analysis
        content_lower = content.lower()
        if "telia norge as" in content_lower:
            print(f"  Contains: Telia Norge AS")
        if "telia company ab" in content_lower:
            print(f"  Contains: Telia Company AB")
        
        print()
    
    print(f"=== SUMMARY ===")
    print(f"Successful tests: {successful_tests}/{total_tests}")
    print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Test pattern analysis
    print(f"\n=== PATTERN ANALYSIS ===")
    print("Telia patterns:")
    for i, pattern in enumerate(detector.supplier_patterns['telia'], 1):
        print(f"  {i}. {pattern}")
    
    print(f"\nConfidence threshold: {detector.confidence_threshold}")

def test_signature_extraction():
    """Test signature extraction for both companies."""
    
    print(f"\n=== SIGNATURE EXTRACTION TEST ===")
    
    detector = SupplierDetector()
    
    test_contents = [
        ("Telia Norge AS", """Telia Norge AS
Fakturanummer: INV123
Sergel Norge AS
Samlefaktura
Retur:""")
    ]
    
    for name, content in test_contents:
        signature = detector._extract_signature(content)
        print(f"{name}:")
        print(f"  Signature: {signature}")
        parts = signature.split('|')
        print(f"  Parts: {parts}")
        print()

if __name__ == "__main__":
    test_improved_detection()
    test_signature_extraction()
