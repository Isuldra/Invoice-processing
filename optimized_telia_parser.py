"""
Optimized Telia Invoice Parser using latest pypdf and pdfplumber features.

This implementation showcases:
1. pypdf's new extraction_mode="layout" and visitor functions
2. pdfplumber's repair functionality and visual debugging
3. Enhanced error handling and fallback strategies
4. Performance optimizations and monitoring
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
import traceback
import regex as re  # More performant than standard re module

# PDF processing libraries with conditional imports
try:
    from pypdf import PdfReader
    from pypdf.generic import Destination
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper  # LibYAML for performance
except ImportError:
    from yaml import Loader, Dumper

# Performance monitoring
from functools import wraps
from contextlib import contextmanager
import psutil
import os

logger = logging.getLogger(__name__)


@dataclass
class InvoiceData:
    """Enhanced invoice data structure with validation."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    employee_names: List[str] = None
    raw_text: Optional[str] = None
    extraction_method: Optional[str] = None
    processing_time: Optional[float] = None
    page_count: Optional[int] = None
    
    def __post_init__(self):
        if self.employee_names is None:
            self.employee_names = []


class PerformanceMonitor:
    """Performance monitoring and profiling utilities."""
    
    @staticmethod
    @contextmanager
    def monitor_memory():
        """Monitor memory usage during execution."""
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        yield
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"Memory usage: {mem_before:.2f}MB -> {mem_after:.2f}MB (Δ{mem_after - mem_before:.2f}MB)")
    
    @staticmethod
    def benchmark(func):
        """Decorator to benchmark function execution time."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                logger.info(f"{func.__name__} executed in {end_time - start_time:.4f} seconds")
        return wrapper


class PyPDFLayoutExtractor:
    """Advanced pypdf text extraction using layout-preserving methods."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('pypdf', {})
        self.extraction_mode = self.config.get('extraction_mode', 'layout')
        self.use_visitor_functions = self.config.get('use_visitor_functions', True)
    
    @PerformanceMonitor.benchmark
    def extract_text_with_layout(self, pdf_path: Union[str, Path]) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text using pypdf's new layout-preserving extraction.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                
                metadata = {
                    'page_count': len(reader.pages),
                    'is_encrypted': reader.is_encrypted,
                    'extraction_method': 'pypdf_layout'
                }
                
                # Handle encrypted PDFs
                if reader.is_encrypted:
                    try:
                        reader.decrypt("")  # Try empty password first
                    except Exception:
                        logger.warning(f"Could not decrypt PDF: {pdf_path}")
                        return "", metadata
                
                text_parts = []
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        if self.use_visitor_functions:
                            # Use visitor function for better text extraction
                            text = self._extract_with_visitor(page)
                        else:
                            # Use layout mode for better formatting
                            text = page.extract_text(extraction_mode=self.extraction_mode)
                        
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
                        
                    except Exception as e:
                        logger.warning(f"Error extracting page {page_num + 1}: {e}")
                        continue
                
                full_text = "\n\n".join(text_parts)
                return full_text, metadata
                
        except Exception as e:
            logger.error(f"pypdf extraction failed for {pdf_path}: {e}")
            return "", {'extraction_method': 'pypdf_failed', 'error': str(e)}
    
    def _extract_with_visitor(self, page) -> str:
        """Extract text using visitor functions for better control."""
        text_parts = []
        
        def visitor_body(text, cm, tm, font_dict, font_size):
            """Custom visitor function to process text elements."""
            # Filter out very small text (likely artifacts)
            if font_size and font_size < 6:
                return
            
            # Preserve spacing based on transformation matrix
            if tm and len(tm) >= 6:
                y_position = tm[5]  # Y coordinate
                # Add line breaks for significant Y position changes
                if text_parts and hasattr(visitor_body, 'last_y'):
                    if abs(y_position - visitor_body.last_y) > font_size * 1.2:
                        text_parts.append('\n')
                
                visitor_body.last_y = y_position
            
            text_parts.append(text)
        
        page.extract_text(visitor_text=visitor_body)
        return ''.join(text_parts)


