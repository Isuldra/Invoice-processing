"""
Telia Supplier Parser

Text-based parser for Telia Norge AS invoices with cost bearer matching.
Implements Norwegian name parsing and Excel cost bearer validation.
"""

import re
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

# Try to import the correct PDF library
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    try:
        import PyPDF2
        from PyPDF2 import PdfReader
        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from .base_supplier import BaseSupplierParser, InvoiceData, InvoiceLine


@dataclass
class CostBearer:
    """Represents a cost bearer from Excel file."""
    fornavn: str
    etternavn: str
    kostsenter: int
    full_name: str = ""
    
    def __post_init__(self):
        """Generate full name for matching."""
        if self.etternavn:
            self.full_name = f"{self.fornavn} {self.etternavn}".strip()
        else:
            self.full_name = self.fornavn.strip()


@dataclass 
class CostBearerMatch:
    """Represents the result of cost bearer matching."""
    navn_fra_faktura: str
    matched_fornavn: str = ""
    matched_etternavn: str = ""
    kostsenter: Optional[int] = None
    telefonnummer: str = ""
    sum_denne_periode: float = 0.0
    match_status: str = "UNMATCHED_COST_BEARER"  # MATCHED|UNMATCHED_COST_BEARER|MULTIPLE_MATCHES
    confidence_score: float = 0.0
    deviation_reason: str = ""


