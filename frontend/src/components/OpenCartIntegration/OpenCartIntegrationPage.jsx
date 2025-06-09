import React from 'react'
import { Box, Typography, Card, CardContent, Button, Grid, Chip, Alert } from '@mui/material'
import { Store, Refresh, Link } from '@mui/icons-material'
import { useQuery } from '@tanstack/react-query'
import { apiService } from '../../services/apiService'

function OpenCartIntegrationPage() {
  const { data: opencartStatus, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['opencart-status'],
    queryFn: apiService.testOpenCart,
    refetchInterval: 30000,
  })

  const { data: products, isLoading: productsLoading, refetch: refetchProducts } = useQuery({
    queryKey: ['opencart-products'],
    queryFn: () => apiService.getOpenCartProducts(20),
    enabled: opencartStatus?.status === 'success',
  })

  const isConnected = opencartStatus?.status === 'success'

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
        🛒 OpenCart Integration
      </Typography>

      {/* Connection Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Store sx={{ mr: 2, fontSize: 32 }} />
              <Box>
                <Typography variant="h6">
                  Store Connection
                </Typography>
                <Typography color="text.secondary">
                  https://www.audicoonline.co.za
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Chip 
                label={isConnected ? 'Connected' : 'Disconnected'}
                color={isConnected ? 'success' : 'error'}
                icon={<Link />}
              />
              <Button 
                variant="outlined" 
                startIcon={<Refresh />}
                onClick={() => {
                  refetchStatus()
                  if (isConnected) refetchProducts()
                }}
                disabled={statusLoading}
              >
                Test Connection
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Connection Details */}
      {opencartStatus && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            {isConnected ? (
              <Alert severity="success">
                {opencartStatus.message}
              </Alert>
            ) : (
              <Alert severity="error">
                {opencartStatus.message}
                {opencartStatus.troubleshooting && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      Troubleshooting:
                    </Typography>
                    {opencartStatus.troubleshooting.map((tip, index) => (
                      <Typography key={index} variant="body2">
                        • {tip}
                      </Typography>
                    ))}
                  </Box>
                )}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Products List */}
      {isConnected && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6">
                Store Products
              </Typography>
              <Button 
                variant="outlined" 
                startIcon={<Refresh />}
                onClick={refetchProducts}
                disabled={productsLoading}
              >
                Refresh
              </Button>
            </Box>

            {products?.products && products.products.length > 0 ? (
              <Grid container spacing={2}>
                {products.products.map((product, index) => (
                  <Grid item xs={12} sm={6} md={4} key={product.product_id || index}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }} gutterBottom>
                          {product.name || 'Unnamed Product'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Model: {product.model || 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Price: R{product.price || '0'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Status: {product.status === '1' ? 'Active' : 'Inactive'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                {productsLoading ? 'Loading products...' : 'No products found in store'}
              </Typography>
            )}

            {products && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Showing {products.products?.length || 0} products • Total: {products.total_count || 0}
              </Typography>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default OpenCartIntegrationPage