class PDFPlumberProcessor:
    """Enhanced pdfplumber processing with repair and debugging capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('pdfplumber', {})
        self.use_repair = self.config.get('use_repair', True)
        self.repair_strategy = self.config.get('repair_strategy', 'fix_missing_endstream')
        self.debug_visual = self.config.get('debug_visual', False)
        self.table_settings = self.config.get('table_settings', {})
    
    @PerformanceMonitor.benchmark
    def extract_text_and_tables(self, pdf_path: Union[str, Path]) -> Tuple[str, List[Dict], Dict[str, Any]]:
        """
        Extract text and tables using pdfplumber with repair functionality.
        
        Returns:
            Tuple of (text, tables, metadata)
        """
        try:
            # Handle PDF repair if needed
            pdf_kwargs = {}
            if self.use_repair:
                pdf_kwargs['repair'] = True
                pdf_kwargs['strict_metadata'] = False
            
            with pdfplumber.open(pdf_path, **pdf_kwargs) as pdf:
                metadata = {
                    'page_count': len(pdf.pages),
                    'extraction_method': 'pdfplumber',
                    'repaired': self.use_repair
                }
                
                text_parts = []
                all_tables = []
                
                for page_num, page in enumerate(pdf.pages):
                    try:
                        # Extract text
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
                        
                        # Extract tables with custom settings
                        tables = page.extract_tables(
                            table_settings=self.table_settings
                        )
                        
                        for table_idx, table in enumerate(tables):
                            all_tables.append({
                                'page': page_num + 1,
                                'table_index': table_idx,
                                'data': table
                            })
                        
                        # Visual debugging if enabled
                        if self.debug_visual:
                            self._debug_page_visual(page, page_num, pdf_path)
                            
                    except Exception as e:
                        logger.warning(f"Error processing page {page_num + 1}: {e}")
                        continue
                
                full_text = "\n\n".join(text_parts)
                return full_text, all_tables, metadata
                
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for {pdf_path}: {e}")
            return "", [], {'extraction_method': 'pdfplumber_failed', 'error': str(e)}
    
    def _debug_page_visual(self, page, page_num: int, pdf_path: Path):
        """Generate visual debugging output for troubleshooting."""
        try:
            # Create debug output directory
            debug_dir = Path(pdf_path).parent / "debug_output"
            debug_dir.mkdir(exist_ok=True)
            
            # Save page as image with text boxes highlighted
            im = page.to_image(resolution=150)
            im.debug_tablefinder().save(
                debug_dir / f"{Path(pdf_path).stem}_page_{page_num + 1}_debug.png"
            )
            
        except Exception as e:
            logger.warning(f"Debug visual generation failed for page {page_num + 1}: {e}")


class OptimizedTeliaParser:
    """
    Optimized Telia invoice parser using latest library features.
    
    Features:
    - pypdf layout extraction with visitor functions
    - pdfplumber repair functionality and table extraction
    - Performance monitoring and benchmarking
    - Enhanced error handling with multiple fallback strategies
    - Optimized regex patterns using the regex module
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize parser with configuration."""
        self.config = self._load_config(config_path)
        
        # Initialize extractors
        self.pypdf_extractor = PyPDFLayoutExtractor(self.config['pdf_extraction'])
        self.pdfplumber_processor = PDFPlumberProcessor(self.config['pdf_extraction'])
        
        # Compile regex patterns for performance
        self._compile_patterns()
        
        # Setup logging
        self._setup_logging()
    
    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
        """Load configuration with LibYAML optimization."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                # Use LibYAML's C loader for better performance
                config = yaml.load(file, Loader=Loader)
                logger.info("Configuration loaded successfully with LibYAML")
                return config
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Fallback default configuration."""
        return {
            'pdf_extraction': {
                'pypdf': {'extraction_mode': 'layout', 'use_visitor_functions': True},
                'pdfplumber': {'use_repair': True, 'debug_visual': False}
            },
            'telia_patterns': {
                'invoice_number': {
                    'pattern': r'(?:Invoice|Faktura)\s*(?:Number|Nr\.?)\s*[:]*\s*([A-Z]{3}\d{10})',
                    'flags': ['IGNORECASE', 'MULTILINE']
                }
            }
        }
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        self.compiled_patterns = {}
        patterns_config = self.config.get('telia_patterns', {})
        
        for pattern_name, pattern_config in patterns_config.items():
            try:
                pattern = pattern_config['pattern']
                flags = pattern_config.get('flags', [])
                
                # Convert string flags to regex constants
                regex_flags = 0
                for flag in flags:
                    regex_flags |= getattr(re, flag, 0)
                
                if 'patterns' in pattern_config:  # Multiple patterns
                    self.compiled_patterns[pattern_name] = [
                        re.compile(p, regex_flags) for p in pattern_config['patterns']
                    ]
                else:  # Single pattern
                    self.compiled_patterns[pattern_name] = re.compile(pattern, regex_flags)
                    
            except Exception as e:
                logger.warning(f"Could not compile pattern {pattern_name}: {e}")
    
    def _setup_logging(self):
        """Setup optimized logging configuration."""
        log_config = self.config.get('logging', {})
        
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format=log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_config.get('file', 'telia_parser.log')),
                logging.StreamHandler()
            ]
        )
    
    @PerformanceMonitor.benchmark
    def parse_invoice(self, pdf_path: Union[str, Path]) -> InvoiceData:
        """
        Parse Telia invoice with optimized extraction methods.
        
        Args:
            pdf_path: Path to PDF invoice
            
        Returns:
            InvoiceData object with extracted information
        """
        pdf_path = Path(pdf_path)
        start_time = time.perf_counter()
        
        logger.info(f"Starting invoice parsing: {pdf_path}")
        
        with PerformanceMonitor.monitor_memory():
            # Try multiple extraction methods in order of preference
            extraction_methods = [
                ('pypdf_layout', self._extract_with_pypdf),
                ('pdfplumber', self._extract_with_pdfplumber),
                ('fallback', self._extract_fallback)
            ]
            
            text = ""
            metadata = {}
            tables = []
            
            for method_name, extraction_func in extraction_methods:
                try:
                    logger.info(f"Attempting extraction with {method_name}")
                    text, tables, metadata = extraction_func(pdf_path)
                    
                    if text and len(text.strip()) > 100:  # Minimum viable text length
                        metadata['extraction_method'] = method_name
                        logger.info(f"Successfully extracted text using {method_name}")
                        break
                    else:
                        logger.warning(f"{method_name} produced insufficient text, trying next method")
                        
                except Exception as e:
                    logger.warning(f"{method_name} extraction failed: {e}")
                    continue
            
            # Parse extracted text
            invoice_data = self._parse_text(text, metadata, tables)
            invoice_data.processing_time = time.perf_counter() - start_time
            
            logger.info(f"Invoice parsing completed in {invoice_data.processing_time:.4f} seconds")
            return invoice_data
    
    def _extract_with_pypdf(self, pdf_path: Path) -> Tuple[str, List[Dict], Dict[str, Any]]:
        """Extract using pypdf with layout preservation."""
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf not available")
        
        text, metadata = self.pypdf_extractor.extract_text_with_layout(pdf_path)
        return text, [], metadata  # pypdf doesn't extract tables
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> Tuple[str, List[Dict], Dict[str, Any]]:
        """Extract using pdfplumber with repair functionality."""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not available")
        
        return self.pdfplumber_processor.extract_text_and_tables(pdf_path)
    
    def _extract_fallback(self, pdf_path: Path) -> Tuple[str, List[Dict], Dict[str, Any]]:
        """Fallback extraction method (basic pypdf without layout)."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                text_parts = []
                
                for page in reader.pages:
                    text_parts.append(page.extract_text())
                
                text = "\n".join(text_parts)
                metadata = {'extraction_method': 'pypdf_fallback'}
                
                return text, [], metadata
                
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return "", [], {'extraction_method': 'failed', 'error': str(e)}
    
    def _parse_text(self, text: str, metadata: Dict[str, Any], tables: List[Dict]) -> InvoiceData:
        """Parse extracted text using optimized regex patterns."""
        invoice_data = InvoiceData(
            raw_text=text,
            extraction_method=metadata.get('extraction_method'),
            page_count=metadata.get('page_count')
        )
        
        # Extract invoice number
        if 'invoice_number' in self.compiled_patterns:
            pattern = self.compiled_patterns['invoice_number']
            match = pattern.search(text)
            if match:
                invoice_data.invoice_number = match.group(1)
        
        # Extract invoice date (handling multiple patterns)
        if 'invoice_date' in self.compiled_patterns:
            patterns = self.compiled_patterns['invoice_date']
            if isinstance(patterns, list):
                for pattern in patterns:
                    match = pattern.search(text)
                    if match:
                        invoice_data.invoice_date = match.group(1)
                        break
            else:
                match = patterns.search(text)
                if match:
                    invoice_data.invoice_date = match.group(1)
        
        # Extract total amount
        if 'total_amount' in self.compiled_patterns:
            pattern = self.compiled_patterns['total_amount']
            match = pattern.search(text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    invoice_data.total_amount = float(amount_str)
                except ValueError as e:
                    logger.warning(f"Could not parse amount: {match.group(1)} - {e}")
        
        # Extract employee names
        if 'employee_names' in self.compiled_patterns:
            pattern = self.compiled_patterns['employee_names']
            matches = pattern.findall(text)
            invoice_data.employee_names = [match for match in matches if len(match.strip()) > 2]
        
        # Process table data if available
        if tables:
            self._process_table_data(invoice_data, tables)
        
        return invoice_data
    
    def _process_table_data(self, invoice_data: InvoiceData, tables: List[Dict]):
        """Process extracted table data for additional information."""
        for table_info in tables:
            table_data = table_info['data']
            
            # Look for employee names in table data
            for row in table_data:
                for cell in row:
                    if isinstance(cell, str) and len(cell.strip()) > 2:
                        # Check if cell looks like a name (basic heuristic)
                        if re.match(r'^[A-ZÅÄÖ][a-zåäö]+\s+[A-ZÅÄÖ][a-zåäö]+$', cell.strip()):
                            if cell.strip() not in invoice_data.employee_names:
                                invoice_data.employee_names.append(cell.strip())


# Example usage and testing
if __name__ == "__main__":
    # Initialize parser
    parser = OptimizedTeliaParser()
    
    # Example parsing (you would use your actual PDF files)
    # invoice_data = parser.parse_invoice("path/to/telia_invoice.pdf")
    # print(f"Extracted data: {invoice_data}")
    
    print("Optimized Telia Parser initialized successfully!")
    print(f"pypdf available: {PYPDF_AVAILABLE}")
    print(f"pdfplumber available: {PDFPLUMBER_AVAILABLE}")