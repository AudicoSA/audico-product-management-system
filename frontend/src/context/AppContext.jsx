import React, { createContext, useContext, useReducer, useEffect } from 'react'
import { apiService } from '../services/apiService'

const AppContext = createContext()

const initialState = {
  apiStatus: 'unknown',
  opencartStatus: 'unknown',
  workflows: [],
  currentWorkflow: null,
  notifications: [],
  settings: {
    autoCreateMissing: true,
    autoUpdatePrices: false,
    validationThreshold: 0.7,
    priceTolerancePercent: 5.0,
    batchSize: 10,
    dryRun: true,
  },
}

function appReducer(state, action) {
  switch (action.type) {
    case 'SET_API_STATUS':
      return { ...state, apiStatus: action.payload }
    case 'SET_OPENCART_STATUS':
      return { ...state, opencartStatus: action.payload }
    case 'SET_WORKFLOWS':
      return { ...state, workflows: action.payload }
    case 'SET_CURRENT_WORKFLOW':
      return { ...state, currentWorkflow: action.payload }
    case 'ADD_NOTIFICATION':
      return {
        ...state,
        notifications: [...state.notifications, { id: Date.now(), ...action.payload }],
      }
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      }
    case 'UPDATE_SETTINGS':
      return {
        ...state,
        settings: { ...state.settings, ...action.payload },
      }
    default:
      return state
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState)

  // Check API status on startup
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await apiService.testConnection()
        dispatch({ type: 'SET_API_STATUS', payload: 'connected' })
      } catch (error) {
        dispatch({ type: 'SET_API_STATUS', payload: 'disconnected' })
      }
    }

    const checkOpenCartStatus = async () => {
      try {
        const response = await apiService.testOpenCart()
        dispatch({ type: 'SET_OPENCART_STATUS', payload: response.status === 'success' ? 'connected' : 'error' })
      } catch (error) {
        dispatch({ type: 'SET_OPENCART_STATUS', payload: 'disconnected' })
      }
    }

    checkApiStatus()
    checkOpenCartStatus()
  }, [])

  const actions = {
    addNotification: (notification) => dispatch({ type: 'ADD_NOTIFICATION', payload: notification }),
    removeNotification: (id) => dispatch({ type: 'REMOVE_NOTIFICATION', payload: id }),
    updateSettings: (settings) => dispatch({ type: 'UPDATE_SETTINGS', payload: settings }),
    setCurrentWorkflow: (workflow) => dispatch({ type: 'SET_CURRENT_WORKFLOW', payload: workflow }),
    setWorkflows: (workflows) => dispatch({ type: 'SET_WORKFLOWS', payload: workflows }),
  }

  return (
    <AppContext.Provider value={{ state, actions }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppContext() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider')
  }
  return context
}