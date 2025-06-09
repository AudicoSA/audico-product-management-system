#!/bin/bash

# Audico Product Management System Setup Script

echo "🎵 Setting up Audico Product Management System..."

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+."
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+."
    exit 1
fi

# Backend setup
echo "📦 Setting up backend..."
python -m venv venv

# Activate virtual environment (platform-specific)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file. Please edit with your OpenCart credentials."
fi

# Frontend setup
echo "🎨 Setting up frontend..."
cd frontend
npm install

# Copy frontend environment template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created frontend .env file."
fi

cd ..

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "1. Backend: cd backend/api && python app.py"
echo "2. Frontend: cd frontend && npm run dev"
echo ""
echo "📖 Visit http://localhost:3000 for the dashboard"
echo "🔧 Visit http://localhost:5000 for the API"
