# Building OpenSeismo Lite as .exe

This guide explains how to convert OpenSeismo Lite into a standalone Windows executable (.exe).

## Quick Start

### Option 1: Automated Build (Recommended)
1. Open PowerShell or Command Prompt in the OpenSeismo Lite folder
2. Run: `build.bat`
3. The executable will be created in the `dist` folder

### Option 2: Manual Build with PyInstaller

#### Step 1: Install Dependencies
```powershell
pip install flask requests pyinstaller
```

#### Step 2: Build the Executable
```powershell
pyinstaller --onefile --windowed --name "OpenSeismo Lite" --add-data "index.html.html:." --add-data "tsunami_warning.py:." --add-data "tsunami_warning_display.js:." app.py
```

#### Step 3: Find Your .exe
The executable will be in: `dist/OpenSeismo Lite.exe`

---

## Build Options Explained

- `--onefile`: Creates a single .exe file instead of a folder (slower startup but more convenient)
- `--windowed`: Hides the console window (cleaner appearance)
- `--add-data`: Includes necessary data files in the executable
- `--name`: Sets the executable name

---

## What Happens When You Run the .exe

1. **Starts Flask Server**: Launches the seismic monitoring backend
2. **Opens Browser**: Automatically opens `http://localhost:5000` in your default browser
3. **Keeps Running**: The server runs in the background until you close the window

---

## Advanced Options

### Create a Folder-Based Distribution (Faster Startup)
```powershell
pyinstaller --onedir --windowed --name "OpenSeismo Lite" --add-data "index.html.html:." --add-data "tsunami_warning.py:." --add-data "tsunami_warning_display.js:." app.py
```

### Add a Custom Icon
```powershell
pyinstaller --onefile --windowed --icon icon.ico --name "OpenSeismo Lite" --add-data "index.html.html:." --add-data "tsunami_warning.py:." --add-data "tsunami_warning_display.js:." app.py
```

### Create an Installer with NSIS
After building with PyInstaller, you can use NSIS to create a professional installer:

1. Install NSIS: https://nsis.sourceforge.io/
2. Create an NSIS script to package the dist folder
3. The installer will set up program shortcuts and uninstaller

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
Solution: Install missing dependencies with:
```powershell
pip install flask requests
```

### Executable won't start
- Check if port 5000 is already in use
- Try running in administrator mode
- Check the console for error messages

### Slow first startup
- PyInstaller creates a temporary folder on first run
- Subsequent launches will be faster
- Use `--onedir` instead of `--onefile` for faster startup

---

## Distribution

Once built, you can:

1. **Share the .exe**: Users can run `OpenSeismo Lite.exe` directly (requires Python and dependencies installed)
2. **Use PyInstaller --onefile**: Single executable with all dependencies bundled
3. **Create an Installer**: Use NSIS or InnoSetup for a professional installation experience

---

## File Requirements

Make sure these files are in the same directory as `app.py`:
- `server.py` - Flask backend
- `index.html.html` - Main UI
- `tsunami_warning.py` - Tsunami warning system
- `tsunami_warning_display.js` - Frontend visualization
- Any other data files referenced in the code

---

## Notes

- The executable can only run while the system has Flask and required dependencies
- For true standalone distribution, use `--onefile` and ensure all modules are included
- The app runs on `localhost:5000` and cannot be accessed from other computers
- To allow network access, modify `server.py` to use a different host/port configuration
