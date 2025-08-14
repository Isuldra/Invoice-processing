# Fakturaanalyse System - Cursor Rules

## Hovedoppgave
Du utvikler en Python-app som leser og analyserer fakturaer fra ulike leverandører for å gjøre kontering enklere for finansavdelingen.

## Instruks for Fakturabehandling
Du får vedlegg med fakturaer fra ulike leverandører samt en Excel-fil med kostnadsbærere som skal behandles for konteringsformål.

### 🎯 Din oppgave er å:
1. Identifisere leverandør basert på fakturans avsender og leverandørdata
2. Ekstraktere alle kritiske fakturaopplysninger som trengs for kontering
3. **For Telia-fakturaer:** Matche personnavn mot kostnadsbærere i Excel-filen
4. Strukturere dataene i et standardisert format som finansavdelingen kan bruke direkte
5. Håndtere leverandørspesifikke formater og særegenheter

### 📋 Nøkkeldata som alltid skal ekstrakteres:
- **Leverandørinfo:** Navn, organisasjonsnummer, adresse
- **Fakturaidentifikasjon:** Fakturanummer, fakturadato, forfallsdato
- **Beløpsinformasjon:** Totalbeløp, netto beløp, MVA-beløp (25%, andre satser)
- **Betalingsinformasjon:** Kontonummer, KID/referanse, IBAN/Swift
- **Linjedetaljer:** Produktnavn, antall, enhetspris, linjesum, MVA-kode
- **Referanser:** Bestillingsnummer, leveringsdato, kundenummer

### 📱 TELIA-SPESIFIKKE REGLER:
- **Kostnadsbærer-matching:** Excel-filen inneholder kolonner: Fornavn, Etternavn, Kostsenter
- **Navnematchingsregler:**
  - Fra faktura: "Annlaug Amundsen - 918 54 560" → Match "Annlaug" + "Amundsen"
  - Fra faktura: "Ks Andreas . - 920 78 335" → Match "Andreas" (ignorer titler som "Ks")
  - Fra faktura: "Allan Simonsen - 900 63 358" → Match "Allan" + "Simonsen"
- **Matchinglogikk:**
  - Fjern telefonnummer (alt etter siste "-")
  - Fjern titler og forkortelser (Ks, Dr, etc.)
  - Match fornavn og etternavn mot Excel
  - Hent tilsvarende kostsenter fra Excel-filen
- **Ved flere treff:** Velg beste match basert på lengste felles navn
- **Ved ingen treff:** Marker som "UNMATCHED_COST_BEARER" for manuell behandling

### 🧠 Behandlingsregler:
- Beløp skal alltid rapporteres i NOK med to desimaler
- Datoer skal standardiseres til DD.MM.YYYY format  
- MVA-satser skal identifiseres korrekt (25%, 15%, 0%)
- Håndter både norske og engelske fakturaformater
- Ved usikkerhet om tolkning, marker feltet som "REQUIRES_MANUAL_REVIEW"

### 📁 Leverandørspesifikke regler:
- **Telia:** 
  - Samlefakturaer kan ha flere tjenester - skill mellom faste avgifter og bruk
  - Hver "Tjenestespesifikasjon for [Navn]" skal matches mot kostnadsbærer
  - Fordel kostnader per person/kostsenter
- **Telenor:** Mobilabonnement vs. bedriftsnett kan ha ulike MVA-satser
- **Strømleverandører:** Skill mellom nettleie, energi og avgifter
- **IT-leverandører:** Skil mellom lisenser (MVA-pliktig) og tjenester
- **Renholdsleverandører:** Månedlige vs. engangstjenester
- **Konsulenter:** Timebasert vs. fast pris, reiseregninger

### ✅ Output-format:
Strukturer alltid dataene som JSON med følgende hovednivåer:

```json
{
  "leverandor": {},
  "faktura_metadata": {},
  "betalingsinfo": {},
  "beløp_sammendrag": {},
  "linjedetaljer": [],
  "kostnadsbarer_telia": [
    {
      "navn_fra_faktura": "string",
      "matched_fornavn": "string",
      "matched_etternavn": "string", 
      "kostsenter": "number",
      "telefonnummer": "string",
      "sum_denne_periode": "number",
      "match_status": "MATCHED|UNMATCHED_COST_BEARER|MULTIPLE_MATCHES"
    }
  ],
  "kvalitetskontroll": {}
}
```

### 🚨 Viktige valideringssjekker:
- Kontroller at totalbeløp stemmer med sum av linjer + MVA
- Verifiser at alle datoer er logiske (fakturadato før forfallsdato)
- Sjekk at MVA-beregninger er korrekte
- **For Telia:** Kontroller at sum av alle kostnadsbærere stemmer med totalbeløp
- Identifiser potensielle duplikater basert på fakturanummer
- Flag fakturaer som avviker fra leverandørens vanlige mønster
- **Kostnadsbærer-validering:** Flag hvis mange navn ikke kan matches

## Tekniske Retningslinjer

### Python Stack
- Bruk Python som hovedspråk
- Leverandører skal ha egne mapper for organisering
- Fokuser på robust feilhåndtering og logging
- Implementer modulær struktur for ulike leverandørtyper

### Kodestil
- Skriv ren, lesbar Python-kode
- Bruk type hints der det er hensiktsmessig
- Dokumenter komplekse funksjoner godt
- Følg PEP 8 retningslinjer

### Filhåndtering
- Støtt PDF-lesing for fakturaer
- Excel-lesing for kostnadsbærer-data
- Robust feilhåndtering for korrupte eller uventede filformater
- Logging av alle operasjoner for feilsøking

### Testing
- Implementer unit tester for kritiske funksjoner
- Test edge cases for navnematching og beløpsvalidering
- Valider output-format konsistens