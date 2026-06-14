@echo off
title Build Seismic Disaster Tracker EXE
set "PYTHON_CMD="
where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD where py >nul 2>nul && set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
  echo Python was not found. Install Python 3 and enable "Add python.exe to PATH", then run this file again.
  pause
  exit /b 1
)

echo Installing requirements...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt
%PYTHON_CMD% -m pip install pyinstaller

echo.
echo Building EXE...
%PYTHON_CMD% -m PyInstaller --onefile --name SeismicDisasterTracker --add-data "templates;templates" --add-data "static;static" app.py

echo.
echo Done.
echo Your EXE should be here:
echo dist\SeismicDisasterTracker.exe
pause
