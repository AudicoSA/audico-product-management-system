# 🎵 Audico Product Management System

A complete, automated product management solution for OpenCart stores that processes PDF pricelists and automatically updates your store inventory.

## 🚀 Features

### 🔧 Backend (Flask API)
- **PDF Processing**: Extract product data from supplier PDF pricelists using OCR
- **Data Validation**: Clean, validate, and normalize extracted product data
- **OpenCart Integration**: Complete API integration with your OpenCart store
- **Product Comparison**: Compare PDF products with existing store inventory
- **Automation Engine**: Automatically create/update products in your store
- **Workflow Management**: Orchestrate complete PDF-to-store workflows

### 🎨 Frontend (React Dashboard)
- **Modern UI**: Beautiful Material-UI dashboard with dark theme
- **PDF Upload**: Drag & drop interface for PDF processing
- **Real-time Monitoring**: Live workflow status and progress tracking
- **Store Integration**: View and manage OpenCart products
- **Analytics**: Charts and reports on processing performance
- **Responsive Design**: Works perfectly on desktop and mobile

## 🏗️ Project Structure

```
audico-product-management-system/
├── backend/                    # Flask API server
│   ├── api/                   # Main Flask application
│   ├── pdf_processor/         # PDF text extraction and parsing
│   ├── opencart_client/       # OpenCart API integration
│   ├── comparison_engine/     # Product comparison logic
│   ├── automation_engine/     # Automated product management
│   └── workflow_engine/       # Workflow orchestration
├── frontend/                  # React dashboard
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API integration
│   │   ├── context/           # State management
│   │   └── theme/             # UI theme configuration
│   └── public/                # Static assets
├── config/                    # Configuration files
├── scripts/                   # Utility scripts
└── docs/                      # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Node.js 16+
- npm or yarn
- OpenCart store with REST API enabled

### 1. Clone or Extract Project
```bash
# If from ZIP
unzip audico-product-management-system.zip
cd audico-product-management-system

# If from Git
git clone <your-repo-url>
cd audico-product-management-system
```

### 2. Backend Setup

```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your OpenCart API credentials
# OPENCART_BASE_URL=https://your-store.com
# OPENCART_BASIC_TOKEN=your-api-token
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit .env if needed (API URL should be http://localhost:5000)
```

### 4. Start the Application

#### Terminal 1 - Backend:
```bash
# From project root, with venv activated
cd backend/api
python app.py
```

#### Terminal 2 - Frontend:
```bash
# From project root
cd frontend
npm run dev
```

### 5. Access the Application
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/test

## 🔧 Configuration

### Backend Environment Variables (.env)
```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000

# OpenCart API
OPENCART_BASE_URL=https://your-store.com
OPENCART_BASIC_TOKEN=your-api-token

# Optional: Database, Google Cloud, AI services
DATABASE_URL=sqlite:///audico_products.db
GOOGLE_CLOUD_PROJECT=your-project
OPENAI_API_KEY=your-openai-key
```

### Frontend Environment Variables (frontend/.env)
```env
VITE_API_URL=http://localhost:5000
VITE_APP_TITLE=Audico Product Management System
```

## 📋 OpenCart Setup

### 1. Install REST API Extension
Install the LetsCMS REST API extension in your OpenCart admin panel.

### 2. Configure API Access
1. Go to System > Settings > API
2. Create a new API user
3. Generate API credentials
4. Note the API URL format: `https://your-store.com/index.php?route=ocrestapi/`

### 3. Test Connection
Use the dashboard to test your OpenCart connection:
- Go to OpenCart Integration page
- Click "Test Connection"
- Verify products are loading

## 🎯 Usage

### 1. Upload PDF Pricelist
1. Go to "PDF Upload" page
2. Drag & drop your supplier PDF
3. Watch real-time processing
4. Review extracted products

### 2. Start Complete Workflow
1. Use the workflow manager
2. Upload PDF with automation options
3. Monitor progress in real-time
4. Review created/updated products

### 3. Monitor Analytics
- View processing statistics
- Track success rates
- Monitor product creation
- Analyze workflow performance

## 🔍 API Endpoints

### Core Endpoints
- `GET /` - API information
- `GET /health` - System health check
- `GET /api/test` - List all endpoints

### PDF Processing
- `POST /api/pdf/upload` - Upload and process PDF
- `POST /api/pdf/validate` - Validate product data

### OpenCart Integration
- `GET /api/opencart/test` - Test store connection
- `GET /api/opencart/products` - Get store products
- `GET /api/opencart/search/{term}` - Search products

### Workflow Management
- `POST /api/workflow/start` - Start complete workflow
- `GET /api/workflow/{id}/status` - Get workflow status
- `GET /api/workflow/list` - List all workflows

## 🐳 Docker Deployment (Optional)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individual containers
docker build -t audico-backend ./backend
docker build -t audico-frontend ./frontend
```

## 🛠️ Development

### Backend Development
```bash
# Install development dependencies
pip install pytest black flake8

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

### Frontend Development
```bash
# Start development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 📊 Supported File Types

### PDF Processing
- **Supplier pricelists** in PDF format
- **Text-based PDFs** (preferred)
- **Image-based PDFs** (uses OCR)
- **Multi-page documents**

### Audio Equipment Categories
- Speakers & Subwoofers
- Amplifiers & Receivers
- Microphones
- Mixers & DJ Equipment
- Headphones & Earphones
- Studio Equipment
- Live Sound Equipment
- Cables & Accessories

## 🔧 Troubleshooting

### Common Issues

#### Backend Won't Start
1. Check Python version (3.8+)
2. Verify virtual environment is activated
3. Install missing dependencies: `pip install -r requirements.txt`
4. Check .env configuration

#### Frontend Won't Start
1. Check Node.js version (16+)
2. Clear node_modules: `rm -rf node_modules && npm install`
3. Check frontend/.env configuration

#### OpenCart Connection Failed
1. Verify OpenCart URL is correct
2. Check API credentials
3. Ensure REST API extension is installed
4. Test API endpoint manually

#### PDF Processing Errors
1. Ensure PDF is not corrupted
2. Check file size (max 10MB)
3. Verify OCR dependencies are installed
4. Try with a different PDF file

### Performance Optimization

#### Backend
- Use production WSGI server (waitress included)
- Configure database connection pooling
- Enable response caching
- Optimize PDF processing settings

#### Frontend
- Build for production: `npm run build`
- Enable gzip compression
- Configure CDN for static assets
- Optimize image assets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is proprietary software for Audico SA.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation in `/docs`

## 🚀 Production Deployment

### Environment Setup
1. Set `FLASK_ENV=production`
2. Use strong secret keys
3. Configure production database
4. Set up SSL certificates
5. Use reverse proxy (nginx)

### Security Considerations
- Keep API credentials secure
- Use HTTPS in production
- Regularly update dependencies
- Monitor for security vulnerabilities
- Implement rate limiting

---

**Built with ❤️ for Audico SA - Transforming audio equipment retail through automation**
