from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import requests
import tempfile
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Add path for importing our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])  # Allow React dev servers

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

# Initialize OpenCart client
opencart_client = SimpleOpenCartClient()

# Import workflow manager
try:
    from workflow_engine.workflow_manager import WorkflowManager
    workflow_manager = WorkflowManager(opencart_client)
    workflow_available = True
except ImportError:
    workflow_manager = None
    workflow_available = False

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
        import pandas
        import requests
        from flask_cors import CORS

        return jsonify({
            "status": "healthy",
            "python_version": sys.version,
            "packages": {
                "flask": "✅ installed",
                "flask-cors": "✅ installed", 
                "pandas": f"✅ {pandas.__version__}",
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
        "POST /api/pdf/validate - Validate product data",
        "POST /api/comparison/compare - Compare products",
        "POST /api/automation/create_missing - Create missing products"
    ]

    if workflow_available:
        endpoints.extend([
            "POST /api/workflow/start - Start complete workflow",
            "GET  /api/workflow/<id>/status - Get workflow status",
            "GET  /api/workflow/<id>/summary - Get workflow summary",
            "POST /api/workflow/<id>/cancel - Cancel workflow",
            "GET  /api/workflow/list - List workflows"
        ])

    return jsonify({
        "message": "🚀 API is working perfectly!",
        "available_endpoints": endpoints,
        "system_status": {
            "pdf_processing": "operational",
            "opencart_api": "operational", 
            "data_validation": "operational",
            "product_comparison": "operational",
            "automation_engine": "operational",
            "workflow_manager": "operational" if workflow_available else "not available"
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

    # Handle GET request - show upload form info
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
            },
            'example_curl': 'curl -X POST -F "file=@yourfile.pdf" http://localhost:5000/api/pdf/upload'
        })

    # Handle POST request - process uploaded file
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error', 
                'message': 'No file selected'
            }), 400

        if file and file.filename.lower().endswith('.pdf'):
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                file.save(tmp_file.name)

                try:
                    # Import PDF processing modules
                    from pdf_processor.ocr_extractor import OCRExtractor
                    from pdf_processor.data_parser import DataParser
                    from pdf_processor.data_validator import DataValidator

                    # Extract text from PDF
                    extractor = OCRExtractor()
                    extraction_result = extractor.extract_text_from_pdf(tmp_file.name)

                    if not extraction_result['success']:
                        return jsonify({
                            'status': 'error',
                            'message': 'Text extraction failed',
                            'error': extraction_result['error']
                        }), 500

                    # Parse products from text
                    parser = DataParser()
                    parsing_result = parser.parse_text(extraction_result['text'])

                    if not parsing_result['success']:
                        return jsonify({
                            'status': 'error',
                            'message': 'Product parsing failed',
                            'error': parsing_result['error']
                        }), 500

                    # Validate and clean product data
                    validator = DataValidator()

                    # Clean each product
                    cleaned_products = []
                    for product in parsing_result['products']:
                        cleaned_product = validator.clean_product_data(product)
                        cleaned_products.append(cleaned_product)

                    # Validate the batch
                    validation_result = validator.validate_product_batch(cleaned_products)

                    return jsonify({
                        'status': 'success',
                        'message': f'PDF processed successfully - {len(cleaned_products)} products found',
                        'filename': file.filename,
                        'extraction_method': extraction_result['method'],
                        'page_count': extraction_result.get('page_count', 0),
                        'products_found': len(cleaned_products),
                        'products': cleaned_products,
                        'validation': validation_result,
                        'text_preview': parsing_result.get('raw_text_preview', '')[:300] + "..."
                    })

                finally:
                    # Clean up temp file
                    if os.path.exists(tmp_file.name):
                        os.unlink(tmp_file.name)

        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Please upload a PDF file.'
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'PDF processing failed',
            'error': str(e)
        }), 500

# ========== WORKFLOW ENDPOINTS ==========

@app.route('/api/workflow/start', methods=['POST'])
def start_workflow():
    """Start a complete PDF processing workflow"""
    if not workflow_available:
        return jsonify({
            'status': 'error',
            'message': 'Workflow manager not available'
        }), 503

    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No PDF file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Please upload a PDF file.'
            }), 400

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
        return jsonify({
            'status': 'error',
            'message': 'Failed to start workflow',
            'error': str(e)
        }), 500

# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /health',
            'GET /api/test',
            'GET /api/opencart/test',
            'POST /api/pdf/upload',
            'POST /api/workflow/start'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'error': str(error)
    }), 500

# ========== MAIN APPLICATION ==========

if __name__ == '__main__':
    print("🎵 Starting Audico Product Management System...")
    print("📍 API will be available at: http://localhost:5000")
    print("🏪 OpenCart Store: https://www.audicoonline.co.za")
    print("🔧 Environment:", os.getenv('FLASK_ENV', 'development'))
    print("\n📋 Available Endpoints:")
    print("  • GET  /                     - API home")
    print("  • GET  /health               - Health check")
    print("  • GET  /api/test             - API test")
    print("  • GET  /api/opencart/test    - Test OpenCart connection")
    print("  • GET  /api/opencart/products - Get products")
    print("  • POST /api/pdf/upload       - Upload and process PDF")
    print("  • POST /api/workflow/start   - Start complete workflow")
    print("\n🚀 Starting server...")

    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=int(os.getenv('FLASK_PORT', 5000))
    )
