import re
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ProductData:
    """Product data structure"""
    name: str = ""
    model: str = ""
    price: float = 0.0
    currency: str = "ZAR"
    description: str = ""
    category: str = ""
    brand: str = ""
    sku: str = ""
    availability: str = "In Stock"
    specifications: Dict = None

    def __post_init__(self):
        if self.specifications is None:
            self.specifications = {}

class DataParser:
    """Parse product data from extracted PDF text"""

    def __init__(self):
        # Audio equipment specific patterns
        self.price_patterns = [
            r'R\s*(\d+[,.]?\d*)',  # R 1,200 or R1200
            r'ZAR\s*(\d+[,.]?\d*)',  # ZAR 1200
            r'(\d+[,.]?\d*)\s*ZAR',  # 1200 ZAR
            r'\$\s*(\d+[,.]?\d*)',   # $ 120
        ]

        self.product_patterns = [
            r'(Speaker|Amplifier|Microphone|Mixer|DJ|Audio|Sound|Music|Headphone|Earphone)',
            r'(Woofer|Tweeter|Subwoofer|Monitor|Cabinet|Box|System)',
            r'(Professional|Pro|Studio|Live|Stage|Concert)',
            r'(AVR|AVC|Receiver|Home)',
        ]

        self.model_patterns = [
            r'Model\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'Part\s*[#\:]?\s*([A-Z0-9\-]+)',
            r'SKU\s*[:\-]?\s*([A-Z0-9\-]+)',
            r'([A-Z]{2,}[\-][A-Z0-9\-]+)',  # Pattern like AVR-X1800H
        ]

    def parse_text(self, text: str) -> Dict:
        """Parse product data from extracted text"""
        try:
            products = []
            lines = text.split('\n')

            current_product = ProductData()

            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # Look for product names (audio equipment)
                if self._is_product_line(line):
                    # Save previous product if valid
                    if current_product.name and current_product.price > 0:
                        products.append(self._product_to_dict(current_product))

                    # Start new product
                    current_product = ProductData()
                    current_product.name = self._clean_product_name(line)
                    current_product.category = self._detect_category(line)
                    current_product.brand = self._detect_brand(line)

                # Look for prices
                price = self._extract_price(line)
                if price and not current_product.price:
                    current_product.price = price

                # Look for model numbers
                model = self._extract_model(line)
                if model and not current_product.model:
                    current_product.model = model

                # Look for descriptions
                if len(line) > 50 and not current_product.description:
                    current_product.description = line[:200]

            # Don't forget the last product
            if current_product.name and current_product.price > 0:
                products.append(self._product_to_dict(current_product))

            return {
                'success': True,
                'products_found': len(products),
                'products': products,
                'raw_text_preview': text[:500] + "..." if len(text) > 500 else text
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Parsing failed: {str(e)}',
                'raw_text_preview': text[:200] if text else ""
            }

    def _is_product_line(self, line: str) -> bool:
        """Check if line contains a product name"""
        line_upper = line.upper()
        for pattern in self.product_patterns:
            if re.search(pattern, line_upper, re.IGNORECASE):
                return True
        return False

    def _extract_price(self, line: str) -> Optional[float]:
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

    def _extract_model(self, line: str) -> Optional[str]:
        """Extract model number from line"""
        for pattern in self.model_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _clean_product_name(self, name: str) -> str:
        """Clean and format product name"""
        # Remove extra whitespace and special characters
        name = re.sub(r'\s+', ' ', name.strip())
        # Remove price information from name
        name = re.sub(r'R\s*\d+[,.]?\d*', '', name)
        return name.strip()

    def _detect_category(self, product_name: str) -> str:
        """Detect product category based on name"""
        name_upper = product_name.upper()

        if any(word in name_upper for word in ['SPEAKER', 'WOOFER', 'TWEETER', 'SUBWOOFER']):
            return 'Speakers'
        elif any(word in name_upper for word in ['AMPLIFIER', 'AMP']):
            return 'Amplifiers'
        elif any(word in name_upper for word in ['MICROPHONE', 'MIC']):
            return 'Microphones'
        elif any(word in name_upper for word in ['MIXER', 'MIXING']):
            return 'Mixers'
        elif any(word in name_upper for word in ['HEADPHONE', 'EARPHONE', 'HEADSET']):
            return 'Headphones'
        elif any(word in name_upper for word in ['AVR', 'AVC', 'RECEIVER']):
            return 'AV Receivers'
        else:
            return 'Audio Equipment'

    def _detect_brand(self, product_name: str) -> str:
        """Detect brand from product name"""
        name_upper = product_name.upper()
        brands = ['DENON', 'JBL', 'YAMAHA', 'BEHRINGER', 'SHURE', 'SENNHEISER', 
                 'PIONEER', 'ALLEN', 'QSC', 'MACKIE', 'AUDIO-TECHNICA', 'SONY', 'BOSE']

        for brand in brands:
            if brand in name_upper:
                return brand.title()
        return ""

    def _product_to_dict(self, product: ProductData) -> Dict:
        """Convert ProductData to dictionary"""
        return {
            'name': product.name,
            'model': product.model,
            'price': product.price,
            'currency': product.currency,
            'description': product.description,
            'category': product.category,
            'brand': product.brand,
            'sku': product.sku,
            'availability': product.availability,
            'specifications': product.specifications
        }
