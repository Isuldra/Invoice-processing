"""
OneMed Fakturabehandling - Streamlit Version

Med OneMed-farger og lys/mørk modus support!
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
    layout="wide",
    initial_sidebar_state="expanded"
)

# OneMed Color Palette
ONEMED_COLORS = {
    "light": {
        "primary": "#2563eb",          # OneMed Medical Blue
        "primary_dark": "#1e40af",     # Darker Blue
        "secondary": "#0f766e",        # Teal Green
        "accent": "#059669",           # Success Green
        "warning": "#d97706",          # Warning Amber
        "error": "#dc2626",            # Error Red
        "background": "#ffffff",       # White
        "surface": "#f8fafc",          # Light Gray
        "text": "#1e293b",             # Dark Text
        "text_secondary": "#64748b",   # Gray Text
        "border": "#e2e8f0"            # Light Border
    },
    "dark": {
        "primary": "#3b82f6",          # Lighter Blue for dark mode
        "primary_dark": "#2563eb",     # Blue
        "secondary": "#14b8a6",        # Lighter Teal
        "accent": "#10b981",           # Lighter Green
        "warning": "#f59e0b",          # Lighter Amber
        "error": "#ef4444",            # Lighter Red
        "background": "#0f172a",       # Dark Background
        "surface": "#1e293b",          # Dark Surface
        "text": "#f1f5f9",             # Light Text
        "text_secondary": "#94a3b8",   # Light Gray Text
        "border": "#334155"            # Dark Border
    }
}

# Initialize theme in session state
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def apply_onemed_theme():
    """Apply OneMed colors with light/dark mode support"""
    theme = "dark" if st.session_state.dark_mode else "light"
    colors = ONEMED_COLORS[theme]
    
    css = f"""
    <style>
        /* Main App Styling */
        .stApp {{
            background-color: {colors["background"]};
            color: {colors["text"]};
        }}
        
        /* Header */
        .onemed-header {{
            background: linear-gradient(135deg, {colors["primary"]} 0%, {colors["primary_dark"]} 100%);
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        
        /* Sidebar Styling */
        .css-1d391kg {{
            background-color: {colors["surface"]};
        }}
        
        /* Metrics Cards */
        [data-testid="metric-container"] {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}
        
        /* Success Messages */
        .stSuccess {{
            background-color: rgba(16, 185, 129, 0.1);
            border-left: 4px solid {colors["accent"]};
            border-radius: 8px;
        }}
        
        /* Error Messages */
        .stError {{
            background-color: rgba(239, 68, 68, 0.1);
            border-left: 4px solid {colors["error"]};
            border-radius: 8px;
        }}
        
        /* Warning Messages */
        .stWarning {{
            background-color: rgba(245, 158, 11, 0.1);
            border-left: 4px solid {colors["warning"]};
            border-radius: 8px;
        }}
        
        /* File Uploader */
        [data-testid="stFileUploader"] {{
            background-color: {colors["surface"]};
            border: 2px dashed {colors["border"]};
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        [data-testid="stFileUploader"]:hover {{
            border-color: {colors["primary"]};
            background-color: rgba({colors["primary"][1:]}, 0.05);
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {colors["primary"]} 0%, {colors["primary_dark"]} 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba({colors["primary"][1:]}, 0.3);
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {colors["surface"]};
            border-radius: 8px;
            border: 1px solid {colors["border"]};
        }}
        
        /* DataFrames */
        .dataframe {{
            border-radius: 8px;
            border: 1px solid {colors["border"]};
        }}
        
        /* Theme Toggle Button */
        .theme-toggle {{
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 999;
            background: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: 50px;
            padding: 0.5rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.05);
        }}
        
        /* Custom Containers */
        .onemed-container {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }}
        
        /* Text Colors */
        .text-primary {{ color: {colors["primary"]}; }}
        .text-secondary {{ color: {colors["text_secondary"]}; }}
        .text-success {{ color: {colors["accent"]}; }}
        .text-error {{ color: {colors["error"]}; }}
        .text-warning {{ color: {colors["warning"]}; }}
        
        /* Hide Streamlit Menu and Footer */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {colors["surface"]};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {colors["primary"]};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {colors["primary_dark"]};
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Initialize parser
@st.cache_resource
def get_parser():
    return TeliaParser()

def main():
    # Apply OneMed theme
    apply_onemed_theme()
    
    # Sidebar with theme toggle
    with st.sidebar:
        st.markdown("### ⚙️ Innstillinger")
        
        # Theme toggle
        theme_emoji = "🌙" if st.session_state.dark_mode else "☀️"
        theme_text = "Lys modus" if st.session_state.dark_mode else "Mørk modus"
        
        if st.button(f"{theme_emoji} {theme_text}", key="theme_toggle", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
        
        st.markdown("---")
        
        # OneMed info
        st.markdown("""
        <div class="onemed-container">
            <h4 class="text-primary">🏥 OneMed</h4>
            <p class="text-secondary" style="font-size: 0.9rem;">
                Profesjonell fakturabehandling for helseteknologi
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # System info
        with st.expander("📊 Systeminfo"):
            current_theme = "Mørk" if st.session_state.dark_mode else "Lys"
            st.write(f"**Tema:** {current_theme}")
            st.write(f"**Versjon:** 1.0")
            st.write(f"**Parser:** Telia Norge AS")
    
    # Header with OneMed styling
    st.markdown("""
    <div class="onemed-header">
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">🏥 OneMed Fakturabehandling</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            Automatisk kontering av Telia Norge AS fakturaer med norsk finansterminologi
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions
    with st.expander("📋 Slik bruker du systemet", expanded=True):
        st.markdown("""
        <div class="onemed-container">
            <ol style="font-size: 1rem; line-height: 1.8;">
                <li><span class="text-primary">📄 <strong>Last opp</strong></span> en Telia Norge AS faktura (PDF-format)</li>
                <li><span class="text-secondary">📊 <strong>Last opp</strong></span> kostnadsbærer-fil (Excel) - valgfritt</li>
                <li><span class="text-success">🔄 <strong>Klikk</strong></span> "Behandle Faktura" for automatisk kontering</li>
                <li><span class="text-warning">📊 <strong>Gjennomgå</strong></span> resultater og håndter eventuelle konteringsavvik</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📁 Filopplasting")
    
    # File uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="onemed-container">
            <h4 class="text-primary">📄 Telia Faktura (PDF)</h4>
            <p class="text-secondary">Påkrevd - Telia Norge AS fakturaer</p>
        </div>
        """, unsafe_allow_html=True)
        
        pdf_file = st.file_uploader(
            "Velg PDF-fil", 
            type=['pdf'], 
            help="Last opp Telia Norge AS faktura i PDF-format",
            key="pdf_upload"
        )
        
        if pdf_file:
            st.success(f"✅ PDF lastet opp: {pdf_file.name} ({pdf_file.size/1024:.1f} KB)")
    
    with col2:
        st.markdown("""
        <div class="onemed-container">
            <h4 class="text-secondary">📊 Kostnadsbærere (Excel)</h4>
            <p class="text-secondary">Valgfritt - bruker mock-data hvis tom</p>
        </div>
        """, unsafe_allow_html=True)
        
        excel_file = st.file_uploader(
            "Velg Excel-fil", 
            type=['xlsx', 'xls'], 
            help="Valgfritt - bruker mock-data hvis ikke angitt",
            key="excel_upload"
        )
        
        if excel_file:
            st.success(f"✅ Excel lastet opp: {excel_file.name} ({excel_file.size/1024:.1f} KB)")
        else:
            st.info("ℹ️ Bruker mock kostnadsbærer-data")
    
    # Process button
    st.markdown("---")
    col_center = st.columns([1, 2, 1])[1]
    with col_center:
        if pdf_file:
            if st.button("🔄 Behandle Faktura", type="primary", use_container_width=True):
                process_invoice(pdf_file, excel_file)
        else:
            st.button("📄 Last opp PDF-fil først", disabled=True, use_container_width=True)

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
    """Display processing results with Norwegian terminology and OneMed styling"""
    
    # Success header
    st.markdown("""
    <div class="onemed-container" style="text-align: center; border-left: 4px solid #059669;">
        <h2 class="text-success">✅ Faktura behandlet med suksess!</h2>
        <p class="text-secondary">Automatisk kontering fullført med norsk finansterminologi</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary metrics
    st.markdown("## 📊 Konteringssammendrag")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Totalt Beløp",
            f"{invoice_data['beløp_sammendrag']['totalbeløp']:.2f} NOK",
            help="Totalt fakturabeløp i norske kroner"
        )
    
    with col2:
        konterte = len([cb for cb in invoice_data['kostnadsbarer_telia'] 
                       if cb['match_status'] == 'KONTERT'])
        totalt = len(invoice_data['kostnadsbarer_telia'])
        delta = f"+{konterte}" if konterte > 0 else None
        st.metric("✅ Konterte Ansatte", f"{konterte}/{totalt}", delta=delta)
    
    with col3:
        avvik = invoice_data['kvalitetskontroll']['unmatched_count']
        delta_color = "inverse" if avvik > 0 else "normal"
        st.metric("🚨 Konteringsavvik", avvik, 
                 delta=f"{avvik} krever manuell behandling" if avvik > 0 else "Ingen avvik",
                 delta_color=delta_color)
    
    with col4:
        tillit = invoice_data['kvalitetskontroll']['processing_confidence'] * 100
        delta_color = "normal" if tillit >= 90 else "inverse"
        st.metric("🎯 Systemtillit", f"{tillit:.0f}%", 
                 delta="Høy tillit" if tillit >= 90 else "Moderat tillit",
                 delta_color=delta_color)
    
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