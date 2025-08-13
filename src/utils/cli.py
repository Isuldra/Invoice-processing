"""
Command Line Interface for Telia PDF Processing System
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from src.core.logging import get_logger
from src.core.config import config

logger = get_logger("cli")


def process_single_file(file_path: str, output_dir: Optional[str] = None) -> bool:
    """
    Process a single Telia invoice file.
    
    Args:
        file_path: Path to the PDF file
        output_dir: Output directory for results
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing single file: {file_path}")
    
    # TODO: Implement actual processing
    # This is a placeholder for the processing pipeline
    
    try:
        # Validate file exists
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return False
            
        # TODO: Add actual processing logic here
        logger.info("Processing completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return False


def process_batch(input_dir: str, output_dir: Optional[str] = None) -> bool:
    """
    Process multiple Telia invoice files in a directory.
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Output directory for results
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Processing batch from directory: {input_dir}")
    
    try:
        input_path = Path(input_dir)
        if not input_path.exists() or not input_path.is_dir():
            logger.error(f"Directory not found: {input_dir}")
            return False
            
        # Find all PDF files
        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in: {input_dir}")
            return False
            
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # TODO: Implement batch processing
        for pdf_file in pdf_files:
            logger.info(f"Processing: {pdf_file.name}")
            # TODO: Add actual processing logic here
            
        logger.info("Batch processing completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        return False


def show_config() -> None:
    """Display current configuration."""
    logger.info("Current Configuration:")
    logger.info(f"OCR Confidence Threshold: {config.ocr.confidence_threshold}")
    logger.info(f"Processing DPI: {config.processing.dpi}")
    logger.info(f"Validation Thresholds: {config.validation.name_confidence_threshold}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Telia PDF Processing System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s process examples/Telia.pdf
  %(prog)s batch examples/
  %(prog)s config
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Process single file command
    process_parser = subparsers.add_parser(
        "process", 
        help="Process a single Telia invoice file"
    )
    process_parser.add_argument(
        "file", 
        help="Path to the PDF file to process"
    )
    process_parser.add_argument(
        "--output", "-o",
        help="Output directory for results"
    )
    
    # Batch process command
    batch_parser = subparsers.add_parser(
        "batch", 
        help="Process multiple Telia invoice files"
    )
    batch_parser.add_argument(
        "directory", 
        help="Directory containing PDF files to process"
    )
    batch_parser.add_argument(
        "--output", "-o",
        help="Output directory for results"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config", 
        help="Show current configuration"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == "process":
            success = process_single_file(args.file, args.output)
            sys.exit(0 if success else 1)
            
        elif args.command == "batch":
            success = process_batch(args.directory, args.output)
            sys.exit(0 if success else 1)
            
        elif args.command == "config":
            show_config()
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
