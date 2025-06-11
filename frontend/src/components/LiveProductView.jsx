import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './LiveProductView.css';

const LiveProductView = () => {
  const [products, setProducts] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [lastUpdate, setLastUpdate] = useState(null);

  // Use main API URL (merged server)
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  const statusConfig = {
    online: { color: '#28a745', icon: '✓', label: 'Online' },
    add: { color: '#007bff', icon: '+', label: 'Add' },
    remove: { color: '#dc3545', icon: '−', label: 'Remove' },
    price: { color: '#ffc107', icon: '$', label: 'Price' },
    update: { color: '#6f42c1', icon: '↻', label: 'Update' }
  };

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/products/compare`);
      setProducts(response.data.products || []);
      setSummary(response.data.summary || {});
      setLastUpdate(new Date(response.data.timestamp));
      setError(null);
    } catch (err) {
      setError('Failed to fetch products: ' + err.message);
      console.error('Error fetching products:', err);
      // Set empty data on error
      setProducts([]);
      setSummary({});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchProducts, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleFilterChange = (filter) => {
    setActiveFilter(filter);
  };

  const filteredProducts = activeFilter === 'all' 
    ? products 
    : products.filter(product => product.status === activeFilter);

  const handleProductAction = (product, action) => {
    // Placeholder for future actions
    console.log(`Action ${action} for product:`, product);
    // TODO: Implement actual actions (add to store, update price, etc.)
  };

  if (loading && products.length === 0) {
    return (
      <div className="live-product-view">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading products...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="live-product-view">
      <div className="header">
        <h2>Live Product Status Dashboard</h2>
        <div className="controls">
          <button onClick={fetchProducts} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          {lastUpdate && (
            <span className="last-update">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <p>⚠️ {error}</p>
          <button onClick={fetchProducts}>Retry</button>
        </div>
      )}

      {/* Summary Dashboard */}
      <div className="summary-dashboard">
        <div className="summary-card">
          <h3>Product Status Summary</h3>
          <div className="summary-grid">
            {Object.entries(statusConfig).map(([status, config]) => (
              <div key={status} className="summary-item">
                <div 
                  className="status-indicator"
                  style={{ backgroundColor: config.color }}
                >
                  {config.icon}
                </div>
                <div className="summary-details">
                  <span className="count">{summary[status] || 0}</span>
                  <span className="label">{config.label}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Status Filters */}
      <div className="status-filters">
        <button 
          className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`}
          onClick={() => handleFilterChange('all')}
        >
          All ({products.length})
        </button>
        {Object.entries(statusConfig).map(([status, config]) => (
          <button 
            key={status}
            className={`filter-btn ${activeFilter === status ? 'active' : ''}`}
            onClick={() => handleFilterChange(status)}
            style={{ 
              borderColor: config.color,
              color: activeFilter === status ? '#fff' : config.color,
              backgroundColor: activeFilter === status ? config.color : 'transparent'
            }}
          >
            {config.icon} {config.label} ({summary[status] || 0})
          </button>
        ))}
      </div>

      {/* Products Grid */}
      <div className="products-grid">
        {filteredProducts.length === 0 ? (
          <div className="empty-state">
            <p>No products found for the selected filter.</p>
          </div>
        ) : (
          filteredProducts.map((product, index) => (
            <ProductCard 
              key={product.sku || index}
              product={product}
              statusConfig={statusConfig}
              onAction={handleProductAction}
            />
          ))
        )}
      </div>
    </div>
  );
};

const ProductCard = ({ product, statusConfig, onAction }) => {
  const status = statusConfig[product.status];
  
  return (
    <div className="product-card">
      <div className="product-header">
        <div 
          className="status-badge"
          style={{ backgroundColor: status.color }}
        >
          {status.icon} {status.label}
        </div>
        {product.opencart_id && (
          <div className="opencart-id">ID: {product.opencart_id}</div>
        )}
      </div>
      
      <div className="product-info">
        <h4 className="product-name">{product.name}</h4>
        <div className="product-details">
          <p><strong>SKU:</strong> {product.sku}</p>
          <p><strong>Model:</strong> {product.model}</p>
          <p><strong>Price:</strong> ${product.price.toFixed(2)}</p>
          {product.price_difference && (
            <p className="price-diff">
              <strong>Price Difference:</strong> 
              <span style={{ color: product.price_difference > 0 ? '#28a745' : '#dc3545' }}>
                {product.price_difference > 0 ? '+' : ''}${product.price_difference.toFixed(2)}
              </span>
            </p>
          )}
          {product.manufacturer && (
            <p><strong>Manufacturer:</strong> {product.manufacturer}</p>
          )}
        </div>
      </div>

      <div className="product-actions">
        {product.status === 'add' && (
          <button 
            className="action-btn add-btn"
            onClick={() => onAction(product, 'add')}
          >
            Add to Store
          </button>
        )}
        {product.status === 'price' && (
          <button 
            className="action-btn update-btn"
            onClick={() => onAction(product, 'update-price')}
          >
            Update Price
          </button>
        )}
        {product.status === 'remove' && (
          <button 
            className="action-btn remove-btn"
            onClick={() => onAction(product, 'remove')}
          >
            Remove from Store
          </button>
        )}
        {product.status === 'online' && (
          <button 
            className="action-btn view-btn"
            onClick={() => onAction(product, 'view')}
          >
            View Details
          </button>
        )}
      </div>
    </div>
  );
};

export default LiveProductView;
