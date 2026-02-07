#!/usr/bin/env python3
"""
PDF Extraction POC - Handles 1000s of docs
MIT License - No schema design needed
"""

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from multiprocessing import Pool, cpu_count
from pathlib import Path
import json
import time

# Initialize Marker once (reuse across all workers)
converter = PdfConverter(artifact_dict=create_model_dict())

def process_single_pdf(pdf_path):
    """Process one PDF and return structured JSON"""
    try:
        # Extract structured data (auto-detects schema!)
        result = converter(str(pdf_path))
        
        # Convert to JSON
        output = {
            'filename': pdf_path.name,
            'status': 'success',
            'data': result.model_dump()
        }
        
        # Save individual result
        output_file = Path('outputs') / f"{pdf_path.stem}.json"
        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        return output
        
    except Exception as e:
        return {
            'filename': pdf_path.name,
            'status': 'failed',
            'error': str(e)
        }

def batch_process_pdfs(pdf_folder, num_workers=None):
    """Process all PDFs in parallel"""
    
    # Auto-detect CPU cores
    if num_workers is None:
        num_workers = cpu_count()
    
    # Get all PDFs
    pdf_files = list(Path(pdf_folder).glob('*.pdf'))
    total = len(pdf_files)
    
    print(f"Found {total} PDFs")
    print(f"Using {num_workers} workers")
    
    start_time = time.time()
    
    # Process in parallel
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_single_pdf, pdf_files)
    
    # Summary
    success = sum(1 for r in results if r['status'] == 'success')
    failed = total - success
    duration = time.time() - start_time
    
    print(f"\nCompleted in {duration:.2f} seconds")
    print(f"Success: {success} | Failed: {failed}")
    print(f"Speed: {total/duration:.1f} docs/second")
    
    return results

if __name__ == '__main__':
    # Usage: python extract.py
    results = batch_process_pdfs('input_pdfs')
    
    # Save summary
    with open('outputs/summary.json', 'w') as f:
        json.dump(results, f, indent=2)