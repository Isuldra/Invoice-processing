"""
Invoice Processing System - Main Entry Point

Text-based invoice processing with cost-free supplier detection and training.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from src.core.logging import setup_logging
from src.extraction.suppliers import auto_detect_supplier, get_supplier_parser
from src.extraction.suppliers.telia import extract_text_from_pdf
from src.utils.train_supplier import SupplierTrainer


def process_invoice(pdf_path: Path, output_dir: Optional[Path] = None) -> bool:
    """
    Process a single invoice using text-based extraction.
    
    Args:
        pdf_path: Path to the PDF invoice
        output_dir: Directory to save output files (optional)
    
    Returns:
        True if processing was successful
    """
    logger = logging.getLogger(__name__)
    
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    try:
        # Extract text from PDF
        logger.info(f"Extracting text from {pdf_path}")
        pdf_text = extract_text_from_pdf(pdf_path)
        
        if not pdf_text:
            logger.error("Could not extract text from PDF")
            return False
        
        # Auto-detect supplier
        logger.info("Detecting supplier...")
        supplier_name = auto_detect_supplier(pdf_text)
        
        if not supplier_name:
            logger.error("Could not detect supplier")
            return False
        
        logger.info(f"Detected supplier: {supplier_name}")
        
        # Get appropriate parser
        parser_class = get_supplier_parser(supplier_name)
        if not parser_class:
            logger.error(f"No parser available for supplier: {supplier_name}")
            return False
        
        # Parse invoice
        parser = parser_class()
        invoice_data = parser.parse_invoice(pdf_text, pdf_path)
        
        # Validate results
        validation = parser.validate_invoice(invoice_data)
        
        if not validation["is_valid"]:
            logger.warning("Invoice validation failed:")
            for error in validation["errors"]:
                logger.warning(f"  - {error}")
        
        # Save results
        if output_dir:
            output_dir.mkdir(exist_ok=True)
            
            # Save JSON output
            json_file = output_dir / f"{pdf_path.stem}_processed.json"
            import json
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(invoice_data.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved results to {json_file}")
        
        # Print summary
        print(f"\n✓ Processed: {pdf_path.name}")
        print(f"  Supplier: {invoice_data.supplier}")
        print(f"  Invoice: {invoice_data.invoice_number}")
        print(f"  Lines: {len(invoice_data.lines)}")
        print(f"  Total: {invoice_data.grand_total} {invoice_data.currency}")
        print(f"  Confidence: {invoice_data.confidence:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to process {pdf_path}: {e}")
        return False


def train_supplier(pdf_path: Path, supplier_name: str) -> bool:
    """
    Add an example invoice to train the supplier detection.
    
    Args:
        pdf_path: Path to the PDF invoice
        supplier_name: Name of the supplier
    
    Returns:
        True if training was successful
    """
    trainer = SupplierTrainer()
    return trainer.add_example(pdf_path, supplier_name)


def show_stats():
    """Show training statistics."""
    trainer = SupplierTrainer()
    stats = trainer.get_training_stats()
    
    print("\n📊 Training Statistics:")
    print(f"  Total suppliers: {stats['total_suppliers']}")
    print(f"  Total examples: {stats['total_examples']}")
    
    if stats['supplier_examples']:
        print("  Examples per supplier:")
        for supplier, count in stats['supplier_examples'].items():
            print(f"    {supplier}: {count}")
    else:
        print("  No examples yet")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Text-based Invoice Processing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single invoice
  python main.py process examples/Telia.pdf
  
  # Train with a new example
  python main.py train examples/Telia.pdf --supplier telia
  
  # Show training statistics
  python main.py stats
  
  # Test supplier detection
  python main.py test examples/Telia.pdf
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process an invoice')
    process_parser.add_argument('pdf_path', type=Path, help='Path to PDF file')
    process_parser.add_argument('--output', type=Path, help='Output directory')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train supplier detection')
    train_parser.add_argument('pdf_path', type=Path, help='Path to PDF file')
    train_parser.add_argument('--supplier', required=True, help='Supplier name')
    
    # Stats command
    subparsers.add_parser('stats', help='Show training statistics')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test supplier detection')
    test_parser.add_argument('pdf_path', type=Path, help='Path to PDF file')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    if args.command == 'process':
        success = process_invoice(args.pdf_path, args.output)
        sys.exit(0 if success else 1)
    
    elif args.command == 'train':
        success = train_supplier(args.pdf_path, args.supplier)
        if success:
            print(f"✓ Added training example: {args.pdf_path.name} -> {args.supplier}")
        else:
            print(f"✗ Failed to add training example")
        sys.exit(0 if success else 1)
    
    elif args.command == 'stats':
        show_stats()
    
    elif args.command == 'test':
        trainer = SupplierTrainer()
        supplier = trainer.test_detection(args.pdf_path)
        if supplier:
            print(f"✓ Detected supplier: {supplier}")
        else:
            print("✗ No supplier detected")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
