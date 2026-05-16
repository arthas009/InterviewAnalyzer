@echo off
echo ============================================
echo  Interview Analyzer - Setup
echo ============================================
echo.

:: Check Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Check Node.js
node --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH.
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo [1/3] Installing Python backend dependencies...
cd /d "%~dp0..\backend"
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies.
    pause
    exit /b 1
)

echo.
echo [2/3] Installing Electron frontend dependencies...
cd /d "%~dp0..\electron"
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies.
    pause
    exit /b 1
)

echo.
echo [3/3] Creating data directory...
if not exist "%APPDATA%\InterviewAnalyzer" mkdir "%APPDATA%\InterviewAnalyzer"
if not exist "%APPDATA%\InterviewAnalyzer\models" mkdir "%APPDATA%\InterviewAnalyzer\models"
if not exist "%APPDATA%\InterviewAnalyzer\logs" mkdir "%APPDATA%\InterviewAnalyzer\logs"

echo.
echo ============================================
echo  Setup complete!
echo ============================================
echo.
echo Next steps:
echo   1. Configure your LLM API key in the app settings
echo   2. Run 'scripts\dev-start.bat' to start in development mode
echo.
pause
