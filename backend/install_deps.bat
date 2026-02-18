@echo off
REM ScholarStream Backend - Windows Dependency Installer
REM بسم الله الرحمن الرحيم

echo ========================================
echo ScholarStream Backend Setup
echo ========================================
echo.

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Conda not found!
    echo Please install Miniconda from: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo Step 1: Creating conda environment 'scholarstream'...
conda create -n scholarstream python=3.11 -y
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create conda environment
    pause
    exit /b 1
)

echo.
echo Step 2: Activating environment...
call conda activate scholarstream

echo.
echo Step 3: Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 4: Checking environment setup...
if not exist .env (
    echo WARNING: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your actual credentials:
    echo   - Firebase credentials
    echo   - Gemini API key
    echo   - Upstash Redis URL and token
    echo.
)

echo.
echo ========================================
echo ✅ Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit the .env file with your credentials
echo   2. Run: conda activate scholarstream
echo   3. Run: python run.py
echo.
echo API will be available at: http://localhost:8000
echo API Docs will be at: http://localhost:8000/docs
echo.
pause
