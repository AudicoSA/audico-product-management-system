import openai
import os
from typing import Dict, List
import json
import re
from dotenv import load_dotenv

load_dotenv()

class OpenAIExtractor:
    """OpenAI-powered PDF text extraction and product parsing"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        openai.api_key = self.api_key
    
    def extract_and_parse_products(self, pdf_text: str) -> Dict:
        """Extract and parse products using OpenAI GPT-4"""
        try:
            # First, extract all products from the text
            extraction_prompt = self._create_extraction_prompt(pdf_text)
            
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at extracting product information from audio equipment pricelists. You must extract ALL products, not just a few examples."
                    },
                    {
                        "role": "user", 
                        "content": extraction_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            # Parse the JSON response
            products_text = response.choices[0].message.content
            
            # Clean up the response and extract JSON
            products_data = self._parse_openai_response(products_text)
            
            if not products_data:
                return {
                    'success': False,
                    'error': 'Failed to parse OpenAI response',
                    'raw_response': products_text
                }
            
            # Enhance product names for OpenCart SEO
            enhanced_products = self._enhance_product_names(products_data)
            
            return {
                'success': True,
                'method': 'openai_extraction',
                'products_found': len(enhanced_products),
                'products': enhanced_products,
                'raw_response': products_text[:500] + "..."
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'OpenAI extraction failed: {str(e)}'
            }
    
    def _create_extraction_prompt(self, pdf_text: str) -> str:
        """Create detailed prompt for product extraction"""
        return f"""
        Extract ALL audio equipment products from this Denon pricelist. This is a complete pricelist with many products.

        For EACH product found, extract:
        1. Full product name/description
        2. Model number (e.g., AVR-X1800H, AVRX-580BT)
        3. New RRP price (the current selling price)
        4. Old RRP price (if available)
        5. Key specifications (channels, power, features)
        6. Product category (AV Receivers, Speakers, etc.)

        Return the data as a JSON array with this exact structure:
        [
          {{
            "name": "Full product name from PDF",
            "model": "Model number",
            "price": 15990.00,
            "old_price": 18990.00,
            "currency": "ZAR",
            "category": "AV Receivers",
            "brand": "Denon",
            "specifications": "7.2 Ch. 175W 8K AV Receiver with HEOS Built-in",
            "features": ["8K", "HEOS", "Bluetooth", "WiFi"]
          }}
        ]

        IMPORTANT: 
        - Extract ALL products, not just examples
        - Use the "New RRP" price as the main price
        - Include detailed specifications
        - Ensure model numbers are accurate
        - If Old RRP and New RRP are the same, set old_price to null

        PDF Content:
        {pdf_text}
        """
    
    def _parse_openai_response(self, response_text: str) -> List[Dict]:
        """Parse OpenAI response and extract JSON"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\[(.*?)\]', response_text, re.DOTALL)
            if json_match:
                json_str = '[' + json_match.group(1) + ']'
                return json.loads(json_str)
            
            # If no brackets found, try parsing the whole response
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            # Try to extract products line by line if JSON parsing fails
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, response_text: str) -> List[Dict]:
        """Fallback parsing if JSON fails"""
        products = []
        lines = response_text.split('\n')
        
        current_product = {}
        for line in lines:
            line = line.strip()
            if 'name' in line.lower() and ':' in line:
                if current_product:
                    products.append(current_product)
                current_product = {'brand': 'Denon', 'currency': 'ZAR'}
                current_product['name'] = line.split(':')[1].strip().strip('"')
            elif 'model' in line.lower() and ':' in line:
                current_product['model'] = line.split(':')[1].strip().strip('"')
            elif 'price' in line.lower() and ':' in line:
                price_str = re.search(r'[\d,]+\.?\d*', line)
                if price_str:
                    current_product['price'] = float(price_str.group().replace(',', ''))
        
        if current_product:
            products.append(current_product)
        
        return products
    
    def _enhance_product_names(self, products: List[Dict]) -> List[Dict]:
        """Enhance product names for better OpenCart SEO and matching"""
        try:
            enhancement_prompt = self._create_enhancement_prompt(products)
            
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an e-commerce SEO expert. Create SEO-friendly product names for online stores that are descriptive but not too long."
                    },
                    {
                        "role": "user",
                        "content": enhancement_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            enhanced_data = response.choices[0].message.content
            enhanced_products = self._parse_enhancement_response(enhanced_data, products)
            
            return enhanced_products
            
        except Exception as e:
            # If enhancement fails, return original products with basic SEO names
            return self._create_basic_seo_names(products)
    
    def _create_enhancement_prompt(self, products: List[Dict]) -> str:
        """Create prompt for enhancing product names"""
        products_text = ""
        for i, product in enumerate(products):
            products_text += f"{i+1}. {product.get('name', '')} - {product.get('model', '')}\n"
        
        return f"""
        Create SEO-friendly e-commerce product names for these Denon audio products. 
        
        Requirements:
        1. Include brand (Denon)
        2. Include model number
        3. Include key features (channels, power, connectivity)
        4. Keep under 70 characters
        5. Make them searchable and professional
        6. Follow this format: "Brand Model - Key Specs - Main Features"
        
        Example: "Denon AVR-X1800H - 7.2Ch 175W AV Receiver - 8K HDMI, HEOS, WiFi"
        
        Products to enhance:
        {products_text}
        
        Return as JSON array with this structure:
        [
          {{
            "original_name": "original name from input",
            "seo_name": "Enhanced SEO-friendly name",
            "search_keywords": ["keyword1", "keyword2", "keyword3"]
          }}
        ]
        """
    
    def _parse_enhancement_response(self, response_text: str, original_products: List[Dict]) -> List[Dict]:
        """Parse enhancement response and merge with original products"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\[(.*?)\]', response_text, re.DOTALL)
            if json_match:
                json_str = '[' + json_match.group(1) + ']'
                enhancements = json.loads(json_str)
                
                # Merge enhancements with original products
                for i, product in enumerate(original_products):
                    if i < len(enhancements):
                        enhancement = enhancements[i]
                        product['seo_name'] = enhancement.get('seo_name', product.get('name'))
                        product['search_keywords'] = enhancement.get('search_keywords', [])
                        product['opencart_name'] = enhancement.get('seo_name', product.get('name'))
                
                return original_products
                
        except:
            pass
        
        # Fallback to basic SEO names
        return self._create_basic_seo_names(original_products)
    
    def _create_basic_seo_names(self, products: List[Dict]) -> List[Dict]:
        """Create basic SEO-friendly names as fallback"""
        for product in products:
            name = product.get('name', '')
            model = product.get('model', '')
            specs = product.get('specifications', '')
            
            # Create basic SEO name
            seo_name = f"Denon {model}"
            if specs:
                # Extract key specs
                if 'Ch.' in specs:
                    channels = re.search(r'(\d+\.?\d*)\s*Ch\.', specs)
                    if channels:
                        seo_name += f" - {channels.group(1)}Ch"
                
                if 'W ' in specs:
                    power = re.search(r'(\d+)W', specs)
                    if power:
                        seo_name += f" {power.group(1)}W"
                
                if '8K' in specs:
                    seo_name += " 8K"
                if 'HEOS' in specs:
                    seo_name += " HEOS"
            
            seo_name += " AV Receiver"
            
            product['seo_name'] = seo_name
            product['opencart_name'] = seo_name
            product['search_keywords'] = [model, 'Denon', 'AV Receiver', '8K', 'HEOS']
        
        return products
