"""
Supplier Training Utility

This module provides a cost-free way to "train" the system by adding
example invoices to improve supplier detection accuracy.
"""

import logging
from pathlib import Path
from typing import Optional
import PyPDF2

from ..extraction.suppliers import SupplierDetector
from ..extraction.suppliers.telia import extract_text_from_pdf

logger = logging.getLogger(__name__)


class SupplierTrainer:
    """
    Cost-free supplier training system.
    
    This allows users to add example invoices to improve detection
    accuracy without requiring any AI/API services.
    """
    
    def __init__(self):
        self.detector = SupplierDetector()
        self.examples_dir = Path(__file__).parent.parent / "extraction" / "suppliers" / "examples"
        self.examples_dir.mkdir(exist_ok=True)
    
    def add_example(self, pdf_path: Path, supplier_name: str) -> bool:
        """
        Add a new example invoice to improve detection.
        
        Args:
            pdf_path: Path to the PDF invoice
            supplier_name: Name of the supplier (e.g., "telia")
        
        Returns:
            True if example was added successfully
        """
        try:
            # Extract text from PDF
            pdf_text = extract_text_from_pdf(pdf_path)
            if not pdf_text:
                logger.error(f"Could not extract text from {pdf_path}")
                return False
            
            # Add to detector's examples
            self.detector.add_example(supplier_name, pdf_text)
            
            # Save example text to file for persistence
            supplier_dir = self.examples_dir / supplier_name
            supplier_dir.mkdir(exist_ok=True)
            
            example_file = supplier_dir / f"{pdf_path.stem}.txt"
            with open(example_file, 'w', encoding='utf-8') as f:
                f.write(pdf_text)
            
            logger.info(f"Added example for {supplier_name}: {pdf_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add example {pdf_path}: {e}")
            return False
    
    def train_from_directory(self, directory: Path, supplier_name: str) -> int:
        """
        Train from all PDF files in a directory.
        
        Args:
            directory: Directory containing PDF files
            supplier_name: Name of the supplier
        
        Returns:
            Number of examples added
        """
        added_count = 0
        
        for pdf_file in directory.glob("*.pdf"):
            if self.add_example(pdf_file, supplier_name):
                added_count += 1
        
        logger.info(f"Added {added_count} examples for {supplier_name}")
        return added_count
    
    def get_training_stats(self) -> dict:
        """Get statistics about the training data."""
        stats = {
            "total_suppliers": 0,
            "total_examples": 0,
            "supplier_examples": {}
        }
        
        for supplier_dir in self.examples_dir.iterdir():
            if supplier_dir.is_dir():
                supplier_name = supplier_dir.name
                example_count = len(list(supplier_dir.glob("*.txt")))
                
                stats["total_suppliers"] += 1
                stats["total_examples"] += example_count
                stats["supplier_examples"][supplier_name] = example_count
        
        return stats
    
    def test_detection(self, pdf_path: Path) -> Optional[str]:
        """
        Test supplier detection on a PDF file.
        
        Args:
            pdf_path: Path to PDF file to test
        
        Returns:
            Detected supplier name or None
        """
        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text:
            return None
        
        return self.detector.detect_supplier(pdf_text)


def main():
    """Command-line interface for supplier training."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train supplier detection system")
    parser.add_argument("command", choices=["add", "train", "stats", "test"])
    parser.add_argument("--pdf", type=Path, help="PDF file path")
    parser.add_argument("--supplier", type=str, help="Supplier name")
    parser.add_argument("--directory", type=Path, help="Directory with PDF files")
    
    args = parser.parse_args()
    
    trainer = SupplierTrainer()
    
    if args.command == "add":
        if not args.pdf or not args.supplier:
            print("Error: --pdf and --supplier required for 'add' command")
            return
        
        if trainer.add_example(args.pdf, args.supplier):
            print(f"✓ Added example: {args.pdf.name} -> {args.supplier}")
        else:
            print(f"✗ Failed to add example: {args.pdf.name}")
    
    elif args.command == "train":
        if not args.directory or not args.supplier:
            print("Error: --directory and --supplier required for 'train' command")
            return
        
        count = trainer.train_from_directory(args.directory, args.supplier)
        print(f"✓ Added {count} examples for {args.supplier}")
    
    elif args.command == "stats":
        stats = trainer.get_training_stats()
        print("Training Statistics:")
        print(f"  Total suppliers: {stats['total_suppliers']}")
        print(f"  Total examples: {stats['total_examples']}")
        print("  Examples per supplier:")
        for supplier, count in stats['supplier_examples'].items():
            print(f"    {supplier}: {count}")
    
    elif args.command == "test":
        if not args.pdf:
            print("Error: --pdf required for 'test' command")
            return
        
        supplier = trainer.test_detection(args.pdf)
        if supplier:
            print(f"✓ Detected supplier: {supplier}")
        else:
            print("✗ No supplier detected")


if __name__ == "__main__":
    main()
