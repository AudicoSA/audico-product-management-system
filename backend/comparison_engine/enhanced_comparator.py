import re
from typing import Dict, List, Tuple
from difflib import SequenceMatcher

class EnhancedProductComparator:
    """Enhanced product comparison with better matching for OpenCart"""
    
    def __init__(self, opencart_client):
        self.opencart_client = opencart_client
        
    def find_matching_products(self, pdf_products: List[Dict]) -> Dict:
        """Find matching products between PDF and OpenCart using enhanced matching"""
        try:
            # Get all OpenCart products
            opencart_result = self.opencart_client.get_products(limit=1000)
            if not opencart_result['success']:
                return {'success': False, 'error': 'Failed to fetch OpenCart products'}
            
            opencart_products = opencart_result['data'].get('data', [])
            
            matches = []
            missing = []
            
            for pdf_product in pdf_products:
                match_result = self._find_best_match(pdf_product, opencart_products)
                
                if match_result['found']:
                    matches.append({
                        'pdf_product': pdf_product,
                        'opencart_product': match_result['match'],
                        'confidence': match_result['confidence'],
                        'matching_method': match_result['method']
                    })
                else:
                    missing.append(pdf_product)
            
            return {
                'success': True,
                'total_pdf_products': len(pdf_products),
                'matches_found': len(matches),
                'missing_products': len(missing),
                'matches': matches,
                'missing': missing
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _find_best_match(self, pdf_product: Dict, opencart_products: List[Dict]) -> Dict:
        """Find the best matching OpenCart product"""
        
        pdf_model = pdf_product.get('model', '').upper()
        pdf_name = pdf_product.get('name', '').upper()
        pdf_seo_name = pdf_product.get('seo_name', '').upper()
        
        best_match = None
        best_confidence = 0.0
        best_method = ""
        
        for oc_product in opencart_products:
            oc_name = oc_product.get('name', '').upper()
            oc_model = oc_product.get('model', '').upper()
            
            # Method 1: Exact model match
            if pdf_model and pdf_model in oc_name:
                confidence = 0.95
                if confidence > best_confidence:
                    best_match = oc_product
                    best_confidence = confidence
                    best_method = "exact_model_match"
            
            # Method 2: Model number similarity
            if pdf_model and oc_model:
                model_similarity = SequenceMatcher(None, pdf_model, oc_model).ratio()
                if model_similarity > 0.8 and model_similarity > best_confidence:
                    best_match = oc_product
                    best_confidence = model_similarity
                    best_method = "model_similarity"
            
            # Method 3: Name similarity with SEO name
            if pdf_seo_name:
                name_similarity = SequenceMatcher(None, pdf_seo_name, oc_name).ratio()
                if name_similarity > 0.7 and name_similarity > best_confidence:
                    best_match = oc_product
                    best_confidence = name_similarity
                    best_method = "seo_name_similarity"
            
            # Method 4: Fallback name similarity
            name_similarity = SequenceMatcher(None, pdf_name, oc_name).ratio()
            if name_similarity > 0.6 and name_similarity > best_confidence:
                best_match = oc_product
                best_confidence = name_similarity
                best_method = "name_similarity"
        
        return {
            'found': best_match is not None,
            'match': best_match,
            'confidence': best_confidence,
            'method': best_method
        }
