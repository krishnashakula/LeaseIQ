#!/usr/bin/env python3
"""
PDF Extraction Web API with Advanced Business Intelligence
Ultra-fast Flask backend with OCR support using PyMuPDF + Tesseract
Enhanced with enterprise-grade lease analysis and portfolio optimization
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
try:
    import fitz  # PyMuPDF
except ImportError:
    try:
        import pymupdf as fitz  # Alternative import method
    except ImportError:
        logging.error("PyMuPDF not installed. Please install with: pip install pymupdf")
        fitz = None
from pathlib import Path
from werkzeug.utils import secure_filename
import json
import uuid
import os
import re
from PIL import Image
import io
from functools import wraps
import traceback

# Initialize Flask app
app = Flask(__name__)

# Load configuration
from config import get_config
config_class = get_config()
app.config.from_object(config_class)
config_class.init_app(app)

# Setup logging
logger = logging.getLogger(__name__)

# Configure CORS with security
CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)

# Import business intelligence features
try:
    from business_api import setup_business_intelligence
    BUSINESS_INTELLIGENCE_AVAILABLE = True
    logger.info("Business Intelligence features loaded")
except ImportError as e:
    BUSINESS_INTELLIGENCE_AVAILABLE = False
    logger.warning(f"Business Intelligence features not available: {e}")

# Configuration shortcuts
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
OUTPUT_FOLDER = app.config['OUTPUT_FOLDER']
ALLOWED_EXTENSIONS = app.config['ALLOWED_EXTENSIONS']

# Setup business intelligence routes immediately (not just in __main__)
if BUSINESS_INTELLIGENCE_AVAILABLE:
    try:
        app = setup_business_intelligence(app)
        logger.info("Business Intelligence routes registered")
    except Exception as e:
        logger.error(f"Business Intelligence setup failed: {e}")
        BUSINESS_INTELLIGENCE_AVAILABLE = False

# Security headers
if app.config['SECURE_HEADERS']:
    @app.after_request
    def set_secure_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_errors(f):
    """Decorator for consistent error handling and logging"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({'status': 'error', 'error': 'Invalid input', 'message': str(e)}), 400
        except FileNotFoundError as e:
            logger.warning(f"File not found in {f.__name__}: {str(e)}")
            return jsonify({'status': 'error', 'error': 'Resource not found'}), 404
        except PermissionError as e:
            logger.error(f"Permission error in {f.__name__}: {str(e)}")
            return jsonify({'status': 'error', 'error': 'Permission denied'}), 403
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}\n{traceback.format_exc()}")
            # Don't expose internal errors in production
            if app.config['DEBUG']:
                return jsonify({'status': 'error', 'error': 'Internal server error', 'details': str(e)}), 500
            return jsonify({'status': 'error', 'error': 'Internal server error'}), 500
    return decorated_function

