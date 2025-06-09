import re
import os
from typing import Dict, List

class DataParser:
    """Enhanced data parser with OpenAI support and improved fallback"""
    
    def __init__(self):
        self.use_openai = bool(os.getenv('OPENAI_API_KEY'))
        self.openai_extractor = None
        
        if self.use_openai:
            try:
                from .openai_extractor import OpenAIExtractor
                self.openai_extractor = OpenAIExtractor()
                print("✅ OpenAI extractor initialized successfully")
            except Exception as e:
                print(f"❌ OpenAI not available: {e}")
                self.use_openai = False
        else:
            print("❌ No OpenAI API key found, using fallback parser")
        
        # Enhanced patterns for Denon products
        self.price_patterns = [
            r'R\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # R9,990.00 or R9990
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*ZAR',  # 9990.00 ZAR
            r'(\d{4,6})\.00',  # Simple format like 8990.00
            r'(\d{4,6})\.\d{2}',  # Format like 8990.50
        ]
        
        self.model_patterns = [
            r'(AVR[A-Z]?-?[A-Z0-9]+[A-Z]?)',  # AVRX-580BT, AVR-X1800H
            r'(AVC-[A-Z0-9]+[A-Z]?)',  # AVC-X3800H
            r'(AVRS-[A-Z0-9]+)',  # AVRS-670H
            r'(DENON[- ][A-Z0-9]+)',  # DENON HOME variants
        ]
    
    def parse_text(self, text: str) -> Dict:
        """Parse product data from text using OpenAI or enhanced fallback"""
        
        print(f"🔍 Parsing text of length: {len(text)}")
        print(f"📄 Text preview: {text[:200]}...")
        
        # Try OpenAI first if available
        if self.use_openai and self.openai_extractor:
            try:
                print("🤖 Attempting OpenAI extraction...")
                result = self.openai_extractor.extract_and_parse_products(text)
                if result['success'] and result.get('products_found', 0) > 0:
                    print(f"✅ OpenAI extracted {result['products_found']} products")
                    return result
                else:
                    print(f"⚠️ OpenAI failed: {result.get('error', 'Unknown error')}, falling back to enhanced parser")
            except Exception as e:
                print(f"❌ OpenAI error: {e}, falling back to enhanced parser")
        
        # Enhanced fallback parsing specifically for Denon format
        print("🔧 Using enhanced fallback parser...")
        return self._parse_denon_format(text)
    
    def _parse_denon_format(self, text: str) -> Dict:
        """Parse Denon pricelist format specifically"""
        try:
            products = []
            
            # Split into lines and clean
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            print(f"Processing {len(lines)} lines...")
            
            # Debug: Print all lines to understand structure
            for i, line in enumerate(lines[:20]):  # First 20 lines for debugging
                print(f"Line {i}: '{line}'")
            
            # Look for the price table pattern
            current_category = "AV Receivers"
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                # Detect category changes
                if any(cat in line.upper() for cat in ['AV RECEIVERS', 'DENON HOME', 'SPEAKERS', 'AMPLIFIERS']):
                    current_category = line
                    print(f"📂 Found category: {current_category}")
                    i += 1
                    continue
                
                # Skip obvious header lines
                if any(skip in line.upper() for skip in [
                    'APRIL 2025', 'BLACK', 'OLD RRP', 'NEW RRP', 'WHITE', 'MONTH', 'YEAR'
                ]):
                    i += 1
                    continue
                
                # Look for product lines
                if self._is_product_line(line):
                    print(f"🔍 Processing potential product line: '{line}'")
                    product = self._extract_denon_product(line, lines, i, current_category)
                    if product:
                        products.append(product)
                        print(f"✅ Found product: {product['name']} - R{product.get('price', 'No price')}")
                    else:
                        print(f"❌ Could not extract product from: '{line}'")
                
                i += 1
            
            print(f"🎯 Enhanced parser extracted {len(products)} products")
            
            # If we found very few products, try alternative parsing
            if len(products) < 5:
                print("🔄 Trying alternative parsing strategy...")
                alt_products = self._alternative_parse(text)
                if len(alt_products) > len(products):
                    products = alt_products
                    print(f"🎯 Alternative parser found {len(products)} products")
            
            return {
                'success': True,
                'products_found': len(products),
                'products': products,
                'method': 'denon_enhanced_parsing',
                'raw_text_preview': text[:500] + "..." if len(text) > 500 else text
            }
            
        except Exception as e:
            print(f"❌ Enhanced parsing failed: {str(e)}")
            return {
                'success': False,
                'error': f'Enhanced parsing failed: {str(e)}',
                'method': 'failed_parsing',
                'raw_text_preview': text[:200] if text else ""
            }
    
    def _is_product_line(self, line: str) -> bool:
        """Check if line contains a product"""
        # Primary indicators: Model patterns
        for pattern in self.model_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        # Secondary indicators: Product description patterns
        product_indicators = [
            # Common Denon product patterns
            ('Ch.' in line and 'W ' in line),  # "5.2 Ch. 130W"
            ('Receiver' in line and any(char.isdigit() for char in line)),
            ('HEOS' in line and ('AVR' in line.upper() or 'AVC' in line.upper())),
            ('8K' in line and 'AV' in line.upper()),
            # Price indicators (if line has prices, likely a product)
            bool(re.search(r'R\s*\d{4,6}', line))
        ]
        
        return any(product_indicators)
    
    def _extract_denon_product(self, line: str, all_lines: List[str], line_index: int, category: str = "AV Receivers") -> Dict:
        """Extract product from Denon format line"""
        try:
            # Basic product structure
            product = {
                'brand': 'Denon',
                'currency': 'ZAR',
                'category': category,
                'availability': 'In Stock',
                'features': []
            }
            
            # Extract model number first
            model = self._extract_model(line)
            if model:
                product['model'] = model
                print(f"🏷️ Found model: {model}")
            
            # Extract product name (clean version without prices)
            clean_name = self._clean_product_name(line)
            product['name'] = clean_name
            product['specifications'] = line
            
            print(f"📝 Product name: {clean_name}")
            
            # Extract prices from current line
            prices = self._extract_all_prices_from_line(line)
            print(f"💰 Prices found in line: {prices}")
            
            # If no prices in current line, check surrounding lines
            if not prices:
                context_prices = self._find_prices_in_context(all_lines, line_index, model or clean_name)
                prices.extend(context_prices)
                print(f"💰 Prices found in context: {context_prices}")
            
            # Assign prices
            if prices:
                prices = sorted(set(prices))  # Remove duplicates and sort
                if len(prices) >= 2:
                    # Usually Old RRP is higher, New RRP is lower
                    if prices[0] > prices[1]:
                        product['old_price'] = prices[0]
                        product['price'] = prices[1]
                    else:
                        product['old_price'] = prices[1]
                        product['price'] = prices[0]
                else:
                    product['price'] = prices[0]
                
                print(f"💰 Final pricing: Price={product.get('price')}, Old Price={product.get('old_price')}")
            
            # Extract features from the product description
            features = self._extract_features(line)
            product['features'] = features
            
            # Create SEO-friendly name
            seo_name = self._create_seo_name(product)
            product['seo_name'] = seo_name
            
            # Only return if we have minimum required info
            if product.get('name') and (product.get('price') or product.get('model')):
                return product
            else:
                print(f"❌ Product missing required fields: name='{product.get('name')}', price={product.get('price')}, model='{product.get('model')}'")
                return None
            
        except Exception as e:
            print(f"❌ Error extracting product from line '{line}': {e}")
            return None
    
    def _extract_model(self, line: str) -> str:
        """Extract model number from line"""
        for pattern in self.model_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def _clean_product_name(self, line: str) -> str:
        """Clean product name by removing prices and extra formatting"""
        # Remove prices
        clean_line = re.sub(r'R\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?', '', line)
        
        # Remove excessive whitespace
        clean_line = re.sub(r'\s+', ' ', clean_line.strip())
        
        # Remove trailing dashes or separators
        clean_line = clean_line.rstrip(' -–—')
        
        return clean_line
    
    def _extract_all_prices_from_line(self, line: str) -> List[float]:
        """Extract all prices from a single line"""
        prices = []
        
        for pattern in self.price_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                try:
                    # Clean the price string
                    price_str = match.replace(',', '').replace(' ', '')
                    if price_str and price_str.replace('.', '').isdigit():
                        price = float(price_str)
                        # Reasonable price range for audio equipment
                        if 500 <= price <= 500000:
                            prices.append(price)
                except (ValueError, AttributeError):
                    continue
        
        return sorted(set(prices))  # Remove duplicates and sort
    
    def _find_prices_in_context(self, lines: List[str], line_index: int, product_identifier: str) -> List[float]:
        """Find prices in surrounding lines that might belong to this product"""
        prices = []
        
        # Check lines around the current one
        search_range = 3  # Check 3 lines before and after
        
        for offset in range(-search_range, search_range + 1):
            if offset == 0:  # Skip current line (already checked)
                continue
                
            idx = line_index + offset
            if 0 <= idx < len(lines):
                context_line = lines[idx]
                
                # If the context line mentions our product or has similar content
                if (product_identifier and product_identifier in context_line) or \
                   (offset in [-1, 1]):  # Always check immediate neighbors
                    context_prices = self._extract_all_prices_from_line(context_line)
                    prices.extend(context_prices)
        
        return sorted(set(prices))
    
    def _extract_features(self, line: str) -> List[str]:
        """Extract features from product description"""
        features = []
        
        # Technical features
        if '8K' in line:
            features.append('8K')
        if '4K' in line:
            features.append('4K')
        if 'HEOS' in line:
            features.append('HEOS')
        if 'Bluetooth' in line:
            features.append('Bluetooth')
        if 'WiFi' in line or 'Wi-Fi' in line:
            features.append('WiFi')
        if 'Receiver' in line:
            features.append('AV Receiver')
        if 'Built-in' in line:
            features.append('Built-in')
        
        # Channel configuration
        channel_match = re.search(r'(\d+\.?\d*)\s*Ch\.', line)
        if channel_match:
            features.append(f"{channel_match.group(1)} Channel")
        
        # Power rating
        power_match = re.search(r'(\d+)W\b', line)
        if power_match:
            features.append(f"{power_match.group(1)}W")
        
        return features
    
    def _create_seo_name(self, product: Dict) -> str:
        """Create SEO-friendly name"""
        parts = ['Denon']
        
        if product.get('model'):
            parts.append(product['model'])
        
        # Add key specs
        specs = product.get('specifications', '')
        if specs:
            # Extract channel info
            channel_match = re.search(r'(\d+\.?\d*)\s*Ch\.', specs)
            if channel_match:
                parts.append(f"{channel_match.group(1)}Ch")
            
            # Extract power info
            power_match = re.search(r'(\d+)W\b', specs)
            if power_match:
                parts.append(f"{power_match.group(1)}W")
        
        # Add category
        if 'Receiver' in product.get('name', ''):
            parts.append('AV Receiver')
        
        # Add key features
        features = product.get('features', [])
        key_features = [f for f in features if f in ['8K', 'HEOS', 'Bluetooth', 'WiFi']]
        if key_features:
            parts.extend(key_features[:2])  # Limit to 2 key features
        
        seo_name = ' '.join(parts)
        return seo_name[:70]  # Limit length for SEO
    
    def _alternative_parse(self, text: str) -> List[Dict]:
        """Alternative parsing strategy for difficult formats"""
        products = []
        
        try:
            print("🔄 Trying line-by-line product detection...")
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # More aggressive product detection
                has_model = bool(re.search(r'AVR|AVC|DENON', line, re.IGNORECASE))
                has_price = bool(re.search(r'R\s*\d{4,6}', line))
                has_specs = bool(re.search(r'\d+\.?\d*\s*Ch\.|W\s|\d+W', line))
                
                if (has_model and has_price) or (has_specs and has_price):
                    product = {
                        'name': self._clean_product_name(line),
                        'model': self._extract_model(line),
                        'specifications': line,
                        'brand': 'Denon',
                        'currency': 'ZAR',
                        'category': 'AV Receivers',
                        'features': self._extract_features(line)
                    }
                    
                    # Extract prices
                    prices = self._extract_all_prices_from_line(line)
                    if prices:
                        if len(prices) >= 2:
                            product['old_price'] = max(prices)
                            product['price'] = min(prices)
                        else:
                            product['price'] = prices[0]
                    
                    if product.get('name') and product.get('price'):
                        products.append(product)
                        print(f"🎯 Alternative parser found: {product['name']} - R{product['price']}")
        
        except Exception as e:
            print(f"❌ Alternative parsing failed: {e}")
        
        return products
