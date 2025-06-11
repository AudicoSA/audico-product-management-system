"""
SqlLantern-style API for Audico Integration
Provides database querying capabilities with SqlLantern interface
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from database_manager import initialize_database, get_database_manager
from product_analyzer import ProductStatusAnalyzer, ProductData
from typing import Dict, List, Any
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Global variables
analyzer = None
last_comparison_result = None
last_update_time = None

def initialize_app():
    """Initialize the application with database connection"""
    global analyzer
    
    # Initialize database connection
    initialize_database(
        host="dedi159.cpt4.host-h.net",
        username="audicdmyde_314",
        password="4hG4xcGS3tSgX76o5FSv",
        database="audicdmyde_db__359",
        port=3306,
        prefix="oc_"
    )
    
    analyzer = ProductStatusAnalyzer()
    logging.info("Application initialized successfully")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db_manager = get_database_manager()
        is_connected = db_manager.test_connection()
        
        return jsonify({
            'status': 'healthy' if is_connected else 'unhealthy',
            'database_connected': is_connected,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/products/opencart', methods=['GET'])
def get_opencart_products():
    """Get products from OpenCart database"""
    try:
        products = analyzer.get_opencart_products()
        
        products_data = []
        for product in products:
            products_data.append({
                'id': product.opencart_id,
                'sku': product.sku,
                'name': product.name,
                'model': product.model,
                'price': float(product.price),
                'description': product.description,
                'manufacturer': product.manufacturer,
                'status': product.status.value
            })
        
        return jsonify({
            'products': products_data,
            'total': len(products_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/pricelist', methods=['GET'])
def get_pricelist_products():
    """Get products from pricelist (sample data for now)"""
    try:
        products = analyzer.create_sample_pricelist_data()
        
        products_data = []
        for product in products:
            products_data.append({
                'sku': product.sku,
                'name': product.name,
                'model': product.model,
                'price': float(product.price),
                'description': product.description,
                'category': product.category,
                'manufacturer': product.manufacturer
            })
        
        return jsonify({
            'products': products_data,
            'total': len(products_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/compare', methods=['GET'])
def compare_products():
    """Compare pricelist products with OpenCart products"""
    global last_comparison_result, last_update_time
    
    try:
        # Use cached result if recent (within 5 minutes)
        if (last_comparison_result and last_update_time and 
            (datetime.now() - last_update_time).seconds < 300):
            return jsonify(last_comparison_result)
        
        # Get fresh comparison
        pricelist_products = analyzer.create_sample_pricelist_data()
        comparison_result = analyzer.compare_products(pricelist_products)
        
        # Format for API response
        products_data = []
        for product in comparison_result.products:
            product_data = {
                'sku': product.sku,
                'name': product.name,
                'model': product.model,
                'price': float(product.price),
                'description': product.description,
                'manufacturer': product.manufacturer,
                'status': product.status.value,
                'opencart_id': product.opencart_id
            }
            
            if product.price_difference:
                product_data['price_difference'] = float(product.price_difference)
            
            products_data.append(product_data)
        
        result = {
            'products': products_data,
            'summary': comparison_result.summary,
            'total': comparison_result.total_products,
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache the result
        last_comparison_result = result
        last_update_time = datetime.now()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/status/<status>', methods=['GET'])
def get_products_by_status(status):
    """Get products filtered by status"""
    try:
        pricelist_products = analyzer.create_sample_pricelist_data()
        comparison_result = analyzer.compare_products(pricelist_products)
        
        filtered_products = [
            p for p in comparison_result.products 
            if p.status.value == status.lower()
        ]
        
        products_data = []
        for product in filtered_products:
            product_data = {
                'sku': product.sku,
                'name': product.name,
                'model': product.model,
                'price': float(product.price),
                'description': product.description,
                'manufacturer': product.manufacturer,
                'status': product.status.value,
                'opencart_id': product.opencart_id
            }
            
            if product.price_difference:
                product_data['price_difference'] = float(product.price_difference)
            
            products_data.append(product_data)
        
        return jsonify({
            'products': products_data,
            'total': len(products_data),
            'status_filter': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/summary', methods=['GET'])
def get_products_summary():
    """Get summary of product statuses"""
    try:
        pricelist_products = analyzer.create_sample_pricelist_data()
        comparison_result = analyzer.compare_products(pricelist_products)
        
        return jsonify({
            'summary': comparison_result.summary,
            'total_products': comparison_result.total_products,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
