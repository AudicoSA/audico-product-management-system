import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error(`API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data)
    return Promise.reject(error)
  }
)

export const apiService = {
  // Basic API endpoints
  testConnection: async () => {
    const response = await api.get('/api/test')
    return response.data
  },

  getHealth: async () => {
    const response = await api.get('/health')
    return response.data
  },

  // OpenCart endpoints
  testOpenCart: async () => {
    const response = await api.get('/api/opencart/test')
    return response.data
  },

  getOpenCartProducts: async (limit = 20) => {
    const response = await api.get(`/api/opencart/products?limit=${limit}`)
    return response.data
  },

  searchOpenCartProducts: async (searchTerm) => {
    const response = await api.get(`/api/opencart/search/${encodeURIComponent(searchTerm)}`)
    return response.data
  },

  // PDF processing endpoints
  uploadPDF: async (file, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/api/pdf/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onProgress(percentCompleted)
        }
      },
    })
    return response.data
  },

  validateProducts: async (products) => {
    const response = await api.post('/api/pdf/validate', { products })
    return response.data
  },

  // Workflow endpoints
  startWorkflow: async (file, options = {}) => {
    const formData = new FormData()
    formData.append('file', file)

    // Add options to form data
    Object.keys(options).forEach(key => {
      formData.append(key, options[key])
    })

    const response = await api.post('/api/workflow/start', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  getWorkflowStatus: async (workflowId) => {
    const response = await api.get(`/api/workflow/${workflowId}/status`)
    return response.data
  },

  getWorkflowSummary: async (workflowId) => {
    const response = await api.get(`/api/workflow/${workflowId}/summary`)
    return response.data
  },

  listWorkflows: async (limit = 20) => {
    const response = await api.get(`/api/workflow/list?limit=${limit}`)
    return response.data
  },

  cancelWorkflow: async (workflowId) => {
    const response = await api.post(`/api/workflow/${workflowId}/cancel`)
    return response.data
  },

  // Comparison endpoints
  compareProducts: async (products) => {
    const response = await api.post('/api/comparison/compare', { products })
    return response.data
  },

  // Automation endpoints
  createMissingProducts: async (products) => {
    const response = await api.post('/api/automation/create_missing', { products })
    return response.data
  },
}

export default api