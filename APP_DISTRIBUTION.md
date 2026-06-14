# OpenSeismo Lite - Desktop App Distribution

## 🚀 Standalone Executable Ready!

Your application has been successfully converted from a web-based app to a standalone desktop application.

### **Executable Location**
```
dist/OpenSeismo Lite/OpenSeismo Lite.exe
```

### **What's Included**
✅ Complete Flask server bundled inside  
✅ Real-time earthquake data from USGS API  
✅ 3D globe visualization with Cesium.js  
✅ Seismic wave propagation animations  
✅ Tsunami warning system  
✅ Intensity calculations (MMI & Shindo)  
✅ Station network monitoring  
✅ Multiple map modes (OpenStreetMap, Satellite, Dark)  

### **How to Run**

#### **Option 1: Direct Launch**
- Navigate to: `dist/OpenSeismo Lite/`
- Double-click: `OpenSeismo Lite.exe`
- The app automatically:
  - Starts the Flask server
  - Prevents multiple instances
  - Opens your default browser
  - Loads the interactive globe

#### **Option 2: Create Desktop Shortcut**
- Right-click on `OpenSeismo Lite.exe`
- Select: "Send to → Desktop (create shortcut)"
- Now launch from your desktop anytime

#### **Option 3: Add to Start Menu**
- Copy the `.exe` to any location (e.g., `C:\Apps\OpenSeismo Lite\`)
- Create a shortcut in:
  ```
  C:\Users\{username}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\
  ```

### **System Requirements**
- Windows 10 or later (64-bit)
- 500 MB free disk space (for dependencies)
- Internet connection for earthquake data
- Modern web browser (built-in support)

### **Features**

#### **Real-Time Earthquake Monitoring**
- Live USGS earthquake data
- Magnitude-based filtering (2.5+, 4.5+, significant)
- Color-coded markers by magnitude
- Click earthquakes to see details

#### **3D Globe Visualization**
- Interactive Cesium.js globe
- Real-time earth imagery
- Zoom, pan, rotate controls
- Multiple imagery modes:
  - **OpenStreetMap**: Light, detailed maps
  - **Satellite**: USGS satellite imagery
  - **Dark**: CartoDB dark theme

#### **Seismic Analysis**
- Epicenter location on interactive map
- P-wave, S-wave, Surface wave propagation
- Animation shows wave expansion in real-time
- Customizable animation timing

#### **Tsunami Warning System**
- JMA-inspired warning levels
- Wave height estimation
- Arrival time calculation
- Risk assessment by location

#### **Station Network**
- Global seismic station monitoring
- Signal quality indicators
- Real-time noise measurements
- Network health status

#### **Intensity Grids**
- Modified Mercalli Intensity (MMI) scale
- Japan Meteorological Agency (Shindo) scale
- Depth-adjusted calculations
- Hazard visualization

### **Troubleshooting**

#### **App won't launch**
- Ensure Windows Defender/antivirus allows the executable
- Try running as Administrator: Right-click → "Run as administrator"
- Check Windows version (requires Windows 10+)

#### **"Port already in use" error**
- Another instance is running (lock prevents multiple launches)
- Wait 10 seconds and try again
- Or terminate any `OpenSeismo Lite` processes in Task Manager

#### **Browser doesn't open automatically**
- Check if default browser is set in Windows Settings
- Manually open: `http://localhost:5000`
- The app server starts on port 5000

#### **Data not loading**
- Check internet connection (needs USGS API access)
- Open browser console (F12) to see error details
- Clear browser cache and refresh

### **Performance Tips**
- Close other browser tabs for smooth globe animation
- Use "Dark" mode for better GPU performance on older computers
- Disable unnecessary map layers (stations, volcanoes) if framerate drops
- Refresh data manually if updates seem stuck

### **Creating an Installer (Optional)**

To create a Windows installer (.msi), you can use:

```powershell
# Install NSIS
choco install nsis

# Build installer from provided script
makensis installer.nsi
```

This creates a proper Windows installer with uninstall support.

### **Source Code**

View the source on GitHub:  
https://github.com/DarkSidePast/darkTM2.3

### **License**

See LICENSE file in the application folder.

---

**Enjoy real-time earthquake monitoring!** 🌍📊
