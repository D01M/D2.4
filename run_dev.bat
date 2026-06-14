@echo off
title Seismic Disaster Tracker
set "PYTHON_CMD="
where python >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD where py >nul 2>nul && set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
  echo Python was not found. Install Python 3 and enable "Add python.exe to PATH", then run this file again.
  pause
  exit /b 1
)

%PYTHON_CMD% -m pip install -r requirements.txt
%PYTHON_CMD% app.py
pause
