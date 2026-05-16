@echo off
echo ============================================
echo  Interview Analyzer - Build
echo ============================================
echo.

:: Step 1: Build Python backend with PyInstaller
echo [1/3] Building Python backend...
cd /d "%~dp0..\backend"
pip install pyinstaller > nul 2>&1
pyinstaller --noconfirm interview_analyzer.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)
echo Backend build complete.

:: Step 2: Build React frontend
echo.
echo [2/3] Building React frontend...
cd /d "%~dp0..\electron"
call npm run build
if errorlevel 1 (
    echo ERROR: Frontend build failed.
    pause
    exit /b 1
)
echo Frontend build complete.

:: Step 3: Package with electron-builder
echo.
echo [3/3] Packaging installer...
call npx electron-builder --win
if errorlevel 1 (
    echo ERROR: Electron builder failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Build complete!
echo  Installer: dist\Interview Analyzer Setup *.exe
echo ============================================
pause
