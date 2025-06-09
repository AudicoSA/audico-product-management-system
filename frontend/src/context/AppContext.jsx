import React, { createContext, useContext, useReducer, useEffect } from 'react';
import apiService from '../services/apiService'; // Use default import

const AppContext = createContext();

// Initial state
const initialState = {
  // System status
  apiConnected: false,
  openCartConnected: false,
  systemHealth: null,
  
  // Current data
  products: [],
  workflows: [],
  currentWorkflow: null,
  
  // UI state
  loading: false,
  error: null,
  notifications: [],
  
  // Processing state
  processingJobs: {},
  
  // Analytics
  stats: {
    totalProducts: 0,
    successfulUploads: 0,
    failedUploads: 0,
    averageProcessingTime: 0,
  },
};

// Action types
const actionTypes = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  SET_API_STATUS: 'SET_API_STATUS',
  SET_OPENCART_STATUS: 'SET_OPENCART_STATUS',
  SET_SYSTEM_HEALTH: 'SET_SYSTEM_HEALTH',
  SET_PRODUCTS: 'SET_PRODUCTS',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  START_PROCESSING: 'START_PROCESSING',
  UPDATE_PROCESSING: 'UPDATE_PROCESSING',
  COMPLETE_PROCESSING: 'COMPLETE_PROCESSING',
  ADD_WORKFLOW: 'ADD_WORKFLOW',
  UPDATE_WORKFLOW: 'UPDATE_WORKFLOW',
  UPDATE_STATS: 'UPDATE_STATS',
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case actionTypes.SET_LOADING:
      return { ...state, loading: action.payload };
    
    case actionTypes.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    
    case actionTypes.CLEAR_ERROR:
      return { ...state, error: null };
    
    case actionTypes.SET_API_STATUS:
      return { ...state, apiConnected: action.payload };
    
    case actionTypes.SET_OPENCART_STATUS:
      return { ...state, openCartConnected: action.payload };
    
    case actionTypes.SET_SYSTEM_HEALTH:
      return { ...state, systemHealth: action.payload };
    
    case actionTypes.SET_PRODUCTS:
      return { ...state, products: action.payload };
    
    case actionTypes.ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [...state.notifications, action.payload],
      };
    
    case actionTypes.REMOVE_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };
    
    case actionTypes.START_PROCESSING:
      return {
        ...state,
        processingJobs: {
          ...state.processingJobs,
          [action.payload.id]: { ...action.payload, status: 'processing' },
        },
      };
    
    case actionTypes.UPDATE_PROCESSING:
      return {
        ...state,
        processingJobs: {
          ...state.processingJobs,
          [action.payload.id]: { ...state.processingJobs[action.payload.id], ...action.payload },
        },
      };
    
    case actionTypes.COMPLETE_PROCESSING:
      return {
        ...state,
        processingJobs: {
          ...state.processingJobs,
          [action.payload.id]: { ...state.processingJobs[action.payload.id], status: 'completed', ...action.payload },
        },
      };
    
    case actionTypes.ADD_WORKFLOW:
      return {
        ...state,
        workflows: [action.payload, ...state.workflows],
      };
    
    case actionTypes.UPDATE_WORKFLOW:
      return {
        ...state,
        workflows: state.workflows.map(w => 
          w.id === action.payload.id ? { ...w, ...action.payload } : w
        ),
      };
    
    case actionTypes.UPDATE_STATS:
      return {
        ...state,
        stats: { ...state.stats, ...action.payload },
      };
    
    default:
      return state;
  }
};

// Context Provider
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Actions
  const actions = {
    setLoading: (loading) => dispatch({ type: actionTypes.SET_LOADING, payload: loading }),
    setError: (error) => dispatch({ type: actionTypes.SET_ERROR, payload: error }),
    clearError: () => dispatch({ type: actionTypes.CLEAR_ERROR }),
    
    // System status checks
    checkSystemHealth: async () => {
      try {
        const health = await apiService.healthCheck();
        dispatch({ type: actionTypes.SET_SYSTEM_HEALTH, payload: health });
        dispatch({ type: actionTypes.SET_API_STATUS, payload: health.status === 'healthy' });
        return health;
      } catch (error) {
        dispatch({ type: actionTypes.SET_API_STATUS, payload: false });
        throw error;
      }
    },

    checkOpenCartConnection: async () => {
      try {
        const result = await apiService.testOpenCart();
        dispatch({ type: actionTypes.SET_OPENCART_STATUS, payload: result.status === 'success' });
        return result;
      } catch (error) {
        dispatch({ type: actionTypes.SET_OPENCART_STATUS, payload: false });
        throw error;
      }
    },

    // Products
    loadProducts: async (limit = 20) => {
      try {
        actions.setLoading(true);
        const result = await apiService.getProducts(limit);
        dispatch({ type: actionTypes.SET_PRODUCTS, payload: result.products || [] });
        return result;
      } catch (error) {
        actions.setError(error.message);
        throw error;
      } finally {
        actions.setLoading(false);
      }
    },

    // Notifications
    addNotification: (notification) => {
      const id = Date.now().toString();
      dispatch({
        type: actionTypes.ADD_NOTIFICATION,
        payload: { id, ...notification, timestamp: new Date() },
      });
      
      // Auto remove after 5 seconds for non-error notifications
      if (notification.type !== 'error') {
        setTimeout(() => {
          actions.removeNotification(id);
        }, 5000);
      }
    },

    removeNotification: (id) => {
      dispatch({ type: actionTypes.REMOVE_NOTIFICATION, payload: id });
    },

    // Processing jobs
    startProcessing: (job) => {
      dispatch({ type: actionTypes.START_PROCESSING, payload: job });
    },

    updateProcessing: (jobUpdate) => {
      dispatch({ type: actionTypes.UPDATE_PROCESSING, payload: jobUpdate });
    },

    completeProcessing: (jobResult) => {
      dispatch({ type: actionTypes.COMPLETE_PROCESSING, payload: jobResult });
    },

    // Workflows
    addWorkflow: (workflow) => {
      dispatch({ type: actionTypes.ADD_WORKFLOW, payload: workflow });
    },

    updateWorkflow: (workflowUpdate) => {
      dispatch({ type: actionTypes.UPDATE_WORKFLOW, payload: workflowUpdate });
    },

    // Stats
    updateStats: (statsUpdate) => {
      dispatch({ type: actionTypes.UPDATE_STATS, payload: statsUpdate });
    },
  };

  // Initialize system health check on mount
  useEffect(() => {
    actions.checkSystemHealth().catch(console.error);
    actions.checkOpenCartConnection().catch(console.error);
  }, []);

  // Provide state and actions
  const value = {
    ...state,
    actions,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Custom hook to use the context
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export default AppContext;
