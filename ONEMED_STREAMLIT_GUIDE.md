# 🏥 OneMed Fakturabehandling - Streamlit Guide

**Enkelt og elegant fakturabehandling med OneMed-design og norsk finansterminologi**

## 🚀 Kom i gang på 2 minutter!

### 1. **Installer Streamlit**
```bash
pip install streamlit
```

### 2. **Kjør OneMed-appen**
```bash
streamlit run streamlit_app.py
```

### 3. **Åpner automatisk i nettleser**
- **URL:** http://localhost:8501
- **Automatisk oppstart** - ingen manuell navigering nødvendig

## ✨ Funksjoner

### 🎨 **OneMed Profesjonelle Farger**
- **Medisinsk blå** (#2563eb) - OneMed sin primærfarge
- **Teal grønn** (#0f766e) - Sekundærfarge 
- **Profesjonell gradient-header** med OneMed-identitet

### 🌙 **Lys/Mørk Modus Toggle**
- **Klikk på 🌙/☀️ knappen** i sidebar
- **Automatisk fargetilpasning** av alle komponenter
- **Øyevennlig mørk modus** for utvidet bruk

### 🇳🇴 **Norsk Finansterminologi**
- ✅ **KONTERT** - Ansatt automatisk allokert til kostsenter
- 🚨 **KREVER_MANUELL_KONTERING** - Avvik som trenger manuell behandling  
- ❓ **FLERE_MULIGE_TREFF** - Tvetydige navn som krever avklaring

## 📋 Slik bruker du systemet

1. **📄 Last opp** Telia Norge AS faktura (PDF)
2. **📊 Last opp** kostnadsbærer-fil (Excel) - valgfritt
3. **🔄 Klikk** "Behandle Faktura"
4. **📊 Se resultater** med OneMed-styling og norsk terminologi

## 🎯 Demo-modus

**Hvis din `src/extraction/` ikke er komplett:**
- Appen fungerer i **demo-modus** med mock-data
- Viser alle OneMed-funksjoner og design
- Perfekt for å teste brukergrensesnittet

**Dr. Maria-casen:**
```
🚨 Dr. Maria Lindström → KREVER_MANUELL_KONTERING
Årsak: Ansatt ikke funnet i OneMed kostnadsbærer-registeret
```

## 🔧 Hvis noe ikke fungerer

**Problem:** "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install streamlit
```

**Problem:** "Port 8501 is already in use"  
```bash
streamlit run streamlit_app.py --server.port 8502
```

**Problem:** Tema endres ikke
- Klikk på 🌙/☀️ i sidebar
- Siden refresher automatisk

## 💰 Kostnader

**100% GRATIS! 🎯**
- Kun lokal bruk (localhost:8501)
- Ingen hosting-kostnader
- Ingen sikkerhetskompleksitet

## ⚙️ Tilpasning

**Farger:** Endre i `ONEMED_COLORS` i `streamlit_app.py`  
**Konfigurasjon:** Juster `.streamlit/config.toml`  
**Styling:** Modifiser CSS i `apply_onemed_theme()`

---

**🏥 OneMed Fakturabehandling - Streamlit Edition**  
*Profesjonell, enkel og kostnadsfri fakturabehandling*

**Start nå:** `streamlit run streamlit_app.py` 🚀