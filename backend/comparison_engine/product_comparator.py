import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
import time

@dataclass
class ComparisonResult:
    """Result of product comparison"""
    pdf_product: Dict
    opencart_matches: List[Dict]
    match_confidence: float
    status: str  # 'missing', 'match_found', 'price_different', 'data_different'
    recommendations: List[str]

class ProductComparator:
    """Compare PDF products with OpenCart inventory using search-based approach"""

    def __init__(self, opencart_client):
        self.opencart_client = opencart_client
        self.name_similarity_threshold = 0.7
        self.price_tolerance_percent = 5.0
        self.search_delay = 0.2  # Delay between searches to avoid overwhelming API

    def compare_products(self, pdf_products: List[Dict]) -> Dict:
        """Compare PDF products using individual searches"""
        try:
            print(f"🔍 Starting SEARCH-BASED comparison for {len(pdf_products)} PDF products")
            
            comparison_results = []
            missing_products = []
            price_differences = []
            exact_matches = []
            search_errors = []

            total_products = len(pdf_products)
            
            for i, pdf_product in enumerate(pdf_products):
                print(f"🔍 Searching {i+1}/{total_products}: {pdf_product.get('name', 'Unknown')}")
                
                try:
                    # Search for this specific product
                    search_result = self._search_single_product(pdf_product)
                    comparison_results.append(search_result)

                    # Categorize results
                    if search_result.status == 'missing':
                        missing_products.append(pdf_product)
                    elif search_result.status == 'price_different':
                        price_differences.append(search_result)
                    elif search_result.status == 'match_found':
                        exact_matches.append(search_result)
                        
                    # Add delay to avoid overwhelming API
                    if i < total_products - 1:
                        time.sleep(self.search_delay)
                        
                except Exception as e:
                    print(f"❌ Error searching for product {pdf_product.get('name', 'Unknown')}: {e}")
                    search_errors.append(str(e))
                    # Add as missing if search fails
                    missing_products.append(pdf_product)
                    comparison_results.append(ComparisonResult(
                        pdf_product=pdf_product,
                        opencart_matches=[],
                        match_confidence=0.0,
                        status='missing',
                        recommendations=[f'Search failed: {str(e)}']
                    ))

            print(f"✅ Search-based comparison complete:")
            print(f"   📊 {len(exact_matches)} exact matches")
            print(f"   💰 {len(price_differences)} price differences") 
            print(f"   ❌ {len(missing_products)} missing products")
            print(f"   🚨 {len(search_errors)} search errors")

            return {
                'success': True,
                'method': 'search_based_comparison',
                'summary': {
                    'total_pdf_products': total_products,
                    'exact_matches': len(exact_matches),
                    'price_differences': len(price_differences),
                    'missing_products': len(missing_products),
                    'search_errors': len(search_errors)
                },
                'missing_products': missing_products,
                'price_differences': [self._serialize_comparison_result(r) for r in price_differences],
                'exact_matches': [self._serialize_comparison_result(r) for r in exact_matches],
                'detailed_results': [self._serialize_comparison_result(r) for r in comparison_results],
                'search_errors': search_errors
            }

        except Exception as e:
            print(f"❌ Search-based comparison failed: {e}")
            return {
                'success': False,
                'error': f'Search-based comparison failed: {str(e)}'
            }

    def _search_single_product(self, pdf_product: Dict) -> ComparisonResult:
        """Search for a single product using multiple search strategies"""
        
        pdf_name = pdf_product.get('name', '')
        pdf_model = pdf_product.get('model', '')
        pdf_price = float(pdf_product.get('price', 0))
        
        print(f"   🔎 Searching for: {pdf_name[:50]}... (Model: {pdf_model})")
        
        # Try multiple search terms in order of specificity
        search_terms = self._generate_search_terms(pdf_product)
        
        all_matches = []
        
        for search_term in search_terms:
            if not search_term:
                continue
                
            try:
                print(f"   🔎 Search term: '{search_term}'")
                search_result = self.opencart_client.search_products(search_term)
                
                if search_result.get('success') and search_result.get('results'):
                    products = search_result['results']
                    print(f"   📦 Found {len(products)} results for '{search_term}'")
                    
                    # Analyze matches for this search term
                    for product in products:
                        match_analysis = self._analyze_match(pdf_product, product)
                        if match_analysis['overall_similarity'] > 0.3:  # Lower threshold for search results
                            all_matches.append(match_analysis)
                else:
                    print(f"   📦 No results for '{search_term}'")
                    
            except Exception as e:
                print(f"   ❌ Search error for '{search_term}': {e}")
                continue
        
        # Sort all matches by similarity
        all_matches.sort(key=lambda x: x['overall_similarity'], reverse=True)
        
        if not all_matches:
            return ComparisonResult(
                pdf_product=pdf_product,
                opencart_matches=[],
                match_confidence=0.0,
                status='missing',
                recommendations=['Product not found in store with any search term']
            )
        
        best_match = all_matches[0]
        
        # Determine match quality and status
        if best_match['overall_similarity'] >= self.name_similarity_threshold:
            # Good match found - check price
            if best_match['price_difference_percent'] <= self.price_tolerance_percent:
                return ComparisonResult(
                    pdf_product=pdf_product,
                    opencart_matches=[best_match['product']],
                    match_confidence=best_match['overall_similarity'],
                    status='match_found',
                    recommendations=[
                        f'✅ Exact match found with {best_match["overall_similarity"]:.1%} similarity',
                        f'Price match: PDF R{pdf_price:.2f} vs Store R{best_match["oc_price"]:.2f}'
                    ]
                )
            else:
                return ComparisonResult(
                    pdf_product=pdf_product,
                    opencart_matches=[best_match['product']],
                    match_confidence=best_match['overall_similarity'],
                    status='price_different',
                    recommendations=[
                        f'✅ Product match found ({best_match["overall_similarity"]:.1%} similarity)',
                        f'💰 Price differs by {best_match["price_difference_percent"]:.1f}%',
                        f'PDF: R{pdf_price:.2f} vs Store: R{best_match["oc_price"]:.2f}'
                    ]
                )
        else:
            return ComparisonResult(
                pdf_product=pdf_product,
                opencart_matches=[best_match['product']] if all_matches else [],
                match_confidence=best_match['overall_similarity'],
                status='missing',
                recommendations=[
                    f'⚠️ Low confidence match ({best_match["overall_similarity"]:.1%} similarity)',
                    f'Best guess: {best_match["product"].get("name", "Unknown")[:50]}...',
                    'Likely a new product that should be added'
                ]
            )

    def _generate_search_terms(self, pdf_product: Dict) -> List[str]:
        """Generate multiple search terms for a product in order of specificity"""
        search_terms = []
        
        name = pdf_product.get('name', '')
        model = pdf_product.get('model', '')
        brand = pdf_product.get('brand', '')
        
        # 1. Exact model number (highest priority)
        if model:
            search_terms.append(model)
            
        # 2. Brand + model
        if brand and model:
            search_terms.append(f"{brand} {model}")
            
        # 3. Key words from product name
        if name:
            # Extract meaningful words (remove common words)
            words = name.split()
            meaningful_words = [w for w in words if len(w) > 3 and w.lower() not in 
                              ['with', 'and', 'the', 'for', 'receiver', 'built', 'channel']]
            
            if len(meaningful_words) >= 2:
                search_terms.append(' '.join(meaningful_words[:3]))  # First 3 meaningful words
                
        # 4. Brand + first few words of name
        if brand and name:
            first_words = ' '.join(name.split()[:3])
            search_terms.append(f"{brand} {first_words}")
            
        # 5. Just brand for broader search
        if brand:
            search_terms.append(brand)
            
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in search_terms:
            if term and term not in seen:
                seen.add(term)
                unique_terms.append(term)
                
        return unique_terms[:5]  # Limit to 5 search terms max

    def _analyze_match(self, pdf_product: Dict, oc_product: Dict) -> Dict:
        """Analyze how well an OpenCart product matches a PDF product"""
        try:
            # Extract data safely
            pdf_name = str(pdf_product.get('name', '')).lower()
            pdf_model = str(pdf_product.get('model', '')).lower()
            pdf_price = float(pdf_product.get('price', 0))
            
            oc_name = str(oc_product.get('name', '')).lower()
            oc_model = str(oc_product.get('model', '')).lower()
            oc_price_str = str(oc_product.get('price', '0'))
            
            # Clean and convert OpenCart price
            oc_price_clean = re.sub(r'[^\d.,]', '', oc_price_str)
            oc_price_clean = oc_price_clean.replace(',', '')
            oc_price = float(oc_price_clean) if oc_price_clean else 0.0
            
            # Calculate similarities
            name_similarity = self._calculate_similarity(pdf_name, oc_name) if pdf_name and oc_name else 0.0
            model_similarity = self._calculate_similarity(pdf_model, oc_model) if pdf_model and oc_model else 0.0
            
            # Model match gets higher weight
            if model_similarity > 0.8:
                overall_similarity = (model_similarity * 0.8) + (name_similarity * 0.2)
            else:
                overall_similarity = (name_similarity * 0.7) + (model_similarity * 0.3)
            
            # Calculate price difference
            price_difference_percent = 0
            if pdf_price > 0:
                price_difference_percent = abs((pdf_price - oc_price) / pdf_price * 100)
            
            return {
                'product': oc_product,
                'name_similarity': name_similarity,
                'model_similarity': model_similarity,
                'overall_similarity': overall_similarity,
                'price_difference': abs(pdf_price - oc_price),
                'price_difference_percent': price_difference_percent,
                'pdf_price': pdf_price,
                'oc_price': oc_price
            }
            
        except Exception as e:
            print(f"   ❌ Error analyzing match: {e}")
            return {
                'product': oc_product,
                'name_similarity': 0.0,
                'model_similarity': 0.0,
                'overall_similarity': 0.0,
                'price_difference': 0,
                'price_difference_percent': 0,
                'pdf_price': 0,
                'oc_price': 0
            }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        try:
            return SequenceMatcher(None, text1, text2).ratio()
        except Exception:
            return 0.0

    def _serialize_comparison_result(self, result: ComparisonResult) -> Dict:
        """Convert ComparisonResult to serializable dict"""
        return {
            'pdf_product': result.pdf_product,
            'opencart_matches': result.opencart_matches,
            'match_confidence': result.match_confidence,
            'status': result.status,
            'recommendations': result.recommendations
        }
