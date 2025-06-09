import re
import os
from typing import Dict, List
from .openai_extractor import OpenAIExtractor

class DataParser:
    """Enhanced data parser with OpenAI support"""
    
    def __init__(self):
        self.use_openai = bool(os.getenv('OPENAI_API_KEY'))
        if self.use_openai:
            try:
                self.openai_extractor = OpenAIExtractor()
            except Exception as e:
                print(f"OpenAI not available: {e}")
                self.use_openai = False
        
        # Fallback patterns
        self.price_patterns = [
            r'R\s*(\d+[,.]?\d*)',
            r'(\d+[,.]?\d*)\s*ZAR',
        ]
    
    def parse_text(self, text: str) -> Dict:
        """Parse product data from text using OpenAI or fallback"""
        
        # Try OpenAI first if available
        if self.use_openai:
            try:
                result = self.openai_extractor.extract_and_parse_products(text)
                if result['success']:
                    print(f"OpenAI extracted {result['products_found']} products")
                    return result
                else:
                    print(f"OpenAI failed: {result['error']}, falling back to basic parser")
            except Exception as e:
                print(f"OpenAI error: {e}, falling back to basic parser")
        
        # Fallback to basic parsing
        return self._basic_parse(text)
    
    def _basic_parse(self, text: str) -> Dict:
        """Basic parsing as fallback"""
        try:
            products = []
            lines = text.split('\n')
            
            current_product = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for product lines with model numbers
                if any(pattern in line.upper() for pattern in ['AVR', 'AVC', 'DENON']) and '-' in line:
                    # Save previous product
                    if current_product.get('name') and current_product.get('price'):
                        products.append(current_product.copy())
                    
                    # Start new product
                    current_product = {
                        'name': self._clean_product_name(line),
                        'model': self._extract_model(line),
                        'category': 'AV Receivers',
                        'brand': 'Denon',
                        'currency': 'ZAR',
                        'availability': 'In Stock'
                    }
                
                # Look for prices
                price = self._extract_price(line)
                if price and current_product:
                    if 'Old RRP' in line or not current_product.get('price'):
                        current_product['price'] = price
            
            # Don't forget the last product
            if current_product.get('name') and current_product.get('price'):
                products.append(current_product)
            
            return {
                'success': True,
                'products_found': len(products),
                'products': products,
                'raw_text_preview': text[:500] + "..." if len(text) > 500 else text,
                'method': 'basic_parsing'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Basic parsing failed: {str(e)}',
                'raw_text_preview': text[:200] if text else ""
            }
    
    def _extract_price(self, line: str) -> float:
        """Extract price from line"""
        for pattern in self.price_patterns:
            match = re.search(pattern, line)
            if match:
                price_str = match.group(1).replace(',', '').replace(' ', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        return None
    
    def _extract_model(self, line: str) -> str:
        """Extract model number"""
        model_match = re.search(r'(AVR[A-Z]?-?[A-Z0-9]+)', line, re.IGNORECASE)
        if model_match:
            return model_match.group(1)
        return ""
    
    def _clean_product_name(self, name: str) -> str:
        """Clean product name"""
        name = re.sub(r'\s+', ' ', name.strip())
        return name
