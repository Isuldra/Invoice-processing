"""
Test script for Telia Parser

This script tests the Telia parser functionality with the existing OCR engines.
"""

import sys
import os
import logging
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from extraction.telia_parser import TeliaParser, InvoiceData, InvoiceLine
    from ocr.engines import TESSERACT_AVAILABLE, EASYOCR_AVAILABLE
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_parser_initialization():
    """Test parser initialization."""
    print("🧪 Testing Parser Initialization")
    print("-" * 40)
    
    try:
        parser = TeliaParser()
        print(f"✅ Parser initialized successfully")
        print(f"   OCR Engines: {len(parser.engines)}")
        print(f"   Cost Center Lookups: {len(parser.cost_center_lookup)}")
        print(f"   Name Lookups: {len(parser.name_lookup)}")
        return True
    except Exception as e:
        print(f"❌ Parser initialization failed: {e}")
        return False


def test_data_structures():
    """Test data structures."""
    print("\n🧪 Testing Data Structures")
    print("-" * 40)
    
    # Test InvoiceLine
    line = InvoiceLine(
        employee_name="John Doe",
        msisdn="92078335",
        sum_this_period=410.65,
        cost_center="12345",
        department="IT",
        source_page=2
    )
    
    print(f"✅ InvoiceLine created: {line.employee_name} - {line.sum_this_period} NOK")
    
    # Test InvoiceData
    invoice = InvoiceData(
        invoice_number="INV-2024-001",
        period_from="2024-01-01",
        period_to="2024-01-31",
        grand_total=21152.34
    )
    invoice.lines.append(line)
    
    print(f"✅ InvoiceData created: {len(invoice.lines)} lines")
    
    # Test totals calculation
    totals = invoice.get_totals()
    print(f"✅ Totals calculated: {totals['lines_count']} lines, {totals['sum_of_lines']} NOK")
    
    # Test JSON conversion
    json_data = invoice.to_dict()
    print(f"✅ JSON conversion successful: {len(json_data)} top-level keys")
    
    return True


def test_regex_patterns():
    """Test regex patterns."""
    print("\n🧪 Testing Regex Patterns")
    print("-" * 40)
    
    parser = TeliaParser()
    
    # Test employee pattern
    test_text = "Tjenestespesifikasjon for John Doe - 92078335"
    match = parser.employee_pattern.search(test_text)
    if match:
        print(f"✅ Employee pattern matched: {match.group('name')} - {match.group('msisdn')}")
    else:
        print("❌ Employee pattern failed")
        return False
    
    # Test sum pattern
    test_text = "SUM DENNE PERIODE: 1 234,56"
    match = parser.sum_pattern.search(test_text)
    if match:
        print(f"✅ Sum pattern matched: {match.group('amount')}")
    else:
        print("❌ Sum pattern failed")
        return False
    
    # Test period pattern
    test_text = "Fakturaperiode 01.01.2024 - 31.01.2024"
    match = parser.period_pattern.search(test_text)
    if match:
        print(f"✅ Period pattern matched: {match.group(1)} - {match.group(2)}")
    else:
        print("❌ Period pattern failed")
        return False
    
    # Test total pattern
    test_text = "Å betale: 21 152,34"
    match = parser.total_pattern.search(test_text)
    if match:
        print(f"✅ Total pattern matched: {match.group('total')}")
    else:
        print("❌ Total pattern failed")
        return False
    
    return True


def test_amount_normalization():
    """Test amount normalization."""
    print("\n🧪 Testing Amount Normalization")
    print("-" * 40)
    
    parser = TeliaParser()
    
    test_cases = [
        ("1 234,56", 1234.56),
        ("1.234,56", 1234.56),
        ("1234,56", 1234.56),
        ("1 234 567,89", 1234567.89),
        ("-1 234,56", -1234.56)
    ]
    
    for input_val, expected in test_cases:
        result = parser._normalize_amount(input_val)
        if result == expected:
            print(f"✅ {input_val} -> {result}")
        else:
            print(f"❌ {input_val} -> {result} (expected {expected})")
            return False
    
    return True


def test_date_normalization():
    """Test date normalization."""
    print("\n🧪 Testing Date Normalization")
    print("-" * 40)
    
    parser = TeliaParser()
    
    test_cases = [
        ("01.01.2024", "2024-01-01"),
        ("31.12.2023", "2023-12-31"),
        ("15.06.2024", "2024-06-15")
    ]
    
    for input_val, expected in test_cases:
        result = parser._normalize_date(input_val)
        if result == expected:
            print(f"✅ {input_val} -> {result}")
        else:
            print(f"❌ {input_val} -> {result} (expected {expected})")
            return False
    
    return True


def test_msisdn_normalization():
    """Test MSISDN normalization."""
    print("\n🧪 Testing MSISDN Normalization")
    print("-" * 40)
    
    parser = TeliaParser()
    
    test_cases = [
        ("92078335", "92078335"),
        ("+47 92078335", "4792078335"),
        ("920 78 335", "92078335"),
        ("+47 920 78 335", "4792078335")
    ]
    
    for input_val, expected in test_cases:
        result = parser._normalize_msisdn(input_val)
        if result == expected:
            print(f"✅ {input_val} -> {result}")
        else:
            print(f"❌ {input_val} -> {result} (expected {expected})")
            return False
    
    return True


def test_cost_center_lookup():
    """Test cost center lookup functionality."""
    print("\n🧪 Testing Cost Center Lookup")
    print("-" * 40)
    
    try:
        parser = TeliaParser()
        
        if len(parser.cost_center_lookup) > 0:
            print(f"✅ Loaded {len(parser.cost_center_lookup)} MSISDN lookups")
            print(f"✅ Loaded {len(parser.name_lookup)} name lookups")
            
            # Test a lookup if we have data
            if parser.cost_center_lookup:
                first_msisdn = list(parser.cost_center_lookup.keys())[0]
                cost_center, department = parser._lookup_cost_center(first_msisdn, "")
                print(f"✅ Lookup test: {first_msisdn} -> {cost_center}, {department}")
        else:
            print("⚠️  No cost center data loaded (Bok2.xlsx may not be available)")
        
        return True
    except Exception as e:
        print(f"❌ Cost center lookup test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Telia Parser Test Suite")
    print("=" * 50)
    
    tests = [
        ("Parser Initialization", test_parser_initialization),
        ("Data Structures", test_data_structures),
        ("Regex Patterns", test_regex_patterns),
        ("Amount Normalization", test_amount_normalization),
        ("Date Normalization", test_date_normalization),
        ("MSISDN Normalization", test_msisdn_normalization),
        ("Cost Center Lookup", test_cost_center_lookup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The parser is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    # Show OCR engine status
    print(f"\n🔧 OCR Engine Status:")
    print(f"   Tesseract: {'✅ Available' if TESSERACT_AVAILABLE else '❌ Not Available'}")
    print(f"   EasyOCR: {'✅ Available' if EASYOCR_AVAILABLE else '❌ Not Available'}")


if __name__ == "__main__":
    main()
