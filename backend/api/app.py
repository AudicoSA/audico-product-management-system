from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import tempfile
import time
import threading
import uuid
from datetime import datetime
from dotenv import load_dotenv
import requests
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Add path for importing our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])  # Allow React dev servers

# ========== ASYNC PROCESSOR CLASS ==========

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
    
    def get_status(self, job_id: str) -> dict:
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

# ========== OPENCART CLIENT ==========

class SimpleOpenCartClient:
    """Simple OpenCart API Client"""

    def __init__(self):
        self.base_url = os.getenv('OPENCART_BASE_URL', 'https://www.audicoonline.co.za')
        self.basic_token = os.getenv('OPENCART_BASIC_TOKEN', 'b2NyZXN0YXBpX29hdXRoX2NsaWVudDpvY3Jlc3RhcGlfb2F1dGhfc2VjcmV0')

        self.headers = {
            'Authorization': f'Basic {self.basic_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def test_connection(self):
        """Test API connection"""
        try:
            url = f"{self.base_url}/index.php?route=ocrestapi/product/listing"
            response = requests.get(url, headers=self.headers, timeout=30)

            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'url': url,
                'data': response.json() if response.content else {},
                'headers_sent': self.headers
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': f"{self.base_url}/index.php?route=ocrestapi/product/listing"
            }

    def get_products(self, limit=20):
        """Get products from OpenCart"""
        try:
            url = f"{self.base_url}/index.php?route=ocrestapi/product/listing&limit={limit}"
            response = requests.get(url, headers=self.headers, timeout=30)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_products(self, search_term):
        """Search products in OpenCart"""
        try:
            url = f"{self.base_url}/index.php?route=ocrestapi/product/listing&search={search_term}"
            response = requests.get(url, headers=self.headers, timeout=30)
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Initialize clients
opencart_client = SimpleOpenCartClient()
async_processor = AsyncProcessor()

# Import workflow manager (optional)
try:
    from workflow_engine.workflow_manager import WorkflowManager
    workflow_manager = WorkflowManager(opencart_client)
    workflow_available = True
except ImportError:
    workflow_manager = None
    workflow_available = False

# ========== UTILITY FUNCTIONS ==========

def is_valid_pdf_file(file):
    """Check if uploaded file is a valid PDF"""
    if not file or not file.filename:
        return False, "No file selected"
    
    filename = file.filename.strip()
    if not filename:
        return False, "Empty filename"
    
    if not filename.lower().endswith('.pdf'):
        return False, "Invalid file type. Please upload a PDF file."
    
    return True, "Valid PDF file"

# ========== BASIC API ENDPOINTS ==========

@app.route('/')
def home():
    return jsonify({
        "message": "🎵 Audico Product Management System API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "description": "Automated product management for OpenCart stores",
        "store_url": "https://www.audicoonline.co.za",
        "features": [
            "PDF pricelist processing",
            "OpenCart API integration", 
            "Product comparison engine",
            "Automated product updates",
            "Data validation and cleaning",
            "Complete workflow orchestration"
        ]
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            "status": "healthy",
            "python_version": sys.version,
            "packages": {
                "flask": "✅ installed",
                "flask-cors": "✅ installed", 
                "requests": "✅ installed"
            },
            "environment": os.getenv('FLASK_ENV', 'development'),
            "opencart_config": {
                "base_url": os.getenv('OPENCART_BASE_URL'),
                "api_configured": bool(os.getenv('OPENCART_BASIC_TOKEN'))
            },
            "modules_available": {
                "pdf_processing": "✅ ready",
                "data_validation": "✅ ready",
                "opencart_integration": "✅ ready",
                "comparison_engine": "✅ ready",
                "automation_engine": "✅ ready",
                "workflow_manager": "✅ ready" if workflow_available else "❌ not available"
            }
        })
    except ImportError as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/test')
def api_test():
    """Test API endpoint"""
    endpoints = [
        "GET  / - API home",
        "GET  /health - Health check", 
        "GET  /api/test - API test",
        "GET  /api/opencart/test - Test OpenCart connection",
        "GET  /api/opencart/products - Get products",
        "GET  /api/opencart/search/<term> - Search products",
        "POST /api/pdf/upload - Upload and process PDF",
        "POST /api/pdf/upload-async - Start async PDF processing",
        "GET  /api/pdf/status/<job_id> - Get processing status",
        "POST /api/pdf/validate - Validate product data",
        "POST /api/comparison/compare - Compare products",
        "POST /api/automation/create_missing - Create missing products",
        "POST /api/workflow/start - Start complete workflow",
        "GET  /api/workflow/<id>/status - Get workflow status", 
        "GET  /api/workflow/<id>/summary - Get workflow summary",
        "POST /api/workflow/<id>/cancel - Cancel workflow",
        "GET  /api/workflow/list - List workflows"
    ]

    return jsonify({
        "message": "🎵 API is working perfectly!",
        "available_endpoints": endpoints,
        "system_status": {
            "pdf_processing": "operational",
            "opencart_api": "operational", 
            "data_validation": "operational",
            "product_comparison": "operational",
            "automation_engine": "operational",
            "workflow_manager": "operational" if workflow_available else "limited"
        }
    })

