#!/usr/bin/env python3
"""
Debug supplier detection to understand why it's failing.
"""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def debug_detection():
    """Debug the supplier detection process."""
    from src.extraction.suppliers.telia import extract_text_from_pdf
    from src.extraction.suppliers.detector import SupplierDetector
    
    pdf_path = Path("src/extraction/suppliers/examples/telia/INV0214068709.pdf")
    
    print("=== PDF Text Extraction ===")
    pdf_text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(pdf_text)} characters")
    print("First 500 characters:")
    print("-" * 50)
    print(pdf_text[:500])
    print("-" * 50)
    
    print("\n=== Supplier Detection ===")
    detector = SupplierDetector()
    
    # Check patterns
    print("Pattern matching:")
    content_lower = pdf_text.lower()
    for supplier, patterns in detector.supplier_patterns.items():
        print(f"  {supplier}:")
        for pattern in patterns:
            match = bool(re.search(pattern, content_lower))
            print(f"    {pattern}: {'✓' if match else '✗'}")
            if match:
                # Show the actual match
                match_obj = re.search(pattern, content_lower)
                if match_obj:
                    start = max(0, match_obj.start() - 20)
                    end = min(len(content_lower), match_obj.end() + 20)
                    print(f"      Match: ...{content_lower[start:end]}...")
    
    # Check signature
    print("\nSignature extraction:")
    current_sig = detector._extract_signature(pdf_text)
    print(f"Current signature: {current_sig}")
    
    print("\nExample signatures:")
    for supplier, signatures in detector.example_signatures.items():
        print(f"  {supplier}: {signatures}")
    
    # Test detection
    print("\n=== Detection Result ===")
    result = detector.detect_supplier(pdf_text)
    print(f"Detected supplier: {result}")
    
    # Debug confidence calculation
    print("\n=== Confidence Debug ===")
    pattern_scores = {}
    for supplier, patterns in detector.supplier_patterns.items():
        matches = sum(1 for pattern in patterns 
                     if re.search(pattern, content_lower))
        pattern_scores[supplier] = matches / len(patterns)
        print(f"Pattern score for {supplier}: {pattern_scores[supplier]} ({matches}/{len(patterns)} matches)")
    
    signature_scores = {}
    for supplier, signatures in detector.example_signatures.items():
        if signatures:
            similarities = [SequenceMatcher(None, current_sig, sig).ratio() 
                          for sig in signatures]
            signature_scores[supplier] = max(similarities)
            print(f"Signature score for {supplier}: {signature_scores[supplier]}")
    
    # Combine scores
    combined = {}
    all_suppliers = set(pattern_scores.keys()) | set(signature_scores.keys())
    
    for supplier in all_suppliers:
        pattern_score = pattern_scores.get(supplier, 0.0)
        signature_score = signature_scores.get(supplier, 0.0)
        combined[supplier] = (pattern_score * 0.7) + (signature_score * 0.3)
        print(f"Combined score for {supplier}: {combined[supplier]}")
    
    print(f"Confidence threshold: {detector.confidence_threshold}")

if __name__ == "__main__":
    import re
    from difflib import SequenceMatcher
    debug_detection()
