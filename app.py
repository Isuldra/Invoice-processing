"""
OneMed Fakturabehandling - Standalone Web Application

Flask web app for processing Telia Norge AS invoices with cost bearer matching.
Inspired by OneMed's professional healthcare technology design.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import sys
import json
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime

# Add src to path for imports
sys.path.append('src')
from extraction.suppliers.telia import TeliaParser
from extraction.suppliers.telia import extract_text_from_pdf

# Configure Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'onemed-faktura-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Telia parser
telia_parser = TeliaParser()

# Allowed file extensions
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def index():
    """Main page with upload interface."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle PDF and Excel file uploads."""
    try:
        # Check if files were uploaded
        if 'pdf_file' not in request.files:
            flash('Ingen PDF-fil valgt', 'error')
            return redirect(url_for('index'))
        
        pdf_file = request.files['pdf_file']
        excel_file = request.files.get('excel_file')
        
        if pdf_file.filename == '':
            flash('Ingen PDF-fil valgt', 'error')
            return redirect(url_for('index'))
        
        if pdf_file and allowed_file(pdf_file.filename, ALLOWED_PDF_EXTENSIONS):
            # Save PDF file
            pdf_filename = secure_filename(pdf_file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            pdf_file.save(pdf_path)
            
            # Save Excel file if provided
            excel_path = None
            if excel_file and excel_file.filename != '' and allowed_file(excel_file.filename, ALLOWED_EXCEL_EXTENSIONS):
                excel_filename = secure_filename(excel_file.filename)
                excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
                excel_file.save(excel_path)
            
            # Process the invoice
            result = process_invoice(pdf_path, excel_path)
            
            if result['success']:
                return render_template('results.html', 
                                     invoice_data=result['data'],
                                     processing_time=result['processing_time'])
            else:
                flash(f'Feil ved behandling av faktura: {result["error"]}', 'error')
                return redirect(url_for('index'))
        
        else:
            flash('Ugyldig filtype. Kun PDF-filer er tillatt.', 'error')
            return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Error in upload_files: {e}")
        flash(f'Systemfeil: {str(e)}', 'error')
        return redirect(url_for('index'))

def process_invoice(pdf_path: str, excel_path: str = None) -> dict:
    """Process the uploaded invoice."""
    start_time = datetime.now()
    
    try:
        # Extract text from PDF
        logger.info(f"Processing PDF: {pdf_path}")
        pdf_content = extract_text_from_pdf(Path(pdf_path))
        
        if not pdf_content:
            return {
                'success': False,
                'error': 'Kunne ikke lese tekst fra PDF-filen'
            }
        
        # Check if it's a Telia invoice
        if not telia_parser.can_parse(pdf_content):
            return {
                'success': False,
                'error': 'Dette ser ikke ut til å være en Telia Norge AS faktura'
            }
        
        # Process with cost bearer matching
        invoice_data = telia_parser.parse_invoice_with_cost_bearers(pdf_content, excel_path)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'success': True,
            'data': invoice_data,
            'processing_time': round(processing_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Error processing invoice: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    
    finally:
        # Clean up uploaded files
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            if excel_path and os.path.exists(excel_path):
                os.remove(excel_path)
        except Exception as e:
            logger.warning(f"Could not clean up files: {e}")

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'OneMed Fakturabehandling',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🏥 OneMed Fakturabehandling")
    print("=" * 40)
    print("🚀 Starter web-applikasjon...")
    print("📍 URL: http://localhost:5000")
    print("📋 Telia Norge AS fakturabehandling")
    print("=" * 40)
    
    app.run(debug=True, host='0.0.0.0', port=5000)