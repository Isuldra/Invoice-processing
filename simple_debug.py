#!/usr/bin/env python3
"""
Simple debug for pattern matching.
"""

import re
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.extraction.suppliers.telia import extract_text_from_pdf

def main():
    pdf_path = Path("src/extraction/suppliers/examples/telia/INV0214068709.pdf")
    pdf_text = extract_text_from_pdf(pdf_path)
    
    print("=== Pattern Matching Test ===")
    content_lower = pdf_text.lower()
    
    patterns = [
        r"Telia Norge AS",
        r"TELIA COMPANY AB", 
        r"Fakturanummer:",
        r"Tjenestespesifikasjon for",
        r"SUM DENNE PERIODE"
    ]
    
    for pattern in patterns:
        match = bool(re.search(pattern, content_lower))
        print(f"{pattern}: {'✓' if match else '✗'}")
        if match:
            match_obj = re.search(pattern, content_lower)
            start = max(0, match_obj.start() - 30)
            end = min(len(content_lower), match_obj.end() + 30)
            print(f"  Found: ...{content_lower[start:end]}...")
    
    # Check for Telia in text
    print(f"\n'Telia' in text: {'Telia' in pdf_text}")
    print(f"'telia' in text: {'telia' in content_lower}")
    
    # Check for specific patterns
    print(f"'Fakturanummer:' in text: {'Fakturanummer:' in pdf_text}")
    print(f"'Tjenestespesifikasjon' in text: {'Tjenestespesifikasjon' in pdf_text}")
    
    # Search for similar patterns
    print("\n=== Searching for similar patterns ===")
    
    # Find all lines containing "Telia"
    telia_lines = [line for line in pdf_text.split('\n') if 'Telia' in line]
    print("Lines containing 'Telia':")
    for line in telia_lines:
        print(f"  '{line.strip()}'")
    
    # Find all lines containing "Fakturanummer"
    invoice_lines = [line for line in pdf_text.split('\n') if 'Fakturanummer' in line]
    print("\nLines containing 'Fakturanummer':")
    for line in invoice_lines:
        print(f"  '{line.strip()}'")
    
    # Find all lines containing "Tjenestespesifikasjon"
    service_lines = [line for line in pdf_text.split('\n') if 'Tjenestespesifikasjon' in line]
    print("\nLines containing 'Tjenestespesifikasjon':")
    for line in service_lines:
        print(f"  '{line.strip()}'")
    
    # Find all lines containing "SUM DENNE PERIODE"
    sum_lines = [line for line in pdf_text.split('\n') if 'SUM DENNE PERIODE' in line]
    print("\nLines containing 'SUM DENNE PERIODE':")
    for line in sum_lines:
        print(f"  '{line.strip()}'")

if __name__ == "__main__":
    main()
