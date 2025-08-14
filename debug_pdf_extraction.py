"""
🔍 OneMed PDF Debug Tool

Dette verktøyet viser NØYAKTIG hva som skjer når vi prosesserer en PDF-faktura.
Bruk dette for å finne ut hvorfor fakturaer viser 0,00 NOK.

Kjør: python3 debug_pdf_extraction.py <pdf_fil>
"""

import sys
import os
from pathlib import Path
import tempfile

# Add src to path
sys.path.append('src')

def debug_pdf_text_extraction(pdf_path: Path):
    """Debug PDF text extraction step by step"""
    print("🔍 PDF TEXT EXTRACTION DEBUG")
    print("=" * 50)
    print(f"📁 Fil: {pdf_path}")
    print(f"📏 Størrelse: {pdf_path.stat().st_size:,} bytes")
    print()
    
    # Method 1: Try pypdf
    print("🔬 METODE 1: pypdf (PyPDF2)")
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += page_text + "\n"
                print(f"   Side {i+1}: {len(page_text)} tegn")
            
            print(f"✅ pypdf OK: {len(text)} totale tegn")
            print(f"📝 Første 200 tegn: {text[:200]}...")
            return text
            
    except Exception as e:
        print(f"❌ pypdf feilet: {e}")
    
    # Method 2: Try pdfplumber
    print("\n🔬 METODE 2: pdfplumber")
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    print(f"   Side {i+1}: {len(page_text)} tegn")
            
            print(f"✅ pdfplumber OK: {len(text)} totale tegn")
            print(f"📝 Første 200 tegn: {text[:200]}...")
            return text
            
    except Exception as e:
        print(f"❌ pdfplumber feilet: {e}")
    
    print("🚨 ALLE PDF-EKSTRAKSJONS-METODER FEILET!")
    return ""

def debug_telia_patterns(pdf_content: str):
    """Debug Telia pattern matching"""
    print("\n🔍 TELIA PATTERN MATCHING DEBUG")
    print("=" * 50)
    
    if not pdf_content:
        print("❌ Ingen PDF-tekst å analysere!")
        return False
    
    print(f"📏 PDF-tekst lengde: {len(pdf_content)} tegn")
    print()
    
    try:
        from extraction.suppliers.telia import TeliaParser
        parser = TeliaParser()
        patterns = parser.get_identification_patterns()
        
        print("🔍 PATTERN-ANALYSE:")
        matches = 0
        for i, pattern in enumerate(patterns, 1):
            import re
            found = re.search(pattern, pdf_content, re.IGNORECASE)
            status = "✅ FUNNET" if found else "❌ IKKE FUNNET"
            print(f"   {i}. {pattern:<30} → {status}")
            if found:
                matches += 1
                context = pdf_content[max(0, found.start()-50):found.end()+50]
                print(f"      Kontekst: ...{context}...")
        
        print(f"\n📊 SAMMENDRAG: {matches}/5 patterns funnet")
        can_parse = matches >= 3
        print(f"🎯 kan_parse(): {'✅ JA' if can_parse else '❌ NEI'}")
        
        if can_parse:
            print("\n🔬 PRØVER Å PARSE FAKTURAEN...")
            try:
                result = parser.parse_invoice_with_cost_bearers(pdf_content)
                print("✅ PARSING VELLYKKET!")
                
                print(f"💰 Totalt beløp: {result['beløp_sammendrag']['totalbeløp']} {result['beløp_sammendrag']['valuta']}")
                print(f"📄 Fakturanummer: {result['faktura_metadata']['fakturanummer']}")
                print(f"📅 Fakturadato: {result['faktura_metadata']['fakturadato']}")
                print(f"👥 Antall linjer: {len(result['linjedetaljer'])}")
                print(f"👥 Antall kostnadsbærere: {len(result['kostnadsbarer_telia'])}")
                
                if result['kostnadsbarer_telia']:
                    print("\n👥 KOSTNADSBÆRERE:")
                    for cb in result['kostnadsbarer_telia'][:3]:  # Vis første 3
                        print(f"   - {cb['navn_fra_faktura']} → {cb['sum_denne_periode']} NOK ({cb['match_status']})")
                
                return result
                
            except Exception as e:
                print(f"❌ PARSING FEILET: {e}")
                import traceback
                traceback.print_exc()
        
        return can_parse
        
    except Exception as e:
        print(f"❌ TeliaParser ikke tilgjengelig: {e}")
        return False

