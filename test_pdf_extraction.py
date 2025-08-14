#!/usr/bin/env python3
"""
Test PDF extraction with different approaches to diagnose PyPDF2 issues.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_pypdf2_extraction(pdf_path: Path) -> Optional[str]:
    """Test PyPDF2 extraction."""
    try:
        import PyPDF2
        print(f"Testing PyPDF2 extraction for: {pdf_path.name}")
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            print(f"  PDF has {len(pdf_reader.pages)} pages")
            
            text = ""
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                print(f"  Page {i+1}: {len(page_text)} characters")
                text += page_text + "\n"
            
            print(f"  Total text length: {len(text)} characters")
            if text.strip():
                print(f"  First 200 chars: {text[:200]}...")
                return text
            else:
                print("  No text extracted!")
                return None
                
    except Exception as e:
        print(f"  PyPDF2 error: {e}")
        return None

def test_pdfplumber_extraction(pdf_path: Path) -> Optional[str]:
    """Test pdfplumber extraction (alternative to PyPDF2)."""
    try:
        import pdfplumber
        print(f"Testing pdfplumber extraction for: {pdf_path.name}")
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"  PDF has {len(pdf.pages)} pages")
            
            text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                print(f"  Page {i+1}: {len(page_text) if page_text else 0} characters")
                if page_text:
                    text += page_text + "\n"
            
            print(f"  Total text length: {len(text)} characters")
            if text.strip():
                print(f"  First 200 chars: {text[:200]}...")
                return text
            else:
                print("  No text extracted!")
                return None
                
    except ImportError:
        print("  pdfplumber not installed")
        return None
    except Exception as e:
        print(f"  pdfplumber error: {e}")
        return None

def test_pymupdf_extraction(pdf_path: Path) -> Optional[str]:
    """Test PyMuPDF (fitz) extraction."""
    try:
        import fitz  # PyMuPDF
        print(f"Testing PyMuPDF extraction for: {pdf_path.name}")
        
        doc = fitz.open(pdf_path)
        print(f"  PDF has {len(doc)} pages")
        
        text = ""
        for i, page in enumerate(doc):
            page_text = page.get_text()
            print(f"  Page {i+1}: {len(page_text)} characters")
            text += page_text + "\n"
        
        doc.close()
        
        print(f"  Total text length: {len(text)} characters")
        if text.strip():
            print(f"  First 200 chars: {text[:200]}...")
            return text
        else:
            print("  No text extracted!")
            return None
            
    except ImportError:
        print("  PyMuPDF not installed")
        return None
    except Exception as e:
        print(f"  PyMuPDF error: {e}")
        return None

def main():
    """Test PDF extraction with different libraries."""
    pdf_dir = Path("src/extraction/suppliers/examples/telia")
    
    if not pdf_dir.exists():
        print(f"PDF directory not found: {pdf_dir}")
        return
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found")
        return
    
    # Test with first PDF file
    test_pdf = pdf_files[0]
    print(f"Testing PDF extraction with: {test_pdf.name}")
    print("=" * 60)
    
    # Test different extraction methods
    methods = [
        ("PyPDF2", test_pypdf2_extraction),
        ("pdfplumber", test_pdfplumber_extraction),
        ("PyMuPDF", test_pymupdf_extraction),
    ]
    
    results = {}
    for name, method in methods:
        print(f"\n{name}:")
        print("-" * 30)
        result = method(test_pdf)
        results[name] = result
    
    # Compare results
    print("\n" + "=" * 60)
    print("COMPARISON:")
    print("=" * 60)
    
    for name, text in results.items():
        if text:
            print(f"{name}: SUCCESS ({len(text)} chars)")
            # Check for key Telia patterns
            telia_patterns = ["Telia", "Fakturanummer", "Tjenestespesifikasjon"]
            found_patterns = [p for p in telia_patterns if p in text]
            print(f"  Found patterns: {found_patterns}")
        else:
            print(f"{name}: FAILED")

if __name__ == "__main__":
    main()
