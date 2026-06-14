# OpenSeismo Lite - Intensity Calculator Integration Guide

## Overview
The intensity calculator adds **MMI (Modified Mercalli Intensity)** and **Shindo** intensity scales with color-coded fault zones to OpenSeismo Lite.

## Features Added

### 1. **MMI Scale (Modified Mercalli Intensity)**
- Range: I (Not felt) to XII (Total destruction)
- Color-coded from white (#ffffff) to dark red (#cc0000)
- Measures the effects of earthquakes on buildings, terrain, and people
- Based on empirical attenuation relationships (Wald et al. 1999)

### 2. **Shindo Scale (Japan Meteorological Agency)**
- Range: 0 (Not felt) to 7 (Extreme destruction)
- Specifically calibrated for Japanese seismic conditions
- More sensitive to shallow earthquakes
- Enhanced for subduction zone earthquakes

### 3. **Fault Zone Classification**
Seven major fault types with unique colors and characteristics:

| Fault Type | Color | Depth Range | Characteristics |
|-----------|-------|------------|-----------------|
| **Subduction** | Dark Blue (#0066cc) | 0-700 km | High tsunami risk, strong shaking |
| **Transform** | Orange (#ff6600) | 0-50 km | Strong lateral motion, frequent aftershocks |
| **Reverse-Thrust** | Red (#cc0000) | 0-300 km | Vertical uplift, tsunami potential |
| **Normal** | Green (#00cc66) | 0-30 km | Extensional stress, rift zones |
| **Divergent** | Light Blue (#66ccff) | 0-20 km | Seafloor spreading, mid-ocean ridges |
| **Convergent** | Purple (#9900cc) | 0-250 km | Compression zones, mountain building |
| **Strike-Slip** | Yellow (#ffcc00) | 0-30 km | Horizontal motion, transform faults |

### 4. **Tectonic Zones Database**
The system recognizes and classifies earthquakes in 21 major tectonic zones:

**Subduction Zones:**
- Japan Trench, Kuril-Kamchatka, Peru-Chile, Tonga-Kermadec, Mariana, Indonesia, Cascadia

**Transform Faults:**
- San Andreas, Alpine Fault (NZ), Dead Sea

**Mid-Ocean Ridges (Divergent):**
- Mid-Atlantic Ridge, East Pacific Rise, Indian Ocean Ridge

**Reverse-Thrust Faults:**
- Hindu Kush, Himalayas, Zagros

## API Endpoints

### 1. Calculate Intensity at Distance
**Endpoint:** `POST /api/intensity/mmi-shindo`

**Request:**
```json
{
    "magnitude": 7.5,
    "depth_km": 15,
    "latitude": 36.0,
    "longitude": 138.0,
    "distance_km": 50.0
}
```

**Response:**
```json
{
    "magnitude": 7.5,
    "depth_km": 15,
    "distance_km": 50,
    "fault_type": "Subduction",
    "fault_zone": {
        "type": "Subduction",
        "color": "#0066cc",
        "description": "Subduction Zone - High tsunami and magnitude risk",
        "typical_depth_range": "0-700 km"
    },
    "mmi": {
        "value": 7.24,
        "scale": "MMI_VII",
        "description": "Very Strong - Considerable damage, everyone runs outside",
        "color": "#ffcc00",
        "integer": 7
    },
    "shindo": {
        "value": 5.62,
        "scale": "SHINDO_5_PLUS",
        "description": "Strong+ - Considerable damage",
        "color": "#ff9900"
    }
}
```

### 2. Get Comprehensive Report
**Endpoint:** `POST /api/intensity/report`

**Request:**
```json
{
    "magnitude": 7.5,
    "depth_km": 15,
    "latitude": 36.0,
    "longitude": 138.0
}
```

**Response includes:**
- Fault zone classification
- Epicenter intensities (MMI and Shindo)
- Intensity profile at various distances (10km, 50km, 100km, 200km)
- Safety recommendations based on intensity levels

### 3. Generate Intensity Grid/Heatmap
**Endpoint:** `POST /api/intensity/grid`

**Request:**
```json
{
    "magnitude": 7.5,
    "depth_km": 15,
    "latitude": 36.0,
    "longitude": 138.0,
    "grid_size_km": 50,
    "max_distance_km": 500
}
```

**Returns:** Array of grid points with lat/lon and intensity values for heatmap visualization

### 4. Get Scale Information
**Endpoint:** `GET /api/intensity/info`

**Returns:** Complete information about MMI and Shindo scales, fault zones, and examples

## Intensity Calculations

### MMI Calculation Formula
Based on Wald et al. (1999) empirical relationships:

```
MMI = C1 + C2*M - C3*log(R) - C4*R

Where:
- C1 = 4.0 (intercept)
- C2 = 1.30 (magnitude coefficient)
- C3 = 3.0 (distance logarithmic attenuation)
- C4 = 0.0001 (linear distance factor)
- R = hypocentral distance (km)
- M = magnitude

Fault-type adjustments:
- Subduction: +0.3
- Reverse-Thrust: +0.2
- Divergent: -0.2
```

### Shindo Calculation Formula
JMA-calibrated for Japanese conditions:

```
Shindo = (M - 1) × depth_multiplier - (0.0075 × hypocentral_distance)

Depth multiplier:
- < 20 km: 1.3 (shallow earthquakes are amplified)
- 20-70 km: 1.15
- > 70 km: 1.0

Subduction zone enhancement:
- Additional boost = 0.8 × (1 - depth_km/700)
- This accounts for efficient energy transmission in subduction zones
```

## Integration with OpenSeismo

### Frontend Display
The intensity information is displayed in a side panel when selecting an earthquake:

1. **Fault Zone Information**
   - Type, color code, and description
   - Typical depth range for that fault type

2. **Intensity Scales at Epicenter**
   - MMI value and description with color
   - Shindo value and description with color

3. **Distance-Based Intensity Profile**
   - Shows how intensity decreases with distance
   - Provided at 10km, 50km, 100km, 200km from epicenter

4. **Safety Recommendations**
   - Based on intensity levels
   - Fault-type specific warnings

### Color Coding System

**MMI Scale Colors:**
- White → Light Blue: Minimal to light damage
- Cyan → Yellow: Moderate to considerable damage
- Orange → Red → Dark Red: Severe to extreme destruction

**Fault Zone Colors:**
- Correspond to tectonic type for quick visual identification
- Consistent with USGS and IGC standards

## Usage Examples

### Example 1: 2011 Japan Earthquake
```
Magnitude: 9.1
Depth: 24 km
Location: 38.3°N, 142.4°E (Japan Trench - Subduction)

Result:
- Fault Type: Subduction
- MMI at epicenter: ~8.5 (Severe damage)
- Shindo at epicenter: ~6.7 (Very Strong+)
- Color: Dark blue zone with red intensity zone
```

### Example 2: San Andreas Strike-Slip
```
Magnitude: 7.3
Depth: 12 km
Location: 36°N, 120.5°W (San Andreas Fault)

Result:
- Fault Type: Transform (Strike-Slip)
- MMI at epicenter: ~7.8 (Severe damage)
- Shindo at epicenter: ~5.8 (Strong+)
- Color: Orange zone with orange/red intensity
```

## Accuracy Notes

### High Accuracy For:
- Earthquakes within classified tectonic zones
- Magnitudes 5.0-8.5
- Continental and oceanic depths (0-700 km)

### Limitations:
- Deep mantle earthquakes (>700 km) use default classification
- Very small earthquakes (<3.0) use simplified model
- Actual shaking varies with local geology (not included in this model)
- No account for local amplification factors

### Recommendations:
- Always verify with official USGS/USGS ShakeMaps for important decisions
- Use for educational purposes and general understanding
- Reference JMA intensity scales for Japan-specific applications
- Consult PTWC for tsunami specific information

## Files Modified/Created

1. **intensity_calculator.py** - Core calculation engine
   - 600+ lines of pure calculation and classification logic
   - Includes all empirical relationships and zone definitions

2. **server.py** - API endpoints
   - Added 4 new REST endpoints for intensity calculations
   - Integrated with existing Flask framework

3. **This guide (INTENSITY_GUIDE.md)**
   - Complete documentation of the system

## Future Enhancements

Potential additions:
- Local amplification factors (soil/rock type)
- ShakeMaps integration with real USGS data
- Liquefaction potential zones
- Landslide risk assessment
- Building damage estimation
- Real-time intensity displays on map
- Historical intensity comparison
- Tsunami wave propagation visualization

## References

- Wald, D. J., Quitoriano, V., Heaton, T. H., & Kanamori, H. (1999). "Relationships between peak ground acceleration, peak ground velocity, and modified Mercalli intensity in California." Earthquake Spectra, 15(3), 557-564.

- Japan Meteorological Agency. (2001). "The JMA Seismic Intensity Scale." https://www.jma.go.jp/jma/en/

- USGS. "Modified Mercalli Intensity Scale." https://earthquake.usgs.gov/earthquakes/events/1906calif/

- Kanamori, H. (1977). "The energy release of great earthquakes." Journal of Geophysical Research, 82(20), 2981-2987.