def debug_regex_patterns(pdf_content: str):
    """Debug specific regex patterns used in TeliaParser"""
    print("\n🔍 REGEX PATTERN DEBUG")
    print("=" * 50)
    
    if not pdf_content:
        return
    
    import re
    
    # Test critical patterns
    test_patterns = [
        ("Fakturanummer", r'Fakturanummer:\s*(\d+)'),
        ("Fakturadato", r'Fakturadato:\s*(\d{2}\.\d{2}\.\d{4})'),
        ("Periode", r'Periode:\s*(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}\.\d{2}\.\d{4})'),
        ("Totalt beløp", r'Å betale:\s*(\d+[,.]?\d*)'),
        ("Ansatt linjer", r'([A-ZÆØÅÄÖÜ][a-zæøåäöüéèàáâîïôûçñA-ZÆØÅÄÖÜÉÈÀÁÂÎÏÔÛÇÑ\s\.]+?)\s*[-–—]\s*(\d{3}\s*\d{2}\s*\d{3})\s*(\d+[,.]?\d*)')
    ]
    
    print("🎯 REGEX TESTING:")
    for name, pattern in test_patterns:
        matches = list(re.finditer(pattern, pdf_content, re.IGNORECASE))
        print(f"   {name:<15} → {len(matches)} treff")
        for i, match in enumerate(matches[:2]):  # Vis første 2
            context = pdf_content[max(0, match.start()-30):match.end()+30]
            print(f"      Treff {i+1}: ...{context}...")

def main():
    print("🏥 OneMed PDF Debug Tool")
    print("=" * 60)
    
    if len(sys.argv) != 2:
        print("❌ Bruk: python3 debug_pdf_extraction.py <pdf_fil>")
        print()
        print("📋 Eksempel:")
        print("   python3 debug_pdf_extraction.py /path/to/telia_invoice.pdf")
        return
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"❌ PDF-filen finnes ikke: {pdf_path}")
        return
    
    print(f"🔍 Analyserer: {pdf_path}")
    print()
    
    # Step 1: Extract PDF text
    pdf_content = debug_pdf_text_extraction(pdf_path)
    
    # Step 2: Test Telia patterns
    can_parse = debug_telia_patterns(pdf_content)
    
    # Step 3: Debug specific regex patterns
    debug_regex_patterns(pdf_content)
    
    # Step 4: Show raw PDF sample
    if pdf_content:
        print("\n📄 PDF TEKST SAMPLE (første 500 tegn):")
        print("-" * 50)
        print(pdf_content[:500])
        print("-" * 50)
        
        print("\n💡 TIPS for å fikse problemet:")
        if not can_parse:
            print("   1. Sjekk at PDF-en inneholder 'Telia Norge AS'")
            print("   2. Sjekk at PDF-en har 'Fakturanummer:' feltet")
            print("   3. Sjekk at PDF-en har 'SUM DENNE PERIODE'")
            print("   4. Mulig at PDF-strukturen er annerledes enn forventet")
        else:
            print("   1. PDF-en ser OK ut - problem kan være i streamlit_app.py")
            print("   2. Sjekk at can_parse() returnerer True")
            print("   3. Sjekk at parse_invoice_with_cost_bearers() fungerer")
    
    print(f"\n✅ Debug fullført for: {pdf_path.name}")

if __name__ == "__main__":
    main()