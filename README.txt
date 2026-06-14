# 🌍 OpenSeismo Lite

OpenSeismo Lite is a multi-source seismic monitoring dashboard focused on:

- real public earthquake data
- scientific transparency
- station monitoring
- educational/seismological visualization
- regional + global situational awareness

This project was created as an educational and scientific monitoring tool and is **NOT** an official earthquake warning system.

---

# ✨ Features

## 🌎 Earthquake Monitoring
- Multi-source real seismic data
- USGS 6-month historical global backbone
- EMSC / CSEM integration
- GeoNet New Zealand integration
- INGV Italy integration
- GFZ / GEOFON integration
- JMA-linked aggregated data support where available

---

## 📡 Seismic Stations
- Active-only station filtering
- Historical/closed station handling
- Global FDSN-compatible station support
- IRIS / SAGE integration
- Georgian GO network integration
- IliaUni public station metadata support
- Station activity estimation
- Station sample-rate (Hz) display where available

---

## 🎧 Waveform / Sonification
- Station waveform preview
- Educational seismic sonification
- Waveform/data source links
- Real catalog-based nearby activity estimation

NOTE:
This is NOT raw live waveform amplitude monitoring and NOT an official EEW system.

---

## 💾 Infrastructure
- Offline cache support
- Localhost proxy support for CORS-restricted APIs
- Multi-source catalog aggregation
- Real-data-only philosophy
- Transparent source attribution

---

# ⚠️ Important Disclaimer

OpenSeismo Lite is:

- unofficial
- educational
- research-oriented
- visualization-focused

It is NOT intended to replace:

- official earthquake warning systems
- emergency alerts
- governmental seismic agencies
- tsunami warning systems

Always refer to official agencies for emergency information.

---

# 📚 Data Sources & Credits

## Earthquake Data
- USGS Earthquake Hazards Program
- EMSC / CSEM
- GeoNet New Zealand
- INGV Italy
- GFZ / GEOFON
- JMA Japan Meteorological Agency (through aggregated/public feeds where available)

---

## Seismic Station Metadata
- IRIS / SAGE
- FDSN Station Services
- Ilia State University / Institute of Earth Sciences and National Seismic Monitoring Center (Georgia GO network)

Georgian station metadata references publicly available information from Ilia State University public station listings.

---

# ❤️ Philosophy

This project intentionally avoids:

- fake earthquake data
- fake alerts
- fake EEW
- misleading visualizations
- fabricated stations
- fearbait content

Real data and scientific transparency are prioritized over gimmicks.

---

# 🛠️ Setup

## Requirements
- Python 3.x
- Flask
- Requests

Install dependencies:

```bash
pip install flask requests