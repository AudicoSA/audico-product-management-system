@echo off
echo 🎵 Setting up Audico Product Management System...

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+.
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 16+.
    exit /b 1
)

REM Backend setup
echo 📦 Setting up backend...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Copy environment template
if not exist .env (
    copy .env.example .env
    echo ✅ Created .env file. Please edit with your OpenCart credentials.
)

REM Frontend setup
echo 🎨 Setting up frontend...
cd frontend
npm install

REM Copy frontend environment template
if not exist .env (
    copy .env.example .env
    echo ✅ Created frontend .env file.
)

cd ..

echo ✅ Setup complete!
echo.
echo 🚀 To start the application:
echo 1. Backend: cd backend\api ^&^& python app.py
echo 2. Frontend: cd frontend ^&^& npm run dev
echo.
echo 📖 Visit http://localhost:3000 for the dashboard
echo 🔧 Visit http://localhost:5000 for the API

pause
