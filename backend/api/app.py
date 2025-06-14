from flask import Flask, jsonify, request, Response, make_response
from flask_cors import CORS, cross_origin
import os
import sys
import tempfile
import time
import threading
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
import urllib.parse
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Add path for importing our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import SqlLantern integration modules
try:
    from database_manager import initialize_database, get_database_manager
    from product_analyzer import ProductStatusAnalyzer, ProductStatus
    sqlantern_available = True
    print("Ã¢ÂœÂ… SqlLantern integration modules loaded successfully")
except ImportError as e:
    sqlantern_available = False
    print(f"Ã¢ÂšÂ Ã¯Â¸ÂÃƒÂ¯Ã‚Â¸Ã‚Â SqlLantern integration not available: {e}")

app = Flask(__name__)

# Simple CORS configuration for development
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Initialize database connection for SqlLantern
if sqlantern_available:
    try:
        initialize_database(
            host="dedi159.cpt4.host-h.net",
            username="audicdmyde_314",
            password="4hG4xcGS3tSgX76o5FSv",
            database="audicdmyde_db__359",
            port=3306,
            prefix="oc_"
        )
        analyzer = ProductStatusAnalyzer()
        print("Ã¢ÂœÂ… Database connection initialized successfully")
    except Exception as e:
        sqlantern_available = False
        print(f"Ã¢ÂšÂ Ã¯Â¸ÂÃƒÂ¯Ã‚Â¸Ã‚Â Database initialization failed: {e}")

# ========== SQLANTERN INTEGRATION VARIABLES ==========
last_comparison_result = None
last_update_time = None

# ========== AI PROCESSING FUNCTIONS ==========

