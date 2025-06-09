import React from 'react'
import { Box, Typography, Card, CardContent, Grid } from '@mui/material'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../../services/apiService'

const COLORS = ['#3f51b5', '#f50057', '#4caf50', '#ff9800', '#9c27b0']

function AnalyticsPage() {
  const { data: workflows } = useQuery({
    queryKey: ['workflows-analytics'],
    queryFn: () => apiService.listWorkflows(100),
    refetchInterval: 30000,
  })

  // Process data for charts
  const processWorkflowData = () => {
    if (!workflows?.workflows) return { statusData: [], dailyData: [] }

    const statusCounts = workflows.workflows.reduce((acc, workflow) => {
      acc[workflow.status] = (acc[workflow.status] || 0) + 1
      return acc
    }, {})

    const statusData = Object.entries(statusCounts).map(([status, count]) => ({
      name: status,
      value: count,
    }))

    // Group by date (mock data for now)
    const dailyData = [
      { date: '2024-01-01', completed: 12, failed: 2, processing: 1 },
      { date: '2024-01-02', completed: 15, failed: 1, processing: 2 },
      { date: '2024-01-03', completed: 8, failed: 3, processing: 0 },
      { date: '2024-01-04', completed: 20, failed: 1, processing: 1 },
      { date: '2024-01-05', completed: 18, failed: 0, processing: 3 },
    ]

    return { statusData, dailyData }
  }

  const { statusData, dailyData } = processWorkflowData()

  // Calculate stats
  const totalWorkflows = workflows?.workflows?.length || 0
  const completedWorkflows = workflows?.workflows?.filter(w => w.status === 'completed').length || 0
  const successRate = totalWorkflows > 0 ? (completedWorkflows / totalWorkflows * 100).toFixed(1) : 0

  const totalProducts = workflows?.workflows?.reduce((sum, w) => 
    sum + (w.summary?.products_extracted || 0), 0) || 0
  const totalCreated = workflows?.workflows?.reduce((sum, w) => 
    sum + (w.summary?.products_created || 0), 0) || 0

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
        📊 Analytics & Reports
      </Typography>

      {/* Summary Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary" sx={{ fontWeight: 600 }}>
                {totalWorkflows}
              </Typography>
              <Typography color="text.secondary">
                Total Workflows
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="success.main" sx={{ fontWeight: 600 }}>
                {successRate}%
              </Typography>
              <Typography color="text.secondary">
                Success Rate
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="info.main" sx={{ fontWeight: 600 }}>
                {totalProducts}
              </Typography>
              <Typography color="text.secondary">
                Products Processed
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="secondary.main" sx={{ fontWeight: 600 }}>
                {totalCreated}
              </Typography>
              <Typography color="text.secondary">
                Products Created
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Workflow Status Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Workflow Status Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Daily Workflow Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Daily Workflow Activity
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="completed" stackId="a" fill="#4caf50" />
                  <Bar dataKey="failed" stackId="a" fill="#f44336" />
                  <Bar dataKey="processing" stackId="a" fill="#2196f3" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Workflow Activity
              </Typography>
              {workflows?.workflows && workflows.workflows.length > 0 ? (
                <Box>
                  {workflows.workflows.slice(0, 10).map((workflow, index) => (
                    <Box key={workflow.workflow_id || index} sx={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      py: 1,
                      borderBottom: index < 9 ? '1px solid rgba(255, 255, 255, 0.1)' : 'none'
                    }}>
                      <Box>
                        <Typography variant="body2">
                          {workflow.pdf_filename || 'Unknown File'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {workflow.summary?.products_extracted || 0} products extracted
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography variant="caption" color={
                          workflow.status === 'completed' ? 'success.main' :
                          workflow.status === 'failed' ? 'error.main' : 'warning.main'
                        }>
                          {workflow.status}
                        </Typography>
                        {workflow.duration && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                            {workflow.duration.toFixed(1)}s
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">
                  No workflow data available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default AnalyticsPage