# 🏥 OneMed Fakturabehandling - Streamlit Edition

**Profesjonell fakturabehandling med OneMed-farger og lys/mørk modus**

Med norsk finansterminologi og elegant brukergrensesnitt designet for OneMed sin helseteknologi-identitet.

## ✨ Nye Funksjoner

### 🎨 **OneMed Designidentitet**
- **Profesjonelle helseteknologi-farger**: Medisinsk blå (#2563eb) og teal grønn (#0f766e)
- **Consistent branding** gjennom hele applikasjonen
- **Moderne gradients** og profesjonelle overganger
- **Clean typography** med god lesbarhet

### 🌙 **Lys/Mørk Modus**
- **Dynamisk tema-bytte** via sidebar-knappen
- **Automatisk fargetilpasning** av alle komponenter
- **Øyevennlig mørk modus** for lang bruk
- **Elegant overgangsanimationer**

### 🇳🇴 **Norsk Finansterminologi**
- **KONTERT** - Ansatt funnet og automatisk kontert
- **KREVER_MANUELL_KONTERING** - Avvik som trenger manuell behandling
- **FLERE_MULIGE_TREFF** - Tvetydige navn som trenger avklaring

## 🚀 **Kom i gang (Super enkelt!)**

### 1. **Installer Streamlit**
```bash
pip install streamlit
```

### 2. **Kjør applikasjonen**
```bash
streamlit run streamlit_app.py
```

### 3. **Åpner automatisk i nettleser**
- **URL**: http://localhost:8501
- **Automatisk oppstart** - ingen manuell navigering nødvendig
- **Hot reload** - endringer oppdateres automatisk

## 🎯 **Brukergrensesnitt**

### **📱 Sidebar Kontroller**
- **🌙/☀️ Tema-toggle** - Bytt mellom lys og mørk modus
- **⚙️ Systeminnstillinger** - Vis gjeldende konfigurasjon
- **🏥 OneMed Info** - Merkevare og versjonsinformasjon

### **📄 Hovedgrensesnitt**
- **Profesjonell header** med OneMed-gradient
- **Intuitiv filopplasting** med live feedback
- **Elegant instruksjoner** med fargekodede steg
- **Responsivt design** for alle skjermstørrelser

### **📊 Resultatvisning**
- **Interaktive metric-kort** med delta-indikatorer
- **Strukturerte kostnadsbærer-resultater** med kolonnebasert layout
- **Utvidbare detaljer** for fakturaopplysninger og linjer
- **Nedlastbare rapporter** og utskriftsfunksjon

## 🎨 **OneMed Fargepalett**

### **Lys Modus (Standard)**
```css
Primær:      #2563eb  /* OneMed Medical Blue */
Sekundær:    #0f766e  /* Teal Green */
Suksess:     #059669  /* Success Green */
Advarsel:    #d97706  /* Warning Amber */
Feil:        #dc2626  /* Error Red */
Bakgrunn:    #ffffff  /* Clean White */
Overflate:   #f8fafc  /* Light Gray */
```

### **Mørk Modus**
```css
Primær:      #3b82f6  /* Lighter Blue */
Sekundær:    #14b8a6  /* Lighter Teal */
Suksess:     #10b981  /* Lighter Green */
Advarsel:    #f59e0b  /* Lighter Amber */
Feil:        #ef4444  /* Lighter Red */
Bakgrunn:    #0f172a  /* Dark Background */
Overflate:   #1e293b  /* Dark Surface */
```

## 💡 **Fordeler vs Flask**

| **Aspekt** | **Streamlit** | **Flask** |
|------------|---------------|-----------|
| **Kode-mengde** | 90% mindre | Mye boilerplate |
| **UI-utvikling** | Automatisk | Manuell HTML/CSS |
| **Tema-støtte** | Innebygd | Må implementeres |
| **Filhåndtering** | Drag & drop | Kompleks setup |
| **Deployment** | Enkelt | Krever sikkerhetshårdening |
| **Vedlikehold** | Minimalt | Betydelig |

## 📊 **Eksempel på Konteringsresultater**

```
🏥 OneMed Fakturabehandling - Konteringsresultater

📊 KONTERINGSSAMMENDRAG:
💰 Totalt Beløp: 1426.50 NOK
✅ Konterte Ansatte: 3/4 (+3)
🚨 Konteringsavvik: 1 (1 krever manuell behandling)
🎯 Systemtillit: 100% (Høy tillit)

👥 KOSTNADSBÆRER-KONTERING:
✅ Annlaug Amundsen → Kostsenter 1001 → KONTERT → 450.75 NOK
✅ Andreas → Kostsenter 1002 → KONTERT → 320.50 NOK  
✅ Allan Simonsen → Kostsenter 1003 → KONTERT → 275.00 NOK
🚨 Maria Lindström → – → AVVIK → 380.25 NOK
   Årsak: Ansatt 'Maria Lindström' ikke funnet i kostnadsbærer-registeret
```

## ⚙️ **Konfiguration**

### **Streamlit Config (`.streamlit/config.toml`)**
```toml
[theme]
base = "light"
primaryColor = "#2563eb"  # OneMed Medical Blue
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f8fafc"
textColor = "#1e293b"
font = "sans serif"

[server]
headless = false  # Åpner automatisk i nettleser
port = 8501
address = "localhost"  # Kun lokal tilgang

[ui]
hideTopBar = true  # Renere utseende
```

## 🔧 **Troubleshooting**

### **Vanlige Problemer**

**Problem**: "ModuleNotFoundError: No module named 'streamlit'"
```bash
# Løsning:
pip install streamlit
```

**Problem**: "Port 8501 is already in use"
```bash
# Løsning:
streamlit run streamlit_app.py --server.port 8502
```

**Problem**: "Tema endres ikke"
```bash
# Løsning:
# Klikk på tema-toggle knappen i sidebar (🌙/☀️)
# Siden refresher automatisk med nytt tema
```

## 📞 **Support**

### **Funksjoner**
- ✅ **OneMed-farger** med lys/mørk modus
- ✅ **Norsk finansterminologi** 
- ✅ **Drag & drop PDF/Excel opplasting**
- ✅ **Real-time kontering og validering**
- ✅ **Profesjonelle rapporter** med nedlasting/utskrift
- ✅ **Responsive design** for alle enheter

### **Teknisk Stack**
- **Frontend**: Streamlit med custom CSS og OneMed-tema
- **Backend**: Python med Telia Norge AS fakturaparser  
- **Styling**: CSS-in-Python med dynamisk tema-bytte
- **Sikkerhet**: Kun lokal tilgang, ingen web-eksponering

---

**🏥 OneMed Fakturabehandling - Streamlit Edition v1.0**  
*Profesjonell fakturabehandling med elegant OneMed-design og norsk finansterminologi*

**🚀 Kjør nå:** `streamlit run streamlit_app.py`