import React from 'react'
import { Grid, Box, Typography } from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../../services/apiService'
import StatusCard from '../common/StatusCard'
import QuickStats from '../common/QuickStats'

function DashboardPage() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: apiService.getHealth,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: workflows, isLoading: workflowsLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => apiService.listWorkflows(10),
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
        🎵 Audico Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* System Status Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="API Status"
            status={health?.status === 'healthy' ? 'online' : 'offline'}
            description="Backend API Connection"
            loading={healthLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="OpenCart"
            status={health?.opencart_config?.api_configured ? 'connected' : 'disconnected'}
            description="Store Integration"
            loading={healthLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="PDF Processing"
            status={health?.modules_available?.pdf_processing === '✅ ready' ? 'ready' : 'error'}
            description="Document Processing"
            loading={healthLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatusCard
            title="Workflows"
            status={health?.modules_available?.workflow_manager === '✅ ready' ? 'ready' : 'error'}
            description="Automation Engine"
            loading={healthLoading}
          />
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12}>
          <QuickStats 
            workflows={workflows?.workflows || []}
            loading={workflowsLoading}
          />
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Typography variant="h6" component="h2" gutterBottom sx={{ mt: 2 }}>
            Recent Workflows
          </Typography>
          {workflows?.workflows && workflows.workflows.length > 0 ? (
            <Box>
              {workflows.workflows.slice(0, 5).map((workflow, index) => (
                <Box key={workflow.workflow_id || index} sx={{ 
                  p: 2, 
                  mb: 2, 
                  bgcolor: 'background.paper', 
                  borderRadius: 2,
                  border: '1px solid rgba(255, 255, 255, 0.1)'
                }}>
                  <Typography variant="subtitle1">
                    {workflow.pdf_filename || 'Unknown File'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Status: {workflow.status} • Products: {workflow.summary?.products_extracted || 0}
                  </Typography>
                </Box>
              ))}
            </Box>
          ) : (
            <Typography color="text.secondary">
              No workflows found. Upload a PDF to get started!
            </Typography>
          )}
        </Grid>
      </Grid>
    </Box>
  )
}

export default DashboardPage