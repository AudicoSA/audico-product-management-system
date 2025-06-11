import React, { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import LiveProductView from './components/LiveProductView' // NEW IMPORT
import { Box, AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemIcon, ListItemText, IconButton } from '@mui/material'
import { Dashboard, UploadFile, Settings, Analytics, Store, Menu as MenuIcon, Visibility } from '@mui/icons-material' // Added Visibility icon
import { AppProvider } from './context/AppContext'
import DashboardPage from './components/Dashboard/DashboardPage'
import PDFUploadPage from './components/PDFUpload/PDFUploadPage'
import WorkflowManagerPage from './components/WorkflowManager/WorkflowManagerPage'
import OpenCartIntegrationPage from './components/OpenCartIntegration/OpenCartIntegrationPage'
import AnalyticsPage from './components/Analytics/AnalyticsPage'

const drawerWidth = 240

// UPDATED navigation with Live Product View
const navigation = [
  { name: 'Dashboard', icon: Dashboard, path: '/' },
  { name: 'PDF Upload', icon: UploadFile, path: '/upload' },
  { name: 'Live Product View', icon: Visibility, path: '/live-view' }, // NEW MENU ITEM
  { name: 'Workflows', icon: Settings, path: '/workflows' },
  { name: 'OpenCart', icon: Store, path: '/opencart' },
  { name: 'Analytics', icon: Analytics, path: '/analytics' },
]

function App() {
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          🎵 Audico
        </Typography>
      </Toolbar>
      <List>
        {navigation.map((item) => (
          <ListItem button key={item.name} component="a" href={item.path}>
            <ListItemIcon>
              <item.icon />
            </ListItemIcon>
            <ListItemText primary={item.name} />
          </ListItem>
        ))}
      </List>
    </Box>
  )

  return (
    <AppProvider>
      <Router>
        <Box sx={{ display: 'flex' }}>
          <AppBar
            position="fixed"
            sx={{
              width: { sm: `calc(100% - ${drawerWidth}px)` },
              ml: { sm: `${drawerWidth}px` },
            }}
          >
            <Toolbar>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ mr: 2, display: { sm: 'none' } }}
              >
                <MenuIcon />
              </IconButton>
              <Typography variant="h6" noWrap component="div">
                Product Management System
              </Typography>
            </Toolbar>
          </AppBar>
          <Box
            component="nav"
            sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
          >
            <Drawer
              variant="temporary"
              open={mobileOpen}
              onClose={handleDrawerToggle}
              ModalProps={{
                keepMounted: true,
              }}
              sx={{
                display: { xs: 'block', sm: 'none' },
                '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
              }}
            >
              {drawer}
            </Drawer>
            <Drawer
              variant="permanent"
              sx={{
                display: { xs: 'none', sm: 'block' },
                '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
              }}
              open
            >
              {drawer}
            </Drawer>
          </Box>
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              width: { sm: `calc(100% - ${drawerWidth}px)` },
            }}
          >
            <Toolbar />
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/upload" element={<PDFUploadPage />} />
              <Route path="/live-view" element={<LiveProductView />} /> {/* NEW ROUTE */}
              <Route path="/workflows" element={<WorkflowManagerPage />} />
              <Route path="/opencart" element={<OpenCartIntegrationPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </AppProvider>
  )
}

export default App
