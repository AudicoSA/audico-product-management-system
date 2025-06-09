import os
import json
import re
from typing import Dict, List
from dotenv import load_dotenv

# Import the newer OpenAI client
try:
    from openai import OpenAI
except ImportError:
    # Fallback for older OpenAI versions
    import openai as openai_legacy
    OpenAI = None

load_dotenv()

class OpenAIExtractor:
    """OpenAI-powered PDF text extraction and product parsing"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Use the new OpenAI client if available
        if OpenAI:
            self.client = OpenAI(api_key=self.api_key)
        else:
            # Fallback to legacy client
            openai_legacy.api_key = self.api_key
            self.client = None
    
    def extract_and_parse_products(self, pdf_text: str) -> Dict:
        """Extract and parse products using OpenAI GPT-4"""
        try:
            print(f"Starting OpenAI extraction for text length: {len(pdf_text)}")
            
            # Create extraction prompt
            extraction_prompt = self._create_extraction_prompt(pdf_text)
            
            # Make API call using appropriate client
            if self.client:
                # New client
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert at extracting product information from audio equipment pricelists. You must return valid JSON only, with no additional text or formatting."
                        },
                        {
                            "role": "user", 
                            "content": extraction_prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=8000  # Increased token limit
                )
                products_text = response.choices[0].message.content
            else:
                # Legacy client
                response = openai_legacy.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert at extracting product information from audio equipment pricelists. Return only valid JSON."
                        },
                        {
                            "role": "user", 
                            "content": extraction_prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=8000
                )
                products_text = response.choices[0].message.content
            
            print(f"OpenAI response length: {len(products_text)}")
            print(f"Response preview: {products_text[:200]}...")
            
            # Parse the response with multiple fallback strategies
            products_data = self._robust_parse_response(products_text)
            
            if not products_data:
                print("❌ Failed to parse any products from OpenAI response")
                # Try direct text parsing as last resort
                products_data = self._extract_from_text_response(products_text)
            
            if not products_data:
                return {
                    'success': False,
                    'error': 'Failed to parse OpenAI response after multiple attempts',
                    'raw_response': products_text[:500]
                }
            
            print(f"Successfully parsed {len(products_data)} products from OpenAI")
            
            # Clean and validate products
            cleaned_products = self._clean_and_validate_products(products_data)
            
            return {
                'success': True,
                'method': 'openai_extraction',
                'products_found': len(cleaned_products),
                'products': cleaned_products,
                'raw_response': products_text[:500] + "..." if len(products_text) > 500 else products_text
            }
            
        except Exception as e:
            print(f"OpenAI extraction error: {str(e)}")
            return {
                'success': False,
                'error': f'OpenAI extraction failed: {str(e)}'
            }
    
    def _create_extraction_prompt(self, pdf_text: str) -> str:
        """Create detailed prompt for product extraction"""
        # Truncate text if too long
        max_length = 8000
        if len(pdf_text) > max_length:
            pdf_text = pdf_text[:max_length] + "\n... [content truncated]"
        
        return f"""
Extract ALL audio equipment products from this Denon pricelist document.

CRITICAL INSTRUCTIONS:
1. Return ONLY a valid JSON array, no other text
2. Extract ALL products, not just examples
3. Each product must have: name, model, price (required fields)
4. Prices are in ZAR - remove R symbols and convert to numbers
5. If Old RRP = New RRP, set old_price to null

JSON structure (return this exact format):
[
{{"name":"Product Name","model":"MODEL","price":8990.0,"old_price":9990.0,"currency":"ZAR","category":"AV Receivers","brand":"Denon","specifications":"Full specs","features":["8K","HEOS"]}},
{{"name":"Product Name 2","model":"MODEL2","price":11990.0,"old_price":null,"currency":"ZAR","category":"AV Receivers","brand":"Denon","specifications":"Full specs","features":["8K","WiFi"]}}
]

Document content:
{pdf_text}

