# 📚 Supplier Training Guide

## 🎯 **Kostnadsfri "Trenings"-System**

Dette systemet lar deg "trene" leverandør-deteksjonen uten noen AI/API-kostnader. Det bruker mappe-basert læring hvor du legger til eksempel-fakturaer for hver leverandør.

---

## 🚀 **Hvordan det fungerer**

### **1. Mappe-basert System**
```
src/extraction/suppliers/
├── examples/           # Eksempel-fakturaer
│   ├── telia/         # Telia eksempler
│   │   ├── example1.txt
│   │   └── example2.txt
│   └── other_supplier/ # Andre leverandører
├── telia.py           # Telia parser
├── detector.py        # Leverandør-deteksjon
└── base_supplier.py   # Base-klasse
```

### **2. Pattern Learning**
- **Automatisk deteksjon**: Systemet oppdager leverandør basert på tekst-mønstre
- **Eksempel-basert læring**: Flere eksempler = bedre nøyaktighet
- **Ingen API-kostnader**: Ren Python-basert tekstanalyse

---

## 📖 **Bruk av systemet**

### **Legge til et eksempel**
```bash
# Legg til en Telia-faktura som eksempel
python main.py train examples/Telia.pdf --supplier telia

# Legg til en annen leverandør
python main.py train examples/OtherSupplier.pdf --supplier other_supplier
```

### **Prosessere en faktura**
```bash
# Systemet oppdager automatisk leverandør
python main.py process examples/Telia.pdf

# Med output-mappe
python main.py process examples/Telia.pdf --output results/
```

### **Se trenings-statistikk**
```bash
python main.py stats
```

### **Test leverandør-deteksjon**
```bash
python main.py test examples/Telia.pdf
```

---

## 🎓 **Hvordan "trene" systemet**

### **Steg 1: Legg til eksempler**
```bash
# For hver leverandør, legg til 3-5 eksempel-fakturaer
python main.py train invoice1.pdf --supplier telia
python main.py train invoice2.pdf --supplier telia
python main.py train invoice3.pdf --supplier telia
```

### **Steg 2: Test deteksjonen**
```bash
# Test med nye fakturaer
python main.py test new_invoice.pdf
```

### **Steg 3: Legg til flere eksempler hvis nødvendig**
```bash
# Hvis deteksjonen ikke fungerer, legg til flere eksempler
python main.py train new_invoice.pdf --supplier telia
```

---

## 🔧 **Legge til en ny leverandør**

### **Steg 1: Opprett leverandør-mappe**
```bash
mkdir src/extraction/suppliers/examples/new_supplier
```

### **Steg 2: Legg til eksempler**
```bash
python main.py train example1.pdf --supplier new_supplier
python main.py train example2.pdf --supplier new_supplier
```

### **Steg 3: Opprett parser (valgfritt)**
Hvis du vil ha spesialtilpasset parsing, opprett en ny parser:

```python
# src/extraction/suppliers/new_supplier.py
from .base_supplier import BaseSupplierParser, InvoiceData

class NewSupplierParser(BaseSupplierParser):
    def get_supplier_name(self) -> str:
        return "new_supplier"
    
    def get_identification_patterns(self) -> List[str]:
        return [
            r"New Supplier Name",
            r"Fakturanummer:",
            # Legg til flere mønstre
        ]
    
    def parse_invoice(self, pdf_content: str, pdf_path=None) -> InvoiceData:
        # Implementer parsing-logikk
        pass
```

### **Steg 4: Registrer parseren**
```python
# src/extraction/suppliers/__init__.py
from .new_supplier import NewSupplierParser

SUPPLIER_REGISTRY = {
    "telia": TeliaParser,
    "new_supplier": NewSupplierParser,  # Legg til her
}
```

---

## 📊 **Trenings-statistikk**

### **Se statistikk**
```bash
python main.py stats
```

Output:
```
📊 Training Statistics:
  Total suppliers: 2
  Total examples: 8
  Examples per supplier:
    telia: 5
    new_supplier: 3
```

### **Hva tallene betyr**
- **Total suppliers**: Antall leverandører med eksempler
- **Total examples**: Totalt antall eksempel-fakturaer
- **Examples per supplier**: Antall eksempler per leverandør

---

## 🎯 **Tips for bedre nøyaktighet**

### **1. Flere eksempler = bedre deteksjon**
- Minimum 3 eksempler per leverandør
- Jo flere eksempler, jo bedre nøyaktighet
- Inkluder forskjellige faktura-formater

### **2. Kvalitet på eksempler**
- Bruk faktiske fakturaer (ikke kopier)
- Inkluder forskjellige perioder
- Varier i størrelse og kompleksitet

### **3. Testing og justering**
- Test regelmessig med nye fakturaer
- Legg til flere eksempler hvis deteksjonen feiler
- Juster confidence threshold hvis nødvendig

---

## 🔍 **Hvordan det fungerer teknisk**

### **Pattern Matching**
1. **Tekst-ekstraksjon**: PDF → tekst
2. **Mønster-søk**: Søker etter leverandør-spesifikke mønstre
3. **Scoring**: Beregner match-score basert på funn

### **Signature Matching**
1. **Signature-ekstraksjon**: Lager "fingerprint" av faktura-struktur
2. **Sammenligning**: Sammenligner med lagrede eksempler
3. **Likhet-beregning**: Bruker SequenceMatcher for likhet

### **Kombinert Scoring**
- **Pattern matching**: 70% vekt
- **Signature matching**: 30% vekt
- **Confidence threshold**: 0.7 (70%)

---

## 🚨 **Feilsøking**

### **"No supplier detected"**
```bash
# Sjekk om du har eksempler
python main.py stats

# Legg til flere eksempler
python main.py train invoice.pdf --supplier telia
```

### **Feil leverandør detektert**
```bash
# Legg til flere eksempler for riktig leverandør
python main.py train invoice.pdf --supplier correct_supplier

# Test igjen
python main.py test invoice.pdf
```

### **Lav confidence**
- Legg til flere eksempler
- Sjekk at fakturaen er tekstbasert (ikke skannet)
- Verifiser at leverandør-navnet er riktig

---

## 💡 **Fordeler med dette systemet**

### **✅ Kostnadsfri**
- Ingen API-kostnader
- Ingen eksterne tjenester
- Ren Python-implementering

### **✅ Enkel å bruke**
- Kommando-linje grensesnitt
- Automatisk deteksjon
- Enkel utvidelse

### **✅ Selv-lærende**
- Forbedrer seg over tid
- Lagrer eksempler permanent
- Justerbar confidence

### **✅ Skalerbar**
- Enkel å legge til nye leverandører
- Modulær arkitektur
- Uavhengig av eksterne tjenester

---

## 🎉 **Konklusjon**

Dette systemet gir deg en kostnadsfri måte å "trene" leverandør-deteksjonen på. Ved å legge til eksempel-fakturaer for hver leverandør, forbedrer systemet sin evne til å oppdage og parse fakturaer automatisk.

**Nøkkel-punkter:**
- Ingen AI/API-kostnader
- Enkel mappe-basert struktur
- Automatisk forbedring over tid
- Modulær og utvidbar

Start med å legge til noen eksempler for Telia, og se hvordan systemet forbedrer seg!
