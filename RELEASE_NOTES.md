# OpenSeismo Lite v1.0.0 Release

## 🎉 Initial Release with Major Features

### ✨ New Features
- **Tsunami Warning System** - JMA-inspired tsunami warning calculations
  - Real-time wave height estimation
  - Arrival time predictions for affected regions
  - Multi-level warning system (Advisory/Warning/Major Warning)
  - Visual map overlays showing affected zones
  
- **Geopolitically Neutral Map** - CartoDB Positron tiles
  - Professional, neutral visualization
  - Proper rendering of disputed territories
  - Clean, unbiased visual presentation

- **Multi-Source Earthquake Data**
  - USGS Earthquake Hazards Program
  - EMSC/CSEM European Seismic Network
  - GeoNet New Zealand
  - INGV Italy
  - GFZ/GEOFON Global Network

- **Seismic Station Network**
  - Real-time global station metadata from IRIS/SAGE and FDSN
  - Georgian station network (40+ active stations)
  - Station activity scoring based on nearby earthquakes
  - Waveform preview and sonification

### 🐛 Bug Fixes
- **Fixed infinite tab spawning** - App no longer spawns multiple browser tabs on launch
  - Simplified instance management
  - Disabled Flask debug mode in production
  - Single browser window per startup

### 📦 Technical Improvements
- MIT License added
- Professional .gitignore configuration
- Clean separation of concerns (Flask backend, Leaflet frontend)
- Offline caching for earthquake data and station metadata

### 🔧 Requirements
- **Windows 10/11** with 2GB RAM minimum
- **Python 3.14+** (included in desktop app)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### 📥 Installation
1. Download `OpenSeismo-Lite-v1.0.0.zip`
2. Extract to desired location
3. Double-click `OpenSeismo Lite.exe`
4. Browser opens automatically at `http://localhost:5000`

### ⚠️ Disclaimer
This is an **educational/informational system**. Always refer to official tsunami warning agencies:
- **PTWC** (Pacific Tsunami Warning Center)
- **JMA** (Japan Meteorological Agency)
- **Local authorities** in your region

For emergency decisions, consult official sources only.

### 📝 License
MIT License - Free for personal and commercial use. See LICENSE file.

### 🚀 Next Steps
- Mobile app support
- Additional seismic networks
- Real-time waveform streaming
- Advanced statistical analysis

---

**Built:** May 23, 2026  
**Repository:** https://github.com/DarkSidePast/darkTM2.3