def extract_pdf_data(pdf_path):
    """Extract structured data from PDF using PyMuPDF with OCR fallback"""
    if fitz is None:
        raise ImportError("PyMuPDF is not installed")
    doc = fitz.open(pdf_path)
    
    all_text = []
    pages_data = []
    has_ocr = False
    
    for page_num, page in enumerate(doc, 1):
        # Extract text using dict method for better spacing
        text_dict = page.get_text("dict")
        page_text_lines = []
        
        # Process blocks for better spacing
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        if text.strip():
                            # Add space between spans if needed
                            if line_text and not line_text.endswith(" "):
                                line_text += " "
                            line_text += text
                    if line_text.strip():
                        page_text_lines.append(line_text.strip())
        
        page_text = "\n".join(page_text_lines)
        
        # If very little text found, try OCR
        if len(page_text.strip()) < 10:
            try:
                # Get page as image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution for better OCR
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Try OCR with pytesseract
                try:
                    import pytesseract
                    page_text = pytesseract.image_to_string(img)
                    has_ocr = True
                except ImportError:
                    # Fallback: use basic image text detection from PyMuPDF
                    page_text = f"[Page {page_num}: Image-based content - Install pytesseract for OCR]"
            except Exception as e:
                page_text = f"[Page {page_num}: Unable to extract - {str(e)}]"
        
        all_text.append(page_text)
        
        # Get page info
        rect = page.rect
        images = page.get_images()
        
        pages_data.append({
            'page_number': page_num,
            'text': page_text,
            'width': rect.width,
            'height': rect.height,
            'images_count': len(images),
            'char_count': len(page_text)
        })
    
    full_text = '\n\n'.join(all_text)
    
    # Clean up spacing issues
    full_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', full_text)  # Add space between camelCase
    full_text = re.sub(r'(\w)(\d)', r'\1 \2', full_text)  # Space before numbers
    full_text = re.sub(r'(\d)([A-Z])', r'\1 \2', full_text)  # Space after numbers before caps
    full_text = re.sub(r' +', ' ', full_text)  # Multiple spaces to single
    full_text = re.sub(r'\n\n\n+', '\n\n', full_text)  # Multiple newlines to double
    full_text = re.sub(r'\n ', '\n', full_text)  # Remove leading spaces on lines
    
    # Parse sections by detecting headings
    sections = []
    current_section = None
    
    for line in full_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Detect headings: ALL CAPS, numbered sections, or lines ending with colon
        is_heading = (
            (len(line) > 3 and line.isupper() and len(line.split()) <= 10) or
            (line.endswith(':') and len(line.split()) <= 8 and not line.startswith(' ')) or
            (re.match(r'^[A-Z][A-Z\s&-]+$', line) and len(line.split()) <= 10) or
            (re.match(r'^\d+\.\s+[A-Z]', line) and len(line.split()) <= 12) or
            (re.match(r'^SECTION|^ARTICLE|^EXHIBIT|^SCHEDULE', line.upper()))
        )
        
        if is_heading:
            if current_section and current_section['content']:
                sections.append(current_section)
            current_section = {
                'heading': line.rstrip(':'),
                'level': 1,
                'content': []
            }
        elif current_section:
            current_section['content'].append(line)
        else:
            # Content before first heading
            if not current_section:
                current_section = {
                    'heading': 'Introduction',
                    'level': 1,
                    'content': [line]
                }
    
    if current_section and current_section['content']:
        sections.append(current_section)
    
    # Clean up sections
    for section in sections:
        section['content'] = '\n'.join(section['content'])
    
    # Extract metadata
    metadata = {
        'title': doc.metadata.get('title', ''),
        'author': doc.metadata.get('author', ''),
        'subject': doc.metadata.get('subject', ''),
        'creator': doc.metadata.get('creator', ''),
        'producer': doc.metadata.get('producer', ''),
        'num_pages': len(doc),
        'ocr_used': has_ocr
    }
    
    result = {
        'metadata': metadata,
        'full_text': full_text,
        'sections': sections,
        'pages': pages_data,
        'statistics': {
            'total_characters': len(full_text),
            'total_words': len(full_text.split()),
            'total_lines': len(full_text.split('\n')),
            'total_sections': len(sections),
            'total_pages': len(doc),
            'total_images': sum(p['images_count'] for p in pages_data),
            'ocr_applied': has_ocr
        }
    }
    
    doc.close()
    return result

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Check if critical components are available
        checks = {
            'pymupdf': fitz is not None,
            'business_intelligence': BUSINESS_INTELLIGENCE_AVAILABLE,
            'upload_folder': UPLOAD_FOLDER.exists(),
            'output_folder': OUTPUT_FOLDER.exists()
        }
        
        all_healthy = all(checks.values())
        status_code = 200 if all_healthy else 503
        
        return jsonify({
            'status': 'healthy' if all_healthy else 'degraded',
            'service': 'PDF Extractor API',
            'version': '1.0.0',
            'checks': checks
        }), status_code
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': 'Health check failed'}), 503

