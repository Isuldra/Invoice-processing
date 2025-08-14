#!/usr/bin/env python3
"""
Analyze Telia PDF patterns to improve detection accuracy
"""

import sys
import os
from pathlib import Path
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from extraction.suppliers.telia import extract_text_from_pdf
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_telia_patterns():
    """Analyze actual Telia PDFs to find the most reliable patterns."""
    
    print("=== TELIA PATTERN ANALYSIS ===\n")
    
    examples_dir = Path("src/extraction/suppliers/examples/telia")
    pdf_files = list(examples_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found")
        return
    
    # Analyze first few PDFs
    sample_files = pdf_files[:3]
    
    all_patterns = {}
    common_patterns = {}
    
    for pdf_file in sample_files:
        print(f"Analyzing: {pdf_file.name}")
        
        try:
            pdf_text = extract_text_from_pdf(pdf_file)
            if not pdf_text:
                continue
            
            # Convert to lowercase for analysis
            text_lower = pdf_text.lower()
            
            # Look for key Telia patterns
            patterns_found = []
            
            # Company names
            if "telia norge as" in text_lower:
                patterns_found.append("telia norge as")
            if "telia company ab" in text_lower:
                patterns_found.append("telia company ab")
            if "telia" in text_lower:
                patterns_found.append("telia")
            
            # Invoice patterns
            if "fakturanummer" in text_lower:
                patterns_found.append("fakturanummer")
            if "fakturadato" in text_lower:
                patterns_found.append("fakturadato")
            if "kundenummer" in text_lower:
                patterns_found.append("kundenummer")
            
            # Service patterns
            if "tjenestespesifikasjon" in text_lower:
                patterns_found.append("tjenestespesifikasjon")
            if "sum denne periode" in text_lower:
                patterns_found.append("sum denne periode")
            
            # Additional patterns
            if "sergel norge as" in text_lower:
                patterns_found.append("sergel norge as")
            if "samlefaktura" in text_lower:
                patterns_found.append("samlefaktura")
            if "retur:" in text_lower:
                patterns_found.append("retur:")
            
            print(f"  Patterns found: {patterns_found}")
            
            # Count patterns
            for pattern in patterns_found:
                if pattern not in all_patterns:
                    all_patterns[pattern] = 0
                all_patterns[pattern] += 1
            
            # Show first 500 characters
            print(f"  First 500 chars: {pdf_text[:500].replace(chr(10), ' ').replace(chr(13), ' ')}")
            print()
            
        except Exception as e:
            print(f"  Error: {e}")
            print()
    
    # Find most common patterns
    print("=== PATTERN FREQUENCY ANALYSIS ===")
    total_files = len(sample_files)
    
    for pattern, count in sorted(all_patterns.items(), key=lambda x: x[1], reverse=True):
        frequency = count / total_files
        print(f"{pattern}: {count}/{total_files} ({frequency*100:.1f}%)")
        
        if frequency >= 0.8:  # 80% or more files have this pattern
            common_patterns[pattern] = frequency
    
    print(f"\nMost reliable patterns (≥80% frequency):")
    for pattern, freq in common_patterns.items():
        print(f"  ✓ {pattern} ({freq*100:.1f}%)")
    
    return common_patterns

def test_improved_patterns():
    """Test improved pattern detection."""
    
    print("\n=== TESTING IMPROVED PATTERNS ===")
    
    # Current patterns that work well
    current_patterns = [
        r"telia norge as",
        r"telia company ab", 
        r"fakturanummer\s*:",
        r"tjenestespesifikasjon for",
        r"sum denne periode"
    ]
    
    # New patterns based on analysis
    improved_patterns = [
        r"telia norge as",
        r"telia company ab",
        r"telia",  # More general
        r"fakturanummer\s*:",
        r"fakturadato\s*:",
        r"tjenestespesifikasjon",
        r"sum denne periode",
        r"sergel norge as",
        r"samlefaktura",
        r"retur:"
    ]
    
    # Test cases that were failing
    test_cases = [
        ("Weak Telia match", """Invoice from Telia Company AB
Invoice Number: INV123"""),
        ("Partial match", """Telia Norge AS
Some other content"""),
        ("Strong match", """Telia Norge AS
Fakturanummer: INV0214068709
Tjenestespesifikasjon for
SUM DENNE PERIODE""")
    ]
    
    print("Testing current patterns:")
    for name, content in test_cases:
        content_lower = content.lower()
        matches = sum(1 for pattern in current_patterns 
                     if re.search(pattern, content_lower))
        score = matches / len(current_patterns)
        print(f"  {name}: {matches}/{len(current_patterns)} patterns ({score*100:.1f}%)")
    
    print("\nTesting improved patterns:")
    for name, content in test_cases:
        content_lower = content.lower()
        matches = sum(1 for pattern in improved_patterns 
                     if re.search(pattern, content_lower))
        score = matches / len(improved_patterns)
        print(f"  {name}: {matches}/{len(improved_patterns)} patterns ({score*100:.1f}%)")

if __name__ == "__main__":
    analyze_telia_patterns()
    test_improved_patterns()
