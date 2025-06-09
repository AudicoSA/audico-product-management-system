import time
from typing import Dict, List, Optional
from datetime import datetime

class ProductAutomator:
    """Automate product creation and updates in OpenCart"""

    def __init__(self, opencart_client):
        self.opencart_client = opencart_client
        self.batch_size = 10
        self.delay_between_requests = 1.0  # seconds

    def create_products_batch(self, products_to_create: List[Dict]) -> Dict:
        """Create multiple products in OpenCart"""
        try:
            results = []
            success_count = 0
            error_count = 0

            total_products = len(products_to_create)

            for i, product_data in enumerate(products_to_create):
                try:
                    # Convert PDF product data to OpenCart format
                    opencart_product = self._convert_to_opencart_format(product_data)

                    # Create product via API (simulation)
                    result = self._create_single_product(opencart_product)

                    results.append({
                        'index': i + 1,
                        'product_name': product_data.get('name', 'Unknown'),
                        'success': result['success'],
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    })

                    if result['success']:
                        success_count += 1
                    else:
                        error_count += 1

                    # Add delay to avoid overwhelming the API
                    if i < total_products - 1:
                        time.sleep(self.delay_between_requests)

                except Exception as e:
                    error_count += 1
                    results.append({
                        'index': i + 1,
                        'product_name': product_data.get('name', 'Unknown'),
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })

            return {
                'success': True,
                'summary': {
                    'total_attempted': total_products,
                    'successful_creations': success_count,
                    'failed_creations': error_count,
                    'success_rate': f"{(success_count/total_products*100):.1f}%" if total_products > 0 else "0%"
                },
                'detailed_results': results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Batch creation failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }

    def _convert_to_opencart_format(self, pdf_product: Dict) -> Dict:
        """Convert PDF product data to OpenCart API format"""
        return {
            'name': pdf_product.get('name', ''),
            'model': pdf_product.get('model', pdf_product.get('sku', '')),
            'price': str(pdf_product.get('price', 0)),
            'quantity': '10',  # Default stock
            'status': '1',  # Enabled
            'description': pdf_product.get('description', ''),
            'meta_title': pdf_product.get('name', ''),
            'meta_description': pdf_product.get('description', '')[:160],
            'tag': pdf_product.get('category', ''),
            'category_id': self._get_category_id(pdf_product.get('category', '')),
            'manufacturer_id': self._get_manufacturer_id(pdf_product.get('brand', '')),
            'weight': '1',
            'weight_class_id': '1',
            'length_class_id': '1',
            'tax_class_id': '0',
            'stock_status_id': '7'  # In Stock
        }

    def _create_single_product(self, product_data: Dict) -> Dict:
        """Create a single product via OpenCart API"""
        try:
            # This would use the actual OpenCart API
            # For now, return a simulation
            return {
                'success': True,
                'product_id': f"new_{int(time.time())}",
                'message': 'Product created successfully',
                'data': product_data
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_category_id(self, category_name: str) -> str:
        """Get OpenCart category ID for category name"""
        # Map category names to OpenCart category IDs
        category_map = {
            'Speakers': '20',
            'Amplifiers': '21',
            'Microphones': '22',
            'Mixers': '23',
            'Headphones': '24',
            'DJ Equipment': '25',
            'Audio Equipment': '26',
            'AV Receivers': '27'
        }
        return category_map.get(category_name, '26')  # Default to Audio Equipment

    def _get_manufacturer_id(self, brand_name: str) -> str:
        """Get OpenCart manufacturer ID for brand name"""
        # Map brand names to OpenCart manufacturer IDs
        brand_map = {
            'JBL': '1',
            'Yamaha': '2',
            'Behringer': '3',
            'Shure': '4',
            'Sennheiser': '5',
            'Denon': '6'
        }
        return brand_map.get(brand_name, '0')  # Default to no manufacturer
