import axios from 'axios';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000',
  timeout: 120000, // 2 minutes timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging
apiClient.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.config?.url, error.response?.data);
    return Promise.reject(error);
  }
);

// API Methods Object
const apiService = {
  // Health check
  healthCheck: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Test API connection
  testConnection: async () => {
    try {
      const response = await apiClient.get('/api/test');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // OpenCart methods
  testOpenCart: async () => {
    try {
      const response = await apiClient.get('/api/opencart/test');
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  getProducts: async (limit = 20) => {
    try {
      const response = await apiClient.get(`/api/opencart/products?limit=${limit}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  searchProducts: async (searchTerm) => {
    try {
      const response = await apiClient.get(`/api/opencart/search/${encodeURIComponent(searchTerm)}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // PDF processing methods
  uploadPDF: async (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/api/pdf/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percentCompleted);
          }
        },
      });
      return response.data;
    } catch (error) {
      console.error('PDF Upload Error:', error);
      
      if (error.code === 'ECONNABORTED') {
        throw new Error('Upload timed out. The file might be too large or processing is taking longer than expected.');
      }
      
      throw error;
    }
  },

  // Async PDF processing
  uploadPDFAsync: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/api/pdf/upload-async', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000, // 30 seconds for starting the job
      });
      return response.data;
    } catch (error) {
      console.error('Async PDF Upload Error:', error);
      throw error;
    }
  },

  // Get processing status
  getProcessingStatus: async (jobId) => {
    try {
      const response = await apiClient.get(`/api/pdf/status/${jobId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Simple PDF upload for testing
  uploadPDFSimple: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await apiClient.post('/api/pdf/upload-simple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000,
      });
      return response.data;
    } catch (error) {
      console.error('Simple PDF Upload Error:', error);
      throw error;
    }
  },

  // Workflow methods
  startWorkflow: async (file, options = {}) => {
    const formData = new FormData();
    formData.append('file', file);
    
    // Add options to form data
    Object.keys(options).forEach(key => {
      formData.append(key, String(options[key]));
    });

    try {
      const response = await apiClient.post('/api/workflow/start', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes
      });
      return response.data;
    } catch (error) {
      console.error('Workflow Start Error:', error);
      throw error;
    }
  },

  getWorkflowStatus: async (workflowId) => {
    try {
      const response = await apiClient.get(`/api/workflow/${workflowId}/status`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  listWorkflows: async (limit = 20) => {
    try {
      const response = await apiClient.get(`/api/workflow/list?limit=${limit}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Product validation
  validateProducts: async (products) => {
    try {
      const response = await apiClient.post('/api/pdf/validate', { products });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Product comparison
  compareProducts: async (products) => {
    try {
      const response = await apiClient.post('/api/comparison/compare', { products });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // Automation
  createMissingProducts: async (products) => {
    try {
      const response = await apiClient.post('/api/automation/create_missing', { products });
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

// Export the apiService object as default
export default apiService;

// Named exports for individual methods (for backward compatibility)
export const {
  healthCheck,
  testConnection,
  testOpenCart,
  getProducts,
  searchProducts,
  uploadPDF,
  uploadPDFAsync,
  uploadPDFSimple,
  getProcessingStatus,
  startWorkflow,
  getWorkflowStatus,
  listWorkflows,
  validateProducts,
  compareProducts,
  createMissingProducts,
} = apiService;

// Also export as named export for the context
export { apiService };
