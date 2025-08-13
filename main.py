#!/usr/bin/env python3
"""
Telia PDF Processing System - Main Entry Point

This is the main entry point for the Telia PDF processing system.
It provides both GUI and CLI interfaces for processing Telia invoices.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.gui import main as gui_main
from src.utils.cli import main as cli_main


def main():
    """Main entry point for the application."""
    if len(sys.argv) > 1:
        # CLI mode
        cli_main()
    else:
        # GUI mode
        gui_main()


if __name__ == "__main__":
    main()
