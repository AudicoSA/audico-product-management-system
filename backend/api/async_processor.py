import threading
import uuid
import time
from datetime import datetime
from typing import Dict
import os
import tempfile

class AsyncProcessor:
    """Handle async PDF processing"""
    
    def __init__(self):
        self.jobs = {}  # In-memory storage (use Redis in production)
    
    def start_processing(self, file, filename: str) -> str:
        """Start async PDF processing"""
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        self.jobs[job_id] = {
            'id': job_id,
            'filename': filename,
            'status': 'processing',
            'started_at': datetime.now().isoformat(),
            'progress': 0,
            'result': None,
            'error': None
        }
        
        # Start processing in background thread
        thread = threading.Thread(
            target=self._process_file,
            args=(job_id, file, filename)
        )
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def get_status(self, job_id: str) -> Dict:
        """Get processing status"""
        return self.jobs.get(job_id, {
            'id': job_id,
            'status': 'not_found',
            'error': 'Job not found'
        })
    
    def _process_file(self, job_id: str, file, filename: str):
        """Process file in background"""
        tmp_file_path = None
        
        try:
            # Update progress
            self.jobs[job_id]['progress'] = 10
            self.jobs[job_id]['status'] = 'extracting_text'
            
            # Save temp file
            fd, tmp_file_path = tempfile.mkstemp(suffix='.pdf')
            
            with os.fdopen(fd, 'wb') as tmp_file:
                file.save(tmp_file)
            
            time.sleep(0.1)  # Ensure file is written
            
            # Update progress
            self.jobs[job_id]['progress'] = 30
            
            # Import processing modules
            try:
                from pdf_processor.ocr_extractor import OCRExtractor
                from pdf_processor.data_parser import DataParser
                from pdf_processor.data_validator import DataValidator
            except ImportError as ie:
                self.jobs[job_id]['status'] = 'error'
                self.jobs[job_id]['error'] = f'Import error: {str(ie)}'
                return
            
            # Extract text
            self.jobs[job_id]['progress'] = 50
            self.jobs[job_id]['status'] = 'extracting_text'
            
            extractor = OCRExtractor()
            extraction_result = extractor.extract_text_from_pdf(tmp_file_path)
            
            if not extraction_result['success']:
                self.jobs[job_id]['status'] = 'error'
                self.jobs[job_id]['error'] = extraction_result['error']
                return
            
            # Parse products
            self.jobs[job_id]['progress'] = 70
            self.jobs[job_id]['status'] = 'parsing_products'
            
            parser = DataParser()
            parsing_result = parser.parse_text(extraction_result['text'])
            
            if not parsing_result['success']:
                self.jobs[job_id]['status'] = 'error'
                self.jobs[job_id]['error'] = parsing_result['error']
                return
            
            # Validate products
            self.jobs[job_id]['progress'] = 90
            self.jobs[job_id]['status'] = 'validating_data'
            
            validator = DataValidator()
            cleaned_products = []
            for product in parsing_result['products']:
                cleaned_product = validator.clean_product_data(product)
                cleaned_products.append(cleaned_product)
            
            validation_result = validator.validate_product_batch(cleaned_products)
            
            # Complete
            self.jobs[job_id]['progress'] = 100
            self.jobs[job_id]['status'] = 'completed'
            self.jobs[job_id]['completed_at'] = datetime.now().isoformat()
            self.jobs[job_id]['result'] = {
                'products_found': len(cleaned_products),
                'products': cleaned_products,
                'validation': validation_result,
                'extraction_method': extraction_result['method']
            }
            
        except Exception as e:
            self.jobs[job_id]['status'] = 'error'
            self.jobs[job_id]['error'] = str(e)
            
        finally:
            # Cleanup
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass

# Global processor instance
async_processor = AsyncProcessor()
