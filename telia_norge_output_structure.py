"""
Telia Norge AS - Strukturert Output Format
for Fakturaanalyse og Kostnadsbærer-matching

Basert på cursor-rules-faktura.md for norsk regnskapsføring.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from decimal import Decimal
import json
from enum import Enum


class MatchStatus(Enum):
    """Status for kostnadsbærer matching."""
    MATCHED = "MATCHED"
    UNMATCHED_COST_BEARER = "UNMATCHED_COST_BEARER" 
    MULTIPLE_MATCHES = "MULTIPLE_MATCHES"
    REQUIRES_MANUAL_REVIEW = "REQUIRES_MANUAL_REVIEW"


class MVASats(Enum):
    """Norske MVA-satser."""
    MVA_25 = "25%"
    MVA_15 = "15%"
    MVA_12 = "12%"
    MVA_0 = "0%"
    FRITATT = "Fritatt"


@dataclass
class Leverandor:
    """Leverandørinformasjon fra fakturaen."""
    navn: str = "Telia Norge AS"
    organisasjonsnummer: Optional[str] = None
    adresse: Optional[str] = None
    postboks: Optional[str] = None
    postnummer: Optional[str] = None
    poststed: Optional[str] = None
    telefon: Optional[str] = None
    epost: Optional[str] = None
    kontaktperson: Optional[str] = None


@dataclass
class FakturaMetadata:
    """Metadata om fakturaen."""
    fakturanummer: str
    fakturadato: str  # DD.MM.YYYY format
    forfallsdato: Optional[str] = None  # DD.MM.YYYY format
    leveringsdato: Optional[str] = None
    periode_fra: Optional[str] = None  # For abonnementsfakturaer
    periode_til: Optional[str] = None
    kundenummer: Optional[str] = None
    avtalenummer: Optional[str] = None
    bestillingsnummer: Optional[str] = None
    referanse: Optional[str] = None
    valuta: str = "NOK"
    språk: str = "NO"


@dataclass
class Betalingsinfo:
    """Betalingsinformasjon."""
    kontonummer: Optional[str] = None
    iban: Optional[str] = None
    swift_bic: Optional[str] = None
    kid_nummer: Optional[str] = None
    referanse: Optional[str] = None
    betalingsfrist_dager: Optional[int] = None
    rentesats_ved_forsinket_betaling: Optional[Decimal] = None


@dataclass
class BeløpSammendrag:
    """Sammendrag av beløp på fakturaen."""
    netto_beløp: Decimal
    mva_beløp_25: Decimal = field(default_factory=lambda: Decimal('0.00'))
    mva_beløp_15: Decimal = field(default_factory=lambda: Decimal('0.00'))
    mva_beløp_12: Decimal = field(default_factory=lambda: Decimal('0.00'))
    mva_beløp_0: Decimal = field(default_factory=lambda: Decimal('0.00'))
    mva_beløp_fritatt: Decimal = field(default_factory=lambda: Decimal('0.00'))
    total_mva: Decimal = field(default_factory=lambda: Decimal('0.00'))
    total_beløp: Decimal = field(default_factory=lambda: Decimal('0.00'))
    avrunding: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    def __post_init__(self):
        """Beregn totaler automatisk."""
        self.total_mva = (
            self.mva_beløp_25 + self.mva_beløp_15 + 
            self.mva_beløp_12 + self.mva_beløp_0 + self.mva_beløp_fritatt
        )
        self.total_beløp = self.netto_beløp + self.total_mva + self.avrunding


@dataclass
class Linjedetalj:
    """Detaljer for hver linje på fakturaen."""
    linjenummer: int
    produktnavn: str
    beskrivelse: Optional[str] = None
    periode_fra: Optional[str] = None
    periode_til: Optional[str] = None
    antall: Decimal = field(default_factory=lambda: Decimal('1'))
    enhet: str = "stk"
    enhetspris: Decimal = field(default_factory=lambda: Decimal('0.00'))
    rabatt_prosent: Decimal = field(default_factory=lambda: Decimal('0.00'))
    netto_linjesum: Decimal = field(default_factory=lambda: Decimal('0.00'))
    mva_sats: str = "25%"
    mva_beløp: Decimal = field(default_factory=lambda: Decimal('0.00'))
    brutto_linjesum: Decimal = field(default_factory=lambda: Decimal('0.00'))
    kostnadskategori: Optional[str] = None  # Mobil, Fasttelefon, Internet, etc.
    tilknyttet_telefonnummer: Optional[str] = None
    tilknyttet_person: Optional[str] = None


@dataclass
class KostnadsbærerTelia:
    """
    Kostnadsbærer-matching for Telia-fakturaer.
    Følger reglene i cursor-rules-faktura.md.
    """
    navn_fra_faktura: str  # Original navn som funnet i faktura
    telefonnummer: Optional[str] = None  # Telefonnummer fra faktura
    
    # Matching resultater
    matched_fornavn: Optional[str] = None
    matched_etternavn: Optional[str] = None
    matched_fullt_navn: Optional[str] = None
    kostsenter: Optional[str] = None
    kostsenter_navn: Optional[str] = None
    avdeling: Optional[str] = None
    
    # Beløpsinformasjon for denne personen
    sum_denne_periode: Decimal = field(default_factory=lambda: Decimal('0.00'))
    faste_avgifter: Decimal = field(default_factory=lambda: Decimal('0.00'))
    bruksavgifter: Decimal = field(default_factory=lambda: Decimal('0.00'))
    
    # Matching status og kvalitet
    match_status: MatchStatus = MatchStatus.UNMATCHED_COST_BEARER
    match_score: float = 0.0  # 0.0 - 1.0 konfidensverdi
    alternative_matches: List[Dict[str, Any]] = field(default_factory=list)
    
    # Detaljer om tjenester for denne personen
    tjenester: List[Dict[str, Any]] = field(default_factory=list)
    
    # Kommentarer og notater
    matching_notater: Optional[str] = None
    requires_manual_review: bool = False
    
    def add_tjeneste(self, tjeneste_navn: str, beløp: Decimal, periode: Optional[str] = None):
        """Legg til en tjeneste for denne kostnadsbæreren."""
        self.tjenester.append({
            'tjeneste': tjeneste_navn,
            'beløp': beløp,
            'periode': periode
        })
        self.sum_denne_periode += beløp


@dataclass
class Kvalitetskontroll:
    """Kvalitetskontroll og valideringsstatus."""
    
    # Beløpsvalidering
    beløp_validering: Dict[str, Any] = field(default_factory=dict)
    
    # Dato-validering
    dato_validering: Dict[str, Any] = field(default_factory=dict)
    
    # MVA-validering
    mva_validering: Dict[str, Any] = field(default_factory=dict)
    
    # Kostnadsbærer-validering
    kostnadsbærer_validering: Dict[str, Any] = field(default_factory=dict)
    
    # Generell kvalitet
    total_konfidensverdi: float = 0.0
    potensielle_feil: List[str] = field(default_factory=list)
    advarsler: List[str] = field(default_factory=list)
    anbefalinger: List[str] = field(default_factory=list)
    
    # Statistikk
    antall_linjer_prosessert: int = 0
    antall_kostnadsbærere_funnet: int = 0
    antall_matchede_kostnadsbærere: int = 0
    matching_rate: float = 0.0
    
    def __post_init__(self):
        """Initialiser validering dictionaries."""
        if not self.beløp_validering:
            self.beløp_validering = {
                'sum_linjer_stemmer': False,
                'mva_beregning_korrekt': False,
                'total_beløp_korrekt': False,
                'avvik_funnet': []
            }
        
        if not self.dato_validering:
            self.dato_validering = {
                'fakturadato_gyldig': False,
                'forfallsdato_etter_fakturadato': False,
                'periode_logisk': False,
                'dato_feil': []
            }
        
        if not self.mva_validering:
            self.mva_validering = {
                'mva_satser_gyldige': False,
                'mva_beregning_stemmer': False,
                'mva_feil': []
            }
        
        if not self.kostnadsbærer_validering:
            self.kostnadsbærer_validering = {
                'alle_navn_prosessert': False,
                'matching_rate_akseptabel': False,
                'sum_kostnadsbærere_stemmer': False,
                'kostnadsbærer_feil': []
            }


@dataclass
class TeliaNogeInvoiceOutput:
    """
    Hovedstruktur for Telia Norge AS fakturaanalyse output.
    
    Følger JSON-strukturen definert i cursor-rules-faktura.md
    """
    leverandor: Leverandor
    faktura_metadata: FakturaMetadata
    betalingsinfo: Betalingsinfo
    beløp_sammendrag: BeløpSammendrag
    linjedetaljer: List[Linjedetalj]
    kostnadsbarer_telia: List[KostnadsbærerTelia]
    kvalitetskontroll: Kvalitetskontroll
    
    # Metadata om prosessering
    prosessert_tidspunkt: str = field(default_factory=lambda: datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    prosesserings_versjon: str = "1.0"
    kilde_fil: Optional[str] = None
    
    def to_json(self) -> str:
        """Konverter til JSON-format for eksport."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary for JSON serialisering."""
        def convert_dataclass(obj):
            if hasattr(obj, '__dataclass_fields__'):
                result = {}
                for field_name, field_def in obj.__dataclass_fields__.items():
                    value = getattr(obj, field_name)
                    if isinstance(value, list):
                        result[field_name] = [convert_dataclass(item) for item in value]
                    elif hasattr(value, '__dataclass_fields__'):
                        result[field_name] = convert_dataclass(value)
                    elif isinstance(value, Enum):
                        result[field_name] = value.value
                    elif isinstance(value, Decimal):
                        result[field_name] = float(value)
                    else:
                        result[field_name] = value
                return result
            return obj
        
        return convert_dataclass(self)
    
    def validate_output(self) -> List[str]:
        """
        Valider output-strukturen mot reglene i cursor-rules-faktura.md
        
        Returns:
            Liste med valideringsfeil (tom liste hvis alt er OK)
        """
        feil = []
        
        # Sjekk påkrevde felt
        if not self.leverandor.navn:
            feil.append("Leverandørnavn mangler")
        
        if not self.faktura_metadata.fakturanummer:
            feil.append("Fakturanummer mangler")
        
        if not self.faktura_metadata.fakturadato:
            feil.append("Fakturadato mangler")
        
        # Valider beløp
        if self.beløp_sammendrag.total_beløp <= 0:
            feil.append("Total beløp må være større enn 0")
        
        # Valider kostnadsbærere
        total_kostnadsbærere = sum(kb.sum_denne_periode for kb in self.kostnadsbarer_telia)
        if abs(total_kostnadsbærere - self.beløp_sammendrag.total_beløp) > Decimal('0.01'):
            feil.append(f"Sum kostnadsbærere ({total_kostnadsbærere}) stemmer ikke med total beløp ({self.beløp_sammendrag.total_beløp})")
        
        # Valider linjedetaljer
        if not self.linjedetaljer:
            feil.append("Ingen linjedetaljer funnet")
        
        # Sjekk at alle kostnadsbærere har status
        for i, kb in enumerate(self.kostnadsbarer_telia):
            if not kb.match_status:
                feil.append(f"Kostnadsbærer {i+1} mangler match_status")
        
        return feil


