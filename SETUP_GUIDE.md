# OpenSeismo Lite - Complete Setup Guide

OpenSeismo Lite is now enhanced with a **JMA-style Tsunami Warning System** and can be converted to a standalone Windows executable.

---

## 🆕 New Features

### Tsunami Warning System
- **JMA-inspired real-time tsunami assessment** based on earthquake magnitude, depth, and location
- **Multi-region monitoring** covering Pacific rim (Japan, Indonesia, Philippines, New Zealand, US West Coast, Chile, Thailand)
- **Wave height estimation** using empirical tsunami science models
- **Arrival time calculations** for affected regions
- **Visual warning levels**: Advisory → Warning → Major Warning
- **Color-coded alerts** with affected region details

---

## 📦 Files Overview

### Core Application
- `server.py` - Flask backend with tsunami API endpoints
- `app.py` - Desktop app launcher (starts server + opens browser)
- `index.html.html` - Main web UI
- `index.html` - Alias/reference file

### Tsunami Warning System
- `tsunami_warning.py` - Backend tsunami calculation engine
- `tsunami_warning_display.js` - Frontend visualization components

### Seismic Data Integration
- `html_station_patch.js` - Station network patch
- `server_patch.py` - Server configuration patch
- `station_proxy_patch.js` - Station proxy configuration

### Build & Distribution
- `build.bat` - Automated .exe builder (Windows)
- `installer.nsi` - NSIS installer script
- `BUILD_EXE.md` - Detailed build instructions

---

## 🚀 Quick Start

### Option A: Run as Python App (No Build Required)
```powershell
# Install dependencies
pip install flask requests

# Run the app
python app.py
```
This will:
- Start the Flask server
- Automatically open http://localhost:5000 in your browser

### Option B: Build as Windows .exe

#### Method 1: Automated Build
```powershell
# Run the build script (installs PyInstaller automatically)
.\build.bat
```

#### Method 2: Manual Build
```powershell
# Install build tools
pip install flask requests pyinstaller

# Build executable
pyinstaller --onefile --windowed --name "OpenSeismo Lite" `
    --add-data "index.html.html:." `
    --add-data "tsunami_warning.py:." `
    --add-data "tsunami_warning_display.js:." `
    app.py

# Executable is in: dist/OpenSeismo Lite.exe
```

---

## 🌊 Using the Tsunami Warning System

### For Developers

#### Backend API Endpoint
```python
POST /api/tsunami/evaluate
Content-Type: application/json

{
    "magnitude": 7.2,
    "depth_km": 30,
    "latitude": 35.0,
    "longitude": 141.0,
    "time": "2026-05-22T10:30:00Z"
}
```

#### Response
```json
{
    "has_risk": true,
    "warnings": [
        {
            "region": "Japan",
            "distance_km": 150.5,
            "wave_height_m": 2.5,
            "warning_level": "WARNING",
            "arrival_time_minutes": 11,
            "arrival_time_formatted": "11m"
        }
    ],
    "magnitude": 7.2,
    "depth_km": 30,
    "epicenter": {"lat": 35.0, "lon": 141.0}
}
```

#### Info Endpoint
```
GET /api/tsunami/info
```
Returns warning thresholds, monitored regions, and system information.

### For Users
1. Earthquake data is automatically fetched from multi-source feeds
2. Tsunami analysis runs automatically for qualifying earthquakes (M6.5+)
3. Warning panel appears in top-right with:
   - Warning level and description
   - Affected regions
   - Estimated wave heights
   - Arrival times
4. Map shows affected zones with warning circles

---

## ⚙️ Configuration

### Modify Monitored Regions
Edit `tsunami_warning.py`, `COASTAL_REGIONS` section:
```python
COASTAL_REGIONS = {
    "Pacific": {
        "regions": [
            {"name": "Custom Region", "lat": 0.0, "lon": 0.0, "radius": 200},
            # ... more regions
        ]
    }
}
```

