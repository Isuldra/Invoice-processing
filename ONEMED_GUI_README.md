# 🏥 OneMed Fakturabehandling

**Standalone web-basert fakturabehandling for Telia Norge AS** 

Automatisk kontering med norsk finansterminologi og profesjonell OneMed-design.

## ✨ Funksjoner

- **📄 Drag & Drop PDF-opplasting** - Enkelt grensesnitt for fakturaer
- **📊 Excel kostnadsbærer-matching** - Automatisk kontering mot ansattregister  
- **🇳🇴 Norsk finansspråk** - KONTERT, KREVER_MANUELL_KONTERING, Konteringsavvik
- **🎨 OneMed-design** - Profesjonell medisinsk/helseteknologi-identitet
- **🔍 Kvalitetskontroll** - Automatisk validering og avviksrapportering
- **📱 Responsiv design** - Fungerer på alle enheter

## 🚀 Kom i gang

### 1. Installer avhengigheter
```bash
pip install -r requirements.txt
```

### 2. Start web-applikasjonen
```bash
python3 app.py
```

### 3. Åpne nettleseren
Gå til: **http://localhost:5000**

## 📋 Slik bruker du systemet

1. **📄 Last opp Telia faktura (PDF)** - Dra og slipp eller klikk for å velge
2. **📊 Last opp kostnadsbærer-fil (Excel)** - Valgfritt, bruker mock-data hvis ikke angitt
3. **🔄 Klikk "Behandle Faktura"** - Automatisk kontering starter
4. **📊 Gjennomgå resultater** - Se konteringsresultater og eventuelle avvik

## 🇳🇴 Norsk finansterminologi

Systemet bruker profesjonell norsk regnskapsTerminologi:

- **✅ KONTERT** - Ansatt funnet og automatisk kontert til kostsenter
- **🚨 KREVER_MANUELL_KONTERING** - Ansatt ikke funnet i registeret (avvik)
- **❓ FLERE_MULIGE_TREFF** - Tvetydige navn som trenger avklaring  

## 🔍 Eksempelresultater

```
👥 KOSTNADSBÆRER-KONTERING:
✅ Annlaug Amundsen
   Status: KONTERT
   Kostsenter: 1001

✅ Andreas  
   Status: KONTERT
   Kostsenter: 1002
   
🚨 Dr. Maria Lindström
   Status: KREVER_MANUELL_KONTERING  
   Avvik: Ansatt 'Maria Lindström' ikke funnet i kostnadsbærer-registeret
```

## 🏗️ Teknisk arkitektur

- **Backend**: Python Flask med Telia Norge AS fakturaparser
- **Frontend**: Profesjonell HTML/CSS/JS med OneMed-design
- **Sikkerhet**: Automatisk filopprydding og sikker filhåndtering
- **Design**: Medisinsk blå (#2563eb) og teal grønn (#0f766e) fargepalett

## 🎨 OneMed Design

Grensesnittet følger OneMed sin profesjonelle designidentitet:
- Ren og minimalistisk layout
- Medisinsk/helseteknologi fargepalett  
- God lesbarhet og tilgjengelighet
- Moderne web-komponenter
- Tydelige handlingsknapper

## 📊 Kvalitetskontroll

Systemet utfører automatisk validering:
- ✅ Totalbeløp mot sum av linjer
- ✅ Konterte ansatte mot fakturabeløp  
- ✅ Identifisering av konteringsavvik
- ✅ Systemtillitsnivå (confidence score)

## 🔧 Feilsøking

**Problem**: "Kunne ikke lese tekst fra PDF-filen"  
**Løsning**: Kontroller at PDF-en er tekstbasert (ikke skannet bilde)

**Problem**: "Dette ser ikke ut til å være en Telia Norge AS faktura"  
**Løsning**: Kontroller at PDF-en inneholder Telia Norge AS-identifikatorer

## 📞 Support

Dette er et standalone system designet for OneMed sin fakturabehandling.  
For teknisk support, kontakt utviklingsteamet.

---

**🏥 OneMed Fakturabehandling v1.0**  
*Profesjonell fakturabehandling med norsk finansterminologi*