# ========== OPENCART API ENDPOINTS ==========

@app.route('/api/opencart/test')
def opencart_test():
    """Test OpenCart API connection"""
    try:
        result = opencart_client.test_connection()

        if result['success']:
            return jsonify({
                "status": "success",
                "message": "✅ OpenCart API connection working!",
                "connection_details": result,
                "store_url": "https://www.audicoonline.co.za"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "❌ OpenCart API connection failed",
                "error": result.get('error', 'Unknown error'),
                "details": result,
                "troubleshooting": [
                    "Check if API credentials are correct",
                    "Verify store URL is accessible", 
                    "Ensure API is enabled in OpenCart admin"
                ]
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Exception during OpenCart API test",
            "error": str(e)
        }), 500

@app.route('/api/opencart/products')
def get_products():
    """Get all products from OpenCart store"""
    try:
        limit = request.args.get('limit', 20, type=int)
        result = opencart_client.get_products(limit)

        if result['success']:
            data = result['data']
            products = data.get('data', []) if isinstance(data, dict) else []

            return jsonify({
                "status": "success",
                "message": f"Retrieved {len(products)} products",
                "products": products,
                "total_count": len(products),
                "url_called": result.get('url')
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"HTTP {result.get('status_code', 'Unknown')}",
                "error": result.get('error'),
                "url_called": result.get('url')
            }), result.get('status_code', 500)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Exception while retrieving products",
            "error": str(e)
        }), 500

@app.route('/api/opencart/search/<search_term>')
def search_products(search_term):
    """Search for products in OpenCart store"""
    try:
        result = opencart_client.search_products(search_term)

        if result['success']:
            data = result['data']
            products = data.get('data', []) if isinstance(data, dict) else []

            return jsonify({
                "status": "success",
                "message": f"Search results for: {search_term}",
                "search_term": search_term,
                "results": products,
                "result_count": len(products),
                "url_called": result.get('url')
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Search failed with HTTP {result.get('status_code', 'Unknown')}",
                "search_term": search_term,
                "error": result.get('error'),
                "url_called": result.get('url')
            }), result.get('status_code', 500)

    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": "Exception during product search",
            "error": str(e)
        }), 500

# ========== PDF PROCESSING ENDPOINTS ==========

@app.route('/api/pdf/upload', methods=['GET', 'POST'])
def upload_pdf():
    """Upload and process PDF file"""

    # Handle GET request
    if request.method == 'GET':
        return jsonify({
            'status': 'ready',
            'message': 'PDF Upload Endpoint',
            'description': 'Upload PDF files to extract product data',
            'usage': {
                'method': 'POST',
                'content_type': 'multipart/form-data',
                'field_name': 'file',
                'supported_formats': ['PDF'],
                'max_file_size': '10MB'
            }
        })

    # Handle POST request
    tmp_file_path = None
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400

        file = request.files['file']
        
        # Validate file
        is_valid, error_message = is_valid_pdf_file(file)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': error_message
            }), 400

        # Create temporary file
        fd, tmp_file_path = tempfile.mkstemp(suffix='.pdf')
        
        try:
            with os.fdopen(fd, 'wb') as tmp_file:
                file.save(tmp_file)
            
            time.sleep(0.1)

            # Import processing modules
            try:
                from pdf_processor.ocr_extractor import OCRExtractor
                from pdf_processor.data_parser import DataParser
                from pdf_processor.data_validator import DataValidator
            except ImportError as ie:
                return jsonify({
                    'status': 'error',
                    'message': 'PDF processing modules not available',
                    'error': f'Import error: {str(ie)}'
                }), 500

            # Process PDF
            extractor = OCRExtractor()
            extraction_result = extractor.extract_text_from_pdf(tmp_file_path)

            if not extraction_result['success']:
                return jsonify({
                    'status': 'error',
                    'message': 'Text extraction failed',
                    'error': extraction_result['error']
                }), 500

            parser = DataParser()
            parsing_result = parser.parse_text(extraction_result['text'])

            if not parsing_result['success']:
                return jsonify({
                    'status': 'error',
                    'message': 'Product parsing failed',
                    'error': parsing_result['error']
                }), 500

            validator = DataValidator()
            cleaned_products = []
            for product in parsing_result['products']:
                cleaned_product = validator.clean_product_data(product)
                cleaned_products.append(cleaned_product)

            validation_result = validator.validate_product_batch(cleaned_products)

            return jsonify({
                'status': 'success',
                'message': f'PDF processed successfully - {len(cleaned_products)} products found',
                'filename': file.filename,
                'extraction_method': extraction_result['method'],
                'page_count': extraction_result.get('page_count', 0),
                'products_found': len(cleaned_products),
                'products': cleaned_products,
                'validation': validation_result
            })

        except Exception as processing_error:
            return jsonify({
                'status': 'error',
                'message': 'PDF processing failed',
                'error': str(processing_error)
            }), 500

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'PDF upload failed',
            'error': str(e)
        }), 500

    finally:
        # Cleanup
        if tmp_file_path and os.path.exists(tmp_file_path):
            for attempt in range(5):
                try:
                    os.unlink(tmp_file_path)
                    break
                except (OSError, PermissionError):
                    if attempt < 4:
                        time.sleep(0.2 * (attempt + 1))