@app.route('/api/upload', methods=['POST'])
@handle_errors
def upload_pdf():
    """Handle PDF upload and processing"""
    logger.info("PDF upload request received")
    logger.info(f"Request form data: {dict(request.form)}")
    logger.info(f"Request files: {dict(request.files)}")
    
    # Check if user wants to use sample PDF
    # Check in form data, query params, or if no file is provided
    use_sample = (
        request.form.get('use_sample', '').lower() == 'true' or
        request.args.get('use_sample', '').lower() == 'true' or
        (request.form.get('use_sample') == 'true' and 'file' not in request.files)
    )
    
    logger.info(f"use_sample evaluated to: {use_sample}")
    
    if use_sample:
        # Use the default sample PDF
        sample_path = os.path.join(os.path.dirname(__file__), 'sample_lease.pdf')
        if not os.path.exists(sample_path):
            logger.error("Sample PDF not found")
            raise FileNotFoundError('Sample PDF not available')
        
        # Generate unique ID for this processing job
        job_id = str(uuid.uuid4())
        filename = 'sample_lease.pdf'
        
        logger.info(f"Processing sample PDF: job_id={job_id}")
        
        # Copy sample to uploads folder
        upload_path = UPLOAD_FOLDER / f"{job_id}_{filename}"
        import shutil
        shutil.copy2(sample_path, str(upload_path))
        
    else:
        # Validate request
        if 'file' not in request.files:
            logger.warning("Upload request missing file")
            raise ValueError('No file provided')
        
        file = request.files['file']
        
        if file.filename == '':
            logger.warning("Upload request with empty filename")
            raise ValueError('No file selected')
        
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            raise ValueError('Only PDF files are allowed')
        
        # Validate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            logger.warning(f"File too large: {file_size} bytes")
            raise ValueError(f'File too large. Maximum size: {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB')
        
        if file_size == 0:
            logger.warning("Empty file uploaded")
            raise ValueError('File is empty')
            
        # Generate unique ID for this processing job
        job_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        
        logger.info(f"Processing upload: job_id={job_id}, filename={filename}, size={file_size}")
        
        # Save uploaded file
        upload_path = UPLOAD_FOLDER / f"{job_id}_{filename}"
        file.save(str(upload_path))
    
    try:
        # Process PDF
        logger.info(f"Extracting data from PDF: {job_id}")
        extracted_data = extract_pdf_data(str(upload_path))
        
        # Convert to JSON
        output_data = {
            'job_id': job_id,
            'filename': filename,
            'status': 'success',
            'data': extracted_data
        }
        
        # Save output
        output_file = OUTPUT_FOLDER / f"{job_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully processed PDF: {job_id}")
        return jsonify(output_data), 200
        
    finally:
        # Always cleanup uploaded file
        try:
            if upload_path.exists():
                upload_path.unlink()
                logger.debug(f"Cleaned up upload file: {upload_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup upload file {upload_path}: {e}")

@app.route('/api/download/<job_id>', methods=['GET'])
@handle_errors
def download_result(job_id):
    """Download processed JSON result"""
    # Validate job_id format
    try:
        uuid.UUID(job_id)
    except ValueError:
        logger.warning(f"Invalid job_id format: {job_id}")
        raise ValueError('Invalid job ID format')
    
    output_file = OUTPUT_FOLDER / f"{job_id}.json"
    if not output_file.exists():
        logger.warning(f"Result not found: {job_id}")
        raise FileNotFoundError(f'Result not found for job ID: {job_id}')
    
    logger.info(f"Downloading result: {job_id}")
    return send_file(str(output_file), as_attachment=True)

@app.route('/api/results', methods=['GET'])
@handle_errors
def list_results():
    """List all processed results"""
    logger.debug("Listing all results")
    
    results = []
    for file in OUTPUT_FOLDER.glob('*.json'):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                results.append({
                    'job_id': data.get('job_id'),
                    'filename': data.get('filename'),
                    'status': data.get('status'),
                    'timestamp': data.get('timestamp', 'unknown')
                })
        except Exception as e:
            logger.warning(f"Failed to read result file {file}: {e}")
            continue
    
    logger.info(f"Listed {len(results)} results")
    return jsonify({'results': results, 'count': len(results)}), 200

if __name__ == '__main__':
    # Business intelligence already set up above for Gunicorn compatibility
    if not BUSINESS_INTELLIGENCE_AVAILABLE:
        logger.warning("Business Intelligence features disabled")
    
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting PDF Extraction API")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    logger.info(f"Port: {port}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    logger.info(f"Max upload size: {app.config['MAX_CONTENT_LENGTH'] // (1024*1024)}MB")
    
    # Use production WSGI server in production
    if not app.config['DEBUG']:
        try:
            from waitress import serve
            logger.info("Starting production server (Waitress)")
            serve(app, host='0.0.0.0', port=port, threads=4)
        except ImportError:
            logger.warning("Waitress not installed, using Flask development server")
            logger.warning("Install waitress for production: pip install waitress")
            app.run(host='0.0.0.0', port=port, debug=False)
    else:
        logger.info("Starting development server")
        app.run(host='0.0.0.0', port=port, debug=True)