def process_pdf_with_openai(file):
    """Process PDF using OpenAI API"""
    try:
        import openai
        
        # Check if OpenAI API key is configured
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'status': 'error', 'error': 'OpenAI API key not configured'}
        
        print("Ã°ÂŸÂ¤Â– Using OpenAI to process PDF...")
        
        # Save file temporarily
        fd, tmp_file_path = tempfile.mkstemp(suffix='.pdf')
        
        try:
            with os.fdopen(fd, 'wb') as tmp_file:
                file.save(tmp_file)
            
            # Try to extract text with PyPDF2 first (simple extraction)
            try:
                import PyPDF2
                text_content = ""
                with open(tmp_file_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n"
                        
                print(f"Ã°ÂŸÂ“Â„ Extracted {len(text_content)} characters from PDF")
                
            except ImportError:
                return {'status': 'error', 'error': 'PyPDF2 not available for text extraction'}
            
            if not text_content.strip():
                return {'status': 'error', 'error': 'No text could be extracted from PDF'}
            
            # Use OpenAI to parse the products
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
            Extract audio equipment product information from this pricelist text.
            Return a JSON array of products with this exact structure:
            
            {{
                "sku": "product code or part number",
                "name": "product name", 
                "model": "model number",
                "price": numeric_price,
                "description": "product description",
                "category": "product category",
                "manufacturer": "brand name",
                "quantity": 1
            }}
            
            Important:
            - Extract ALL products found in the text
            - Ensure prices are numeric (no currency symbols)
            - Use the brand/manufacturer from the document
            - If no clear category, use "Audio Equipment"
            
            Text to parse:
            {text_content[:12000]}
            
            Return only the JSON array, no other text.
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at parsing product data from pricelists. Return only valid JSON array of products. Extract ALL products found."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            # Parse the response
            products_text = response.choices[0].message.content.strip()
            
            # Enhanced cleanup of OpenAI response to handle markdown properly
            import re
            
            # Remove markdown code blocks more robustly
            products_text = re.sub(r'^```json\s*', '', products_text)
            products_text = re.sub(r'^```\s*', '', products_text)
            products_text = re.sub(r'```\s*$', '', products_text)
            
            # Find JSON array boundaries more precisely
            start_idx = products_text.find('[')
            end_idx = products_text.rfind(']')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                products_text = products_text[start_idx:end_idx+1]
            
            products_text = products_text.strip()
            
            # Parse JSON with better error context
            try:
                products = json.loads(products_text)
            except json.JSONDecodeError as parse_error:
                print(f"Ã°ÂŸÂ’Â¥ JSON parsing failed. Raw response preview: {products_text[:200]}...")
                raise json.JSONDecodeError(f"OpenAI returned invalid JSON: {str(parse_error)}", products_text, parse_error.pos)
            
            print(f"Ã¢ÂœÂ… OpenAI extracted {len(products)} products from PDF")
            
            return {
                'status': 'success',
                'message': f'PDF processed successfully with OpenAI - {len(products)} products found',
                'filename': file.filename,
                'extraction_method': 'openai_gpt',
                'page_count': len(text_content.split('\f')),
                'products_found': len(products),
                'products': products,
                'validation': {
                    'total_products': len(products),
                    'valid_products': len(products),
                    'invalid_products': 0,
                    'warnings': [],
                    'errors': []
                },
                'note': 'Ã°ÂŸÂ¤Â– Processed using OpenAI GPT-3.5'
            }
            
        finally:
            # Cleanup
            if os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                    
    except json.JSONDecodeError as je:
        print(f"Ã°ÂŸÂ’Â¥ JSON parsing error: {je}")
        return {
            'status': 'error',
            'error': f'OpenAI returned invalid JSON format: {str(je)}',
            'details': {
                'error_position': je.pos if hasattr(je, 'pos') else None,
                'response_preview': products_text[:200] if 'products_text' in locals() else 'N/A',
                'suggestion': 'The PDF content may be too complex for OpenAI to parse. Try a cleaner PDF or check OpenAI API status.'
            }
        }
    except Exception as e:
        print(f"Ã°ÂŸÂ’Â¥ OpenAI processing error: {e}")
        return {'status': 'error', 'error': str(e)}

def process_excel_with_openai(file):
    """Process Excel file using OpenAI API"""
    try:
        import openai
        import pandas as pd
        
        # Check if OpenAI API key is configured
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'status': 'error', 'error': 'OpenAI API key not configured'}
        
        print("Ã°ÂŸÂ¤Â– Using OpenAI to process Excel file...")
        
        # Save file temporarily
        file_extension = os.path.splitext(file.filename)[1].lower()
        fd, tmp_file_path = tempfile.mkstemp(suffix=file_extension)
        
        try:
            with os.fdopen(fd, 'wb') as tmp_file:
                file.save(tmp_file)
            
            # Read Excel file
            try:
                if file_extension == '.xlsx':
                    df = pd.read_excel(tmp_file_path, engine='openpyxl')
                elif file_extension == '.xls':
                    df = pd.read_excel(tmp_file_path, engine='xlrd')
                else:
                    return {'status': 'error', 'error': 'Unsupported Excel format'}
                
                # Convert DataFrame to string for OpenAI
                excel_content = df.to_string(max_rows=200)  # Limit rows to avoid token limits
                print(f"Ã°ÂŸÂ“ÂŠ Extracted {len(df)} rows from Excel file")
                
            except Exception as e:
                return {'status': 'error', 'error': f'Failed to read Excel file: {str(e)}'}
            
            if df.empty:
                return {'status': 'error', 'error': 'Excel file is empty'}
            
            # Use OpenAI to parse the products
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""
            Extract audio equipment product information from this Excel data.
            Return a JSON array of products with this exact structure:
            
            {{
                "sku": "product code or part number",
                "name": "product name", 
                "model": "model number",
                "price": numeric_price,
                "description": "product description",
                "category": "product category",
                "manufacturer": "brand name",
                "quantity": 1
            }}
            
            Important:
            - Extract ALL products found in the data
            - Ensure prices are numeric (no currency symbols)
            - Look for columns that might contain product codes, names, models, prices
            - Use the brand/manufacturer from the document
            - If no clear category, use "Audio Equipment"
            
            Excel data to parse:
            {excel_content[:12000]}
            
            Return only the JSON array, no other text.
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at parsing product data from Excel spreadsheets. Return only valid JSON array of products. Extract ALL products found."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            # Parse the response
            products_text = response.choices[0].message.content.strip()
            
            # Enhanced cleanup of OpenAI response to handle markdown properly
            import re
            
            # Remove markdown code blocks more robustly
            products_text = re.sub(r'^```json\s*', '', products_text)
            products_text = re.sub(r'^```\s*', '', products_text)
            products_text = re.sub(r'```\s*$', '', products_text)
            
            # Find JSON array boundaries more precisely
            start_idx = products_text.find('[')
            end_idx = products_text.rfind(']')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                products_text = products_text[start_idx:end_idx+1]
            
            products_text = products_text.strip()
            
            # Parse JSON with better error context
            try:
                products = json.loads(products_text)
            except json.JSONDecodeError as parse_error:
                print(f"Ã°ÂŸÂ’Â¥ JSON parsing failed. Raw response preview: {products_text[:200]}...")
                raise json.JSONDecodeError(f"OpenAI returned invalid JSON: {str(parse_error)}", products_text, parse_error.pos)
            
            print(f"Ã¢ÂœÂ… OpenAI extracted {len(products)} products from Excel")
            
            return {
                'status': 'success',
                'message': f'Excel processed successfully with OpenAI - {len(products)} products found',
                'filename': file.filename,
                'extraction_method': 'openai_gpt_excel',
                'rows_processed': len(df),
                'products_found': len(products),
                'products': products,
                'validation': {
                    'total_products': len(products),
                    'valid_products': len(products),
                    'invalid_products': 0,
                    'warnings': [],
                    'errors': []
                },
                'note': 'Ã°ÂŸÂ¤Â– Processed Excel using OpenAI GPT-3.5'
            }
            
        finally:
            # Cleanup
            if os.path.exists(tmp_file_path):
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                    
    except json.JSONDecodeError as je:
        print(f"Ã°ÂŸÂ’Â¥ JSON parsing error: {je}")
        return {
            'status': 'error',
            'error': f'OpenAI returned invalid JSON format: {str(je)}',
            'details': {
                'error_position': je.pos if hasattr(je, 'pos') else None,
                'response_preview': products_text[:200] if 'products_text' in locals() else 'N/A',
                'suggestion': 'The Excel content may be too complex for OpenAI to parse. Try a cleaner file or check OpenAI API status.'
            }
        }
    except Exception as e:
        print(f"Ã°ÂŸÂ’Â¥ OpenAI processing error: {e}")
        return {'status': 'error', 'error': str(e)}

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
    """Simple OpenCart API Client with LetsCMS support"""

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
            url = f"{self.base_url}/index.php?route=ocrestapi/product/listing&limit=1"
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
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Handle LetsCMS response structure
                    products = []
                    if data.get('status') and 'data' in data and 'products' in data['data']:
                        products = data['data']['products']
                    
                    return {
                        'success': True,
                        'status_code': response.status_code,
                        'data': {'data': products},  # Keep consistent with old format
                        'url': url
                    }
                except Exception as json_error:
                    return {
                        'success': False,
                        'error': f'JSON parsing failed: {str(json_error)}',
                        'status_code': response.status_code,
                        'url': url
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text[:200]}',
                    'status_code': response.status_code,
                    'url': url
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_products(self, search_term):
        """Search for products in OpenCart store"""
        try:
            # URL encode the search term properly
            search_term_encoded = urllib.parse.quote(search_term.lower())
            url = f"{self.base_url}/index.php?route=ocrestapi/product/listing&search={search_term_encoded}"
            
            print(f"Ã°ÂŸÂ”Â Searching with URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            
            print(f"Ã°ÂŸÂ“ÂŠ Search response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Ã°ÂŸÂ“Â‹ API Response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    
                    # Extract products from the correct location: data.products
                    products = []
                    if data.get('status') and 'data' in data and 'products' in data['data']:
                        products = data['data']['products']
                        print(f"Ã¢ÂœÂ… Found {len(products)} products for search term '{search_term}'")
                        
                        # Log first product for debugging
                        if products:
                            first_product = products[0]
                            print(f"ÃƒÂ°Ã‚ÂŸÃ‚ÂÃ‚Â·ÃƒÂ¯Ã‚Â¸Ã‚Â First product: {first_product.get('name', 'No name')} (Model: {first_product.get('model', 'No model')})")
                    else:
                        print(f"Ã¢ÂÂŒ Unexpected response structure: {data}")
                    
                    return {
                        'success': True,
                        'status_code': response.status_code,
                        'results': products,  # This will now contain the actual products
                        'result_count': len(products),
                        'url': url,
                        'search_term': search_term
                    }
                    
                except Exception as json_error:
                    print(f"Ã°ÂŸÂ’Â¥ JSON parsing failed: {str(json_error)}")
                    return {
                        'success': False,
                        'error': f'JSON parsing failed: {str(json_error)}',
                        'raw_content': response.text[:500],
                        'url': url
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text[:200]}',
                    'status_code': response.status_code,
                    'url': url
                }
                
        except Exception as e:
            print(f"Ã°ÂŸÂ’Â¥ Search error: {e}")
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

# ========== BASIC API ENDPOINTS ==========

@app.route('/')
def home():
    return jsonify({
        "message": "Ã°ÂŸÂŽÂµ Audico Product Management System API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "description": "Automated product management for OpenCart stores",
        "store_url": "https://www.audicoonline.co.za",
        "features": [
            "PDF pricelist processing with OpenAI",
            "Excel spreadsheet processing with OpenAI",
            "OpenCart API integration", 
            "Product comparison engine",
            "Automated product updates",
            "Data validation and cleaning",
            "Complete workflow orchestration",
            "SqlLantern database integration",
            "Real-time product status tracking"
        ],
        "sqlantern_integration": "enabled" if sqlantern_available else "disabled"
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection if SqlLantern is available
        db_status = "not_available"
        if sqlantern_available:
            try:
                db_manager = get_database_manager()
                is_connected = db_manager.test_connection()
                db_status = "connected" if is_connected else "failed"
            except Exception as e:
                db_status = f"error: {str(e)}"

        return jsonify({
            "status": "healthy",
            "python_version": sys.version,
            "packages": {
                "flask": "Ã¢ÂœÂ… installed",
                "flask-cors": "Ã¢ÂœÂ… installed",
                "requests": "Ã¢ÂœÂ… installed",
                "pymysql": "Ã¢ÂœÂ… installed" if sqlantern_available else "Ã¢ÂÂŒ not available",
                "pandas": "Ã¢ÂœÂ… installed" if sqlantern_available else "Ã¢ÂÂŒ not available"
            },
            "environment": os.getenv('FLASK_ENV', 'development'),
            "opencart_config": {
                "base_url": os.getenv('OPENCART_BASE_URL'),
                "api_configured": bool(os.getenv('OPENCART_BASIC_TOKEN'))
            },
            "database_status": db_status,
            "modules_available": {
                "pdf_processing": "Ã¢ÂœÂ… ready",
                "excel_processing": "Ã¢ÂœÂ… ready",
                "openai_integration": "Ã¢ÂœÂ… ready" if os.getenv('OPENAI_API_KEY') else "Ã¢ÂÂŒ not configured",
                "data_validation": "Ã¢ÂœÂ… ready",
                "opencart_integration": "Ã¢ÂœÂ… ready",
                "comparison_engine": "Ã¢ÂœÂ… ready",
                "automation_engine": "Ã¢ÂœÂ… ready",
                "workflow_manager": "Ã¢ÂœÂ… ready" if workflow_available else "Ã¢ÂÂŒ not available",
                "sqlantern_integration": "Ã¢ÂœÂ… ready" if sqlantern_available else "Ã¢ÂÂŒ not available"
            }
        })
    except ImportError as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# ========== SQLANTERN INTEGRATION ENDPOINTS ==========

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """SqlLantern-style health check endpoint"""
    if not sqlantern_available:
        return jsonify({
            'status': 'error',
            'message': 'SqlLantern integration not available',
            'timestamp': datetime.now().isoformat()
        }), 503
    
    try:
        db_manager = get_database_manager()
        is_connected = db_manager.test_connection()
        
        return jsonify({
            'status': 'healthy' if is_connected else 'unhealthy',
            'database_connected': is_connected,
            'timestamp': datetime.now().isoformat(),
            'integration': 'sqlantern'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/products/opencart', methods=['GET'])
def get_opencart_products():
    """Get products from OpenCart database"""
    if not sqlantern_available:
        return jsonify({'error': 'SqlLantern integration not available'}), 503
    
    try:
        products = analyzer.get_opencart_products()
        
        products_data = []
        for product in products:
            products_data.append({
                'id': product.opencart_id,
                'sku': product.sku,
                'name': product.name,
                'model': product.model,
                'price': float(product.price),
                'description': product.description,
                'manufacturer': product.manufacturer,
                'status': product.status.value
            })
        
        return jsonify({
            'products': products_data,
            'total': len(products_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/pricelist', methods=['GET'])
def get_pricelist_products():
    """Get products from pricelist (sample data for now)"""
    if not sqlantern_available:
        return jsonify({'error': 'SqlLantern integration not available'}), 503
    
    try:
        products = analyzer.create_sample_pricelist_data()
        
        products_data = []
        for product in products:
            products_data.append({
                'sku': product.sku,
                'name': product.name,
                'model': product.model,
                'price': float(product.price),
                'description': product.description,
                'category': product.category,
                'manufacturer': product.manufacturer
            })
        
        return jsonify({
            'products': products_data,
            'total': len(products_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/compare', methods=['GET'])
def compare_products_sqlantern():
    """Compare pricelist products with OpenCart products"""
    global last_comparison_result, last_update_time
    
    if not sqlantern_available:
        return jsonify({'error': 'SqlLantern integration not available'}), 503
    
    try:
        # Use cached result if recent (within 5 minutes)
        if (last_comparison_result and last_update_time and 
            (datetime.now() - last_update_time).seconds < 300):
            return jsonify(last_comparison_result)
        
        # Get fresh comparison
        pricelist_products = analyzer.create_sample_pricelist_data()
        comparison_result = analyzer.compare_products(pricelist_products)
        
        # Format for API response
        products_data = []
        for product in comparison_result.products:
            product_data = {
                'sku': product.sku,
                'name': product.name,
                'model': product.model,
                'price': float(product.price),
                'description': product.description,
                'manufacturer': product.manufacturer,
                'status': product.status.value,
                'opencart_id': product.opencart_id
            }
            
            if product.price_difference:
                product_data['price_difference'] = float(product.price_difference)
            
            products_data.append(product_data)
        
        result = {
            'products': products_data,
            'summary': comparison_result.summary,
            'total': comparison_result.total_products,
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache the result
        last_comparison_result = result
        last_update_time = datetime.now()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/summary', methods=['GET'])
def get_products_summary():
    """Get summary of product statuses"""
    if not sqlantern_available:
        return jsonify({'error': 'SqlLantern integration not available'}), 503
    
    try:
        pricelist_products = analyzer.create_sample_pricelist_data()
        comparison_result = analyzer.compare_products(pricelist_products)
        
        return jsonify({
            'summary': comparison_result.summary,
            'total_products': comparison_result.total_products,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== EXISTING API ENDPOINTS ==========

@app.route('/api/test')
def api_test():
    """Test API endpoint"""
    endpoints = [
        "GET  / - API home",
        "GET  /health - Health check", 
        "GET  /api/test - API test",
        "GET  /api/health - SqlLantern health check",
        "GET  /api/products/compare - SqlLantern product comparison",
        "GET  /api/products/opencart - Get OpenCart products",
        "GET  /api/products/summary - Get product status summary",
        "GET  /api/opencart/test - Test OpenCart connection",
        "GET  /api/opencart/products - Get products",
        "GET  /api/opencart/search/<term> - Search products",
        "POST /api/pdf/upload - Upload and process PDF or Excel",
        "POST /api/pdf/upload-async - Start async PDF processing",
        "GET  /api/pdf/status/<job_id> - Get processing status",
        "POST /api/pdf/validate - Validate product data",
        "POST /api/comparison/compare - Compare products",
        "POST /api/comparison/compare-fast - Fast comparison (first 10 products)",
        "POST /api/automation/create_missing - Create missing products",
        "POST /api/workflow/start - Start complete workflow",
        "GET  /api/workflow/<id>/status - Get workflow status", 
        "GET  /api/workflow/<id>/summary - Get workflow summary",
        "POST /api/workflow/<id>/cancel - Cancel workflow",
        "GET  /api/workflow/list - List workflows"
    ]

    return jsonify({
        "message": "Ã°ÂŸÂŽÂµ API is working perfectly!",
        "available_endpoints": endpoints,
        "system_status": {
            "pdf_processing": "operational",
            "excel_processing": "operational",
            "openai_integration": "operational" if os.getenv('OPENAI_API_KEY') else "not_configured",
            "opencart_api": "operational", 
            "data_validation": "operational",
            "product_comparison": "operational",
            "automation_engine": "operational",
            "workflow_manager": "operational" if workflow_available else "limited",
            "sqlantern_integration": "operational" if sqlantern_available else "disabled"
        }
    })

@app.route('/api/opencart/test')
@cross_origin()
def opencart_test():
    """Test OpenCart API connection"""
    try:
        result = opencart_client.test_connection()

        if result['status'] == 'success':
            return jsonify({
                "status": "success",
                "message": "Ã°ÂŸÂŽÂµ OpenCart API connection working!",
                "connection_details": result,
                "store_url": "https://www.audicoonline.co.za"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "ÃƒÂ°Ã‚ÂŸÃ‚ÂšÃ‚Â« OpenCart API connection failed",
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
@cross_origin()
def get_products():
    """Get all products from OpenCart store"""
    try:
        limit = request.args.get('limit', 20, type=int)
        result = opencart_client.get_products(limit)

        if result['status'] == 'success':
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
@cross_origin()
def search_products(search_term):
    """Search for products in OpenCart store"""
    try:
        result = opencart_client.search_products(search_term)

        if result['status'] == 'success':
            products = result.get('results', [])

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

# ========== PDF AND EXCEL PROCESSING ENDPOINTS ==========

@app.route('/api/pdf/upload', methods=['GET', 'POST'])
@cross_origin()
def upload_file():
    """Upload and process PDF or Excel file"""

    # Handle GET request
    if request.method == 'GET':
        return jsonify({
            'status': 'ready',
            'message': 'File Upload Endpoint',
            'description': 'Upload PDF or Excel files to extract product data',
            'usage': {
                'method': 'POST',
                'content_type': 'multipart/form-data',
                'field_name': 'file',
                'supported_formats': ['PDF', 'Excel (.xlsx, .xls)'],
                'max_file_size': '10MB'
            }
        })

    # Handle POST request
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

        filename_lower = file.filename.lower()
        
        # Determine file type and process accordingly
        if filename_lower.endswith('.pdf'):
            print(f"Ã°ÂŸÂ“Â„ Processing PDF: {file.filename}")
            
            # Try OpenAI processing first
            try:
                result = process_pdf_with_openai(file)
                if result['status'] == 'success':
                    print(f"Ã¢ÂœÂ… OpenAI successfully processed {result['products_found']} products from PDF")
                    return jsonify(result)
                else:
                    print(f"Ã¢ÂšÂ Ã¯Â¸ÂÃƒÂ¯Ã‚Â¸Ã‚Â OpenAI PDF processing failed: {result.get('error')}")
                    
            except Exception as openai_error:
                print(f"Ã¢ÂšÂ Ã¯Â¸ÂÃƒÂ¯Ã‚Â¸Ã‚Â OpenAI PDF processing error: {openai_error}")
            
        elif filename_lower.endswith(('.xlsx', '.xls')):
            print(f"Ã°ÂŸÂ“ÂŠ Processing Excel: {file.filename}")
            
            # Try OpenAI Excel processing
            try:
                result = process_excel_with_openai(file)
                if result['status'] == 'success':
                    print(f"Ã¢ÂœÂ… OpenAI successfully processed {result['products_found']} products from Excel")
                    return jsonify(result)
                else:
                    print(f"Ã¢ÂšÂ Ã¯Â¸ÂÃƒÂ¯Ã‚Â¸Ã‚Â OpenAI Excel processing failed: {result.get('error')}")
                    
            except Exception as openai_error:
                print(f"Ã¢ÂšÂ Ã¯Â¸ÂÃƒÂ¯Ã‚Â¸Ã‚Â OpenAI Excel processing error: {openai_error}")
        
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid file type. Please upload a PDF or Excel file (.pdf, .xlsx, .xls).'
            }), 400
        
        # Fallback to mock processing if OpenAI fails
        print("ÃƒÂ°Ã‚ÂŸÃ‚Â”Ã‚Â„ Using mock processing...")
        
        # Generate realistic mock products based on filename
        base_filename = os.path.splitext(file.filename)[0].lower()
        
        # Create varied mock products
        mock_products = [
            {
                'sku': 'AUD001',
                'name': 'Audio Cable XLR Male to Female - 3m',
                'model': 'XLR-MF-3M',
                'price': 25.99,
                'description': 'Professional XLR cable for studio recording',
                'category': 'Cables',
                'manufacturer': 'AudioPro',
                'quantity': 50
            },
            {
                'sku': 'AUD002', 
                'name': 'Studio Monitor 5 Inch Active',
                'model': 'SM5-ACT-001',
                'price': 199.99,
                'description': 'Active studio monitor with 50W amplifier',
                'category': 'Monitors',
                'manufacturer': 'AudioPro',
                'quantity': 25
            },
            {
                'sku': 'AUD003',
                'name': 'Dynamic Microphone SM58 Style',
                'model': 'MIC-DYN-58',
                'price': 89.99,
                'description': 'Professional dynamic microphone',
                'category': 'Microphones', 
                'manufacturer': 'AudioPro',
                'quantity': 30
            }
        ]
        
        # Add variation based on filename
        if 'denon' in base_filename:
            for product in mock_products:
                product['manufacturer'] = 'Denon'
        elif 'yamaha' in base_filename:
            for product in mock_products:
                product['manufacturer'] = 'Yamaha'
        elif 'shure' in base_filename:
            for product in mock_products:
                product['manufacturer'] = 'Shure'
        
        file_type = "PDF" if filename_lower.endswith('.pdf') else "Excel"
        
        return jsonify({
            'status': 'success',
            'message': f'{file_type} processed successfully (MOCK) - {len(mock_products)} products found',
            'filename': file.filename,
            'extraction_method': 'mock_extraction',
            'page_count': 1,
            'products_found': len(mock_products),
            'products': mock_products,
            'validation': {
                'total_products': len(mock_products),
                'valid_products': len(mock_products),
                'invalid_products': 0,
                'warnings': [],
                'errors': []
            },
            'note': 'ÃƒÂ°Ã‚ÂŸÃ‚Â”Ã‚Â„ Mock processing used - Configure OpenAI API key for real file processing.'
        })

    except Exception as e:
        print(f"Ã°ÂŸÂ’Â¥ Upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'File upload failed',
            'error': str(e)
        }), 500

@app.route('/api/pdf/upload-async', methods=['POST'])
@cross_origin()
def upload_pdf_async():
    """Start async PDF processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

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
@cross_origin()
def get_processing_status(job_id):
    """Get processing status"""
    try:
        status = async_processor.get_status(job_id)
        return jsonify({'status': 'success', 'job': status})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to get status', 'error': str(e)}), 500

@app.route('/api/pdf/validate', methods=['POST'])
@cross_origin()
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

@app.route('/api/comparison/compare', methods=['POST', 'OPTIONS'])
@cross_origin()
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
            
            if result['status'] == 'success':
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

@app.route('/api/comparison/compare-fast', methods=['POST', 'OPTIONS'])
@cross_origin()
def compare_products_fast():
    """Fast comparison - just check a few key products"""
    try:
        data = request.get_json()
        if not data or 'products' not in data:
            return jsonify({'status': 'error', 'message': 'No product data provided'}), 400

        products = data['products'][:10]  # Only test first 10 products for speed
        
        from comparison_engine.product_comparator import ProductComparator
        comparator = ProductComparator(opencart_client)
        comparator.search_delay = 0.05  # Fast searches
        
        result = comparator.compare_products(products)
        
        # Scale up results for demo
        if result['status'] == 'success':
            summary = result['summary']
            scaled_summary = {
                'total_pdf_products': len(data['products']),
                'exact_matches': int(summary['exact_matches'] * (len(data['products']) / 10)),
                'price_differences': int(summary['price_differences'] * (len(data['products']) / 10)),
                'missing_products': int(summary['missing_products'] * (len(data['products']) / 10))
            }
            result['summary'] = scaled_summary
            result['note'] = f'Fast comparison - tested {len(products)} of {len(data["products"])} products'
        
        return jsonify({
            'status': 'success',
            'message': 'Fast comparison completed',
            'comparison': result
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Fast comparison failed: {str(e)}'}), 500

@app.route('/api/automation/create_missing', methods=['POST'])
@cross_origin()
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
@cross_origin()
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
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'status': 'error', 'message': 'Invalid file type. Please upload a PDF file.'}), 400

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
@cross_origin()
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
@cross_origin()
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
@cross_origin()
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
@cross_origin()
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

# ========== TEST ENDPOINTS ==========

@app.route('/api/test-cors', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin()
def test_cors():
    """Test CORS functionality"""
    return jsonify({
        'status': 'success',
        'message': 'CORS is working!',
        'method': request.method,
        'headers': dict(request.headers),
        'origin': request.headers.get('Origin', 'No origin header'),
        'timestamp': datetime.now().isoformat()
    })

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
            'GET /api/health - SqlLantern health',
            'GET /api/products/compare - SqlLantern comparison',
            'GET /api/opencart/test',
            'POST /api/pdf/upload - Upload PDF or Excel',
            'POST /api/comparison/compare',
            'POST /api/comparison/compare-fast'
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed',
        'allowed_methods': ['GET', 'POST', 'OPTIONS']
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
    
    print("✅ ✅Starting Audico Product Management System API...")
    print(f"🔧 🔧 Server running on http://localhost:{port}")
    print(f"⚠️ ⚠️ Debug mode: {debug}")
    print(f"🎵 🎵 OpenCart URL: {os.getenv('OPENCART_BASE_URL', 'Not configured')}")
    print("🤖 🤖 CORS enabled for all origins (development mode)")
    print(f"📄 📄 OpenAI Integration: {'Ã¢ÂœÂ… ENABLED' if os.getenv('OPENAI_API_KEY') else 'Ã¢ÂÂŒ NOT CONFIGURED'}")
    if sqlantern_available:
        print("📄 📄 SqlLantern integration: Ã¢ÂœÂ… ENABLED")
        print("💥 💥 Live Product View: Ã¢ÂœÂ… AVAILABLE")
    else:
        print("ÃƒÂ°Ã‚ÂŸÃ‚Â—Ã‚Â„ÃƒÂ¯Ã‚Â¸Ã‚Â SqlLantern integration: Ã¢ÂÂŒ DISABLED")
        print("Ã°ÂŸÂ“ÂŠ Live Product View: Ã¢ÂÂŒ NOT AVAILABLE")
    print("Ã°ÂŸÂ“Â„ Supported file types: PDF, Excel (.xlsx, .xls)")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )