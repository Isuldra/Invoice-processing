#!/usr/bin/env python3
"""
Test the updated PDF extraction function with fallback support.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_extraction():
    """Test the updated extraction function."""
    from src.extraction.suppliers.telia import extract_text_from_pdf
    
    pdf_dir = Path("src/extraction/suppliers/examples/telia")
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found")
        return
    
    # Test with first PDF file
    test_pdf = pdf_files[0]
    print(f"Testing updated extraction with: {test_pdf.name}")
    print("=" * 60)
    
    # Extract text
    text = extract_text_from_pdf(test_pdf)
    
    if text:
        print(f"✓ SUCCESS: Extracted {len(text)} characters")
        print(f"First 300 characters:")
        print("-" * 40)
        print(text[:300])
        print("-" * 40)
        
        # Check for Telia patterns
        telia_patterns = ["Telia", "Fakturanummer", "Tjenestespesifikasjon", "SUM DENNE PERIODE"]
        found_patterns = [p for p in telia_patterns if p in text]
        print(f"Found Telia patterns: {found_patterns}")
        
        # Check for invoice number
        import re
        invoice_match = re.search(r'Fakturanummer:\s*(\d+)', text)
        if invoice_match:
            print(f"Invoice number found: {invoice_match.group(1)}")
        
    else:
        print("✗ FAILED: No text extracted")

if __name__ == "__main__":
    test_extraction()
