"""
Optimized Excel Processing System for Invoice Processing.

Features:
1. Intelligent Excel engine selection (openpyxl, calamine, pyxlsb)
2. Chunked reading for large files
3. Memory-efficient data processing
4. Advanced pandas optimizations
5. Performance monitoring and caching
"""

import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Iterator
import warnings
from functools import lru_cache
import hashlib

import pandas as pd
import numpy as np

# Conditional imports for Excel engines
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import calamine
    CALAMINE_AVAILABLE = True
except ImportError:
    CALAMINE_AVAILABLE = False

try:
    import pyxlsb
    PYXLSB_AVAILABLE = True
except ImportError:
    PYXLSB_AVAILABLE = False

# Performance monitoring
from contextlib import contextmanager
import psutil

logger = logging.getLogger(__name__)


@dataclass
class ExcelFileMetadata:
    """Metadata about an Excel file for optimization decisions."""
    file_path: Path
    file_size_mb: float
    sheet_names: List[str]
    estimated_rows: Optional[int] = None
    file_format: str = "xlsx"  # xlsx, xlsb, xls
    recommended_engine: str = "openpyxl"
    requires_chunking: bool = False
    last_modified: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Determine optimal processing strategy."""
        self.file_format = self._detect_format()
        self.recommended_engine = self._get_optimal_engine()
        self.requires_chunking = self._should_use_chunking()
    
    def _detect_format(self) -> str:
        """Detect Excel file format from extension."""
        suffix = self.file_path.suffix.lower()
        format_map = {
            '.xlsx': 'xlsx',
            '.xlsm': 'xlsx', 
            '.xlsb': 'xlsb',
            '.xls': 'xls'
        }
        return format_map.get(suffix, 'xlsx')
    
    def _get_optimal_engine(self) -> str:
        """Select optimal engine based on file characteristics."""
        # Engine selection logic based on file size and format
        if self.file_format == 'xlsb' and PYXLSB_AVAILABLE:
            return 'pyxlsb'
        elif self.file_format == 'xls':
            return 'xlrd'  # Only option for .xls files
        elif self.file_size_mb > 10 and CALAMINE_AVAILABLE:
            return 'calamine'  # Fastest for large files
        elif OPENPYXL_AVAILABLE:
            return 'openpyxl'  # Default for small-medium files
        else:
            return None  # Use pandas default
    
    def _should_use_chunking(self) -> bool:
        """Determine if chunked reading is beneficial."""
        # Conservative estimate: chunk if > 50MB or estimated > 100k rows
        return (self.file_size_mb > 50 or 
                (self.estimated_rows and self.estimated_rows > 100000))


class ExcelEngineManager:
    """Manages Excel engine selection and optimization."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('excel_processing', {})
        self.engines = self.config.get('engines', {})
        self.chunk_size = self.config.get('chunk_size', 10000)
        self.memory_threshold_mb = self.config.get('memory_threshold_mb', 500)
        self.dtype_optimization = self.config.get('dtype_optimization', True)
        
        # Log available engines
        self._log_available_engines()
    
    def _log_available_engines(self):
        """Log which Excel engines are available."""
        engines = {
            'openpyxl': OPENPYXL_AVAILABLE,
            'calamine': CALAMINE_AVAILABLE,
            'pyxlsb': PYXLSB_AVAILABLE,
        }
        
        available = [name for name, available in engines.items() if available]
        unavailable = [name for name, available in engines.items() if not available]
        
        logger.info(f"Available Excel engines: {available}")
        if unavailable:
            logger.warning(f"Unavailable Excel engines: {unavailable}")
    
    @lru_cache(maxsize=128)
    def analyze_file(self, file_path: Union[str, Path]) -> ExcelFileMetadata:
        """Analyze Excel file and create optimization metadata."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        # Get file size
        file_size_bytes = file_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Get sheet names using openpyxl (lightweight for metadata)
        sheet_names = []
        try:
            if file_path.suffix.lower() in ['.xlsx', '.xlsm'] and OPENPYXL_AVAILABLE:
                wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                sheet_names = wb.sheetnames
                wb.close()
            else:
                # Fallback: use pandas to get sheet names
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    excel_file = pd.ExcelFile(file_path)
                    sheet_names = excel_file.sheet_names
                    excel_file.close()
                    
        except Exception as e:
            logger.warning(f"Could not read sheet names from {file_path}: {e}")
            sheet_names = ['Sheet1']  # Assume default
        
        metadata = ExcelFileMetadata(
            file_path=file_path,
            file_size_mb=file_size_mb,
            sheet_names=sheet_names,
            last_modified=file_path.stat().st_mtime
        )
        
        logger.info(f"Analyzed {file_path}: {file_size_mb:.2f}MB, "
                   f"engine={metadata.recommended_engine}, "
                   f"chunking={metadata.requires_chunking}")
        
        return metadata
    
    def read_excel_optimized(self, 
                           file_path: Union[str, Path], 
                           sheet_name: Optional[str] = None,
                           **kwargs) -> pd.DataFrame:
        """
        Read Excel file with optimal engine and settings.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet to read (None for first sheet)
            **kwargs: Additional pandas.read_excel arguments
            
        Returns:
            DataFrame with optimized dtypes
        """
        metadata = self.analyze_file(file_path)
        
        # Select sheet
        if sheet_name is None:
            sheet_name = metadata.sheet_names[0] if metadata.sheet_names else 0
        
        # Configure engine
        engine = metadata.recommended_engine
        if engine and engine not in kwargs:
            kwargs['engine'] = engine
        
        # Memory monitoring
        process = psutil.Process()
        mem_before = process.memory_info().rss / 1024 / 1024
        
        start_time = time.perf_counter()
        
        try:
            if metadata.requires_chunking:
                # Use chunked reading for large files
                df = self._read_excel_chunked(metadata, sheet_name, **kwargs)
            else:
                # Direct reading for smaller files
                df = pd.read_excel(
                    file_path, 
                    sheet_name=sheet_name,
                    **kwargs
                )
            
            # Optimize data types
            if self.dtype_optimization:
                df = self._optimize_dtypes(df)
            
            # Log performance
            end_time = time.perf_counter()
            mem_after = process.memory_info().rss / 1024 / 1024
            
            logger.info(f"Excel read completed: {end_time - start_time:.2f}s, "
                       f"memory: {mem_before:.1f}→{mem_after:.1f}MB, "
                       f"shape: {df.shape}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to read Excel file {file_path}: {e}")
            # Try fallback method
            return self._read_excel_fallback(file_path, sheet_name, **kwargs)
    
    def _read_excel_chunked(self, 
                           metadata: ExcelFileMetadata, 
                           sheet_name: str,
                           **kwargs) -> pd.DataFrame:
        """Read Excel file in chunks for memory efficiency."""
        logger.info(f"Using chunked reading for {metadata.file_path}")
        
        chunks = []
        chunk_start = 0
        
        while True:
            try:
                # Read chunk
                chunk_kwargs = kwargs.copy()
                chunk_kwargs.update({
                    'skiprows': chunk_start,
                    'nrows': self.chunk_size,
                    'header': 0 if chunk_start == 0 else None
                })
                
                chunk = pd.read_excel(
                    metadata.file_path,
                    sheet_name=sheet_name,
                    **chunk_kwargs
                )
                
                if chunk.empty:
                    break
                
                # Set column names from first chunk
                if chunk_start == 0:
                    column_names = chunk.columns
                else:
                    chunk.columns = column_names
                
                chunks.append(chunk)
                chunk_start += self.chunk_size
                
                logger.debug(f"Read chunk {len(chunks)}: rows {chunk_start}-{chunk_start + len(chunk)}")
                
            except Exception as e:
                logger.warning(f"Error reading chunk starting at row {chunk_start}: {e}")
                break
        
        if not chunks:
            raise ValueError("No data could be read from file")
        
        # Combine chunks
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Combined {len(chunks)} chunks into DataFrame with shape {df.shape}")
        
        return df
    
    def _read_excel_fallback(self, 
                            file_path: Union[str, Path], 
                            sheet_name: str, 
                            **kwargs) -> pd.DataFrame:
        """Fallback Excel reading method."""
        logger.warning(f"Using fallback method for {file_path}")
        
        # Remove engine specification and try default
        fallback_kwargs = {k: v for k, v in kwargs.items() if k != 'engine'}
        
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, **fallback_kwargs)
        except Exception as e:
            logger.error(f"Fallback Excel reading failed: {e}")
            raise
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame data types for memory efficiency."""
        logger.debug("Optimizing DataFrame data types")
        
        original_memory = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        
        # Optimize numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                numeric_series = pd.to_numeric(df[col], errors='ignore', downcast='integer')
                if not numeric_series.dtype == 'object':
                    df[col] = numeric_series
                    continue
                
                # Try to convert to category if low cardinality
                if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique
                    df[col] = df[col].astype('category')
            
            elif df[col].dtype in ['int64', 'int32']:
                # Downcast integers
                df[col] = pd.to_numeric(df[col], downcast='integer')
            
            elif df[col].dtype in ['float64', 'float32']:
                # Downcast floats
                df[col] = pd.to_numeric(df[col], downcast='float')
        
        optimized_memory = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        reduction = (1 - optimized_memory / original_memory) * 100
        
        logger.info(f"Memory optimization: {original_memory:.1f}MB → {optimized_memory:.1f}MB "
                   f"({reduction:.1f}% reduction)")
        
        return df


