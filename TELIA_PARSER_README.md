# Telia Invoice Parser

A comprehensive parser for Telia invoices that extracts employee data, invoice details, and performs cost center lookups.

## Features

✅ **Multi-OCR Engine Support**: Uses both Tesseract and EasyOCR for improved accuracy  
✅ **Employee Data Extraction**: Extracts "SUM DENNE PERIODE" amounts per person/number  
✅ **Invoice Details**: Gets invoice period and total from first page  
✅ **Cost Center Lookup**: Looks up cost centers from Bok2.xlsx file  
✅ **Multiple Output Formats**: Generates both JSON and CSV outputs  
✅ **Norwegian Number Format**: Handles Norwegian number formats (1.234,56)  
✅ **Robust Text Processing**: Uses regex patterns to extract structured data  

## Quick Start

### Prerequisites

1. **Python Dependencies** (already in requirements.txt):
   ```bash
   pip install -r requirements.txt
   ```

2. **OCR Engines**:
   - **Tesseract**: Install from https://github.com/UB-Mannheim/tesseract/wiki
   - **EasyOCR**: Automatically installed via pip

3. **For PDF Processing** (optional):
   - **Poppler**: Download from https://github.com/oschwartz10612/poppler-windows/releases
   - Or install via conda: `conda install -c conda-forge poppler`

### File Structure

```
Invoice Processing/
├── examples/
│   ├── Telia.pdf              # Telia invoice to process
│   └── Bok2 1.xlsx           # Cost center lookup data
├── src/extraction/
│   └── telia_parser.py       # Main parser implementation
├── output/                   # Generated output files
├── test_telia_parser.py      # Unit tests
├── demo_telia_parser.py      # Full demo with real PDF
└── test_parser_with_sample.py # Demo with sample data
```

## Usage

### 1. Test the Parser

Run the unit tests to verify everything works:

```bash
python test_telia_parser.py
```

### 2. Demo with Sample Data

Test the parser functionality with sample data:

```bash
python test_parser_with_sample.py
```

### 3. Process Real Telia PDF

Process the actual Telia invoice (requires Poppler):

```bash
python demo_telia_parser.py
```

### 4. Use in Your Code

```python
from src.extraction.telia_parser import TeliaParser

# Initialize parser
parser = TeliaParser(bok2_path="examples/Bok2 1.xlsx")

# Process invoice
result = parser.process_invoice("examples/Telia.pdf")

# Access results
invoice_data = result['invoice_data']
print(f"Found {len(invoice_data.lines)} employee lines")
print(f"Total: {invoice_data.grand_total} NOK")

# Output files are saved to output/ directory
```

## Output Formats

### JSON Output

```json
{
  "invoice": {
    "supplier": "TELIA COMPANY AB",
    "invoice_number": "INV-2024-001",
    "period": {
      "from": "2024-01-01",
      "to": "2024-01-31"
    },
    "currency": "NOK",
    "grand_total": 21152.34
  },
  "lines": [
    {
      "employee_name": "John Doe",
      "msisdn": "92078335",
      "sum_this_period": 410.65,
      "currency": "NOK",
      "cost_center": "12345",
      "department": "IT",
      "source_page": 2
    }
  ],
  "totals": {
    "lines_count": 1,
    "sum_of_lines": 410.65,
    "diff_vs_grand_total": 20741.69
  }
}
```

### CSV Output

```csv
Employee;MSISDN;SumDennePeriode;Currency;CostCenter;Department;SourcePage
John Doe;92078335;410.65;NOK;12345;IT;2
```

## Extraction Rules

### Employee Data Extraction

1. **Pattern**: `^Tjenestespesifikasjon for\s+(?<name>.+?)\s*[-–]\s*(?<msisdn>(?:\+?47)?\s?\d[\d\s]{6,})`
2. **Amount**: `^SUM DENNE PERIODE\s*[:\-]?\s*(?<amount>-?\d{1,3}(?:[ .]\d{3})*,\d{2})`
3. **Multiple amounts**: Takes the last occurrence if multiple found

### Invoice Details

