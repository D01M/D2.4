# OpenSeismo Lite - Desktop Application

## Overview

**OpenSeismo Lite** is now available as a **native Windows desktop application**. The desktop version maintains all features of the web application while providing a native GUI interface.

## Features

### Earthquake Monitoring
- ✅ Real-time earthquake detection and alerts
- ✅ Global earthquake database (100,000+ events from USGS, ESMC, CSEM, JMA)
- ✅ Live streaming with Server-Sent Events (SSE)
- ✅ 70+ seismic monitoring stations worldwide

### Alert Systems
- 🚨 **EEW (Earthquake Early Warning)**: M5.0+ earthquakes with 5-30 second advance warning
- 🌊 **Tsunami Alerts**: Japanese-style siren warnings for M6.5+ earthquakes
- 🔊 **Sound Notifications**: Web Audio API generated tones with customizable volume
- 🔔 **Desktop Notifications**: Browser-like notifications with earthquake details

### Intensity Calculations
- 📊 MMI (Modified Mercalli Intensity Scale) calculations
- 📊 Shindo (JMA Intensity Scale) calculations
- 📊 Multi-agency support (USGS ShakeMap, ESMC, CSEM, JMA)

### Alert Controls
- 🎛️ **Sound Control**: Enable/disable with volume slider (0-100%)
- 🎛️ **Tsunami Control**: Enable/disable tsunami alerts separately
- 🎛️ **EEW Control**: Enable/disable early warning beeps
- 🎛️ **Magnitude Threshold**: Filter earthquakes (3.0 - 7.0 Richter)
- 🎛️ **Mute Function**: Quick mute for 60 seconds
- 🎛️ **Auto-update**: Toggle real-time monitoring

## Building the EXE

### Prerequisites
- Windows 7 or later
- Python 3.8+ installed and in PATH
- Internet connection (for dependencies)

### Method 1: Batch File (Easiest)
```batch
# Run from command prompt in the OpenSeismoLite folder
build_desktop_exe.bat
```

This will:
1. Install Python dependencies
2. Install PyInstaller
3. Build the desktop EXE
4. Create `dist/OpenSeismo Lite.exe`

### Method 2: Python Script
```bash
python build_desktop_exe.py
```

### Method 3: Manual PyInstaller
```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile desktop_app.spec
```

## Running the Application

### After Building
1. Navigate to `dist/` folder
2. Double-click `OpenSeismo Lite.exe`
3. The application will:
   - Start the Flask backend server
   - Open the native GUI window
   - Begin monitoring earthquakes in real-time

### During Runtime
- **Earthquake List**: Shows all earthquakes above your magnitude threshold
- **Real-time Updates**: Automatically refreshes every 10 seconds
- **Alert Panel**: Control all preferences from the interface
- **Status Bar**: Shows connection status and last update time

## Settings & Preferences

### Sound Alerts
- **Enabled**: Turn sound alerts on/off
- **Volume**: Control alert volume (0-100%)
- **Thresholds**: Different sounds for different magnitude levels
  - M4.0-5.0: 440Hz, 100ms
  - M5.0-6.0: 660Hz, 200ms
  - M6.0-7.0: 880Hz, 300ms
  - M7.0+: 1046Hz, 400ms

### Tsunami Alerts
- **Enabled**: Turn tsunami warnings on/off
- **Japanese Siren**: Frequency sweep 600-1200Hz (when alert triggers)
- **Alert Levels**:
  - Advisory (0.5-1.0m): 2 cycles
  - Warning (1.0-3.0m): 3 cycles
  - Major Warning (3.0m+): 4 cycles

### EEW (Earthquake Early Warning)
- **Enabled**: Turn EEW beeps on/off
- **Alert Levels**:
  - Level 1 (Weak/Distant): 1000Hz, 5 beeps
  - Level 2 (Moderate): 1200Hz, 7 beeps
  - Level 3 (Severe/Close): 1400Hz, 10 beeps
- **Coverage**: 22 major cities worldwide
- **Advance Warning**: 5-30 seconds depending on distance and magnitude

### Magnitude Threshold
- Filter earthquakes by minimum magnitude
- Range: 3.0 - 7.0 Richter scale
- Default: 4.5

## Seismic Stations

The application monitors 70 seismic stations worldwide:

