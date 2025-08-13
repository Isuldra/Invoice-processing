"""
Telia Invoice Parser

This module provides a comprehensive parser for Telia invoices that extracts:
- Employee data and "SUM DENNE PERIODE" amounts
- Invoice period and total from first page
- Cost center lookups from Bok2.xlsx
- Outputs both JSON and CSV formats
"""

import re
import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
from pdf2image import convert_from_path
from PIL import Image

# Import OCR engines with fallback
try:
    from ..ocr.engines import (
        TesseractEngine, 
        EasyOCREngine, 
        EngineConfig,
        TESSERACT_AVAILABLE,
        EASYOCR_AVAILABLE
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.ocr.engines import (
        TesseractEngine, 
        EasyOCREngine, 
        EngineConfig,
        TESSERACT_AVAILABLE,
        EASYOCR_AVAILABLE
    )

logger = logging.getLogger(__name__)


@dataclass
class InvoiceLine:
    """Represents a single line item from the invoice."""
    employee_name: str
    msisdn: str
    sum_this_period: float
    currency: str = "NOK"
    cost_center: Optional[str] = None
    department: Optional[str] = None
    source_page: int = 0


@dataclass
class InvoiceData:
    """Represents the complete invoice data."""
    supplier: str = "TELIA COMPANY AB"
    invoice_number: str = ""
    period_from: str = ""
    period_to: str = ""
    currency: str = "NOK"
    grand_total: float = 0.0
    lines: List[InvoiceLine] = None
    
    def __post_init__(self):
        if self.lines is None:
            self.lines = []
    
    def get_totals(self) -> Dict[str, Any]:
        """Calculate totals from the invoice lines."""
        sum_of_lines = sum(line.sum_this_period for line in self.lines)
        diff_vs_grand_total = round(self.grand_total - sum_of_lines, 2)
        
        return {
            "lines_count": len(self.lines),
            "sum_of_lines": sum_of_lines,
            "diff_vs_grand_total": diff_vs_grand_total
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output."""
        totals = self.get_totals()
        
        return {
            "invoice": {
                "supplier": self.supplier,
                "invoice_number": self.invoice_number,
                "period": {
                    "from": self.period_from,
                    "to": self.period_to
                },
                "currency": self.currency,
                "grand_total": self.grand_total
            },
            "lines": [asdict(line) for line in self.lines],
            "totals": totals
        }


class TeliaParser:
    """
    Parser for Telia invoices with OCR extraction and cost center lookup.
    """
    
    def __init__(self, bok2_path: str = "examples/Bok2 1.xlsx"):
        """
        Initialize the Telia parser.
        
        Args:
            bok2_path: Path to the Bok2.xlsx file for cost center lookups
        """
        self.bok2_path = bok2_path
        self.cost_center_lookup = {}
        self.name_lookup = {}
        
        # Initialize OCR engines
        self.engines = []
        self._initialize_ocr_engines()
        
        # Load cost center data
        self._load_cost_center_data()
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _initialize_ocr_engines(self):
        """Initialize available OCR engines."""
        if TESSERACT_AVAILABLE:
            tesseract_config = EngineConfig(
                name="tesseract_primary",
                enabled=True,
                priority=1,
                confidence_threshold=0.5
            )
            tesseract_engine = TesseractEngine(tesseract_config)
            if tesseract_engine.initialize():
                self.engines.append(tesseract_engine)
                logger.info("Tesseract engine initialized")
        
        if EASYOCR_AVAILABLE:
            easyocr_config = EngineConfig(
                name="easyocr_secondary",
                enabled=True,
                priority=2,
                confidence_threshold=0.5
            )
            easyocr_engine = EasyOCREngine(easyocr_config)
            if easyocr_engine.initialize():
                self.engines.append(easyocr_engine)
                logger.info("EasyOCR engine initialized")
        
        if not self.engines:
            raise RuntimeError("No OCR engines available")
    
    def _load_cost_center_data(self):
        """Load cost center data from Bok2.xlsx."""
        try:
            # Try to read the sheet (try different possible names)
            sheet_names = ["bok2", "Ark1", "Sheet1"]
            df = None
            
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(self.bok2_path, sheet_name=sheet_name)
                    logger.info(f"Successfully loaded sheet: {sheet_name}")
                    break
                except:
                    continue
            
            if df is None:
                # If no specific sheet found, try the first sheet
                df = pd.read_excel(self.bok2_path, sheet_name=0)
                logger.info("Loaded first sheet (default)")
            
            # Determine column names (case-insensitive)
            columns = [col.lower() for col in df.columns]
            
            # Find relevant columns
            name_col = None
            msisdn_col = None
            cost_center_col = None
            department_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if 'name' in col_lower or 'navn' in col_lower or 'fornavn' in col_lower or 'etternavn' in col_lower:
                    name_col = col
                elif 'msisdn' in col_lower or 'telefon' in col_lower or 'nummer' in col_lower:
                    msisdn_col = col
                elif 'cost' in col_lower or 'kostnadssted' in col_lower or 'kostsenter' in col_lower:
                    cost_center_col = col
                elif 'department' in col_lower or 'avdeling' in col_lower:
                    department_col = col
            
            # Special handling for Norwegian column structure
            if 'Fornavn' in df.columns and 'Etternavn' in df.columns:
                # Combine first and last name
                df['Full_Name'] = df['Fornavn'].astype(str) + ' ' + df['Etternavn'].astype(str)
                name_col = 'Full_Name'
                logger.info("Combined Fornavn and Etternavn into Full_Name")
            
            if 'Kostsenter' in df.columns:
                cost_center_col = 'Kostsenter'
                logger.info("Found Kostsenter column")
            
            if not name_col:
                logger.warning(f"Could not find name columns in {self.bok2_path}")
                logger.info(f"Available columns: {list(df.columns)}")
                return
            
            # Note: MSISDN column is optional - we can do name-only lookups
            if not msisdn_col:
                logger.info("No MSISDN column found - will use name-only lookups")
            
            # Build lookup tables
            for _, row in df.iterrows():
                name_val = row[name_col] if name_col is not None else ""
                msisdn_val = row[msisdn_col] if msisdn_col is not None else ""
                cost_center_val = row[cost_center_col] if cost_center_col is not None else ""
                department_val = row[department_col] if department_col is not None else ""
                
                name = str(name_val).strip() if pd.notna(name_val) else ""
                msisdn = str(msisdn_val).strip() if pd.notna(msisdn_val) else ""
                cost_center = str(cost_center_val).strip() if pd.notna(cost_center_val) else ""
                department = str(department_val).strip() if pd.notna(department_val) else ""
                
                if name:
                    # Normalize name for lookup
                    normalized_name = name.lower().strip()
                    self.name_lookup[normalized_name] = {
                        'cost_center': cost_center,
                        'department': department
                    }
                    
                    # If we have MSISDN, also add to MSISDN lookup
                    if msisdn:
                        normalized_msisdn = re.sub(r'[^\d]', '', msisdn)
                        if normalized_msisdn:
                            self.cost_center_lookup[normalized_msisdn] = {
                                'cost_center': cost_center,
                                'department': department
                            }
            
            logger.info(f"Loaded {len(self.cost_center_lookup)} MSISDN lookups and {len(self.name_lookup)} name lookups")
            
        except Exception as e:
            logger.error(f"Error loading cost center data: {e}")
    
    def _compile_patterns(self):
        """Compile regex patterns for text extraction."""
        # Pattern for employee/phone number section
        self.employee_pattern = re.compile(
            r'^Tjenestespesifikasjon for\s+(?P<name>.+?)\s*[-–]\s*(?P<msisdn>(?:\+?47)?\s?\d[\d\s]{6,})',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern for "SUM DENNE PERIODE"
        self.sum_pattern = re.compile(
            r'^SUM DENNE PERIODE\s*[:\-]?\s*(?P<amount>-?\d{1,3}(?:[ .]\d{3})*,\d{2})',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern for invoice period
        self.period_pattern = re.compile(
            r'Fakturaperiode\s*[:\-]?\s*(\d{2}\.\d{2}\.\d{4})\s*[–-]\s*(\d{2}\.\d{2}\.\d{4})',
            re.IGNORECASE
        )
        
        # Pattern for invoice total
        self.total_pattern = re.compile(
            r'(?:Å betale|Total|Sum å betale|Fakturabeløp)\s*[:\-]?\s*(?P<total>-?\d{1,3}(?:[ .]\d{3})*,\d{2})',
            re.IGNORECASE
        )
        
        # Pattern for invoice number
        self.invoice_number_pattern = re.compile(
            r'(?:Fakturanummer|Invoice Number|Faktura nr\.?)\s*[:\-]?\s*(\S+)',
            re.IGNORECASE
        )
    
    def _normalize_amount(self, amount_str: str) -> float:
        """Convert Norwegian amount format to float."""
        # Remove spaces
        normalized = amount_str.replace(' ', '')
        
        # Handle Norwegian number format: 1.234,56 or 1 234,56
        # First, check if we have a comma as decimal separator
        if ',' in normalized:
            # Remove dots (thousand separators) and replace comma with dot
            normalized = normalized.replace('.', '').replace(',', '.')
        else:
            # No comma, assume dot is decimal separator
            pass
        
        return float(normalized)
    
    def _normalize_date(self, date_str: str) -> str:
        """Convert DD.MM.YYYY to YYYY-MM-DD."""
        try:
            date_obj = datetime.strptime(date_str, '%d.%m.%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return date_str
    
    def _normalize_msisdn(self, msisdn: str) -> str:
        """Normalize MSISDN to digits only."""
        return re.sub(r'[^\d]', '', msisdn)
    
    def _lookup_cost_center(self, msisdn: str, name: str) -> Tuple[Optional[str], Optional[str]]:
        """Look up cost center and department for given MSISDN or name."""
        # First try MSISDN lookup
        normalized_msisdn = self._normalize_msisdn(msisdn)
        if normalized_msisdn in self.cost_center_lookup:
            data = self.cost_center_lookup[normalized_msisdn]
            return data['cost_center'], data['department']
        
        # Then try name lookup
        normalized_name = name.lower().strip()
        if normalized_name in self.name_lookup:
            data = self.name_lookup[normalized_name]
            return data['cost_center'], data['department']
        
        return None, None
    
    def _extract_text_from_pdf(self, pdf_path: str) -> List[str]:
        """Extract text from PDF using OCR engines."""
        all_texts = []
        
        try:
            # Set Poppler path for Windows
            poppler_path = r"C:\Users\andre\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path)
            logger.info(f"Converted PDF to {len(images)} images")
            
            for page_num, image in enumerate(images):
                page_texts = []
                
                for engine in self.engines:
                    try:
                        results = engine.extract_text_from_image(image)
                        for result in results:
                            if result.text.strip():
                                page_texts.append(result.text.strip())
                    except Exception as e:
                        logger.warning(f"Error with {engine.name} on page {page_num}: {e}")
                
                # Combine texts from all engines for this page
                if page_texts:
                    combined_text = '\n'.join(page_texts)
                    all_texts.append(combined_text)
                    logger.debug(f"Page {page_num + 1}: {len(combined_text)} characters")
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
        
        return all_texts
    
    def parse_invoice(self, pdf_path: str) -> InvoiceData:
        """
        Parse a Telia invoice PDF.
        
        Args:
            pdf_path: Path to the Telia PDF invoice
            
        Returns:
            InvoiceData object with extracted information
        """
        logger.info(f"Parsing Telia invoice: {pdf_path}")
        
        # Extract text from PDF
        page_texts = self._extract_text_from_pdf(pdf_path)
        if not page_texts:
            raise ValueError("No text extracted from PDF")
        
        # Initialize invoice data
        invoice_data = InvoiceData()
        
        # Extract invoice-level information from first page
        first_page_text = page_texts[0]
        
        # Extract invoice number
        invoice_match = self.invoice_number_pattern.search(first_page_text)
        if invoice_match:
            invoice_data.invoice_number = invoice_match.group(1)
        
        # Extract period
        period_match = self.period_pattern.search(first_page_text)
        if period_match:
            invoice_data.period_from = self._normalize_date(period_match.group(1))
            invoice_data.period_to = self._normalize_date(period_match.group(2))
        
        # Extract total
        total_match = self.total_pattern.search(first_page_text)
        if total_match:
            invoice_data.grand_total = self._normalize_amount(total_match.group('total'))
        
        # Extract employee data from all pages
        for page_num, page_text in enumerate(page_texts):
            self._extract_employee_data(page_text, page_num + 1, invoice_data)
        
        logger.info(f"Extracted {len(invoice_data.lines)} employee lines")
        return invoice_data
    
    def _extract_employee_data(self, page_text: str, page_num: int, invoice_data: InvoiceData):
        """Extract employee data from a single page."""
        # Find all employee sections
        employee_matches = list(self.employee_pattern.finditer(page_text))
        
        for match in employee_matches:
            name = match.group('name').strip()
            msisdn = match.group('msisdn').strip()
            
            # Find the end of this employee section (next employee or end of text)
            start_pos = match.end()
            if employee_matches.index(match) + 1 < len(employee_matches):
                end_pos = employee_matches[employee_matches.index(match) + 1].start()
            else:
                end_pos = len(page_text)
            
            employee_section = page_text[start_pos:end_pos]
            
            # Find "SUM DENNE PERIODE" in this section
            sum_matches = list(self.sum_pattern.finditer(employee_section))
            if sum_matches:
                # Take the last occurrence if multiple
                last_sum_match = sum_matches[-1]
                amount_str = last_sum_match.group('amount')
                amount = self._normalize_amount(amount_str)
                
                # Look up cost center
                cost_center, department = self._lookup_cost_center(msisdn, name)
                
                # Create invoice line
                line = InvoiceLine(
                    employee_name=name,
                    msisdn=self._normalize_msisdn(msisdn),
                    sum_this_period=amount,
                    cost_center=cost_center,
                    department=department,
                    source_page=page_num
                )
                
                invoice_data.lines.append(line)
                logger.debug(f"Found employee: {name} ({msisdn}) - {amount} NOK")
    
    def save_json(self, invoice_data: InvoiceData, output_path: str = None):
        """Save invoice data as JSON."""
        if output_path is None:
            invoice_num = invoice_data.invoice_number or "unknown"
            output_path = f"output/telia_invoice_{invoice_num}.json"
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(invoice_data.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved JSON output to: {output_path}")
        return output_path
    
    def save_csv(self, invoice_data: InvoiceData, output_path: str = None):
        """Save invoice data as CSV."""
        if output_path is None:
            invoice_num = invoice_data.invoice_number or "unknown"
            output_path = f"output/telia_invoice_{invoice_num}.csv"
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Write header
            writer.writerow([
                'Employee', 'MSISDN', 'SumDennePeriode', 'Currency', 
                'CostCenter', 'Department', 'SourcePage'
            ])
            
            # Write data
            for line in invoice_data.lines:
                writer.writerow([
                    line.employee_name,
                    line.msisdn,
                    line.sum_this_period,
                    line.currency,
                    line.cost_center or '',
                    line.department or '',
                    line.source_page
                ])
        
        logger.info(f"Saved CSV output to: {output_path}")
        return output_path
    
    def process_invoice(self, pdf_path: str, output_dir: str = "output") -> Dict[str, str]:
        """
        Process a Telia invoice and save both JSON and CSV outputs.
        
        Args:
            pdf_path: Path to the Telia PDF invoice
            output_dir: Directory to save output files
            
        Returns:
            Dictionary with paths to output files
        """
        # Parse the invoice
        invoice_data = self.parse_invoice(pdf_path)
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate output filenames
        invoice_num = invoice_data.invoice_number or "unknown"
        json_path = f"{output_dir}/telia_invoice_{invoice_num}.json"
        csv_path = f"{output_dir}/telia_invoice_{invoice_num}.csv"
        
        # Save outputs
        self.save_json(invoice_data, json_path)
        self.save_csv(invoice_data, csv_path)
        
        return {
            'json': json_path,
            'csv': csv_path,
            'invoice_data': invoice_data
        } 