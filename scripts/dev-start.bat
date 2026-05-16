@echo off
echo ============================================
echo  Interview Analyzer - Development Mode
echo ============================================
echo.

:: Start backend
echo [1/2] Starting Python backend...
cd /d "%~dp0..\backend"
start "Backend" cmd /c "python main.py --port 19400 --data-dir %APPDATA%\InterviewAnalyzer"

:: Wait for backend
echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

:: Start frontend
echo [2/2] Starting Electron frontend...
cd /d "%~dp0..\electron"
call npm run electron:dev

echo.
echo Done.
pause