### Asia-Pacific (12)
- Japan: Tokyo (JPN), Osaka, Fukuoka
- Taiwan: Taipei
- Indonesia: Jakarta
- Philippines: Manila
- Thailand: Bangkok
- Korea: Seoul
- China: Beijing, Shanghai
- India: Chennai, Mumbai
- Nepal: Kathmandu

### Europe (7)
- Italy: Rome, Milan
- Greece: Athens
- Germany: Berlin
- France: Paris
- UK: London
- Switzerland: Zurich
- Poland: Warsaw

### Americas (15)
- USA: LA, San Francisco, Seattle, Philadelphia, NYC, Denver
- Canada: Toronto, Vancouver
- Mexico: Mexico City
- Central America: El Salvador, Guatemala
- South America: Lima, Bogota, Quito, Brazil, Buenos Aires

### Africa & Middle East (10)
- Egypt: Cairo
- Kenya: Nairobi
- Ethiopia: Addis Ababa
- South Africa: Johannesburg, Cape Town
- Turkey: Istanbul, Ankara
- UAE: Dubai
- Iran: Tehran
- Lebanon: Beirut

### Oceania (5)
- Australia: Sydney, Melbourne, Perth
- New Zealand: Auckland, Wellington

### Caucasus (GO/IES Network - Georgia)
- Tbilisi (TBS)
- Batumi (BAT)
- Gori (GOR)
- Kutaisi (KUT)
- Zugdidi (ZUG)

## System Requirements

### Minimum
- Windows 7 or later
- 512 MB RAM
- 300 MB disk space (for EXE + data)
- Dual-core processor

### Recommended
- Windows 10/11
- 2+ GB RAM
- 500 MB disk space
- Internet connection (for live updates)

## Data Sources

- **USGS**: United States Geological Survey
- **ESMC**: European-Mediterranean Seismic Centre
- **CSEM**: China Seismic Networks Center
- **JMA**: Japan Meteorological Agency

## Architecture

### Backend (Python Flask)
- `server.py`: Main Flask application
- `intensity_calculator.py`: Intensity calculations
- `tsunami_warning.py`: Tsunami alert system
- `live_earthquake_detector.py`: Real-time monitoring
- `location_search.py`: Geographic location queries

### Frontend (PySimpleGUI)
- `desktop_app.py`: Main desktop application
- Native Windows interface
- Real-time earthquake display
- Alert configuration panel

### Communication
- **HTTP REST API**: Backend exposes JSON endpoints
- **Server-Sent Events (SSE)**: Real-time earthquake stream
- **localStorage**: Preference persistence

## Performance

- **Update Frequency**: 10 seconds (configurable)
- **Memory Usage**: ~50-100 MB runtime
- **CPU Usage**: <5% idle, <15% during alerts
- **Network**: ~50-100 KB per update

## Troubleshooting

### Application won't start
1. Ensure Python 3.8+ is installed
2. Try rebuilding: `build_desktop_exe.bat`
3. Check Windows Firewall (port 5000)

### No earthquakes showing
1. Check internet connection
2. Click "Refresh" button
3. Lower magnitude threshold
4. Check API connectivity at http://localhost:5000/api/earthquakes

### Sound not working
1. Check Windows volume
2. Enable "Sound Alerts" in preferences
3. Adjust volume slider
4. Test speaker volume

### Server won't start
1. Port 5000 may be in use
2. Edit `server.py` to use different port
3. Restart application

## Known Limitations

- Desktop version requires Flask backend running on localhost:5000
- Internet connection required for live earthquake data
- Sound playback requires working audio device
- Windows-only (PySimpleGUI desktop interface)

## Future Enhancements

- [ ] Multi-language support (Japanese, Spanish, Chinese)
- [ ] Offline data caching
- [ ] Map visualization in desktop window
- [ ] Historical earthquake database browser
- [ ] Custom alert sounds
- [ ] macOS/Linux support (with Qt5)
- [ ] Mobile companion app
- [ ] Database backend (SQLite/PostgreSQL)

## License

See LICENSE file in main directory

## Support

For issues or feature requests, please check the project repository or contact the development team.

---

**Version**: 6.0 Desktop Edition
**Build Date**: 2026-06-14
**Status**: Production Ready ✅
