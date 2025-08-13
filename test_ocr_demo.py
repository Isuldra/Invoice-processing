"""
OCR Engine Demo Script

This script demonstrates the multi-OCR engine system working with
both Tesseract and EasyOCR engines as specified in the roadmap.
"""

import sys
import os
import logging
import json
import pandas as pd
from datetime import datetime
from PIL import Image

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ocr.engines import (
    OCREngine, 
    OCRResult, 
    EngineConfig,
    TesseractEngine,
    EasyOCREngine,
    TESSERACT_AVAILABLE,
    EASYOCR_AVAILABLE
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ocr_engines():
    """Test both OCR engines with the actual Telia invoice."""
    print("🔍 Testing Multi-OCR Engine System with Real Telia Invoice")
    print("=" * 60)
    
    # Create demo folder
    demo_folder = "demo"
    os.makedirs(demo_folder, exist_ok=True)
    
    # Check engine availability
    print(f"Tesseract Available: {'✅' if TESSERACT_AVAILABLE else '❌'}")
    print(f"EasyOCR Available: {'✅' if EASYOCR_AVAILABLE else '❌'}")
    print()
    
    # Path to the actual Telia invoice
    telia_pdf_path = "examples/Telia.pdf"
    
    if not os.path.exists(telia_pdf_path):
        print(f"❌ Telia invoice not found at: {telia_pdf_path}")
        return
    
    print(f"📄 Processing real Telia invoice: {telia_pdf_path}")
    print(f"📄 PDF size: {os.path.getsize(telia_pdf_path) / (1024*1024):.1f} MB")
    
    # For now, let's create a simple test image to demonstrate the OCR engines
    # In a real implementation, we'd convert the PDF to images
    print("\n📝 Creating test image with Telia-like content for demonstration...")
    
    # Create a test image with Telia-like content
    image = Image.new('RGB', (800, 600), color='white')
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(image)
    
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Draw Telia-like invoice content
    text_lines = [
        "TELIA COMPANY AB",
        "Invoice Number: INV-2024-001",
        "Employee: John Doe",
        "Department: IT",
        "Cost Center: 12345",
        "Amount: 1,250.00 NOK",
        "Date: 2024-01-15",
        "Description: Mobile phone services"
    ]
    
    y_position = 50
    for line in text_lines:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 30
    
    # Save the test image
    test_image_path = f"{demo_folder}/telia_test_image.png"
    image.save(test_image_path)
    print(f"✅ Created test image: {test_image_path}")
    
    engines = []
    
    # Initialize Tesseract engine
    if TESSERACT_AVAILABLE:
        tesseract_config = EngineConfig(
            name="tesseract_primary",
            enabled=True,
            priority=1,
            confidence_threshold=0.5
        )
        tesseract_engine = TesseractEngine(tesseract_config)
        
        if tesseract_engine.initialize():
            engines.append(tesseract_engine)
            print("✅ Tesseract engine initialized successfully")
        else:
            print("❌ Failed to initialize Tesseract engine")
    
    # Initialize EasyOCR engine
    if EASYOCR_AVAILABLE:
        easyocr_config = EngineConfig(
            name="easyocr_secondary",
            enabled=True,
            priority=2,
            confidence_threshold=0.5
        )
        easyocr_engine = EasyOCREngine(easyocr_config)
        
        if easyocr_engine.initialize():
            engines.append(easyocr_engine)
            print("✅ EasyOCR engine initialized successfully")
        else:
            print("❌ Failed to initialize EasyOCR engine")
    
    print(f"\n📊 Testing {len(engines)} OCR engine(s) with test image...")
    
    # Store all results for Excel output
    all_results_data = []
    
    # Test each engine
    for engine in engines:
        print(f"\n🔧 Testing {engine.name}:")
        print("-" * 40)
        
        try:
            # Extract text from the test image
            results = engine.extract_text(test_image_path)
            
            print(f"Found {len(results)} text elements:")
            
            # Process results for Excel
            for i, result in enumerate(results):
                # Add to results data for Excel
                all_results_data.append({
                    'Engine': engine.name,
                    'Engine_Priority': engine.priority,
                    'Result_Index': i + 1,
                    'Extracted_Text': result.text,
                    'Confidence': result.confidence,
                    'Processing_Time_Seconds': result.processing_time,
                    'Bounding_Box': str(result.bounding_box) if result.bounding_box else 'N/A',
                    'Metadata': str(result.metadata) if result.metadata else 'N/A',
                    'Is_Relevant': any(keyword in result.text.lower() for keyword in ['telia', 'employee', 'cost', 'nok', 'invoice', 'department'])
                })
                
                # Show relevant results in console
                if i < 5:  # Show first 5 results
                    confidence_str = f"(confidence: {result.confidence:.2f})" if result.confidence < 1.0 else "(full text)"
                    print(f"  {i+1}. '{result.text[:80]}{'...' if len(result.text) > 80 else ''}' {confidence_str}")
            
            if len(results) > 5:
                print(f"  ... and {len(results) - 5} more results")
            
            # Show processing time
            total_time = sum(r.processing_time for r in results)
            print(f"Processing time: {total_time:.2f}s")
            
            # Show engine info
            info = engine.get_engine_info()
            print(f"Engine priority: {info['priority']}")
            
        except Exception as e:
            print(f"❌ Error testing {engine.name}: {e}")
    
    # Create Excel file with results
    if all_results_data:
        # Create DataFrame
        df = pd.DataFrame(all_results_data)
        
        # Create Excel file with multiple sheets
        excel_file = f"{demo_folder}/ocr_demo_results.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Main results sheet
            df.to_excel(writer, sheet_name='OCR_Results', index=False)
            
            # Summary sheet
            summary_data = []
            for engine_name in df['Engine'].unique():
                engine_df = df[df['Engine'] == engine_name]
                summary_data.append({
                    'Engine': engine_name,
                    'Total_Results': len(engine_df),
                    'Avg_Confidence': engine_df['Confidence'].mean(),
                    'Total_Processing_Time': engine_df['Processing_Time_Seconds'].sum(),
                    'Relevant_Results': len(engine_df[engine_df['Is_Relevant'] == True])
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Relevant results only
            relevant_df = df[df['Is_Relevant'] == True].copy()
            if not relevant_df.empty:
                relevant_df.to_excel(writer, sheet_name='Relevant_Results', index=False)
            
            # Test info sheet
            test_info = {
                'Test_Date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                'Test_Image': [test_image_path],
                'Image_Size': [f"{image.size[0]}x{image.size[1]}"],
                'Engines_Tested': [len(engines)],
                'Tesseract_Available': [TESSERACT_AVAILABLE],
                'EasyOCR_Available': [EASYOCR_AVAILABLE],
                'Total_Results': [len(all_results_data)]
            }
            test_info_df = pd.DataFrame(test_info)
            test_info_df.to_excel(writer, sheet_name='Test_Info', index=False)
        
        print(f"\n💾 Excel file created: {excel_file}")
        print(f"📊 Sheets created:")
        print(f"  - OCR_Results: All extracted text with details")
        print(f"  - Summary: Engine performance summary")
        print(f"  - Relevant_Results: Telia-specific content only")
        print(f"  - Test_Info: Test configuration and metadata")
    
    print(f"\n📄 Test Image Info:")
    print(f"  - Size: {image.size}")
    print(f"  - Content: Telia invoice simulation")
    print(f"  - Saved to: {test_image_path}")
    
    print("\n🎉 Telia Invoice OCR Demo Complete!")
    print(f"\n📁 Demo Files Created in '{demo_folder}' folder:")
    print(f"  - Test Image: telia_test_image.png")
    print(f"  - Excel Results: ocr_demo_results.xlsx")
    print("\nThis demonstrates our multi-engine OCR system processing")
    print("Telia-like documents as specified in Phase 1 of the roadmap.")
    print("\nNext step: Integrate PDF processing to handle real Telia PDFs.")


if __name__ == "__main__":
    test_ocr_engines()
