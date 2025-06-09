import React, { useState } from 'react'
import { 
  Box, Typography, Card, CardContent, Button, LinearProgress, Alert, 
  FormControlLabel, Switch, Divider, Chip, Grid, Paper, Table, 
  TableBody, TableCell, TableContainer, TableHead, TableRow, Tabs, Tab
} from '@mui/material'
import { useDropzone } from 'react-dropzone'
import { 
  CloudUpload, CheckCircle, Error, Timer, PlayArrow, 
  Compare, AutoAwesome, Visibility, TrendingUp, TrendingDown, Add
} from '@mui/icons-material'
import { useMutation } from '@tanstack/react-query'
import { apiService } from '../../services/apiService'
import { useNavigate } from 'react-router-dom'

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`comparison-tabpanel-${index}`}
      aria-labelledby={`comparison-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

function PDFUploadPage() {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadResult, setUploadResult] = useState(null)
  const [comparisonResult, setComparisonResult] = useState(null)
  const [useAsyncMode, setUseAsyncMode] = useState(false)
  const [useSimpleMode, setUseSimpleMode] = useState(false)
  const [tabValue, setTabValue] = useState(0)
  const [workflowOptions, setWorkflowOptions] = useState({
    auto_create_missing: true,
    auto_update_prices: false,
    validation_threshold: 0.7,
    price_tolerance_percent: 5.0,
    batch_size: 10,
    dry_run: false
  })

  const navigate = useNavigate()

  // Regular upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file) => {
      if (useSimpleMode) {
        return apiService.uploadPDFSimple(file)
      } else if (useAsyncMode) {
        return apiService.uploadPDFAsync(file)
      } else {
        return apiService.uploadPDF(file, setUploadProgress)
      }
    },
    onSuccess: (data) => {
      setUploadResult(data)
      setUploadProgress(0)
      setComparisonResult(null) // Clear previous comparison
    },
    onError: (error) => {
      console.error('Upload error:', error)
      let errorMessage = error.message || 'Upload failed'
      
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Upload timed out. Try using Simple Mode for testing.'
      } else if (error.response?.status === 404) {
        errorMessage = 'Backend server not found. Make sure the Flask server is running on http://localhost:5000'
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error during processing. Check the backend logs.'
      } else if (!error.response) {
        errorMessage = 'Cannot connect to server. Make sure the backend is running.'
      }
      
      setUploadResult({ status: 'error', message: errorMessage })
      setUploadProgress(0)
    },
  })

  // Comparison mutation
  const comparisonMutation = useMutation({
    mutationFn: (products) => apiService.compareProducts(products),
    onSuccess: (data) => {
      console.log('Comparison result:', data)
      setComparisonResult(data.comparison)
      setTabValue(1) // Switch to results tab
    },
    onError: (error) => {
      setUploadResult({
        ...uploadResult,
        comparisonError: error.message
      })
    }
  })

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: () => apiService.testConnection(),
    onSuccess: (data) => {
      setUploadResult({
        status: 'success',
        message: 'Backend connection successful!',
        data: data
      })
    },
    onError: (error) => {
      setUploadResult({
        status: 'error',
        message: `Backend connection failed: ${error.message}`
      })
    },
  })

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB limit
    onDrop: (files, rejectedFiles) => {
      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0]
        if (rejection.errors.some(e => e.code === 'file-too-large')) {
          setUploadResult({
            status: 'error',
            message: 'File too large. Maximum size is 10MB.'
          })
          return
        }
      }
      
      if (files.length > 0) {
        setUploadResult(null)
        setComparisonResult(null)
        uploadMutation.mutate(files[0])
      }
    },
  })

  const isUploading = uploadMutation.isPending
  const isTesting = testConnectionMutation.isPending
  const isComparing = comparisonMutation.isPending

  const hasExtractedProducts = uploadResult?.status === 'success' && 
                               uploadResult?.products && 
                               uploadResult.products.length > 0

  const handleStartComparison = () => {
    if (hasExtractedProducts) {
      comparisonMutation.mutate(uploadResult.products)
    }
  }

  const renderComparisonResults = () => {
    if (!comparisonResult) return null

    const { summary, missing_products, exact_matches, price_differences } = comparisonResult

    return (
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📊 Comparison Results
          </Typography>
          
          {/* Summary Cards */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.main', color: 'white' }}>
                <Typography variant="h4">{summary?.exact_matches || 0}</Typography>
                <Typography variant="body2">Exact Matches</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.main', color: 'white' }}>
                <Typography variant="h4">{summary?.price_differences || 0}</Typography>
                <Typography variant="body2">Price Differences</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'error.main', color: 'white' }}>
                <Typography variant="h4">{summary?.missing_products || 0}</Typography>
                <Typography variant="body2">Missing Products</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.main', color: 'white' }}>
                <Typography variant="h4">{summary?.total_pdf_products || 0}</Typography>
                <Typography variant="body2">Total Products</Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Detailed Results Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
              <Tab label={`Missing (${missing_products?.length || 0})`} icon={<Add />} />
              <Tab label={`Price Diffs (${price_differences?.length || 0})`} icon={<TrendingDown />} />
              <Tab label={`Exact Matches (${exact_matches?.length || 0})`} icon={<CheckCircle />} />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Typography variant="h6" gutterBottom color="error">
              Missing Products (Need to be Added)
            </Typography>
            {missing_products && missing_products.length > 0 ? (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Product Name</TableCell>
                      <TableCell>Model</TableCell>
                      <TableCell>Price</TableCell>
                      <TableCell>Category</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {missing_products.map((product, index) => (
                      <TableRow key={index}>
                        <TableCell>{product.name}</TableCell>
                        <TableCell>{product.model}</TableCell>
                        <TableCell>R{product.price}</TableCell>
                        <TableCell>{product.category}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="success">
                🎉 Great! All products from the PDF are already in your store.
              </Alert>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Typography variant="h6" gutterBottom color="warning.main">
              Price Differences (May Need Updates)
            </Typography>
            {price_differences && price_differences.length > 0 ? (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Product Name</TableCell>
                      <TableCell>PDF Price</TableCell>
                      <TableCell>Store Price</TableCell>
                      <TableCell>Difference</TableCell>
                      <TableCell>Confidence</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {price_differences.map((result, index) => (
                      <TableRow key={index}>
                        <TableCell>{result.pdf_product.name}</TableCell>
                        <TableCell>R{result.pdf_product.price}</TableCell>
                        <TableCell>
                          {result.opencart_matches?.[0]?.price || 'N/A'}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            icon={<TrendingDown />}
                            label={`${((result.pdf_product.price - parseFloat(result.opencart_matches?.[0]?.price?.replace(/[R,]/g, '') || 0)) > 0 ? '+' : '')}${(result.pdf_product.price - parseFloat(result.opencart_matches?.[0]?.price?.replace(/[R,]/g, '') || 0)).toFixed(2)}`}
                            color="warning"
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={`${(result.match_confidence * 100).toFixed(0)}%`}
                            color={result.match_confidence > 0.8 ? 'success' : 'warning'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="success">
                🎉 All matched products have correct prices.
              </Alert>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" gutterBottom color="success.main">
              Exact Matches (Already in Store)
            </Typography>
            {exact_matches && exact_matches.length > 0 ? (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Product Name</TableCell>
                      <TableCell>Model</TableCell>
                      <TableCell>Price</TableCell>
                      <TableCell>Confidence</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {exact_matches.map((result, index) => (
                      <TableRow key={index}>
                        <TableCell>{result.pdf_product.name}</TableCell>
                        <TableCell>{result.pdf_product.model}</TableCell>
                        <TableCell>R{result.pdf_product.price}</TableCell>
                        <TableCell>
                          <Chip 
                            label={`${(result.match_confidence * 100).toFixed(0)}%`}
                            color="success"
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="info">
                No exact matches found.
              </Alert>
            )}
          </TabPanel>

          {/* Action Buttons */}
          {missing_products && missing_products.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Divider sx={{ mb: 2 }}>
                <Chip label="Next Actions" />
              </Divider>
              <Grid container spacing={2}>
                <Grid item>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<Add />}
                    onClick={() => {
                      // Here you could trigger product creation
                      alert(`Ready to create ${missing_products.length} missing products!`)
                    }}
                  >
                    Create {missing_products.length} Missing Products
                  </Button>
                </Grid>
                <Grid item>
                  <Button
                    variant="outlined"
                    startIcon={<PlayArrow />}
                    onClick={() => navigate('/workflows')}
                  >
                    Start Full Workflow
                  </Button>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
        📄 PDF Upload & Processing
      </Typography>

      {/* Test Connection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Backend Connection Test
          </Typography>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            Test the connection to the Flask backend before uploading files.
          </Typography>
          <Button
            variant="outlined"
            onClick={() => testConnectionMutation.mutate()}
            disabled={isTesting}
            startIcon={isTesting ? <Timer /> : undefined}
          >
            {isTesting ? 'Testing...' : 'Test Backend Connection'}
          </Button>
        </CardContent>
      </Card>

      {/* Upload Options */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Upload Options
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={useSimpleMode}
                onChange={(e) => {
                  setUseSimpleMode(e.target.checked)
                  if (e.target.checked) setUseAsyncMode(false)
                }}
              />
            }
            label="Simple Mode (for testing - no actual processing)"
          />
          <br />
          <FormControlLabel
            control={
              <Switch
                checked={useAsyncMode}
                onChange={(e) => {
                  setUseAsyncMode(e.target.checked)
                  if (e.target.checked) setUseSimpleMode(false)
                }}
              />
            }
            label="Async Mode (background processing)"
          />
        </CardContent>
      </Card>

      {/* Upload Area */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.500',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'action.hover' : 'transparent',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'action.hover',
              },
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Drop the PDF here' : 'Drag & drop a PDF file here'}
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              or click to select a file (max 10MB)
            </Typography>
            <Button variant="outlined" component="span" disabled={isUploading}>
              Select PDF File
            </Button>
            {useSimpleMode && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Simple mode is enabled - file will be uploaded but not processed
              </Alert>
            )}
            {useAsyncMode && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Async mode is enabled - processing will happen in the background
              </Alert>
            )}
          </Box>

          {/* Upload Progress */}
          {isUploading && !useAsyncMode && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Uploading and processing... {uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}

          {/* Async Processing Info */}
          {isUploading && useAsyncMode && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Starting background processing...
              </Typography>
              <LinearProgress />
            </Box>
          )}

          {/* Accepted Files */}
          {acceptedFiles.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2">Selected file:</Typography>
              <Typography color="text.secondary">
                {acceptedFiles[0].name} ({(acceptedFiles[0].size / 1024 / 1024).toFixed(2)} MB)
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Upload Result */}
      {uploadResult && (
        <Card>
          <CardContent>
            {uploadResult.status === 'success' ? (
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CheckCircle color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6" color="success.main">
                    {uploadResult.job_id ? 'Background Processing Started!' : 'Upload Successful!'}
                  </Typography>
                </Box>
                <Alert severity="success" sx={{ mb: 2 }}>
                  {uploadResult.message}
                </Alert>

                {/* Product Summary */}
                {hasExtractedProducts && (
                  <Grid container spacing={2} sx={{ mb: 3 }}>
                    <Grid item xs={12} sm={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {uploadResult.products_found}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Products Found
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h6" color="info.main">
                          {uploadResult.extraction_method}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Extraction Method
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4">
                          {uploadResult.page_count}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Pages Processed
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                )}

                {/* Action Buttons for Extracted Products */}
                {hasExtractedProducts && !comparisonResult && (
                  <Box sx={{ mb: 3 }}>
                    <Divider sx={{ mb: 2 }}>
                      <Chip label="Next Steps" />
                    </Divider>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Button
                          fullWidth
                          variant="contained"
                          startIcon={<Compare />}
                          onClick={handleStartComparison}
                          disabled={isComparing}
                        >
                          {isComparing ? 'Comparing...' : 'Compare with Store'}
                        </Button>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Button
                          fullWidth
                          variant="outlined"
                          startIcon={<Visibility />}
                          onClick={() => navigate('/workflows')}
                        >
                          View Workflows
                        </Button>
                      </Grid>
                    </Grid>

                    {isComparing && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Comparing {uploadResult.products_found} products with your store...
                        </Typography>
                        <LinearProgress />
                      </Box>
                    )}
                  </Box>
                )}

                {/* Show comparison results */}
                {renderComparisonResults()}

                {/* Error Messages */}
                {uploadResult.comparisonError && (
                  <Alert severity="error" sx={{ mt: 2 }}>
                    Comparison Error: {uploadResult.comparisonError}
                  </Alert>
                )}
              </Box>
            ) : (
              <Box>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Error color="error" sx={{ mr: 1 }} />
                  <Typography variant="h6" color="error.main">
                    Upload Failed
                  </Typography>
                </Box>
                <Alert severity="error" sx={{ mb: 2 }}>
                  {uploadResult.message}
                </Alert>
                <Typography variant="body2" color="text.secondary">
                  <strong>Troubleshooting steps:</strong>
                </Typography>
                <Box component="ul" sx={{ mt: 1, pl: 2 }}>
                  <li>Make sure the Flask backend is running: <code>cd backend/api && python app.py</code></li>
                  <li>Check that the backend is accessible at <code>http://localhost:5000</code></li>
                  <li>Try the "Test Backend Connection" button above</li>
                  <li>For large files, try using Simple Mode or Async Mode</li>
                  <li>Check the browser console and backend logs for detailed errors</li>
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default PDFUploadPage