Return only the JSON array, no markdown formatting, no explanation text:"""
    
    def _robust_parse_response(self, response_text: str) -> List[Dict]:
        """Parse OpenAI response with multiple fallback strategies"""
        
        # Strategy 1: Clean and parse as JSON
        try:
            cleaned_response = self._clean_json_response(response_text)
            return json.loads(cleaned_response)
        except Exception as e:
            print(f"Strategy 1 failed: {e}")
        
        # Strategy 2: Extract JSON array from response
        try:
            json_array = self._extract_json_array(response_text)
            if json_array:
                return json.loads(json_array)
        except Exception as e:
            print(f"Strategy 2 failed: {e}")
        
        # Strategy 3: Fix common JSON issues and retry
        try:
            fixed_json = self._fix_json_issues(response_text)
            return json.loads(fixed_json)
        except Exception as e:
            print(f"Strategy 3 failed: {e}")
        
        # Strategy 4: Line-by-line object extraction
        try:
            return self._extract_objects_from_lines(response_text)
        except Exception as e:
            print(f"Strategy 4 failed: {e}")
        
        return []
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean response text for JSON parsing"""
        # Remove markdown formatting
        response_text = response_text.strip()
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        
        # Remove any explanatory text before/after JSON
        lines = response_text.split('\n')
        start_idx = -1
        end_idx = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('['):
                start_idx = i
                break
        
        for i in range(len(lines)-1, -1, -1):
            if lines[i].strip().endswith(']'):
                end_idx = i
                break
        
        if start_idx >= 0 and end_idx >= 0:
            return '\n'.join(lines[start_idx:end_idx+1])
        
        return response_text
    
    def _extract_json_array(self, response_text: str) -> str:
        """Extract JSON array from response text"""
        # Find the JSON array boundaries
        start_pos = response_text.find('[')
        if start_pos == -1:
            return None
        
        # Find matching closing bracket
        bracket_count = 0
        end_pos = -1
        
        for i in range(start_pos, len(response_text)):
            if response_text[i] == '[':
                bracket_count += 1
            elif response_text[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end_pos = i
                    break
        
        if end_pos > start_pos:
            return response_text[start_pos:end_pos+1]
        
        return None
    
    def _fix_json_issues(self, response_text: str) -> str:
        """Fix common JSON formatting issues"""
        # Extract potential JSON content
        json_content = self._extract_json_array(response_text)
        if not json_content:
            return response_text
        
        # Fix common issues
        fixed = json_content
        
        # Fix trailing commas
        fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
        
        # Fix missing quotes around field names
        fixed = re.sub(r'(\w+):', r'"\1":', fixed)
        
        # Fix single quotes
        fixed = fixed.replace("'", '"')
        
        # Try to complete truncated JSON
        if not fixed.strip().endswith(']'):
            # Count open braces/brackets
            open_braces = fixed.count('{') - fixed.count('}')
            open_brackets = fixed.count('[') - fixed.count(']')
            
            # Add missing closing braces
            for _ in range(open_braces):
                fixed += '}'
            
            # Add missing closing brackets
            for _ in range(open_brackets):
                fixed += ']'
        
        return fixed
    
    def _extract_objects_from_lines(self, response_text: str) -> List[Dict]:
        """Extract product objects by parsing line by line"""
        products = []
        lines = response_text.split('\n')
        current_product = {}
        
        for line in lines:
            line = line.strip()
            if not line or line in ['{', '}', '[', ']', ',']:
                continue
            
            # Remove trailing comma
            line = line.rstrip(',')
            
            # Parse key-value pairs
            if '":' in line:
                try:
                    # Extract key and value
                    key_match = re.search(r'"([^"]+)":', line)
                    if key_match:
                        key = key_match.group(1)
                        
                        # Extract value (handle different types)
                        value_part = line.split(':', 1)[1].strip()
                        
                        if value_part.startswith('"') and value_part.endswith('"'):
                            # String value
                            value = value_part[1:-1]
                        elif value_part.lower() in ['true', 'false']:
                            # Boolean value
                            value = value_part.lower() == 'true'
                        elif value_part.lower() == 'null':
                            # Null value
                            value = None
                        elif value_part.startswith('[') and value_part.endswith(']'):
                            # Array value
                            try:
                                value = json.loads(value_part)
                            except:
                                value = []
                        else:
                            # Numeric value
                            try:
                                value = float(value_part) if '.' in value_part else int(value_part)
                            except:
                                value = value_part.strip('"')
                        
                        current_product[key] = value
                        
                        # If we have a complete product, save it
                        if key == 'features' and current_product.get('name') and current_product.get('price'):
                            products.append(current_product.copy())
                            current_product = {}
                
                except Exception as e:
                    print(f"Error parsing line '{line}': {e}")
                    continue
        
        # Add last product if it's complete
        if current_product.get('name') and current_product.get('price'):
            products.append(current_product)
        
        return products
    
    def _extract_from_text_response(self, response_text: str) -> List[Dict]:
        """Extract products from plain text response"""
        products = []
        
        # Look for product mentions in the text
        lines = response_text.split('\n')
        
        for line in lines:
            # Skip empty lines and JSON formatting
            if not line.strip() or line.strip() in ['{', '}', '[', ']', ',']:
                continue
            
            # Look for lines that mention model numbers and prices
            if any(pattern in line.upper() for pattern in ['AVR', 'AVC', 'DENON']) and 'R' in line:
                product = self._extract_product_from_text_line(line)
                if product:
                    products.append(product)
        
        return products
    
    def _extract_product_from_text_line(self, line: str) -> Dict:
        """Extract product info from a single text line"""
        try:
            product = {
                'brand': 'Denon',
                'currency': 'ZAR',
                'category': 'AV Receivers',
                'features': ['AV Receiver']
            }
            
            # Extract model
            model_match = re.search(r'(AVR[A-Z]?-?[A-Z0-9]+|AVC-[A-Z0-9]+)', line, re.IGNORECASE)
            if model_match:
                product['model'] = model_match.group(1)
            
            # Extract prices
            price_matches = re.findall(r'R\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', line)
            if price_matches:
                prices = [float(p.replace(',', '')) for p in price_matches]
                if len(prices) >= 2:
                    product['old_price'] = prices[0]
                    product['price'] = prices[1]
                else:
                    product['price'] = prices[0]
            
            # Use the line as the name
            product['name'] = line.strip()
            product['specifications'] = line.strip()
            
            # Extract features
            if '8K' in line:
                product['features'].append('8K')
            if 'HEOS' in line:
                product['features'].append('HEOS')
            if 'Bluetooth' in line:
                product['features'].append('Bluetooth')
            
            return product if product.get('name') and product.get('price') else None
            
        except Exception as e:
            print(f"Error extracting from text line: {e}")
            return None
    
    def _clean_and_validate_products(self, products: List[Dict]) -> List[Dict]:
        """Clean and validate extracted products"""
        cleaned_products = []
        
        for product in products:
            try:
                # Ensure required fields
                if not product.get('name') or not product.get('price'):
                    continue
                
                # Clean price - ensure it's a float
                price = product.get('price')
                if isinstance(price, str):
                    # Remove currency symbols and convert
                    price_str = re.sub(r'[R,\s]', '', str(price))
                    if price_str:
                        try:
                            price = float(price_str)
                        except ValueError:
                            continue
                    else:
                        continue
                
                if not isinstance(price, (int, float)) or price <= 0:
                    continue
                
                # Clean old price
                old_price = product.get('old_price')
                if old_price and isinstance(old_price, str):
                    old_price_str = re.sub(r'[R,\s]', '', str(old_price))
                    try:
                        old_price = float(old_price_str) if old_price_str else None
                    except ValueError:
                        old_price = None
                
                # Build clean product
                clean_product = {
                    'name': str(product.get('name', '')).strip(),
                    'model': str(product.get('model', '')).strip(),
                    'price': float(price),
                    'old_price': float(old_price) if old_price and old_price != price else None,
                    'currency': product.get('currency', 'ZAR'),
                    'category': product.get('category', 'AV Receivers'),
                    'brand': product.get('brand', 'Denon'),
                    'specifications': str(product.get('specifications', '')).strip(),
                    'features': product.get('features', [])
                }
                
                # Create SEO-friendly name
                if clean_product['model']:
                    clean_product['seo_name'] = f"Denon {clean_product['model']} - {clean_product['specifications'][:50]}"
                else:
                    clean_product['seo_name'] = clean_product['name'][:70]
                
                cleaned_products.append(clean_product)
                
            except Exception as e:
                print(f"Error cleaning product {product}: {e}")
                continue
        
        return cleaned_products
