"""
Telia Invoice Parser Demo

This script demonstrates the Telia invoice parser working with real data:
- Telia.pdf - the actual invoice
- Bok2 1.xlsx - cost center lookup data
"""

import sys
import os
import logging
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from extraction.telia_parser import TeliaParser, InvoiceData

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main demo function."""
    print("🔍 Telia Invoice Parser Demo")
    print("=" * 50)
    
    # Check if required files exist
    telia_pdf = "examples/Telia.pdf"
    bok2_excel = "examples/Bok2 1.xlsx"
    
    if not os.path.exists(telia_pdf):
        print(f"❌ Telia PDF not found: {telia_pdf}")
        return
    
    if not os.path.exists(bok2_excel):
        print(f"❌ Bok2 Excel file not found: {bok2_excel}")
        return
    
    print(f"✅ Found Telia PDF: {telia_pdf}")
    print(f"✅ Found Bok2 Excel: {bok2_excel}")
    print()
    
    try:
        # Initialize parser
        print("🔧 Initializing Telia Parser...")
        parser = TeliaParser(bok2_path=bok2_excel)
        print(f"✅ Parser initialized with {len(parser.engines)} OCR engine(s)")
        print()
        
        # Process the invoice
        print("📄 Processing Telia invoice...")
        print("This may take a few minutes for OCR processing...")
        print()
        
        result = parser.process_invoice(telia_pdf)
        
        print("✅ Processing complete!")
        print()
        
        # Display results
        invoice_data = result['invoice_data']
        
        print("📊 Invoice Summary:")
        print(f"  Invoice Number: {invoice_data.invoice_number or 'Not found'}")
        print(f"  Period: {invoice_data.period_from} to {invoice_data.period_to}")
        print(f"  Grand Total: {invoice_data.grand_total:,.2f} NOK")
        print(f"  Employee Lines: {len(invoice_data.lines)}")
        print()
        
        # Show employee details
        if invoice_data.lines:
            print("👥 Employee Details:")
            print("-" * 80)
            print(f"{'Name':<25} {'MSISDN':<15} {'Amount':<12} {'Cost Center':<15} {'Department':<15}")
            print("-" * 80)
            
            for line in invoice_data.lines:
                print(f"{line.employee_name[:24]:<25} {line.msisdn:<15} "
                      f"{line.sum_this_period:>10,.2f} {line.cost_center or 'N/A':<15} "
                      f"{line.department or 'N/A':<15}")
            print()
        
        # Show totals
        totals = invoice_data.get_totals()
        print("💰 Financial Summary:")
        print(f"  Sum of Employee Lines: {totals['sum_of_lines']:,.2f} NOK")
        print(f"  Difference vs Grand Total: {totals['diff_vs_grand_total']:,.2f} NOK")
        print(f"  (This difference typically represents admin fees, etc.)")
        print()
        
        # Show output files
        print("💾 Output Files Created:")
        print(f"  JSON: {result['json']}")
        print(f"  CSV: {result['csv']}")
        print()
        
        # Show JSON structure
        print("📋 JSON Structure Preview:")
        json_data = invoice_data.to_dict()
        print(json.dumps(json_data, indent=2, ensure_ascii=False)[:1000] + "...")
        print()
        
        # Show CSV preview
        print("📋 CSV Structure Preview:")
        with open(result['csv'], 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:5]):  # Show first 5 lines
                print(f"  {line.strip()}")
            if len(lines) > 5:
                print(f"  ... and {len(lines) - 5} more lines")
        print()
        
        print("🎉 Demo completed successfully!")
        print("\nThe parser has extracted all employee data with 'SUM DENNE PERIODE'")
        print("amounts and looked up cost centers from the Bok2.xlsx file.")
        print("\nYou can now use the JSON and CSV files for further processing.")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        logger.exception("Demo failed")


if __name__ == "__main__":
    main() 