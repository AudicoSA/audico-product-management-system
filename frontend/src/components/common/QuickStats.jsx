import React from 'react'
import { Card, CardContent, Typography, Grid, Box } from '@mui/material'
import { TrendingUp, Schedule, CheckCircle, Error } from '@mui/icons-material'

function QuickStats({ workflows = [], loading = false }) {
  const calculateStats = () => {
    if (!workflows.length) {
      return {
        total: 0,
        completed: 0,
        failed: 0,
        processing: 0,
        successRate: 0,
        totalProducts: 0,
      }
    }

    const total = workflows.length
    const completed = workflows.filter(w => w.status === 'completed').length
    const failed = workflows.filter(w => w.status === 'failed').length
    const processing = workflows.filter(w => w.status === 'processing').length
    const successRate = total > 0 ? (completed / total * 100).toFixed(1) : 0
    const totalProducts = workflows.reduce((sum, w) => 
      sum + (w.summary?.products_extracted || 0), 0)

    return {
      total,
      completed,
      failed,
      processing,
      successRate,
      totalProducts,
    }
  }

  const stats = calculateStats()

  const statCards = [
    {
      title: 'Total Workflows',
      value: stats.total,
      icon: <Schedule />,
      color: 'primary.main',
    },
    {
      title: 'Success Rate',
      value: `${stats.successRate}%`,
      icon: <TrendingUp />,
      color: 'success.main',
    },
    {
      title: 'Completed',
      value: stats.completed,
      icon: <CheckCircle />,
      color: 'success.main',
    },
    {
      title: 'Products Processed',
      value: stats.totalProducts,
      icon: <TrendingUp />,
      color: 'info.main',
    },
  ]

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Quick Statistics
        </Typography>

        <Grid container spacing={2}>
          {statCards.map((stat, index) => (
            <Grid item xs={6} sm={3} key={index}>
              <Box sx={{ 
                textAlign: 'center', 
                p: 2, 
                bgcolor: 'background.default', 
                borderRadius: 2,
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                <Box sx={{ color: stat.color, mb: 1 }}>
                  {stat.icon}
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 600, color: stat.color }}>
                  {loading ? '...' : stat.value}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {stat.title}
                </Typography>
              </Box>
            </Grid>
          ))}
        </Grid>

        {workflows.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Last updated: {new Date().toLocaleTimeString()}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

export default QuickStats