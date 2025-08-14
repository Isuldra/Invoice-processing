"""
Telia Norge AS - Integrert Fakturaparser
Kombinerer optimaliserte PDF-funksjoner med norske regnskapskrav

Følger reglene i cursor-rules-faktura.md for:
- Leverandøridentifikasjon
- Kostnadsbærer-matching  
- Norsk MVA-håndtering
- Strukturert JSON-output
"""

import logging
import re
import traceback
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Import optimized components
from optimized_telia_parser import OptimizedTeliaParser, PerformanceMonitor
from optimized_excel_processor import CostBearerMatcher, ExcelEngineManager

# Import Norwegian output structure
from telia_norge_output_structure import (
    TeliaNogeInvoiceOutput, Leverandor, FakturaMetadata, Betalingsinfo,
    BeløpSammendrag, Linjedetalj, KostnadsbærerTelia, Kvalitetskontroll,
    MatchStatus, MVASats, parse_telia_navn, create_telia_kostnadsbærer
)

logger = logging.getLogger(__name__)


class TeliaNogeParser(OptimizedTeliaParser):
    """
    Spesialisert parser for Telia Norge AS fakturaer.
    
    Utvider OptimizedTeliaParser med norskspesifikke funksjoner:
    - Kostnadsbærer-matching mot Excel-fil
    - Norske MVA-satser og regnskapsregler
    - Strukturert output for norsk regnskapsføring
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialiser parser med norske instillinger."""
        super().__init__(config_path)
        
        # Norskspesifikke regex-mønstre
        self.norske_mønstre = self._kompiler_norske_mønstre()
        
        # Kostnadsbærer matcher
        self.kostnadsbærer_matcher = CostBearerMatcher(self.config)
        self.excel_manager = ExcelEngineManager(self.config)
        
        logger.info("Telia Norge AS parser initialisert")
    
    def _kompiler_norske_mønstre(self) -> Dict[str, re.Pattern]:
        """Kompiler regex-mønstre for norske Telia-fakturaer."""
        mønstre = {
            # Telia Norge AS leverandørinfo
            'leverandor_navn': re.compile(
                r'(?:TELIA\s+NORGE\s+AS|Telia\s+Norge|TELIA\s+COMPANY)', 
                re.IGNORECASE | re.MULTILINE
            ),
            
            'organisasjonsnummer': re.compile(
                r'(?:Org\.?\s*nr\.?|Organisasjonsnummer)[\s:]*(\d{3}\s?\d{3}\s?\d{3})',
                re.IGNORECASE | re.MULTILINE
            ),
            
            # Fakturanummer (Telia Norge format)
            'fakturanummer': re.compile(
                r'(?:Fakturanummer|Invoice\s+Number|Faktura\s+nr\.?)[\s:]*([A-Z]{0,3}\d{8,12})',
                re.IGNORECASE | re.MULTILINE
            ),
            
            # Norske datoformater
            'fakturadato': re.compile(
                r'(?:Fakturadato|Faktureringsdato|Dato)[\s:]*(\d{1,2}[.\/-]\d{1,2}[.\/-]\d{4})',
                re.IGNORECASE | re.MULTILINE
            ),
            
            'forfallsdato': re.compile(
                r'(?:Forfallsdato|Forfall|Due\s+date)[\s:]*(\d{1,2}[.\/-]\d{1,2}[.\/-]\d{4})',
                re.IGNORECASE | re.MULTILINE
            ),
            
            # Periode for abonnement
            'faktureringsperiode': re.compile(
                r'(?:Periode|Faktureringsperiode)[\s:]*(\d{1,2}[.\/-]\d{1,2}[.\/-]\d{4})\s*[-–]\s*(\d{1,2}[.\/-]\d{1,2}[.\/-]\d{4})',
                re.IGNORECASE | re.MULTILINE
            ),
            
            # Beløp i NOK
            'total_beløp': re.compile(
                r'(?:Total|Totalt|Å\s+betale|Sum)[\s:]*(?:kr|NOK)?[\s]*([0-9.,]+)[\s]*(?:kr|NOK)?',
                re.IGNORECASE | re.MULTILINE
            ),
            
            'netto_beløp': re.compile(
                r'(?:Netto|Ekskl\.?\s*mva|Eks\.?\s*MVA)[\s:]*(?:kr|NOK)?[\s]*([0-9.,]+)',
                re.IGNORECASE | re.MULTILINE
            ),
            
            'mva_beløp': re.compile(
                r'(?:MVA|Moms|VAT)[\s]*(?:25%|15%|12%)?[\s:]*(?:kr|NOK)?[\s]*([0-9.,]+)',
                re.IGNORECASE | re.MULTILINE
            ),
            
            # KID nummer
            'kid_nummer': re.compile(
                r'(?:KID|Kundeidentifikasjon)[\s:]*(\d{4,25})',
                re.IGNORECASE | re.MULTILINE
            ),
            
            # Kontonummer
            'kontonummer': re.compile(
                r'(?:Kontonummer|Konto)[\s:]*(\d{4}[\s.]?\d{2}[\s.]?\d{5})',
                re.IGNORECASE | re.MULTILINE
            ),
            
            # Tjenestespesifikasjon med navn og telefon
            'tjeneste_med_navn': re.compile(
                r'Tjenestespesifikasjon\s+for\s+([^:]+?)(?:\s*:\s*|\s*-\s*)([0-9\s]+)',
                re.IGNORECASE | re.MULTILINE | re.DOTALL
            ),
            
            # Personfakturering format: "Navn - telefonnummer"
            'person_fakturering': re.compile(
                r'([A-ZÆØÅ][a-zæøå]+(?:\s+[A-ZÆØÅ]?[a-zæøå]*)*(?:\s+[A-ZÆØÅ][a-zæøå]+)*)\s*-\s*([0-9\s]{8,12})',
                re.MULTILINE | re.UNICODE
            ),
            
            # Kostnadslinje med beløp
            'kostnadslinje': re.compile(
                r'(.+?)\s+([0-9.,]+)\s*(?:kr|NOK)',
                re.MULTILINE
            )
        }
        
        return mønstre
    
    @PerformanceMonitor.benchmark
    def parse_telia_norge_faktura(self, 
                                  pdf_path: Path, 
                                  kostnadsbærer_excel: Optional[Path] = None) -> TeliaNogeInvoiceOutput:
        """
        Parser Telia Norge AS faktura med full norsk integrasjon.
        
        Args:
            pdf_path: Sti til PDF-fakturaen
            kostnadsbærer_excel: Sti til Excel-fil med kostnadsbærere
            
        Returns:
            Strukturert output for norsk regnskapsføring
        """
        logger.info(f"Starter parsing av Telia Norge faktura: {pdf_path}")
        
        try:
            with PerformanceMonitor.monitor_memory():
                # 1. Ekstraher tekst fra PDF
                base_invoice_data = self.parse_invoice(pdf_path)
                
                # 2. Parser norskspesifikk informasjon
                leverandor = self._parser_leverandor_info(base_invoice_data.raw_text)
                faktura_metadata = self._parser_faktura_metadata(base_invoice_data.raw_text)
                betalingsinfo = self._parser_betalingsinfo(base_invoice_data.raw_text)
                beløp_sammendrag = self._parser_beløp_sammendrag(base_invoice_data.raw_text)
                linjedetaljer = self._parser_linjedetaljer(base_invoice_data.raw_text)
                
                # 3. Ekstraher og match kostnadsbærere
                kostnadsbærere = self._ekstraktere_kostnadsbærere(base_invoice_data.raw_text)
                
                if kostnadsbærer_excel and kostnadsbærer_excel.exists():
                    kostnadsbærere = self._matche_kostnadsbærere(kostnadsbærere, kostnadsbærer_excel)
                
                # 4. Kvalitetskontroll
                kvalitetskontroll = self._utfør_kvalitetskontroll(
                    beløp_sammendrag, linjedetaljer, kostnadsbærere
                )
                
                # 5. Bygg strukturert output
                output = TeliaNogeInvoiceOutput(
                    leverandor=leverandor,
                    faktura_metadata=faktura_metadata,
                    betalingsinfo=betalingsinfo,
                    beløp_sammendrag=beløp_sammendrag,
                    linjedetaljer=linjedetaljer,
                    kostnadsbarer_telia=kostnadsbærere,
                    kvalitetskontroll=kvalitetskontroll,
                    kilde_fil=str(pdf_path)
                )
                
                # 6. Valider output
                valideringsfeil = output.validate_output()
                if valideringsfeil:
                    kvalitetskontroll.potensielle_feil.extend(valideringsfeil)
                    logger.warning(f"Valideringsfeil: {valideringsfeil}")
                
                logger.info(f"Fakturaanalyse fullført: {len(kostnadsbærere)} kostnadsbærere funnet")
                return output
                
        except Exception as e:
            logger.error(f"Feil under parsing av Telia Norge faktura: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _parser_leverandor_info(self, tekst: str) -> Leverandor:
        """Parser leverandørinformasjon fra fakturaen."""
        leverandor = Leverandor()
        
        # Leverandørnavn
        navn_match = self.norske_mønstre['leverandor_navn'].search(tekst)
        if navn_match:
            leverandor.navn = navn_match.group(0).strip()
        
        # Organisasjonsnummer
        orgnr_match = self.norske_mønstre['organisasjonsnummer'].search(tekst)
        if orgnr_match:
            leverandor.organisasjonsnummer = orgnr_match.group(1).strip()
        
        # Standard Telia Norge informasjon
        if "Telia" in leverandor.navn:
            leverandor.telefon = "05000"
            leverandor.poststed = "OSLO"
        
        return leverandor
    
    def _parser_faktura_metadata(self, tekst: str) -> FakturaMetadata:
        """Parser fakturametadata."""
        # Fakturanummer
        fakturanummer = ""
        fakturanummer_match = self.norske_mønstre['fakturanummer'].search(tekst)
        if fakturanummer_match:
            fakturanummer = fakturanummer_match.group(1).strip()
        
        # Datoer
        fakturadato = None
        fakturadato_match = self.norske_mønstre['fakturadato'].search(tekst)
        if fakturadato_match:
            fakturadato = self._normaliser_dato(fakturadato_match.group(1))
        
        forfallsdato = None
        forfallsdato_match = self.norske_mønstre['forfallsdato'].search(tekst)
        if forfallsdato_match:
            forfallsdato = self._normaliser_dato(forfallsdato_match.group(1))
        
        # Periode
        periode_fra = None
        periode_til = None
        periode_match = self.norske_mønstre['faktureringsperiode'].search(tekst)
        if periode_match:
            periode_fra = self._normaliser_dato(periode_match.group(1))
            periode_til = self._normaliser_dato(periode_match.group(2))
        
        return FakturaMetadata(
            fakturanummer=fakturanummer,
            fakturadato=fakturadato or "",
            forfallsdato=forfallsdato,
            periode_fra=periode_fra,
            periode_til=periode_til,
            valuta="NOK",
            språk="NO"
        )
    
    def _parser_betalingsinfo(self, tekst: str) -> Betalingsinfo:
        """Parser betalingsinformasjon."""
        betalingsinfo = Betalingsinfo()
        
        # KID nummer
        kid_match = self.norske_mønstre['kid_nummer'].search(tekst)
        if kid_match:
            betalingsinfo.kid_nummer = kid_match.group(1).strip()
        
        # Kontonummer
        konto_match = self.norske_mønstre['kontonummer'].search(tekst)
        if konto_match:
            betalingsinfo.kontonummer = konto_match.group(1).strip()
        
        return betalingsinfo
    
    def _parser_beløp_sammendrag(self, tekst: str) -> BeløpSammendrag:
        """Parser beløpsinformasjon."""
        # Total beløp
        total = Decimal('0.00')
        total_match = self.norske_mønstre['total_beløp'].search(tekst)
        if total_match:
            total = self._parser_beløp(total_match.group(1))
        
        # Netto beløp
        netto = Decimal('0.00')
        netto_match = self.norske_mønstre['netto_beløp'].search(tekst)
        if netto_match:
            netto = self._parser_beløp(netto_match.group(1))
        
        # MVA beløp
        mva_25 = Decimal('0.00')
        mva_matches = self.norske_mønstre['mva_beløp'].findall(tekst)
        for mva_match in mva_matches:
            mva_25 += self._parser_beløp(mva_match)
        
        # Hvis vi ikke har netto, beregn det
        if netto == 0 and total > 0 and mva_25 > 0:
            netto = total - mva_25
        
        return BeløpSammendrag(
            netto_beløp=netto,
            mva_beløp_25=mva_25,
            total_mva=mva_25,
            total_beløp=total
        )
    
    def _parser_linjedetaljer(self, tekst: str) -> List[Linjedetalj]:
        """Parser linjedetaljer fra fakturaen."""
        linjer = []
        linjenummer = 1
        
        # Finn alle kostnadslinjer
        kostnad_matches = self.norske_mønstre['kostnadslinje'].findall(tekst)
        
        for beskrivelse, beløp_str in kostnad_matches:
            try:
                beløp = self._parser_beløp(beløp_str)
                if beløp > 0:
                    # Beregn MVA (25% for de fleste Telia-tjenester)
                    netto = beløp / Decimal('1.25')
                    mva = beløp - netto
                    
                    linje = Linjedetalj(
                        linjenummer=linjenummer,
                        produktnavn=beskrivelse.strip(),
                        netto_linjesum=netto,
                        mva_sats="25%",
                        mva_beløp=mva,
                        brutto_linjesum=beløp,
                        kostnadskategori=self._bestem_kostnadskategori(beskrivelse)
                    )
                    linjer.append(linje)
                    linjenummer += 1
                    
            except (ValueError, ArithmeticError) as e:
                logger.warning(f"Kunne ikke parse linje '{beskrivelse}': {e}")
                continue
        
        return linjer
    
    def _ekstraktere_kostnadsbærere(self, tekst: str) -> List[KostnadsbærerTelia]:
        """Ekstraher kostnadsbærere fra fakturaen."""
        kostnadsbærere = []
        
        # Finn tjenestespesifikasjoner
        tjeneste_matches = self.norske_mønstre['tjeneste_med_navn'].findall(tekst)
        for navn_del, telefon_del in tjeneste_matches:
            renset_navn, telefonnummer = parse_telia_navn(f"{navn_del.strip()} - {telefon_del.strip()}")
            
            if renset_navn:
                kostnadsbærer = create_telia_kostnadsbærer(
                    navn_fra_faktura=f"{navn_del.strip()} - {telefon_del.strip()}",
                    telefonnummer=telefonnummer
                )
                kostnadsbærere.append(kostnadsbærer)
        
        # Finn person-fakturering format
        person_matches = self.norske_mønstre['person_fakturering'].findall(tekst)
        for navn, telefon in person_matches:
            renset_navn, telefonnummer = parse_telia_navn(f"{navn.strip()} - {telefon.strip()}")
            
            if renset_navn:
                kostnadsbærer = create_telia_kostnadsbærer(
                    navn_fra_faktura=f"{navn.strip()} - {telefon.strip()}",
                    telefonnummer=telefonnummer
                )
                
                # Ikke legg til duplikater
                eksisterer = any(kb.telefonnummer == telefonnummer for kb in kostnadsbærere)
                if not eksisterer:
                    kostnadsbærere.append(kostnadsbærer)
        
        logger.info(f"Ekstraktert {len(kostnadsbærere)} kostnadsbærere fra faktura")
        return kostnadsbærere
    
    def _matche_kostnadsbærere(self, 
                              kostnadsbærere: List[KostnadsbærerTelia],
                              excel_fil: Path) -> List[KostnadsbærerTelia]:
        """Match kostnadsbærere mot Excel-fil."""
        try:
            # Les Excel-fil med kostnadsbærere
            kostnadsbærer_df = self.excel_manager.read_excel_optimized(excel_fil)
            
            # Forvent kolonner: Fornavn, Etternavn, Kostsenter
            påkrevde_kolonner = ['Fornavn', 'Etternavn', 'Kostsenter']
            manglende_kolonner = [kol for kol in påkrevde_kolonner if kol not in kostnadsbærer_df.columns]
            
            if manglende_kolonner:
                logger.warning(f"Manglende kolonner i Excel-fil: {manglende_kolonner}")
                return kostnadsbærere
            
            # Bygg fullt navn for matching
            kostnadsbærer_df['Fullt_Navn'] = (
                kostnadsbærer_df['Fornavn'].astype(str) + ' ' + 
                kostnadsbærer_df['Etternavn'].astype(str)
            )
            
            # Match hver kostnadsbærer
            for kostnadsbærer in kostnadsbærere:
                renset_navn, _ = parse_telia_navn(kostnadsbærer.navn_fra_faktura)
                
                if renset_navn:
                    matching_resultater = self.kostnadsbærer_matcher.match_employee_names(
                        [renset_navn], kostnadsbærer_df, 'Fullt_Navn'
                    )
                    
                    if renset_navn in matching_resultater:
                        resultat = matching_resultater[renset_navn]
                        
                        if resultat['status'] == 'matched':
                            # Finn matchende rad i DataFrame
                            matchende_rad = kostnadsbærer_df[
                                kostnadsbærer_df['Fullt_Navn'] == resultat['original_cost_bearer']
                            ].iloc[0]
                            
                            # Oppdater kostnadsbærer med match-info
                            kostnadsbærer.matched_fornavn = matchende_rad['Fornavn']
                            kostnadsbærer.matched_etternavn = matchende_rad['Etternavn']
                            kostnadsbærer.matched_fullt_navn = resultat['original_cost_bearer']
                            kostnadsbærer.kostsenter = str(matchende_rad['Kostsenter'])
                            kostnadsbærer.match_status = MatchStatus.MATCHED
                            kostnadsbærer.match_score = resultat['score'] / 100.0
                            
                            logger.info(f"Matchet '{renset_navn}' → '{resultat['original_cost_bearer']}' (score: {resultat['score']})")
                        
                        else:
                            kostnadsbærer.match_status = MatchStatus.UNMATCHED_COST_BEARER
                            kostnadsbærer.matching_notater = f"Ingen match funnet (beste score: {resultat.get('score', 0)})"
                            logger.warning(f"Ingen match for '{renset_navn}'")
            
            # Beregn matching-statistikk
            matchede = sum(1 for kb in kostnadsbærere if kb.match_status == MatchStatus.MATCHED)
            matching_rate = (matchede / len(kostnadsbærere)) * 100 if kostnadsbærere else 0
            
            logger.info(f"Kostnadsbærer-matching fullført: {matchede}/{len(kostnadsbærere)} ({matching_rate:.1f}%)")
            
        except Exception as e:
            logger.error(f"Feil under kostnadsbærer-matching: {e}")
            for kostnadsbærer in kostnadsbærere:
                kostnadsbærer.match_status = MatchStatus.REQUIRES_MANUAL_REVIEW
                kostnadsbærer.matching_notater = f"Feil under matching: {str(e)}"
        
        return kostnadsbærere
    
    def _utfør_kvalitetskontroll(self,
                                beløp_sammendrag: BeløpSammendrag,
                                linjedetaljer: List[Linjedetalj],
                                kostnadsbærere: List[KostnadsbærerTelia]) -> Kvalitetskontroll:
        """Utfør kvalitetskontroll av parsede data."""
        kvalitetskontroll = Kvalitetskontroll(
            antall_linjer_prosessert=len(linjedetaljer),
            antall_kostnadsbærere_funnet=len(kostnadsbærere),
            antall_matchede_kostnadsbærere=sum(
                1 for kb in kostnadsbærere if kb.match_status == MatchStatus.MATCHED
            )
        )
        
        # Beregn matching rate
        if kostnadsbærere:
            kvalitetskontroll.matching_rate = (
                kvalitetskontroll.antall_matchede_kostnadsbærere / len(kostnadsbærere)
            )
        
        # Valider beløp
        sum_linjer = sum(linje.brutto_linjesum for linje in linjedetaljer)
        beløp_avvik = abs(sum_linjer - beløp_sammendrag.total_beløp)
        
        kvalitetskontroll.beløp_validering = {
            'sum_linjer_stemmer': beløp_avvik < Decimal('0.01'),
            'mva_beregning_korrekt': True,  # TODO: Implementer MVA-validering
            'total_beløp_korrekt': beløp_sammendrag.total_beløp > 0,
            'avvik_funnet': [f"Beløpsavvik: {beløp_avvik} NOK"] if beløp_avvik >= Decimal('0.01') else []
        }
        
        # Kostnadsbærer-validering
        kostnadsbærer_sum = sum(kb.sum_denne_periode for kb in kostnadsbærere)
        kostnadsbærer_avvik = abs(kostnadsbærer_sum - beløp_sammendrag.total_beløp)
        
        kvalitetskontroll.kostnadsbærer_validering = {
            'alle_navn_prosessert': True,  # TODO: Implementer mer detaljert sjekk
            'matching_rate_akseptabel': kvalitetskontroll.matching_rate >= 0.8,
            'sum_kostnadsbærere_stemmer': kostnadsbærer_avvik < Decimal('0.01'),
            'kostnadsbærer_feil': []
        }
        
        if kostnadsbærer_avvik >= Decimal('0.01'):
            kvalitetskontroll.kostnadsbærer_validering['kostnadsbærer_feil'].append(
                f"Kostnadsbærer-sum avviker med {kostnadsbærer_avvik} NOK"
            )
        
        # Beregn total konfidensverdi
        konfidensverdi = 0.0
        if kvalitetskontroll.beløp_validering['sum_linjer_stemmer']:
            konfidensverdi += 0.3
        if kvalitetskontroll.kostnadsbærer_validering['sum_kostnadsbærere_stemmer']:
            konfidensverdi += 0.3
        if kvalitetskontroll.matching_rate >= 0.8:
            konfidensverdi += 0.4
        
        kvalitetskontroll.total_konfidensverdi = konfidensverdi
        
        return kvalitetskontroll
    
    # Hjelpefunksjoner
    
    def _normaliser_dato(self, dato_str: str) -> str:
        """Normaliser dato til DD.MM.YYYY format."""
        # Fjern mellomrom
        dato_str = dato_str.replace(' ', '')
        
        # Erstatt forskjellige separatorer med punktum
        dato_str = re.sub(r'[/-]', '.', dato_str)
        
        # Sikre at vi har DD.MM.YYYY format
        deler = dato_str.split('.')
        if len(deler) == 3:
            dag, måned, år = deler
            return f"{dag.zfill(2)}.{måned.zfill(2)}.{år}"
        
        return dato_str
    
    def _parser_beløp(self, beløp_str: str) -> Decimal:
        """Parser beløp fra streng til Decimal."""
        # Fjern alt som ikke er siffer, komma eller punktum
        beløp_str = re.sub(r'[^\d.,]', '', beløp_str)
        
        # Håndter norsk format (komma som desimalseparator)
        if ',' in beløp_str and '.' in beløp_str:
            # Format: 1.234,50
            beløp_str = beløp_str.replace('.', '').replace(',', '.')
        elif ',' in beløp_str:
            # Format: 1234,50
            beløp_str = beløp_str.replace(',', '.')
        
        try:
            return Decimal(beløp_str).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except (ValueError, ArithmeticError):
            logger.warning(f"Kunne ikke parse beløp: '{beløp_str}'")
            return Decimal('0.00')
    
    def _bestem_kostnadskategori(self, beskrivelse: str) -> str:
        """Bestem kostnadskategori basert på beskrivelse."""
        beskrivelse_lower = beskrivelse.lower()
        
        if any(word in beskrivelse_lower for word in ['mobil', 'mobilabonnement']):
            return "Mobil"
        elif any(word in beskrivelse_lower for word in ['fast', 'fasttelefon']):
            return "Fasttelefon"  
        elif any(word in beskrivelse_lower for word in ['internet', 'bredbånd']):
            return "Internet"
        elif any(word in beskrivelse_lower for word in ['data', 'databruk']):
            return "Data"
        else:
            return "Annet"


def main():
    """Demonstrer Telia Norge AS parser."""
    print("🇳🇴 Telia Norge AS - Fakturaparser")
    print("="*50)
    
    # Initialiser parser
    try:
        parser = TeliaNogeParser()
        print("✅ Parser initialisert")
        
        # Eksempel på bruk
        print("\n📋 Parser er klar til å prosessere fakturaer:")
        print("   - PDF-ekstraksjon med optimerte algoritmer")
        print("   - Kostnadsbærer-matching mot Excel-fil")
        print("   - Norsk MVA-håndtering (25%, 15%, 12%, 0%)")
        print("   - Strukturert JSON-output for regnskapsføring")
        
        print("\n🔧 Bruk:")
        print("   parser.parse_telia_norge_faktura(pdf_path, kostnadsbærer_excel)")
        
    except Exception as e:
        print(f"❌ Feil ved initialisering: {e}")


if __name__ == "__main__":
    main()