class CostBearerMatcher:
    """Optimized employee name matching against Excel cost bearer database."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('name_matching', {})
        self.algorithm = self.config.get('algorithm', 'rapidfuzz')
        self.threshold = self.config.get('threshold', 85)
        self.preprocessing = self.config.get('preprocessing', {})
        
        # Initialize fuzzy matching library
        self._init_fuzzy_matcher()
        
        # Caching for processed names
        self._name_cache = {}
    
    def _init_fuzzy_matcher(self):
        """Initialize the optimal fuzzy matching library."""
        if self.algorithm == 'rapidfuzz':
            try:
                from rapidfuzz import fuzz, process
                self.fuzz = fuzz
                self.process = process
                logger.info("Using rapidfuzz for name matching (fastest)")
            except ImportError:
                logger.warning("rapidfuzz not available, falling back to fuzzywuzzy")
                self.algorithm = 'fuzzywuzzy'
        
        if self.algorithm == 'fuzzywuzzy':
            try:
                from fuzzywuzzy import fuzz, process
                self.fuzz = fuzz
                self.process = process
                logger.info("Using fuzzywuzzy for name matching")
            except ImportError:
                logger.error("No fuzzy matching library available")
                raise ImportError("Install either rapidfuzz or fuzzywuzzy")
    
    @lru_cache(maxsize=1000)
    def preprocess_name(self, name: str) -> str:
        """Preprocess name for better matching accuracy."""
        if not isinstance(name, str):
            return ""
        
        processed = name.strip()
        
        if self.preprocessing.get('normalize_case', True):
            processed = processed.lower()
        
        # Remove titles
        titles = self.preprocessing.get('remove_titles', [])
        for title in titles:
            processed = processed.replace(f"{title.lower()} ", "")
            processed = processed.replace(f"{title.lower()}.", "")
        
        # Remove suffixes
        suffixes = self.preprocessing.get('remove_suffixes', [])
        for suffix in suffixes:
            if processed.endswith(f" {suffix.lower()}"):
                processed = processed[:-len(f" {suffix.lower()}")]
        
        # Normalize whitespace
        processed = " ".join(processed.split())
        
        return processed
    
    def match_employee_names(self, 
                           employee_names: List[str], 
                           cost_bearer_df: pd.DataFrame,
                           name_column: str = 'Name') -> Dict[str, Dict[str, Any]]:
        """
        Match employee names against cost bearer database with optimized fuzzy matching.
        
        Args:
            employee_names: List of employee names to match
            cost_bearer_df: DataFrame with cost bearer information
            name_column: Column name containing employee names
            
        Returns:
            Dictionary mapping employee names to match results
        """
        start_time = time.perf_counter()
        
        # Preprocess cost bearer names
        if name_column not in cost_bearer_df.columns:
            raise ValueError(f"Column '{name_column}' not found in cost bearer DataFrame")
        
        # Create processed name mapping
        cost_bearer_names = cost_bearer_df[name_column].dropna().astype(str).tolist()
        processed_cost_bearers = [self.preprocess_name(name) for name in cost_bearer_names]
        
        # Create lookup dictionary for original names
        name_lookup = dict(zip(processed_cost_bearers, cost_bearer_names))
        
        results = {}
        total_matches = 0
        
        for employee_name in employee_names:
            processed_employee = self.preprocess_name(employee_name)
            
            if not processed_employee:
                results[employee_name] = {
                    'match': None,
                    'score': 0,
                    'original_cost_bearer': None,
                    'status': 'empty_name'
                }
                continue
            
            # Find best match using the selected algorithm
            try:
                if self.algorithm in ['rapidfuzz', 'fuzzywuzzy']:
                    # Use process.extractOne for best single match
                    match_result = self.process.extractOne(
                        processed_employee,
                        processed_cost_bearers,
                        scorer=self.fuzz.ratio
                    )
                    
                    if match_result and match_result[1] >= self.threshold:
                        matched_processed = match_result[0]
                        score = match_result[1]
                        original_cost_bearer = name_lookup[matched_processed]
                        
                        # Get additional information from DataFrame
                        cost_bearer_info = cost_bearer_df[
                            cost_bearer_df[name_column] == original_cost_bearer
                        ].iloc[0].to_dict()
                        
                        results[employee_name] = {
                            'match': matched_processed,
                            'score': score,
                            'original_cost_bearer': original_cost_bearer,
                            'cost_bearer_info': cost_bearer_info,
                            'status': 'matched'
                        }
                        total_matches += 1
                    else:
                        results[employee_name] = {
                            'match': None,
                            'score': match_result[1] if match_result else 0,
                            'original_cost_bearer': None,
                            'status': 'no_match'
                        }
                
            except Exception as e:
                logger.warning(f"Error matching name '{employee_name}': {e}")
                results[employee_name] = {
                    'match': None,
                    'score': 0,
                    'original_cost_bearer': None,
                    'status': 'error'
                }
        
        # Log performance
        end_time = time.perf_counter()
        match_rate = (total_matches / len(employee_names)) * 100 if employee_names else 0
        
        logger.info(f"Name matching completed: {end_time - start_time:.2f}s, "
                   f"{total_matches}/{len(employee_names)} matches ({match_rate:.1f}%)")
        
        return results
    
    def batch_match_with_caching(self, 
                                employee_names: List[str], 
                                cost_bearer_file: Union[str, Path],
                                sheet_name: Optional[str] = None,
                                name_column: str = 'Name') -> Dict[str, Dict[str, Any]]:
        """
        Batch match with intelligent caching based on file modification time.
        
        Args:
            employee_names: List of names to match
            cost_bearer_file: Path to Excel file with cost bearer data
            sheet_name: Sheet name to read
            name_column: Column containing names
            
        Returns:
            Matching results dictionary
        """
        file_path = Path(cost_bearer_file)
        
        # Create cache key based on file path and modification time
        file_mtime = file_path.stat().st_mtime
        cache_key = f"{file_path}_{file_mtime}_{sheet_name}_{name_column}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Check if we have cached cost bearer data
        if cache_hash not in self._name_cache:
            logger.info(f"Loading cost bearer data from {file_path}")
            
            # Use optimized Excel reading
            excel_manager = ExcelEngineManager(self.config)
            cost_bearer_df = excel_manager.read_excel_optimized(
                file_path, 
                sheet_name=sheet_name
            )
            
            self._name_cache[cache_hash] = cost_bearer_df
        else:
            logger.info("Using cached cost bearer data")
            cost_bearer_df = self._name_cache[cache_hash]
        
        # Perform matching
        return self.match_employee_names(employee_names, cost_bearer_df, name_column)


# Integration class combining all components
class OptimizedInvoiceProcessor:
    """
    Complete optimized invoice processing system.
    
    Combines PDF extraction, Excel processing, and name matching.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the complete processing system."""
        # Load configuration (reusing from the parser)
        import yaml
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader
        
        if config_path:
            with open(config_path, 'r') as f:
                self.config = yaml.load(f, Loader=Loader)
        else:
            self.config = self._get_default_config()
        
        # Initialize components
        self.excel_manager = ExcelEngineManager(self.config)
        self.name_matcher = CostBearerMatcher(self.config)
        
        logger.info("Optimized Invoice Processor initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration."""
        return {
            'excel_processing': {
                'engines': {
                    'xlsx_small': 'openpyxl',
                    'xlsx_large': 'calamine',
                    'xlsb': 'pyxlsb'
                },
                'chunk_size': 10000,
                'memory_threshold_mb': 500,
                'dtype_optimization': True
            },
            'name_matching': {
                'algorithm': 'rapidfuzz',
                'threshold': 85,
                'preprocessing': {
                    'normalize_case': True,
                    'remove_titles': ['mr', 'mrs', 'ms', 'dr']
                }
            }
        }
    
    def process_invoice_batch(self, 
                            invoice_data_list: List[Dict[str, Any]], 
                            cost_bearer_file: Union[str, Path],
                            sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process a batch of invoice data with cost bearer matching.
        
        Args:
            invoice_data_list: List of invoice data dictionaries
            cost_bearer_file: Path to Excel file with cost bearers
            sheet_name: Sheet to read from Excel file
            
        Returns:
            List of processed invoice data with matching results
        """
        start_time = time.perf_counter()
        
        # Collect all employee names for batch matching
        all_employee_names = []
        for invoice_data in invoice_data_list:
            employee_names = invoice_data.get('employee_names', [])
            all_employee_names.extend(employee_names)
        
        # Remove duplicates while preserving order
        unique_names = list(dict.fromkeys(all_employee_names))
        
        logger.info(f"Processing batch: {len(invoice_data_list)} invoices, "
                   f"{len(unique_names)} unique employee names")
        
        # Batch match all names
        matching_results = self.name_matcher.batch_match_with_caching(
            unique_names, 
            cost_bearer_file, 
            sheet_name
        )
        
        # Apply matching results to each invoice
        processed_invoices = []
        for invoice_data in invoice_data_list:
            processed_invoice = invoice_data.copy()
            processed_invoice['name_matches'] = {}
            
            for employee_name in invoice_data.get('employee_names', []):
                if employee_name in matching_results:
                    processed_invoice['name_matches'][employee_name] = matching_results[employee_name]
            
            processed_invoices.append(processed_invoice)
        
        end_time = time.perf_counter()
        logger.info(f"Batch processing completed in {end_time - start_time:.2f} seconds")
        
        return processed_invoices


# Example usage and testing
if __name__ == "__main__":
    # Test Excel processing
    excel_manager = ExcelEngineManager({
        'excel_processing': {
            'chunk_size': 5000,
            'dtype_optimization': True
        }
    })
    
    print("Optimized Excel Processor initialized!")
    print(f"Available engines - openpyxl: {OPENPYXL_AVAILABLE}, calamine: {CALAMINE_AVAILABLE}, pyxlsb: {PYXLSB_AVAILABLE}")
    
    # Test name matching
    name_matcher = CostBearerMatcher({
        'name_matching': {
            'algorithm': 'rapidfuzz',
            'threshold': 80
        }
    })
    
    print("Name matcher initialized!")