@echo off
REM Build script for OpenSeismo Lite Desktop EXE
REM Creates a standalone Windows executable

echo.
echo ============================================================
echo  OpenSeismo Lite Desktop EXE Builder
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/4] Upgrading pip...
python -m pip install --upgrade pip -q

echo [2/4] Installing dependencies...
python -m pip install -r requirements.txt -q

echo [3/4] Installing PyInstaller...
python -m pip install pyinstaller -q

echo [4/4] Building OpenSeismo Lite.exe...
python -m PyInstaller --onefile desktop_app.spec

echo.
if exist "dist\OpenSeismo Lite.exe" (
    echo.
    echo ============================================================
    echo  SUCCESS! Desktop EXE created
    echo ============================================================
    echo.
    echo Location: dist\OpenSeismo Lite.exe
    echo.
    echo To run the application:
    echo   1. Navigate to the 'dist' folder
    echo   2. Double-click 'OpenSeismo Lite.exe'
    echo.
    echo Features:
    echo   - Real-time earthquake monitoring
    echo   - EEW alerts (M5.0+ with global coverage)
    echo   - Tsunami warnings (Japanese siren alerts)
    echo   - Sound notifications with Web Audio API
    echo   - Live updates from USGS, ESMC, CSEM, JMA
    echo   - 70+ seismic stations worldwide
    echo.
    pause
) else (
    echo.
    echo ERROR: Build failed! EXE not found in dist folder
    echo.
    pause
    exit /b 1
)
