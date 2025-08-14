"""
Telia Supplier Parser

Text-based parser for Telia invoices without OCR dependency.
"""

import re
import logging
from pathlib import Path
from typing import List, Optional

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


class TeliaParser(BaseSupplierParser):
    """Text-based parser for Telia Norge AS invoices."""
    
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
