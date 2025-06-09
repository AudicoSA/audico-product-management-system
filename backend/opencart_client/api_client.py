import requests
import base64
import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class OpenCartAPIClient:
    """Complete OpenCart API Client for Audico Online Store"""

    def __init__(self):
        self.base_url = os.getenv('OPENCART_BASE_URL', 'https://www.audicoonline.co.za')
        self.basic_token = os.getenv('OPENCART_BASIC_TOKEN', 'b2NyZXN0YXBpX29hdXRoX2NsaWVudDpvY3Jlc3RhcGlfb2F1dGhfc2VjcmV0')

        self.headers = {
            'Authorization': f'Basic {self.basic_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict:
        """Make API request to OpenCart"""
        url = f"{self.base_url}/{endpoint}"

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return {
                'success': True,
                'data': response.json() if response.content else {},
                'status_code': response.status_code
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': getattr(e.response, 'status_code', 500)
            }

    def test_connection(self) -> Dict:
        """Test API connection"""
        try:
            endpoint = "index.php?route=ocrestapi/product/listing"
            result = self._make_request(endpoint)

            if result['success']:
                return {
                    'success': True,
                    'message': 'OpenCart API connection successful',
                    'api_url': f"{self.base_url}/{endpoint}",
                    'response_data': result['data']
                }
            else:
                return {
                    'success': False,
                    'message': 'OpenCart API connection failed',
                    'error': result['error']
                }

        except Exception as e:
            return {
                'success': False,
                'message': 'OpenCart API connection error',
                'error': str(e)
            }

    def get_products(self, limit: int = 100) -> Dict:
        """Get all products from store"""
        endpoint = f"index.php?route=ocrestapi/product/listing&limit={limit}"
        return self._make_request(endpoint)

    def search_products(self, search_term: str) -> Dict:
        """Search for products in OpenCart store"""
        endpoint = f"index.php?route=ocrestapi/product/listing&search={search_term}"
        return self._make_request(endpoint)

    def get_product(self, product_id: str) -> Dict:
        """Get specific product by ID"""
        endpoint = f"index.php?route=ocrestapi/product/product&id={product_id}"
        return self._make_request(endpoint)

    def create_product(self, product_data: Dict) -> Dict:
        """Create new product in OpenCart"""
        endpoint = "index.php?route=ocrestapi/product/product"
        return self._make_request(endpoint, method='POST', data=product_data)

    def update_product(self, product_id: str, product_data: Dict) -> Dict:
        """Update existing product"""
        endpoint = f"index.php?route=ocrestapi/product/product&id={product_id}"
        return self._make_request(endpoint, method='PUT', data=product_data)

    def delete_product(self, product_id: str) -> Dict:
        """Delete product from store"""
        endpoint = f"index.php?route=ocrestapi/product/product&id={product_id}"
        return self._make_request(endpoint, method='DELETE')

    def get_categories(self) -> Dict:
        """Get all product categories"""
        endpoint = "index.php?route=ocrestapi/category/listing"
        return self._make_request(endpoint)
