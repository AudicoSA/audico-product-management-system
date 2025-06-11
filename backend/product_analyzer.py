"""
Product Status Analyzer for Audico-SqlLantern Integration
Compares products between pricelists and OpenCart database
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import logging
from decimal import Decimal
from database_manager import get_database_manager

class ProductStatus(Enum):
    """Product status enumeration"""
    ONLINE = "online"      # Product exists in both pricelist and OpenCart
    ADD = "add"           # Product in pricelist but not in OpenCart
    REMOVE = "remove"     # Product in OpenCart but not in pricelist
    PRICE = "price"       # Product exists but price differs
    UPDATE = "update"     # Product exists but other details differ

@dataclass
class ProductData:
    """Product data structure"""
    sku: str
    name: str
    model: str
    price: Decimal
    description: str = ""
    category: str = ""
    manufacturer: str = ""
    status: ProductStatus = ProductStatus.ADD
    opencart_id: Optional[int] = None
    price_difference: Optional[Decimal] = None

@dataclass
class ComparisonResult:
    """Result of product comparison"""
    products: List[ProductData]
    summary: Dict[str, int]
    total_products: int

class ProductStatusAnalyzer:
    """Analyzes product status between pricelist and OpenCart"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
    
    def get_opencart_products(self) -> List[ProductData]:
        """Retrieve products from OpenCart database"""
        try:
            query = """
            SELECT 
                p.product_id,
                p.model,
                p.sku,
                p.price,
                p.quantity,
                p.status,
                pd.name,
                pd.description,
                m.name as manufacturer
            FROM {products} p
            LEFT JOIN {product_description} pd ON p.product_id = pd.product_id
            LEFT JOIN {manufacturer} m ON p.manufacturer_id = m.manufacturer_id
            WHERE pd.language_id = 1 AND p.status = 1
            ORDER BY p.product_id
            """.format(
                products=self.db_manager.get_table_name('product'),
                product_description=self.db_manager.get_table_name('product_description'),
                manufacturer=self.db_manager.get_table_name('manufacturer')
            )
            
            results = self.db_manager.execute_query(query)
            
            products = []
            for row in results:
                product = ProductData(
                    sku=row.get('sku', ''),
                    name=row.get('name', ''),
                    model=row.get('model', ''),
                    price=Decimal(str(row.get('price', 0))),
                    description=row.get('description', ''),
                    manufacturer=row.get('manufacturer', ''),
                    status=ProductStatus.ONLINE,
                    opencart_id=row.get('product_id')
                )
                products.append(product)
            
            logging.info(f"Retrieved {len(products)} products from OpenCart")
            return products
            
        except Exception as e:
            logging.error(f"Failed to retrieve OpenCart products: {e}")
            return []
    
    def create_sample_pricelist_data(self) -> List[ProductData]:
        """Create sample pricelist data for testing"""
        return [
            ProductData(
                sku="AUD001",
                name="Audio Cable XLR Male to Female",
                model="XLR-MF-001",
                price=Decimal("25.99"),
                description="Professional XLR cable",
                category="Cables",
                manufacturer="AudioPro"
            ),
            ProductData(
                sku="AUD002", 
                name="Studio Monitor 5 Inch",
                model="MON-5-001",
                price=Decimal("199.99"),
                description="Active studio monitor",
                category="Monitors",
                manufacturer="AudioPro"
            ),
            ProductData(
                sku="AUD003",
                name="Microphone Dynamic SM58",
                model="MIC-DYN-58",
                price=Decimal("99.99"),
                description="Dynamic microphone",
                category="Microphones", 
                manufacturer="AudioPro"
            )
        ]
    
    def compare_products(self, pricelist_products: List[ProductData]) -> ComparisonResult:
        """Compare pricelist products with OpenCart products"""
        opencart_products = self.get_opencart_products()
        
        # Create lookup dictionaries
        opencart_by_sku = {p.sku: p for p in opencart_products if p.sku}
        opencart_by_model = {p.model: p for p in opencart_products if p.model}
        
        compared_products = []
        opencart_matched = set()
        
        # Process pricelist products
        for pricelist_product in pricelist_products:
            # Try to match by SKU first, then by model
            opencart_match = None
            if pricelist_product.sku in opencart_by_sku:
                opencart_match = opencart_by_sku[pricelist_product.sku]
            elif pricelist_product.model in opencart_by_model:
                opencart_match = opencart_by_model[pricelist_product.model]
            
            if opencart_match:
                opencart_matched.add(opencart_match.opencart_id)
                
                # Compare prices
                price_diff = abs(pricelist_product.price - opencart_match.price)
                if price_diff > Decimal('0.01'):  # Price difference threshold
                    pricelist_product.status = ProductStatus.PRICE
                    pricelist_product.price_difference = pricelist_product.price - opencart_match.price
                else:
                    pricelist_product.status = ProductStatus.ONLINE
                
                pricelist_product.opencart_id = opencart_match.opencart_id
            else:
                pricelist_product.status = ProductStatus.ADD
            
            compared_products.append(pricelist_product)
        
        # Find products to remove (in OpenCart but not in pricelist)
        for opencart_product in opencart_products:
            if opencart_product.opencart_id not in opencart_matched:
                opencart_product.status = ProductStatus.REMOVE
                compared_products.append(opencart_product)
        
        # Generate summary
        summary = {
            'online': len([p for p in compared_products if p.status == ProductStatus.ONLINE]),
            'add': len([p for p in compared_products if p.status == ProductStatus.ADD]),
            'remove': len([p for p in compared_products if p.status == ProductStatus.REMOVE]),
            'price': len([p for p in compared_products if p.status == ProductStatus.PRICE]),
            'update': len([p for p in compared_products if p.status == ProductStatus.UPDATE])
        }
        
        return ComparisonResult(
            products=compared_products,
            summary=summary,
            total_products=len(compared_products)
        )
    
    def get_status_summary(self, products: List[ProductData]) -> Dict[str, int]:
        """Get summary of product statuses"""
        summary = {status.value: 0 for status in ProductStatus}
        for product in products:
            summary[product.status.value] += 1
        return summary
