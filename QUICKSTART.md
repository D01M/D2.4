# 🚀 Quick Start - OpenSeismo Lite

## What's New ✨

✅ **JMA-style Tsunami Warning System** - Real-time tsunami risk assessment
✅ **Converted to Windows .exe** - Run as a desktop app without Python

---

## 🎯 Run the App

### Option 1: Standalone .exe (No Setup Required)
```
dist/OpenSeismo Lite.exe
```
- Click and run!
- No Python needed
- App launches in seconds

### Option 2: Python Script
```powershell
python app.py
```
- Requires Python 3.7+
- Automatically opens browser

### Option 3: Direct Server
```powershell
python server.py
# Visit http://localhost:5000 manually
```

---

## 📊 Files Overview

```
OpenSeismoLite/
├── dist/
│   └── OpenSeismo Lite.exe          ← Run this!
├── app.py                            ← Desktop launcher
├── server.py                         ← Flask backend
├── tsunami_warning.py                ← Tsunami calculations
├── tsunami_warning_display.js        ← Frontend visualization
├── index.html.html                   ← Main UI
└── [Build Tools]
    ├── build.bat                     ← Windows batch builder
    ├── build.ps1                     ← PowerShell builder
    ├── installer.nsi                 ← NSIS installer script
    ├── BUILD_EXE.md                  ← Detailed build docs
    └── SETUP_GUIDE.md                ← Complete setup guide
```

---

## 🌊 Tsunami Warning Features

### Automatic Detection
- Monitors earthquakes M6.5+
- Calculates tsunami risk for:
  - Japan
  - Indonesia
  - Philippines
  - New Zealand
  - US West Coast
  - Chile
  - Thailand

### Warning Levels
- 🚨 **MAJOR WARNING** (3m+ waves)
- ⚠️ **WARNING** (1m+ waves)
- ℹ️ **ADVISORY** (0.5m+ waves)
- ✓ **NO WARNING**

### Information Provided
- Estimated wave height
- Distance to coast
- Arrival time estimate
- Affected regions
- Color-coded risk visualization

---

## 🔧 System Requirements

- **Windows 10/11** (for .exe)
- **200 MB** disk space
- **Internet connection** (for earthquake data)
- No Python installation needed (bundled in .exe)

---

## 📡 Data Sources

- USGS Earthquake Hazards Program
- EMSC / CSEM
- GeoNet (New Zealand)
- IRIS/FDSN Stations
- GEOFON Network

---

## ⚖️ DISCLAIMER

**This is an EDUCATIONAL and SCIENTIFIC tool, NOT an official warning system.**

- For official tsunami warnings: Contact JMA, USGS, or local authorities
- Use for visualization and learning only
- Do not rely on this for emergency decisions

---

## 🐛 Troubleshooting

### .exe won't start
1. Run as Administrator
2. Check antivirus isn't blocking it
3. Try: `python app.py` instead

### Port 5000 already in use
```powershell
# Edit server.py and change:
app.run(host="127.0.0.1", port=5000, debug=True)
# to:
app.run(host="127.0.0.1", port=5001, debug=True)
```

### No browser opens
- Manually visit http://localhost:5000
- Server still runs in background

---

## 📝 Next Steps

1. **Test the .exe**: Run `dist/OpenSeismo Lite.exe`
2. **Create Installer** (optional):
   ```
   Download NSIS from https://nsis.sourceforge.io/
   Then: makensis installer.nsi
   ```
3. **Share**: Send the .exe to friends/colleagues

---

## 💻 Development

Want to rebuild or modify?

### Rebuild .exe
```powershell
# Clean rebuild
python -m PyInstaller --onefile --windowed --name "OpenSeismo Lite" `
    --add-data "index.html.html:." `
    --add-data "tsunami_warning.py:." `
    --add-data "tsunami_warning_display.js:." `
    app.py
```

### Modify Tsunami Parameters
Edit `tsunami_warning.py`:
- Change `COASTAL_REGIONS` to add/remove regions
- Adjust `WAVE_HEIGHT_THRESHOLDS` for warning levels
- Modify `estimate_wave_height()` for calculation changes

### Add Features
- Edit `index.html.html` for UI changes
- Modify `server.py` to add new endpoints
- Update `tsunami_warning_display.js` for visualization

---

## 📚 Documentation

- [BUILD_EXE.md](BUILD_EXE.md) - Detailed build instructions
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete system guide
- [tsunami_warning.py](tsunami_warning.py) - API documentation in code

---

## 🎓 Learning Resources

- **Tsunami Science**: https://www.ncei.noaa.gov/
- **JMA Warnings**: https://www.jma.go.jp/
- **USGS Earthquakes**: https://earthquake.usgs.gov/
- **Seismic Networks**: https://www.fdsn.org/

---

**Version**: 2.0 (with Tsunami Warning System & .exe Distribution)
**Last Updated**: May 22, 2026
