@echo off
REM Build OpenSeismo Lite as .exe
REM This script converts the Python app into a standalone executable

echo Building OpenSeismo Lite...
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Creating executable...
echo.

REM Build the .exe
REM --onefile: Creates a single .exe file (not a folder)
REM --windowed: Hides the console window
REM --icon: Sets the app icon (optional)
REM --name: Sets the exe name
REM --distpath: Output directory for the executable

pyinstaller --onefile --windowed --name "OpenSeismo Lite" --add-data "index.html.html:." --add-data "tsunami_warning.py:." --add-data "tsunami_warning_display.js:." app.py

echo.
echo Build complete!
echo The executable is located in the 'dist' folder: OpenSeismo Lite.exe
echo.
pause
