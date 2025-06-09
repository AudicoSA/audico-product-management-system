import React, { useState } from 'react'
import { Box, Typography, Card, CardContent, Button, Grid, Chip, Dialog, DialogTitle, DialogContent } from '@mui/material'
import { PlayArrow, Visibility, Cancel } from '@mui/icons-material'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiService } from '../../services/apiService'

function WorkflowManagerPage() {
  const [selectedWorkflow, setSelectedWorkflow] = useState(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  const { data: workflows, isLoading, refetch } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => apiService.listWorkflows(50),
    refetchInterval: 5000,
  })

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success'
      case 'processing': return 'info'
      case 'failed': return 'error'
      case 'cancelled': return 'default'
      default: return 'warning'
    }
  }

  const handleViewDetails = async (workflow) => {
    try {
      const details = await apiService.getWorkflowStatus(workflow.workflow_id)
      setSelectedWorkflow(details.workflow)
      setDialogOpen(true)
    } catch (error) {
      console.error('Failed to load workflow details:', error)
    }
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
        ⚙️ Workflow Manager
      </Typography>

      {/* Workflows List */}
      <Grid container spacing={3}>
        {workflows?.workflows?.map((workflow) => (
          <Grid item xs={12} md={6} lg={4} key={workflow.workflow_id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" component="h3" sx={{ 
                    fontWeight: 600,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    maxWidth: '200px'
                  }}>
                    {workflow.pdf_filename || 'Unknown File'}
                  </Typography>
                  <Chip 
                    label={workflow.status} 
                    color={getStatusColor(workflow.status)}
                    size="small"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Step: {workflow.current_step}
                </Typography>

                {workflow.summary && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      Products Extracted: {workflow.summary.products_extracted}
                    </Typography>
                    <Typography variant="body2">
                      Products Missing: {workflow.summary.products_missing}
                    </Typography>
                    <Typography variant="body2">
                      Products Created: {workflow.summary.products_created}
                    </Typography>
                  </Box>
                )}

                {workflow.duration && (
                  <Typography variant="caption" color="text.secondary">
                    Duration: {workflow.duration.toFixed(2)}s
                  </Typography>
                )}

                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <Button
                    size="small"
                    startIcon={<Visibility />}
                    onClick={() => handleViewDetails(workflow)}
                  >
                    View Details
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}

        {(!workflows?.workflows || workflows.workflows.length === 0) && !isLoading && (
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 6 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No workflows found
                </Typography>
                <Typography color="text.secondary">
                  Upload a PDF file to start your first workflow
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Workflow Details Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Workflow Details
        </DialogTitle>
        <DialogContent>
          {selectedWorkflow && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedWorkflow.pdf_filename}
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>Status:</strong> {selectedWorkflow.status}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>Current Step:</strong> {selectedWorkflow.current_step}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>Products Extracted:</strong> {selectedWorkflow.products_extracted}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>Products Missing:</strong> {selectedWorkflow.products_missing}
                  </Typography>
                </Grid>
              </Grid>

              {selectedWorkflow.errors && selectedWorkflow.errors.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="error">Errors:</Typography>
                  {selectedWorkflow.errors.map((error, index) => (
                    <Typography key={index} variant="body2" color="error">
                      • {error}
                    </Typography>
                  ))}
                </Box>
              )}

              {selectedWorkflow.warnings && selectedWorkflow.warnings.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="warning.main">Warnings:</Typography>
                  {selectedWorkflow.warnings.map((warning, index) => (
                    <Typography key={index} variant="body2" color="warning.main">
                      • {warning}
                    </Typography>
                  ))}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default WorkflowManagerPage