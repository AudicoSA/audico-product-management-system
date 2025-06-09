import React, { useState } from 'react'
import { Box, Typography, Card, CardContent, Button, LinearProgress, Alert } from '@mui/material'
import { useDropzone } from 'react-dropzone'
import { CloudUpload, CheckCircle, Error } from '@mui/icons-material'
import { useMutation } from '@tanstack/react-query'
import { apiService } from '../../services/apiService'

function PDFUploadPage() {
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadResult, setUploadResult] = useState(null)

  const uploadMutation = useMutation({
    mutationFn: (file) => apiService.uploadPDF(file, setUploadProgress),
    onSuccess: (data) => {
      setUploadResult(data)
      setUploadProgress(0)
    },
    onError: (error) => {
      setUploadResult({ status: 'error', message: error.message })
      setUploadProgress(0)
    },
  })

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    onDrop: (files) => {
      if (files.length > 0) {
        setUploadResult(null)
        uploadMutation.mutate(files[0])
      }
    },
  })

  const isUploading = uploadMutation.isPending

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
        📄 PDF Upload & Processing
      </Typography>

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
              or click to select a file
            </Typography>
            <Button variant="outlined" component="span" disabled={isUploading}>
              Select PDF File
            </Button>
          </Box>

          {/* Upload Progress */}
          {isUploading && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Uploading and processing... {uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
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
                    Upload Successful!
                  </Typography>
                </Box>
                <Alert severity="success" sx={{ mb: 2 }}>
                  {uploadResult.message}
                </Alert>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Products Found:</strong> {uploadResult.products_found}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Extraction Method:</strong> {uploadResult.extraction_method}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Page Count:</strong> {uploadResult.page_count}
                </Typography>

                {uploadResult.products && uploadResult.products.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Extracted Products:
                    </Typography>
                    <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
                      {uploadResult.products.slice(0, 10).map((product, index) => (
                        <Box key={index} sx={{ 
                          p: 2, 
                          mb: 1, 
                          bgcolor: 'background.default', 
                          borderRadius: 1 
                        }}>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {product.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Price: R{product.price} • Category: {product.category} • Brand: {product.brand}
                          </Typography>
                        </Box>
                      ))}
                      {uploadResult.products.length > 10 && (
                        <Typography variant="caption" color="text.secondary">
                          ... and {uploadResult.products.length - 10} more products
                        </Typography>
                      )}
                    </Box>
                  </Box>
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
                <Alert severity="error">
                  {uploadResult.message}
                </Alert>
              </Box>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  )
}

export default PDFUploadPage