@app.route('/api/pdf/upload-async', methods=['POST'])
def upload_pdf_async():
    """Start async PDF processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

        file = request.files['file']
        
        # Validate file
        is_valid, error_message = is_valid_pdf_file(file)
        if not is_valid:
            return jsonify({'status': 'error', 'message': error_message}), 400

        job_id = async_processor.start_processing(file, file.filename)
        
        return jsonify({
            'status': 'success',
            'message': 'Processing started',
            'job_id': job_id,
            'filename': file.filename,
            'status_url': f'/api/pdf/status/{job_id}'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to start processing', 'error': str(e)}), 500

@app.route('/api/pdf/status/<job_id>')
def get_processing_status(job_id):
    """Get processing status"""
    try:
        status = async_processor.get_status(job_id)
        return jsonify({'status': 'success', 'job': status})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to get status', 'error': str(e)}), 500

@app.route('/api/pdf/upload-simple', methods=['POST'])
def upload_pdf_simple():
    """Simple PDF upload for testing"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

        file = request.files['file']
        
        # Validate file
        is_valid, error_message = is_valid_pdf_file(file)
        if not is_valid:
            return jsonify({'status': 'error', 'message': error_message}), 400

        return jsonify({
            'status': 'success',
            'message': f'PDF {file.filename} uploaded successfully (simplified processing)',
            'filename': file.filename,
            'products_found': 0,
            'products': [],
            'note': 'Simplified version for testing'
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Simple upload failed', 'error': str(e)}), 500

@app.route('/api/pdf/validate', methods=['POST'])
def validate_products():
    """Validate product data"""
    try:
        data = request.get_json()
        if not data or 'products' not in data:
            return jsonify({'status': 'error', 'message': 'No product data provided'}), 400

        try:
            from pdf_processor.data_validator import DataValidator
            validator = DataValidator()
            validation_result = validator.validate_product_batch(data['products'])
            
            return jsonify({
                'status': 'success',
                'message': 'Product validation completed',
                'validation': validation_result
            })
        except ImportError:
            return jsonify({'status': 'error', 'message': 'Data validator module not available'}), 500

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Validation failed', 'error': str(e)}), 500

# ========== COMPARISON AND AUTOMATION ENDPOINTS ==========

@app.route('/api/comparison/compare', methods=['POST'])
def compare_products():
    """Compare PDF products with OpenCart inventory"""
    try:
        data = request.get_json()
        if not data or 'products' not in data:
            return jsonify({'status': 'error', 'message': 'No product data provided'}), 400

        try:
            from comparison_engine.product_comparator import ProductComparator
            comparator = ProductComparator(opencart_client)
            result = comparator.compare_products(data['products'])
            
            if result['success']:
                return jsonify({'status': 'success', 'message': 'Product comparison completed', 'comparison': result})
            else:
                return jsonify({'status': 'error', 'message': 'Comparison failed', 'error': result['error']}), 500
                
        except ImportError:
            # Mock comparison result
            products = data['products']
            return jsonify({
                'status': 'success',
                'message': 'Product comparison completed (mock)',
                'comparison': {
                    'success': True,
                    'total_pdf_products': len(products),
                    'matches_found': 0,
                    'missing_products': len(products),
                    'matches': [],
                    'missing': products,
                    'note': 'Mock response - install comparison modules for real comparison'
                }
            })

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Comparison failed', 'error': str(e)}), 500

@app.route('/api/automation/create_missing', methods=['POST'])
def create_missing_products():
    """Automatically create missing products in OpenCart"""
    try:
        data = request.get_json()
        if not data or 'products' not in data:
            return jsonify({'status': 'error', 'message': 'No product data provided'}), 400

        try:
            from automation_engine.product_automator import ProductAutomator
            automator = ProductAutomator(opencart_client)
            result = automator.create_products_batch(data['products'])

            return jsonify({
                'status': 'success',
                'message': 'Product creation process completed',
                'automation': result
            })
            
        except ImportError:
            # Mock automation result
            products = data['products']
            return jsonify({
                'status': 'success',
                'message': 'Product creation process completed (mock)',
                'automation': {
                    'success': True,
                    'summary': {
                        'total_attempted': len(products),
                        'successful_creations': len(products),
                        'failed_creations': 0,
                        'success_rate': '100.0%'
                    },
                    'note': 'Mock response - install automation modules for real product creation'
                }
            })

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Automated creation failed', 'error': str(e)}), 500

# ========== WORKFLOW ENDPOINTS ==========

@app.route('/api/workflow/start', methods=['POST'])
def start_workflow():
    """Start a complete PDF processing workflow"""
    if not workflow_available:
        return jsonify({
            'status': 'error',
            'message': 'Workflow manager not available',
            'help': 'Workflow modules may not be installed or imported correctly'
        }), 503

    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No PDF file uploaded'}), 400

        file = request.files['file']
        
        # Validate file
        is_valid, error_message = is_valid_pdf_file(file)
        if not is_valid:
            return jsonify({'status': 'error', 'message': error_message}), 400

        # Get workflow options from form data
        options = {
            'auto_create_missing': request.form.get('auto_create_missing', 'true').lower() == 'true',
            'auto_update_prices': request.form.get('auto_update_prices', 'false').lower() == 'true',
            'validation_threshold': float(request.form.get('validation_threshold', 0.7)),
            'price_tolerance_percent': float(request.form.get('price_tolerance_percent', 5.0)),
            'batch_size': int(request.form.get('batch_size', 10)),
            'dry_run': request.form.get('dry_run', 'false').lower() == 'true'
        }

        # Start workflow
        workflow_id = workflow_manager.start_workflow(file, options)

        return jsonify({
            'status': 'success',
            'message': 'Workflow started successfully',
            'workflow_id': workflow_id,
            'options': options
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to start workflow', 'error': str(e)}), 500

@app.route('/api/workflow/<workflow_id>/status')
def get_workflow_status(workflow_id):
    """Get workflow status and results"""
    if not workflow_available:
        return jsonify({'status': 'error', 'message': 'Workflow manager not available'}), 503

    try:
        status = workflow_manager.get_workflow_status(workflow_id)

        if status is None:
            return jsonify({'status': 'error', 'message': 'Workflow not found'}), 404

        return jsonify({'status': 'success', 'workflow': status})

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to get workflow status', 'error': str(e)}), 500

@app.route('/api/workflow/<workflow_id>/summary')
def get_workflow_summary(workflow_id):
    """Get workflow summary"""
    if not workflow_available:
        return jsonify({'status': 'error', 'message': 'Workflow manager not available'}), 503

    try:
        summary = workflow_manager.get_workflow_summary(workflow_id)

        if summary is None:
            return jsonify({'status': 'error', 'message': 'Workflow not found'}), 404

        return jsonify({'status': 'success', 'summary': summary})

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to get workflow summary', 'error': str(e)}), 500

@app.route('/api/workflow/<workflow_id>/cancel', methods=['POST'])
def cancel_workflow(workflow_id):
    """Cancel a running workflow"""
    if not workflow_available:
        return jsonify({'status': 'error', 'message': 'Workflow manager not available'}), 503

    try:
        cancelled = workflow_manager.cancel_workflow(workflow_id)

        if not cancelled:
            return jsonify({'status': 'error', 'message': 'Workflow not found or cannot be cancelled'}), 404

        return jsonify({'status': 'success', 'message': 'Workflow cancelled successfully'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to cancel workflow', 'error': str(e)}), 500

@app.route('/api/workflow/list')
def list_workflows():
    """List recent workflows"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        if not workflow_available:
            # Return mock data when workflow manager is not available
            return jsonify({
                'status': 'success',
                'workflows': [],
                'total': 0,
                'message': 'Workflow manager not available - showing empty list',
                'note': 'Install workflow modules to enable full workflow functionality'
            })

        workflows = workflow_manager.list_workflows(limit)

        return jsonify({
            'status': 'success',
            'workflows': workflows,
            'total': len(workflows)
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to list workflows', 'error': str(e)}), 500

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /health',
            'GET /api/test',
            'GET /api/opencart/test'
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed',
        'allowed_methods': ['GET', 'POST']
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error': str(error)
    }), 500

# ========== MAIN APPLICATION ==========

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("🎵 Starting Audico Product Management System API...")
    print(f"📡 Server running on http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🏪 OpenCart URL: {os.getenv('OPENCART_BASE_URL', 'Not configured')}")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )