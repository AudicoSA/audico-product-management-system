import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Validation result structure"""
    is_valid: bool
    confidence_score: float  # 0.0 to 1.0
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class DataValidator:
    """Validate and clean extracted product data"""

    def __init__(self):
        self.min_price = 1.0
        self.max_price = 1000000.0
        self.min_name_length = 3
        self.max_name_length = 200

        # Valid categories for audio equipment
        self.valid_categories = {
            'Speakers', 'Amplifiers', 'Microphones', 'Mixers', 
            'Headphones', 'Audio Equipment', 'DJ Equipment',
            'Studio Equipment', 'Live Sound', 'Cables & Accessories',
            'AV Receivers'
        }

        # Common audio brands
        self.known_brands = {
            'JBL', 'Yamaha', 'Behringer', 'Shure', 'Sennheiser',
            'Pioneer', 'Denon', 'Allen & Heath', 'QSC', 'Mackie',
            'Audio-Technica', 'Sony', 'Bose', 'Harman Kardon',
            'Electro-Voice', 'Martin Audio', 'd&b audiotechnik'
        }

    def validate_product_batch(self, products: List[Dict]) -> Dict:
        """Validate a batch of products"""
        results = []
        total_confidence = 0.0
        valid_count = 0

        for i, product in enumerate(products):
            validation = self.validate_product(product)
            results.append({
                'index': i,
                'product_name': product.get('name', 'Unknown'),
                'validation': validation
            })

            total_confidence += validation.confidence_score
            if validation.is_valid:
                valid_count += 1

        avg_confidence = total_confidence / len(products) if products else 0.0

        return {
            'total_products': len(products),
            'valid_products': valid_count,
            'invalid_products': len(products) - valid_count,
            'average_confidence': round(avg_confidence, 2),
            'overall_quality': self._get_quality_rating(avg_confidence),
            'results': results
        }

    def validate_product(self, product: Dict) -> ValidationResult:
        """Validate a single product"""
        errors = []
        warnings = []
        suggestions = []
        confidence_score = 1.0

        # Validate required fields
        if not product.get('name'):
            errors.append("Product name is required")
            confidence_score -= 0.3
        elif len(product['name']) < self.min_name_length:
            errors.append(f"Product name too short (minimum {self.min_name_length} characters)")
            confidence_score -= 0.2

        # Validate price
        price = product.get('price', 0)
        if not price or price <= 0:
            errors.append("Valid price is required")
            confidence_score -= 0.4
        elif price < self.min_price:
            warnings.append(f"Price seems very low (R{price})")
            confidence_score -= 0.1

        # Ensure confidence score is within bounds
        confidence_score = max(0.0, min(1.0, confidence_score))

        return ValidationResult(
            is_valid=len(errors) == 0,
            confidence_score=confidence_score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    def clean_product_data(self, product: Dict) -> Dict:
        """Clean and normalize product data"""
        cleaned = product.copy()

        # Clean product name
        if 'name' in cleaned:
            cleaned['name'] = self._clean_text(cleaned['name'])
            cleaned['name'] = self._capitalize_properly(cleaned['name'])

        # Normalize price
        if 'price' in cleaned:
            cleaned['price'] = round(float(cleaned['price']), 2)

        # Set default currency
        if not cleaned.get('currency'):
            cleaned['currency'] = 'ZAR'

        return cleaned

    def _clean_text(self, text: str) -> str:
        """Clean text data"""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\-\.\,\(\)\/]', '', text)

        return text

    def _capitalize_properly(self, text: str) -> str:
        """Properly capitalize product names"""
        # Words that should stay lowercase
        lowercase_words = {'and', 'or', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}

        words = text.split()
        result = []

        for i, word in enumerate(words):
            if i == 0 or word.lower() not in lowercase_words:
                result.append(word.capitalize())
            else:
                result.append(word.lower())

        return ' '.join(result)

    def _get_quality_rating(self, confidence: float) -> str:
        """Get quality rating based on confidence score"""
        if confidence >= 0.9:
            return "Excellent"
        elif confidence >= 0.8:
            return "Good"
        elif confidence >= 0.7:
            return "Fair"
        elif confidence >= 0.6:
            return "Poor"
        else:
            return "Very Poor"