### Adjust Warning Thresholds
Edit `WAVE_HEIGHT_THRESHOLDS` in `tsunami_warning.py`:
```python
WAVE_HEIGHT_THRESHOLDS = {
    TsunamiWarningLevel.MAJOR_WARNING: 3.0,    # 3m+
    TsunamiWarningLevel.WARNING: 1.0,          # 1m+
    TsunamiWarningLevel.ADVISORY: 0.5,         # 0.5m+
}
```

---

## 📊 System Architecture

```
┌─ Frontend (Browser) ─────────────────────┐
│  • OpenSeismo Dashboard                  │
│  • Real-time Earthquake Display         │
│  • Tsunami Warning Visualization        │
│  • Station Monitoring                   │
└────────────────────┬──────────────────────┘
                     │ HTTP/JSON
┌────────────────────▼──────────────────────┐
│  Flask Backend (Python)                   │
├───────────────────────────────────────────┤
│  • /api/tsunami/evaluate                 │
│  • /api/tsunami/info                     │
│  • /proxy/stations/* (IRIS, GEOFON, etc) │
└────────────────────┬──────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    ┌───▼──┐   ┌─────▼──┐   ┌─────▼──┐
    │ USGS │   │  EMSC  │   │  GeoNet│
    └──────┘   └────────┘   └────────┘
    
Tsunami Engine:
  • Magnitude/Depth Analysis
  • Distance Calculations
  • Wave Height Estimation
  • Arrival Time Prediction
```

---

## 🔍 Testing the Tsunami Warning

### Test with curl
```bash
curl -X POST http://localhost:5000/api/tsunami/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "magnitude": 7.5,
    "depth_km": 20,
    "latitude": 35.0,
    "longitude": 141.0
  }'
```

### Historical Test Cases
```python
# 2011 Tōhoku Earthquake (M9.0)
magnitude: 9.0, depth: 29, lat: 38.3, lon: 142.4 → MAJOR WARNINGS

# 2004 Indian Ocean (M9.1)
magnitude: 9.1, depth: 30, lat: 3.3, lon: 95.8 → MAJOR WARNINGS

# Typical Pacific M7.0
magnitude: 7.0, depth: 50, lat: -20.0, lon: -175.0 → ADVISORIES/WARNINGS
```

---

## 📋 System Requirements

### To Run as Python App
- Python 3.7+
- Flask
- Requests
- 50MB disk space

### To Build .exe
- Python 3.7+
- PyInstaller
- All runtime dependencies bundled in executable
- ~100-150MB disk space

### To Create Installer
- NSIS (free, https://nsis.sourceforge.io/)
- Built .exe file

---

## 🐛 Troubleshooting

### Port 5000 Already in Use
```powershell
# Find what's using port 5000
netstat -ano | findstr :5000

# Kill the process
taskkill /PID [PID] /F
```

### Module Not Found Errors
```powershell
pip install flask requests pyinstaller
```

### .exe Won't Start
- Run as Administrator
- Check that Python is installed and in PATH
- Delete `__pycache__` folder and rebuild

### Browser Doesn't Open
- The server still starts; manually visit http://localhost:5000
- Check if default browser is set

---

## 📝 DISCLAIMER

This is an **educational and scientific monitoring tool**, NOT an official earthquake warning system (EEW) or tsunami warning system (TWS). 

- Do not rely on this for emergency decisions
- Always follow official government warnings
- For official warnings, consult JMA, USGS, or local authorities
- This tool provides scientific visualization only

---

## 🔗 Resources

- **JMA Tsunami Warning**: https://www.jma.go.jp/
- **USGS Earthquakes**: https://earthquake.usgs.gov/
- **Tsunami Science**: https://www.ncei.noaa.gov/products/etopo-global-relief-model
- **FDSN Networks**: https://www.fdsn.org/

---

## 📄 License

This project combines educational earthquake monitoring with tsunami assessment science.
Refer to individual component licenses for usage terms.

---

## ✉️ Support

For issues with:
- **Seismic data**: Check upstream sources (USGS, EMSC, GeoNet)
- **Tsunami calculations**: Review parameters in `tsunami_warning.py`
- **Build/deployment**: See `BUILD_EXE.md` for detailed troubleshooting
