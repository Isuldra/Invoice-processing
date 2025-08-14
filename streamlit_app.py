"""
OneMed Fakturabehandling - Streamlit Version

Mye enklere enn Flask, perfekt for interne verktøy!
Kjør med: streamlit run streamlit_app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path
import tempfile

# Add src to path
sys.path.append('src')
from extraction.suppliers.telia import TeliaParser, extract_text_from_pdf

# Configure page
st.set_page_config(
    page_title="🏥 OneMed Fakturabehandling", 
    page_icon="🏥",
    layout="wide"
)

# Initialize parser
@st.cache_resource
def get_parser():
    return TeliaParser()

def main():
    # Header with OneMed styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0;">🏥 OneMed Fakturabehandling</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0;">
            Automatisk kontering av Telia Norge AS fakturaer
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions
    with st.expander("📋 Slik bruker du systemet", expanded=True):
        st.markdown("""
        1. **📄 Last opp** en Telia Norge AS faktura (PDF-format)
        2. **📊 Last opp** kostnadsbærer-fil (Excel) - valgfritt
        3. **🔄 Klikk** "Behandle Faktura" for automatisk kontering  
        4. **📊 Gjennomgå** resultater og håndter eventuelle konteringsavvik
        """)
    
    # File uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📄 Telia Faktura (PDF)")
        pdf_file = st.file_uploader(
            "Dra og slipp PDF-fil her", 
            type=['pdf'], 
            help="Last opp Telia Norge AS faktura i PDF-format"
        )
    
    with col2:
        st.markdown("### 📊 Kostnadsbærere (Excel)")
        excel_file = st.file_uploader(
            "Dra og slipp Excel-fil her", 
            type=['xlsx', 'xls'], 
            help="Valgfritt - bruker mock-data hvis ikke angitt"
        )
    
    # Process button
    if pdf_file and st.button("🔄 Behandle Faktura", type="primary"):
        process_invoice(pdf_file, excel_file)

def process_invoice(pdf_file, excel_file):
    """Process the uploaded invoice"""
    
    parser = get_parser()
    
    with st.spinner("⏳ Behandler faktura..."):
        try:
            # Save PDF to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_file.getvalue())
                pdf_path = tmp_file.name
            
            # Extract text
            pdf_content = extract_text_from_pdf(Path(pdf_path))
            
            # Clean up temp file
            os.unlink(pdf_path)
            
            if not pdf_content:
                st.error("❌ Kunne ikke lese tekst fra PDF-filen")
                return
            
            # Check if it's a Telia invoice
            if not parser.can_parse(pdf_content):
                st.error("❌ Dette ser ikke ut til å være en Telia Norge AS faktura")
                return
            
            # Process with cost bearer matching
            result = parser.parse_invoice_with_cost_bearers(pdf_content)
            
            # Display results
            display_results(result)
            
        except Exception as e:
            st.error(f"❌ Feil ved behandling av faktura: {str(e)}")

def display_results(invoice_data):
    """Display processing results with Norwegian terminology"""
    
    st.success("✅ Faktura behandlet successfully!")
    
    # Summary metrics
    st.markdown("## 📊 Sammendrag")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Totalt Beløp",
            f"{invoice_data['beløp_sammendrag']['totalbeløp']:.2f} NOK"
        )
    
    with col2:
        konterte = len([cb for cb in invoice_data['kostnadsbarer_telia'] 
                       if cb['match_status'] == 'KONTERT'])
        totalt = len(invoice_data['kostnadsbarer_telia'])
        st.metric("✅ Konterte Ansatte", f"{konterte}/{totalt}")
    
    with col3:
        avvik = invoice_data['kvalitetskontroll']['unmatched_count']
        st.metric("🚨 Konteringsavvik", avvik, delta=f"-{avvik}" if avvik > 0 else None)
    
    with col4:
        tillit = invoice_data['kvalitetskontroll']['processing_confidence'] * 100
        st.metric("🎯 Systemtillit", f"{tillit:.0f}%")
    
    # Quality control alerts
    if invoice_data['kvalitetskontroll']['validation_errors']:
        st.markdown("## 🚨 Kvalitetskontroll")
        for error in invoice_data['kvalitetskontroll']['validation_errors']:
            st.warning(f"⚠️ {error}")
    
    # Cost bearer results
    st.markdown("## 👥 Kostnadsbærer-kontering")
    
    for cb in invoice_data['kostnadsbarer_telia']:
        with st.container():
            if cb['match_status'] == 'KONTERT':
                st.success(f"✅ **{cb['navn_fra_faktura']}** → Kostsenter {cb['kostsenter']} ({cb['sum_denne_periode']:.2f} NOK)")
            else:
                st.error(f"🚨 **{cb['navn_fra_faktura']}** → {cb['match_status']}")
                if cb['deviation_reason']:
                    st.caption(f"Årsak: {cb['deviation_reason']}")
    
    # Invoice details
    with st.expander("📄 Fakturaopplysninger", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Leverandør:** " + invoice_data['leverandor']['navn'])
            st.markdown("**Fakturanummer:** " + invoice_data['faktura_metadata']['fakturanummer'])
            st.markdown("**Fakturadato:** " + invoice_data['faktura_metadata']['fakturadato'])
        
        with col2:
            if invoice_data['faktura_metadata']['periode_fra']:
                st.markdown(f"**Periode:** {invoice_data['faktura_metadata']['periode_fra']} - {invoice_data['faktura_metadata']['periode_til']}")
    
    # Line details table
    with st.expander("📋 Linjedetaljer", expanded=False):
        import pandas as pd
        
        lines_data = []
        for line in invoice_data['linjedetaljer']:
            lines_data.append({
                'Tjeneste': line['produktnavn'],
                'Ansatt': line['employee_name'],
                'Telefon': line['phone_number'],
                'Beløp': f"{line['linjesum']:.2f} NOK"
            })
        
        df = pd.DataFrame(lines_data)
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()