@echo off
echo Starting Interview Analyzer (Dev Mode)...
echo.

set ELECTRON_DIR=%~dp0..\electron

:: Electron's main.js will start the backend automatically
cd /d "%ELECTRON_DIR%"
npx electron .