1. **Period**: `Fakturaperiode\s*[:\-]?\s*(\d{2}\.\d{2}\.\d{4})\s*[–-]\s*(\d{2}\.\d{2}\.\d{4})`
2. **Total**: `(?:Å betale|Total|Sum å betale|Fakturabeløp)\s*[:\-]?\s*(?<total>-?\d{1,3}(?:[ .]\d{3})*,\d{2})`
3. **Invoice Number**: `(?:Fakturanummer|Invoice Number|Faktura nr\.?)\s*[:\-]?\s*(\S+)`

### Cost Center Lookup

1. **MSISDN Lookup**: First tries to match by phone number
2. **Name Lookup**: Falls back to name matching (case-insensitive)
3. **Norwegian Columns**: Handles 'Fornavn', 'Etternavn', 'Kostsenter' columns

## Data Processing

### Number Format Handling

- **Norwegian Format**: `1 234,56` or `1.234,56` → `1234.56`
- **Currency**: Always NOK
- **Negative Values**: Supported for corrections

### Date Format Handling

- **Input**: `DD.MM.YYYY` (Norwegian format)
- **Output**: `YYYY-MM-DD` (ISO format)

### MSISDN Normalization

- **Input**: `+47 920 78 335` or `92078335`
- **Output**: `92078335` (digits only for lookup)

## Configuration

### Bok2.xlsx Structure

The parser expects a file with these columns:
- **Name columns**: 'Fornavn', 'Etternavn' (combined into full name)
- **Cost center**: 'Kostsenter'
- **Optional**: MSISDN/phone number column

### OCR Engine Configuration

```python
from src.ocr.engines import EngineConfig, TesseractEngine, EasyOCREngine

# Tesseract configuration
tesseract_config = EngineConfig(
    name="tesseract_primary",
    enabled=True,
    priority=1,
    confidence_threshold=0.5
)

# EasyOCR configuration
easyocr_config = EngineConfig(
    name="easyocr_secondary", 
    enabled=True,
    priority=2,
    confidence_threshold=0.5
)
```

## Troubleshooting

### Common Issues

1. **"No text extracted from PDF"**
   - Install Poppler: `conda install -c conda-forge poppler`
   - Or download from: https://github.com/oschwartz10612/poppler-windows/releases

2. **"Tesseract not found"**
   - Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
   - Ensure it's in PATH or specify path in code

3. **"Could not find name columns in Bok2.xlsx"**
   - Check column names in the Excel file
   - Ensure sheet name is correct (tries 'bok2', 'Ark1', 'Sheet1')

4. **"No cost center data loaded"**
   - Verify Bok2.xlsx file exists and has correct structure
   - Check that name columns contain data

### Performance Tips

1. **GPU Acceleration**: EasyOCR is much faster with GPU
2. **Image Resolution**: Parser optimizes DPI to 200-250 for speed
3. **Batch Processing**: Process multiple invoices in sequence

## API Reference

### TeliaParser Class

```python
class TeliaParser:
    def __init__(self, bok2_path: str = "examples/Bok2 1.xlsx")
    def parse_invoice(self, pdf_path: str) -> InvoiceData
    def process_invoice(self, pdf_path: str, output_dir: str = "output") -> Dict[str, str]
    def save_json(self, invoice_data: InvoiceData, output_path: str = None)
    def save_csv(self, invoice_data: InvoiceData, output_path: str = None)
```

### Data Classes

```python
@dataclass
class InvoiceLine:
    employee_name: str
    msisdn: str
    sum_this_period: float
    currency: str = "NOK"
    cost_center: Optional[str] = None
    department: Optional[str] = None
    source_page: int = 0

@dataclass
class InvoiceData:
    supplier: str = "TELIA COMPANY AB"
    invoice_number: str = ""
    period_from: str = ""
    period_to: str = ""
    currency: str = "NOK"
    grand_total: float = 0.0
    lines: List[InvoiceLine] = None
```

## Development

### Running Tests

```bash
# Unit tests
python test_telia_parser.py

# Sample data demo
python test_parser_with_sample.py

# Full demo (requires Poppler)
python demo_telia_parser.py
```

### Adding New Features

1. **New OCR Engine**: Implement `OCREngine` interface
2. **New Output Format**: Add method to `TeliaParser` class
3. **New Extraction Pattern**: Add regex pattern to `_compile_patterns()`

## License

This project is part of the Invoice Processing system.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Run the test scripts to verify functionality
3. Check the logs for detailed error messages