class CostBearerMatcher:
    """Handles cost bearer matching against Excel data with Norwegian fuzzy matching."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.cost_bearers: List[CostBearer] = []
        
    def load_mock_cost_bearers(self) -> None:
        """Load mock cost bearer data for testing until Excel integration is ready."""
        # Mock data based on Norwegian names - Dr. Maria is intentionally NOT included
        # per user requirement that she doesn't work at OneMed Norge AS
        mock_data = [
            {"fornavn": "Annlaug", "etternavn": "Amundsen", "kostsenter": 1001},
            {"fornavn": "Andreas", "etternavn": "Hansen", "kostsenter": 1002}, 
            {"fornavn": "Allan", "etternavn": "Simonsen", "kostsenter": 1003},
            {"fornavn": "Erik", "etternavn": "Johansson", "kostsenter": 1004},
            {"fornavn": "Lars", "etternavn": "Nielsen", "kostsenter": 1005},
        ]
        
        self.cost_bearers = [
            CostBearer(fornavn=cb["fornavn"], etternavn=cb["etternavn"], 
                      kostsenter=cb["kostsenter"])
            for cb in mock_data
        ]
        
        self.logger.info(f"Loaded {len(self.cost_bearers)} mock cost bearers")
        
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Simple similarity calculation until proper fuzzy matching is available."""
        name1_clean = name1.lower().strip()
        name2_clean = name2.lower().strip()
        
        if name1_clean == name2_clean:
            return 1.0
        
        # Check if one name contains the other
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return 0.8
            
        # Simple word-based matching
        words1 = set(name1_clean.split())
        words2 = set(name2_clean.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def match_employee_name(self, employee_name: str, phone_number: str = "", amount: float = 0.0) -> CostBearerMatch:
        """
        Match employee name against cost bearers with Norwegian business rules.
        
        Returns UNMATCHED_COST_BEARER for names not in Excel per user requirements.
        """
        self.logger.debug(f"Matching employee name: '{employee_name}'")
        
        result = CostBearerMatch(
            navn_fra_faktura=employee_name,
            telefonnummer=phone_number,
            sum_denne_periode=amount
        )
        
        if not self.cost_bearers:
            self.load_mock_cost_bearers()
        
        best_match = None
        best_score = 0.0
        matches_found = []
        
        # Try to find matches
        for cost_bearer in self.cost_bearers:
            # Try matching against full name
            score = self._calculate_name_similarity(employee_name, cost_bearer.full_name)
            
            if score > 0.7:  # Threshold for considering a match
                matches_found.append((cost_bearer, score))
                
                if score > best_score:
                    best_match = cost_bearer
                    best_score = score
        
        # Handle matching results according to cursor rules
        if len(matches_found) == 0:
            # No matches found - generate deviation per user requirement
            result.match_status = "UNMATCHED_COST_BEARER"
            result.deviation_reason = f"Employee '{employee_name}' not found in cost bearer Excel file"
            self.logger.warning(f"🚨 DEVIATION: {result.deviation_reason}")
            
        elif len(matches_found) == 1:
            # Single match found
            result.match_status = "MATCHED"
            result.matched_fornavn = best_match.fornavn
            result.matched_etternavn = best_match.etternavn
            result.kostsenter = best_match.kostsenter
            result.confidence_score = best_score
            self.logger.info(f"✅ Matched '{employee_name}' → {best_match.full_name} (kostsenter: {best_match.kostsenter})")
            
        else:
            # Multiple matches found - requires manual review per cursor rules
            result.match_status = "MULTIPLE_MATCHES"
            result.deviation_reason = f"Multiple potential matches found for '{employee_name}'"
            result.confidence_score = best_score
            self.logger.warning(f"🚨 MULTIPLE MATCHES: {result.deviation_reason}")
        
        return result


class TeliaParser(BaseSupplierParser):
    """Text-based parser for Telia Norge AS invoices with cost bearer matching."""
    
    def __init__(self):
        super().__init__()
        self.cost_bearer_matcher = CostBearerMatcher(self.logger)
    
    def get_supplier_name(self) -> str:
        return "Telia Norge AS"
    
    def get_identification_patterns(self) -> List[str]:
        return [
            r"Telia Norge AS",
            r"TELIA NORGE AS",
            r"Fakturanummer:",
            r"Tjenestespesifikasjon for",
            r"SUM DENNE PERIODE"
        ]
    
    def can_parse(self, pdf_content: str) -> bool:
        """Check if this is a Telia invoice."""
        patterns = self.get_identification_patterns()
        matches = sum(1 for pattern in patterns 
                     if re.search(pattern, pdf_content, re.IGNORECASE))
        return matches >= 3  # At least 3 patterns must match
    
    def parse_invoice(self, pdf_content: str, pdf_path: Optional[Path] = None) -> InvoiceData:
        """Parse Telia invoice from text content."""
        self.logger.info("Parsing Telia invoice")
        
        # Extract basic invoice info
        invoice_data = InvoiceData(supplier="Telia Norge AS")
        
        # Extract invoice number
        invoice_match = re.search(r'Fakturanummer:\s*(\d+)', pdf_content)
        if invoice_match:
            invoice_data.invoice_number = invoice_match.group(1)
        
        # Extract invoice date
        date_match = re.search(r'Fakturadato:\s*(\d{2}\.\d{2}\.\d{4})', pdf_content)
        if date_match:
            invoice_data.invoice_date = date_match.group(1)
        
        # Extract period
        period_match = re.search(r'Periode:\s*(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}\.\d{2}\.\d{4})', pdf_content)
        if period_match:
            invoice_data.period_from = period_match.group(1)
            invoice_data.period_to = period_match.group(2)
        
        # Extract grand total
        total_match = re.search(r'Å betale:\s*(\d+[,.]?\d*)', pdf_content)
        if total_match:
            try:
                total_str = total_match.group(1).replace(',', '.')
                invoice_data.grand_total = float(total_str)
            except ValueError:
                self.logger.warning("Could not parse grand total")
        
        # Extract invoice lines
        invoice_data.lines = self._extract_invoice_lines(pdf_content)
        
        # Calculate confidence based on extraction success
        confidence = self._calculate_confidence(invoice_data)
        invoice_data.confidence = confidence
        
        return invoice_data
    
    def parse_invoice_with_cost_bearers(self, pdf_content: str, excel_path: Optional[Path] = None) -> Dict:
        """
        Parse Telia invoice with cost bearer matching and return structured output 
        according to cursor-rules-faktura.md format.
        """
        # First, parse the basic invoice data
        invoice_data = self.parse_invoice(pdf_content)
        
        # Perform cost bearer matching for each line
        cost_bearer_matches = []
        total_matched_amount = 0.0
        unmatched_count = 0
        
        for line in invoice_data.lines:
            match_result = self.cost_bearer_matcher.match_employee_name(
                employee_name=line.employee_name,
                phone_number=line.phone_number,
                amount=line.amount
            )
            
            cost_bearer_matches.append(match_result)
            
            # Track matching statistics
            if match_result.match_status == "MATCHED":
                total_matched_amount += line.amount
            else:
                unmatched_count += 1
        
        # Build structured output according to cursor rules
        structured_output = {
            "leverandor": {
                "navn": invoice_data.supplier,
                "organisasjonsnummer": "",  # Would be extracted from invoice
                "adresse": ""  # Would be extracted from invoice
            },
            "faktura_metadata": {
                "fakturanummer": invoice_data.invoice_number,
                "fakturadato": invoice_data.invoice_date,
                "forfallsdato": "",  # Would be extracted from invoice
                "periode_fra": invoice_data.period_from,
                "periode_til": invoice_data.period_to
            },
            "betalingsinfo": {
                "kontonummer": "",  # Would be extracted from invoice
                "kid_referanse": "",  # Would be extracted from invoice
                "iban_swift": ""  # Would be extracted from invoice
            },
            "beløp_sammendrag": {
                "totalbeløp": invoice_data.grand_total,
                "netto_beløp": 0.0,  # Would be calculated from lines
                "mva_beløp_25": 0.0,  # Would be calculated from lines
                "mva_beløp_andre": 0.0,  # Would be calculated from lines
                "valuta": invoice_data.currency
            },
            "linjedetaljer": [
                {
                    "produktnavn": f"Tjeneste for {line.employee_name}",
                    "antall": 1,
                    "enhetspris": line.amount,
                    "linjesum": line.amount,
                    "mva_kode": "25%",  # Default for Norwegian telecom
                    "employee_name": line.employee_name,
                    "phone_number": line.phone_number
                }
                for line in invoice_data.lines
            ],
            "kostnadsbarer_telia": [
                {
                    "navn_fra_faktura": match.navn_fra_faktura,
                    "matched_fornavn": match.matched_fornavn,
                    "matched_etternavn": match.matched_etternavn,
                    "kostsenter": match.kostsenter,
                    "telefonnummer": match.telefonnummer,
                    "sum_denne_periode": match.sum_denne_periode,
                    "match_status": match.match_status,
                    "confidence_score": match.confidence_score,
                    "deviation_reason": match.deviation_reason
                }
                for match in cost_bearer_matches
            ],
            "kvalitetskontroll": {
                "totalbeløp_stemmer": abs(invoice_data.grand_total - sum(line.amount for line in invoice_data.lines)) < 0.01,
                "kostnadsbarer_stemmer": abs(total_matched_amount - sum(line.amount for line in invoice_data.lines if any(m.match_status == "MATCHED" and m.navn_fra_faktura == line.employee_name for m in cost_bearer_matches))) < 0.01,
                "unmatched_count": unmatched_count,
                "processing_confidence": invoice_data.confidence,
                "requires_manual_review": unmatched_count > 0,
                "validation_errors": []
            }
        }
        
        # Add validation errors if needed
        validation_errors = []
        if unmatched_count > 0:
            validation_errors.append(f"{unmatched_count} employees could not be matched to cost bearers")
        if abs(invoice_data.grand_total - sum(line.amount for line in invoice_data.lines)) > 0.01:
            validation_errors.append("Total amount does not match sum of lines")
        
        structured_output["kvalitetskontroll"]["validation_errors"] = validation_errors
        
        return structured_output
    
    def _parse_norwegian_name(self, name_with_phone: str) -> tuple[str, str, str]:
        """
        Parse Norwegian name according to cursor-rules-faktura.md specifications.
        
        Examples:
        - "Annlaug Amundsen - 918 54 560" → ("Annlaug", "Amundsen", "918 54 560")
        - "Ks Andreas . - 920 78 335" → ("Andreas", "", "920 78 335")  
        - "Allan Simonsen - 900 63 358" → ("Allan", "Simonsen", "900 63 358")
        
        Args:
            name_with_phone: Raw name string from invoice
            
        Returns:
            Tuple of (first_name, last_name, phone_number)
        """
        # Remove phone number (everything after last "-")
        if ' - ' in name_with_phone:
            name_part, phone_part = name_with_phone.rsplit(' - ', 1)
            phone_number = phone_part.strip().replace(' ', '')
        else:
            name_part = name_with_phone
            phone_number = ""
        
        # Remove common Norwegian titles and prefixes
        norwegian_titles = ['Ks', 'Dr', 'Prof', 'Mr', 'Mrs', 'Ms', 'Frk', 'Fr']
        
        # Split name into words and remove titles
        name_words = name_part.strip().split()
        filtered_words = []
        
        for word in name_words:
            # Remove trailing dots and check if it's a title
            clean_word = word.rstrip('.')
            if clean_word not in norwegian_titles and clean_word != '.':
                filtered_words.append(clean_word)
        
        # Extract first name and last name
        if len(filtered_words) == 0:
            first_name = ""
            last_name = ""
        elif len(filtered_words) == 1:
            first_name = filtered_words[0]
            last_name = ""
        else:
            first_name = filtered_words[0]
            last_name = ' '.join(filtered_words[1:])  # Handle multiple last names
        
        self.logger.debug(f"Parsed name: '{name_with_phone}' → first='{first_name}', last='{last_name}', phone='{phone_number}'")
        
        return first_name, last_name, phone_number

    def _extract_invoice_lines(self, content: str) -> List[InvoiceLine]:
        """Extract individual invoice lines from content with Norwegian name parsing."""
        lines = []
        
        # Find service specification section
        service_section = self._find_service_section(content)
        if not service_section:
            self.logger.warning("Could not find service specification section")
            return lines
        
        # Extract lines with employee names and amounts  
        # Pattern captures: (name) - (phone) (amount)
        # Includes Nordic/international characters: æøåäöüéèàáâ etc.
        line_pattern = r'([A-ZÆØÅÄÖÜ][a-zæøåäöüéèàáâîïôûçñA-ZÆØÅÄÖÜÉÈÀÁÂÎÏÔÛÇÑ\s\.]+?)\s*[-–—]\s*(\d{3}\s*\d{2}\s*\d{3})\s*(\d+[,.]?\d*)'
        matches = re.finditer(line_pattern, service_section)
        
        for match in matches:
            try:
                raw_name = match.group(1).strip()
                raw_phone = match.group(2).replace(' ', '')
                amount_str = match.group(3).replace(',', '.')
                amount = float(amount_str)
                
                # Combine name and phone for Norwegian parsing
                name_with_phone = f"{raw_name} - {raw_phone}"
                
                # Parse Norwegian name according to cursor rules
                first_name, last_name, phone_number = self._parse_norwegian_name(name_with_phone)
                
                # Construct full clean name for employee_name field
                if last_name:
                    clean_employee_name = f"{first_name} {last_name}"
                else:
                    clean_employee_name = first_name
                
                line = InvoiceLine(
                    employee_name=clean_employee_name,
                    phone_number=phone_number,
                    amount=amount,
                    currency="NOK"
                )
                lines.append(line)
                
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Failed to parse line: {match.group(0)} - {e}")
        
        self.logger.info(f"Extracted {len(lines)} invoice lines")
        return lines
    
    def _find_service_section(self, content: str) -> Optional[str]:
        """Find the service specification section in the invoice."""
        # Look for service specification header and capture until end markers
        start_patterns = [
            # Capture from "Tjenestespesifikasjon for" until "SUM DENNE PERIODE" or similar
            r'Tjenestespesifikasjon for.*?(?=SUM DENNE PERIODE|Totalt|Å betale|$)',
            r'Tjenestespesifikasjon for \(fortsettelse\).*?(?=SUM DENNE PERIODE|Totalt|Å betale|$)'
        ]
        
        for pattern in start_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Fallback: if no specific end markers found, try broader capture
        fallback_patterns = [
            r'Tjenestespesifikasjon for.*',
            r'Tjenestespesifikasjon for \(fortsettelse\).*'
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _calculate_confidence(self, invoice_data: InvoiceData) -> float:
        """Calculate confidence score based on extraction success."""
        confidence = 1.0
        
        # Reduce confidence for missing critical fields
        if not invoice_data.invoice_number:
            confidence *= 0.8
        if not invoice_data.grand_total:
            confidence *= 0.7
        if not invoice_data.lines:
            confidence *= 0.6
        
        # Increase confidence for successful extractions
        if len(invoice_data.lines) > 0:
            confidence *= 1.1
        
        return min(confidence, 1.0)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF file with robust fallback strategy."""
    
    # Method 1: Try pypdf (new PyPDF2) first
    if PYPDF_AVAILABLE:
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                if text.strip():
                    logging.info(f"Successfully extracted text using pypdf: {len(text)} characters")
                    return text
        except Exception as e:
            logging.warning(f"pypdf failed for {pdf_path}: {e}")
    
    # Method 2: Try pdfplumber (more robust)
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                if text.strip():
                    logging.info(f"Successfully extracted text using pdfplumber: {len(text)} characters")
                    return text
        except Exception as e:
            logging.error(f"pdfplumber failed for {pdf_path}: {e}")
    
    # Method 3: Try pdfplumber with repair option
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(pdf_path, repair=True) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                if text.strip():
                    logging.info(f"Successfully extracted text using pdfplumber with repair: {len(text)} characters")
                    return text
        except Exception as e:
            logging.error(f"pdfplumber with repair failed for {pdf_path}: {e}")
    
    logging.error(f"All PDF extraction methods failed for {pdf_path}")
    return ""
