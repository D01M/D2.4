# Build OpenSeismo Lite as .exe
# PowerShell script to automate the build process

param(
    [switch]$OnDir = $false,
    [switch]$NoConsole = $false,
    [string]$IconPath = "",
    [switch]$CleanBuild = $false
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  OpenSeismo Lite Builder" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.7+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found: $pythonCheck" -ForegroundColor Green
Write-Host ""

# Install PyInstaller if needed
Write-Host "Checking PyInstaller..." -ForegroundColor Yellow
pip show pyinstaller >$null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✓ PyInstaller is ready" -ForegroundColor Green
Write-Host ""

# Clean previous builds if requested
if ($CleanBuild) {
    Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }
    Write-Host "✓ Cleaned" -ForegroundColor Green
    Write-Host ""
}

# Build arguments
$buildArgs = @(
    if ($OnDir) { "--onedir" } else { "--onefile" },
    "--windowed",
    "--name", "OpenSeismo Lite",
    "--add-data", "index.html.html:.",
    "--add-data", "tsunami_warning.py:.",
    "--add-data", "tsunami_warning_display.js:.",
    if ($IconPath -and (Test-Path $IconPath)) { "--icon"; $IconPath },
    "app.py"
)

# Build
Write-Host "Building executable..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Command: pyinstaller $($buildArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

pyinstaller @buildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  ✓ Build Complete!" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

if ($OnDir) {
    Write-Host "Executable location:" -ForegroundColor Green
    Write-Host "  dist\OpenSeismo Lite\OpenSeismo Lite.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This is an onedir build (folder with dependencies)" -ForegroundColor DarkGray
} else {
    Write-Host "Executable location:" -ForegroundColor Green
    Write-Host "  dist\OpenSeismo Lite.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "This is a single-file executable (may take longer to start)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test the executable by running:" -ForegroundColor White
Write-Host "     .\dist\OpenSeismo Lite.exe" -ForegroundColor Cyan
Write-Host "  2. Optionally create an installer using NSIS:" -ForegroundColor White
Write-Host "     makensis installer.nsi" -ForegroundColor Cyan
Write-Host "  3. Share the .exe or installer with others" -ForegroundColor White
Write-Host ""
Write-Host "Options for rebuilding:" -ForegroundColor Yellow
Write-Host "  -OnDir          Create folder-based build (faster startup)" -ForegroundColor DarkGray
Write-Host "  -CleanBuild     Delete previous build artifacts" -ForegroundColor DarkGray
Write-Host "  -IconPath       Path to .ico file for custom icon" -ForegroundColor DarkGray
Write-Host ""
