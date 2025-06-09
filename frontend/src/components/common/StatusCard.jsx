import React from 'react'
import { Card, CardContent, Typography, Box, CircularProgress } from '@mui/material'
import { CheckCircle, Error, Warning, Wifi, WifiOff } from '@mui/icons-material'

function StatusCard({ title, status, description, loading = false }) {
  const getStatusConfig = (status) => {
    switch (status) {
      case 'online':
      case 'connected':
      case 'ready':
        return { 
          color: 'success.main', 
          icon: <CheckCircle />, 
          bgColor: 'rgba(76, 175, 80, 0.1)' 
        }
      case 'offline':
      case 'disconnected':
      case 'error':
        return { 
          color: 'error.main', 
          icon: <Error />, 
          bgColor: 'rgba(244, 67, 54, 0.1)' 
        }
      case 'warning':
      case 'pending':
        return { 
          color: 'warning.main', 
          icon: <Warning />, 
          bgColor: 'rgba(255, 152, 0, 0.1)' 
        }
      default:
        return { 
          color: 'text.secondary', 
          icon: <Warning />, 
          bgColor: 'rgba(158, 158, 158, 0.1)' 
        }
    }
  }

  const config = getStatusConfig(status)

  return (
    <Card 
      sx={{ 
        height: '100%',
        background: config.bgColor,
        border: `1px solid ${config.color}`,
        borderRadius: 2,
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" component="h3" gutterBottom>
              {title}
            </Typography>
            <Typography color="text.secondary" variant="body2">
              {description}
            </Typography>
            <Typography 
              variant="body1" 
              sx={{ 
                mt: 1, 
                fontWeight: 600,
                color: config.color,
                textTransform: 'capitalize'
              }}
            >
              {loading ? 'Checking...' : status}
            </Typography>
          </Box>
          <Box sx={{ color: config.color }}>
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              config.icon
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

export default StatusCard