# Hjelpefunksjoner for å bygge output-strukturen

def create_telia_kostnadsbærer(
    navn_fra_faktura: str,
    telefonnummer: Optional[str] = None,
    sum_beløp: Decimal = Decimal('0.00')
) -> KostnadsbærerTelia:
    """
    Opprett en kostnadsbærer for Telia-matching.
    
    Args:
        navn_fra_faktura: Navnet som funnet i fakturaen
        telefonnummer: Telefonnummer hvis tilgjengelig
        sum_beløp: Totalbeløp for denne kostnadsbæreren
    """
    return KostnadsbærerTelia(
        navn_fra_faktura=navn_fra_faktura,
        telefonnummer=telefonnummer,
        sum_denne_periode=sum_beløp,
        match_status=MatchStatus.UNMATCHED_COST_BEARER
    )


def parse_telia_navn(navn_med_telefon: str) -> tuple[str, Optional[str]]:
    """
    Parse navn og telefonnummer fra Telia-fakturaformat.
    
    Eksempler:
    - "Annlaug Amundsen - 918 54 560" → ("Annlaug Amundsen", "918 54 560")
    - "Ks Andreas . - 920 78 335" → ("Andreas", "920 78 335")
    - "Allan Simonsen - 900 63 358" → ("Allan Simonsen", "900 63 358")
    
    Args:
        navn_med_telefon: Navn med telefonnummer fra fakturaen
        
    Returns:
        Tuple med (renset_navn, telefonnummer)
    """
    # Split på siste "-" for å separere telefonnummer
    deler = navn_med_telefon.rsplit(' - ', 1)
    
    if len(deler) == 2:
        navn_del, telefon = deler
        telefon = telefon.strip()
    else:
        navn_del = navn_med_telefon
        telefon = None
    
    # Rens navn - fjern titler og ekstra tegn
    titler_å_fjerne = ['Ks', 'Dr', 'Prof', 'Mr', 'Mrs', 'Ms']
    navn_ord = navn_del.split()
    
    rensede_ord = []
    for ord in navn_ord:
        # Fjern punktum og andre tegn
        ord = ord.rstrip('.')
        
        # Hopp over titler
        if ord in titler_å_fjerne:
            continue
            
        # Hopp over tomme ord eller bare punktum
        if ord and ord != '.':
            rensede_ord.append(ord)
    
    renset_navn = ' '.join(rensede_ord)
    
    return renset_navn, telefon


