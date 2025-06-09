import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class ComparisonResult:
    """Result of product comparison"""
    pdf_product: Dict
    opencart_matches: List[Dict]
    match_confidence: float
    status: str  # 'missing', 'match_found', 'price_different', 'data_different'
    recommendations: List[str]

class ProductComparator:
    """Compare PDF products with OpenCart inventory"""

    def __init__(self, opencart_client):
        self.opencart_client = opencart_client
        self.name_similarity_threshold = 0.7
        self.price_tolerance_percent = 5.0

    def compare_products(self, pdf_products: List[Dict]) -> Dict:
        """Compare PDF products with OpenCart store inventory"""
        try:
            # Get all OpenCart products
            opencart_result = self.opencart_client.get_products(limit=1000)

            if not opencart_result['success']:
                return {
                    'success': False,
                    'error': 'Failed to fetch OpenCart products',
                    'details': opencart_result
                }

            opencart_products = opencart_result['data'].get('data', [])

            # Perform comparison
            comparison_results = []
            missing_products = []
            price_differences = []
            exact_matches = []

            for pdf_product in pdf_products:
                result = self._compare_single_product(pdf_product, opencart_products)
                comparison_results.append(result)

                # Categorize results
                if result.status == 'missing':
                    missing_products.append(pdf_product)
                elif result.status == 'price_different':
                    price_differences.append(result)
                elif result.status == 'match_found':
                    exact_matches.append(result)

            return {
                'success': True,
                'summary': {
                    'total_pdf_products': len(pdf_products),
                    'total_opencart_products': len(opencart_products),
                    'missing_products': len(missing_products),
                    'price_differences': len(price_differences),
                    'exact_matches': len(exact_matches)
                },
                'missing_products': missing_products,
                'price_differences': price_differences,
                'exact_matches': exact_matches,
                'detailed_results': comparison_results
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Comparison failed: {str(e)}'
            }

    def _compare_single_product(self, pdf_product: Dict, opencart_products: List[Dict]) -> ComparisonResult:
        """Compare a single PDF product with OpenCart inventory"""

        best_matches = []
        pdf_name = pdf_product.get('name', '').lower()
        pdf_price = float(pdf_product.get('price', 0))
        pdf_model = pdf_product.get('model', '').lower()

        # Find potential matches
        for oc_product in opencart_products:
            oc_name = oc_product.get('name', '').lower()
            oc_price = float(oc_product.get('price', 0))
            oc_model = oc_product.get('model', '').lower()

            # Calculate name similarity
            name_similarity = self._calculate_similarity(pdf_name, oc_name)

            # Calculate model similarity if both have models
            model_similarity = 0.0
            if pdf_model and oc_model:
                model_similarity = self._calculate_similarity(pdf_model, oc_model)

            # Overall similarity (weighted)
            overall_similarity = (name_similarity * 0.7) + (model_similarity * 0.3)

            if overall_similarity > 0.5:  # Potential match
                price_difference_percent = abs((pdf_price - oc_price) / pdf_price * 100) if pdf_price > 0 else 0

                best_matches.append({
                    'product': oc_product,
                    'name_similarity': name_similarity,
                    'model_similarity': model_similarity,
                    'overall_similarity': overall_similarity,
                    'price_difference': abs(pdf_price - oc_price),
                    'price_difference_percent': price_difference_percent
                })

        # Sort by overall similarity
        best_matches.sort(key=lambda x: x['overall_similarity'], reverse=True)

        # Determine status and recommendations
        if not best_matches:
            return ComparisonResult(
                pdf_product=pdf_product,
                opencart_matches=[],
                match_confidence=0.0,
                status='missing',
                recommendations=['Product not found in store - consider adding']
            )

        best_match = best_matches[0]

        if best_match['overall_similarity'] >= self.name_similarity_threshold:
            # Good match found
            if best_match['price_difference_percent'] <= self.price_tolerance_percent:
                return ComparisonResult(
                    pdf_product=pdf_product,
                    opencart_matches=[best_match['product']],
                    match_confidence=best_match['overall_similarity'],
                    status='match_found',
                    recommendations=['Product found with matching price']
                )
            else:
                return ComparisonResult(
                    pdf_product=pdf_product,
                    opencart_matches=[best_match['product']],
                    match_confidence=best_match['overall_similarity'],
                    status='price_different',
                    recommendations=[
                        f'Product found but price differs by {best_match["price_difference_percent"]:.1f}%',
                        f'PDF: R{pdf_price:.2f} vs Store: R{float(best_match["product"].get("price", 0)):.2f}'
                    ]
                )
        else:
            return ComparisonResult(
                pdf_product=pdf_product,
                opencart_matches=best_matches[:3],  # Top 3 potential matches
                match_confidence=best_match['overall_similarity'],
                status='missing',
                recommendations=[
                    'No close match found - likely a new product',
                    f'Closest match: {best_matches[0]["product"].get("name", "Unknown")} ({best_match["overall_similarity"]:.1%} similarity)'
                ]
            )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        return SequenceMatcher(None, text1, text2).ratio()
