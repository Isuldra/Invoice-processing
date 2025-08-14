"""
Graphical User Interface for Telia PDF Processing System
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Optional

from src.core.logging import get_logger
from src.core.config import config

logger = get_logger("gui")


class TeliaProcessorGUI:
    """Main GUI application for Telia PDF processing."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Telia PDF Processing System")
        self.root.geometry("800x600")
        
        # Configure logging
        self.logger = get_logger("gui")
        
        # File selection variables
        self.selected_files: List[str] = []
        self.output_directory: Optional[str] = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Telia PDF Processing System", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        self.setup_file_selection(main_frame)
        
        # Output directory section
        self.setup_output_selection(main_frame)
        
        # Processing options section
        self.setup_processing_options(main_frame)
        
        # Progress section
        self.setup_progress_section(main_frame)
        
        # Control buttons
        self.setup_control_buttons(main_frame)
        
        # Status bar
        self.setup_status_bar(main_frame)
        
    def setup_file_selection(self, parent):
        """Set up file selection widgets."""
        # File selection frame
        file_frame = ttk.LabelFrame(parent, text="File Selection", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # Select files button
        select_files_btn = ttk.Button(file_frame, text="Select PDF Files", 
                                     command=self.select_files)
        select_files_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Selected files label
        self.files_label = ttk.Label(file_frame, text="No files selected")
        self.files_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Clear files button
        clear_files_btn = ttk.Button(file_frame, text="Clear", 
                                    command=self.clear_files)
        clear_files_btn.grid(row=0, column=2)
        
    def setup_output_selection(self, parent):
        """Set up output directory selection."""
        # Output frame
        output_frame = ttk.LabelFrame(parent, text="Output Directory", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        # Select output button
        select_output_btn = ttk.Button(output_frame, text="Select Output Directory", 
                                      command=self.select_output_directory)
        select_output_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Output directory label
        self.output_label = ttk.Label(output_frame, text="No output directory selected")
        self.output_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
    def setup_processing_options(self, parent):
        """Set up processing options."""
        # Options frame
        options_frame = ttk.LabelFrame(parent, text="Processing Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Processing timeout
        ttk.Label(options_frame, text="Processing Timeout (seconds):").grid(row=0, column=0, sticky=tk.W)
        self.timeout_var = tk.IntVar(value=config.processing.timeout_seconds)
        timeout_scale = ttk.Scale(options_frame, from_=30, to=300, 
                                 variable=self.timeout_var, orient=tk.HORIZONTAL)
        timeout_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        # Processing DPI
        ttk.Label(options_frame, text="Processing DPI:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.dpi_var = tk.IntVar(value=config.processing.dpi)
        dpi_spinbox = ttk.Spinbox(options_frame, from_=150, to=300, 
                                 variable=self.dpi_var, width=10)
        dpi_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        options_frame.columnconfigure(1, weight=1)
        
    def setup_progress_section(self, parent):
        """Set up progress tracking widgets."""
        # Progress frame
        progress_frame = ttk.LabelFrame(parent, text="Processing Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Progress label
        self.progress_label = ttk.Label(progress_frame, text="Ready to process")
        self.progress_label.grid(row=1, column=0, sticky=tk.W)
        
    def setup_control_buttons(self, parent):
        """Set up control buttons."""
        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(0, 10))
        
        # Process button
        self.process_btn = ttk.Button(button_frame, text="Process Files", 
                                     command=self.process_files, state=tk.DISABLED)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button
        self.stop_btn = ttk.Button(button_frame, text="Stop", 
                                  command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(button_frame, text="Clear All", 
                              command=self.clear_all)
        clear_btn.pack(side=tk.LEFT)
        
    def setup_status_bar(self, parent):
        """Set up status bar."""
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
    def select_files(self):
        """Open file dialog to select PDF files."""
        files = filedialog.askopenfilenames(
            title="Select Telia PDF Files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if files:
            self.selected_files = list(files)
            self.update_files_label()
            self.update_process_button()
            self.logger.info(f"Selected {len(files)} files")
            
    def select_output_directory(self):
        """Open directory dialog to select output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        
        if directory:
            self.output_directory = directory
            self.output_label.config(text=directory)
            self.update_process_button()
            self.logger.info(f"Selected output directory: {directory}")
            
    def clear_files(self):
        """Clear selected files."""
        self.selected_files.clear()
        self.update_files_label()
        self.update_process_button()
        
    def clear_all(self):
        """Clear all selections."""
        self.clear_files()
        self.output_directory = None
        self.output_label.config(text="No output directory selected")
        self.progress_var.set(0)
        self.progress_label.config(text="Ready to process")
        self.status_var.set("Ready")
        self.update_process_button()
        
    def update_files_label(self):
        """Update the files label."""
        if self.selected_files:
            if len(self.selected_files) == 1:
                text = f"1 file selected: {Path(self.selected_files[0]).name}"
            else:
                text = f"{len(self.selected_files)} files selected"
        else:
            text = "No files selected"
            
        self.files_label.config(text=text)
        
    def update_process_button(self):
        """Update the process button state."""
        if self.selected_files and self.output_directory:
            self.process_btn.config(state=tk.NORMAL)
        else:
            self.process_btn.config(state=tk.DISABLED)
            
    def process_files(self):
        """Process the selected files."""
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select files to process")
            return
            
        if not self.output_directory:
            messagebox.showwarning("No Output", "Please select output directory")
            return
            
        # TODO: Implement actual processing
        self.logger.info("Starting file processing")
        self.status_var.set("Processing...")
        self.process_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Simulate processing
        self.simulate_processing()
        
    def simulate_processing(self):
        """Simulate processing for demonstration."""
        # This is a placeholder - replace with actual processing
        import time
        
        total_files = len(self.selected_files)
        for i, file_path in enumerate(self.selected_files):
            if not hasattr(self, 'processing') or not self.processing:
                break
                
            # Update progress
            progress = (i / total_files) * 100
            self.progress_var.set(progress)
            self.progress_label.config(text=f"Processing {Path(file_path).name}...")
            self.root.update()
            
            # Simulate processing time
            time.sleep(0.5)
            
        # Complete
        self.progress_var.set(100)
        self.progress_label.config(text="Processing completed")
        self.status_var.set("Completed")
        self.process_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        messagebox.showinfo("Complete", "File processing completed successfully!")
        
    def stop_processing(self):
        """Stop the processing."""
        self.processing = False
        self.status_var.set("Stopped")
        self.process_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.logger.info("Processing stopped by user")


def main():
    """Main GUI entry point."""
    root = tk.Tk()
    app = TeliaProcessorGUI(root)
    
    # Initialize processing flag
    app.processing = False
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("GUI interrupted by user")
    except Exception as e:
        logger.error(f"GUI error: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")


if __name__ == "__main__":
    main()