def create_example_telia_output() -> TeliaNogeInvoiceOutput:
    """
    Opprett et eksempel på Telia Norge AS fakturaoutput.
    
    Viser hvordan strukturen skal brukes i praksis.
    """
    # Leverandørinformasjon
    leverandor = Leverandor(
        navn="Telia Norge AS",
        organisasjonsnummer="843 341 992",
        adresse="Stenersgata 2",
        postnummer="0184",
        poststed="OSLO",
        telefon="05000"
    )
    
    # Fakturametadata
    faktura_metadata = FakturaMetadata(
        fakturanummer="INV0123456789",
        fakturadato="15.01.2024",
        forfallsdato="14.02.2024",
        periode_fra="01.12.2023",
        periode_til="31.12.2023",
        kundenummer="123456",
        avtalenummer="AV-789123"
    )
    
    # Betalingsinformasjon
    betalingsinfo = Betalingsinfo(
        kontonummer="1234.56.78901",
        kid_nummer="123456789012345",
        betalingsfrist_dager=30
    )
    
    # Linjedetaljer
    linjedetaljer = [
        Linjedetalj(
            linjenummer=1,
            produktnavn="Mobilabonnement - Bedrift",
            beskrivelse="Månedsabonnement inkl. data",
            antall=Decimal('1'),
            enhetspris=Decimal('299.00'),
            netto_linjesum=Decimal('299.00'),
            mva_sats="25%",
            mva_beløp=Decimal('74.75'),
            brutto_linjesum=Decimal('373.75'),
            kostnadskategori="Mobil",
            tilknyttet_telefonnummer="918 54 560",
            tilknyttet_person="Annlaug Amundsen"
        ),
        Linjedetalj(
            linjenummer=2,
            produktnavn="Ekstra databruk",
            beskrivelse="Overskridelse av inkludert data",
            antall=Decimal('2.5'),
            enhet="GB",
            enhetspris=Decimal('49.00'),
            netto_linjesum=Decimal('122.50'),
            mva_sats="25%",
            mva_beløp=Decimal('30.63'),
            brutto_linjesum=Decimal('153.13'),
            kostnadskategori="Mobil",
            tilknyttet_telefonnummer="918 54 560",
            tilknyttet_person="Annlaug Amundsen"
        )
    ]
    
    # Beløpsammendrag
    beløp_sammendrag = BeløpSammendrag(
        netto_beløp=Decimal('421.50'),
        mva_beløp_25=Decimal('105.38'),
        total_mva=Decimal('105.38'),
        total_beløp=Decimal('526.88')
    )
    
    # Kostnadsbærere
    kostnadsbarer = [
        KostnadsbærerTelia(
            navn_fra_faktura="Annlaug Amundsen - 918 54 560",
            telefonnummer="918 54 560",
            matched_fornavn="Annlaug",
            matched_etternavn="Amundsen",
            matched_fullt_navn="Annlaug Amundsen",
            kostsenter="4501",
            kostsenter_navn="IT-avdelingen",
            sum_denne_periode=Decimal('526.88'),
            faste_avgifter=Decimal('373.75'),
            bruksavgifter=Decimal('153.13'),
            match_status=MatchStatus.MATCHED,
            match_score=0.98,
            tjenester=[
                {"tjeneste": "Mobilabonnement", "beløp": Decimal('373.75')},
                {"tjeneste": "Ekstra data", "beløp": Decimal('153.13')}
            ]
        )
    ]
    
    # Kvalitetskontroll
    kvalitetskontroll = Kvalitetskontroll(
        total_konfidensverdi=0.95,
        antall_linjer_prosessert=2,
        antall_kostnadsbærere_funnet=1,
        antall_matchede_kostnadsbærere=1,
        matching_rate=1.0
    )
    
    # Sett validering
    kvalitetskontroll.beløp_validering = {
        'sum_linjer_stemmer': True,
        'mva_beregning_korrekt': True,
        'total_beløp_korrekt': True,
        'avvik_funnet': []
    }
    
    return TeliaNogeInvoiceOutput(
        leverandor=leverandor,
        faktura_metadata=faktura_metadata,
        betalingsinfo=betalingsinfo,
        beløp_sammendrag=beløp_sammendrag,
        linjedetaljer=linjedetaljer,
        kostnadsbarer_telia=kostnadsbarer,
        kvalitetskontroll=kvalitetskontroll,
        kilde_fil="telia_faktura_januar_2024.pdf"
    )


if __name__ == "__main__":
    # Demonstrer output-strukturen
    eksempel = create_example_telia_output()
    
    # Valider output
    feil = eksempel.validate_output()
    if feil:
        print("Valideringsfeil funnet:")
        for feil_msg in feil:
            print(f"- {feil_msg}")
    else:
        print("✅ Output-struktur validert OK")
    
    # Vis JSON output
    print("\n" + "="*50)
    print("TELIA NORGE AS - STRUKTURERT OUTPUT")
    print("="*50)
    print(eksempel.to_json())
    
    # Vis statistikk
    print(f"\nSTATISTIKK:")
    print(f"- Antall linjer: {len(eksempel.linjedetaljer)}")
    print(f"- Antall kostnadsbærere: {len(eksempel.kostnadsbarer_telia)}")
    print(f"- Total beløp: {eksempel.beløp_sammendrag.total_beløp} NOK")
    print(f"- Matching rate: {eksempel.kvalitetskontroll.matching_rate*100:.1f}%")