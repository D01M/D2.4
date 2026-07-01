from flask import Flask, Response, send_from_directory, request, jsonify
import requests
import json
import os
import threading
import time
from datetime import datetime, timedelta
from tsunami_warning import TsunamiWarningSystem, format_tsunami_report
from intensity_calculator import IntensityCalculator, FaultType, AgencySummaryProcessor
from location_search import LocationSearcher
from live_earthquake_detector import LiveEarthquakeDetector
from openseismo.stations.station_manager import StationManager

app = Flask(__name__, static_folder="static", static_url_path="/static")

station_manager = StationManager()

# ============= LIVE UPDATE SYSTEM =============
# Track last seen earthquakes for new alert detection
last_seen_earthquakes = {}
last_update_time = datetime.utcnow()
connected_clients = []

# Sound alert configuration
SOUND_ALERTS = {
    "low": {
        "frequency": 440,        # Hz (A4 note)
        "duration_ms": 100,
        "volume": 0.3,
        "magnitude_threshold": 4.0,
        "description": "Low magnitude earthquake (4.0-5.0)"
    },
    "moderate": {
        "frequency": 660,        # Hz (E5 note)
        "duration_ms": 200,
        "volume": 0.6,
        "magnitude_threshold": 5.0,
        "description": "Moderate earthquake (5.0-6.0)"
    },
    "high": {
        "frequency": 880,        # Hz (A5 note)
        "duration_ms": 300,
        "volume": 0.8,
        "magnitude_threshold": 6.0,
        "description": "High magnitude earthquake (6.0-7.0)"
    },
    "critical": {
        "frequency": 1046,       # Hz (C6 note)
        "duration_ms": 400,
        "volume": 1.0,
        "magnitude_threshold": 7.0,
        "description": "Critical magnitude earthquake (7.0+)"
    }
}

# Tsunami alert configuration - Japanese-style siren patterns
TSUNAMI_ALERTS = {
    "advisory": {
        "type": "siren",
        "pattern": "sweep",  # Frequency sweep (rising/falling)
        "frequency_start": 600,  # Hz
        "frequency_end": 1200,   # Hz
        "duration_ms": 2000,     # 2 seconds for advisory
        "volume": 0.8,
        "cycles": 2,
        "description": "Tsunami Advisory (0.5-1.0m waves)",
        "label": "津波注意報"  # Japanese: Tsunami Advisory
    },
    "warning": {
        "type": "siren",
        "pattern": "sweep",
        "frequency_start": 600,
        "frequency_end": 1200,
        "duration_ms": 3000,     # 3 seconds for warning
        "volume": 1.0,
        "cycles": 3,
        "description": "Tsunami Warning (1.0-3.0m waves)",
        "label": "津波警報"  # Japanese: Tsunami Warning
    },
    "major_warning": {
        "type": "siren",
        "pattern": "sweep",
        "frequency_start": 600,
        "frequency_end": 1200,
        "duration_ms": 4000,     # 4 seconds for major warning
        "volume": 1.0,
        "cycles": 4,
        "description": "Major Tsunami Warning (3.0m+ waves)",
        "label": "大津波警報"  # Japanese: Major Tsunami Warning
    }
}

# Earthquake Early Warning (EEW) configuration - Japanese style rapid alerts
EEW_ALERTS = {
    "level1": {
        "type": "beep_sequence",
        "pattern": "rapid_beeps",
        "frequency": 1000,       # Hz
        "beep_duration_ms": 150,
        "interval_ms": 100,
        "beep_count": 5,
        "volume": 1.0,
        "description": "EEW Alert - Weak Shaking Expected",
        "label": "緊急地震速報（警報）"  # Japanese: EEW Alert
    },
    "level2": {
        "type": "beep_sequence",
        "pattern": "rapid_beeps",
        "frequency": 1200,
        "beep_duration_ms": 200,
        "interval_ms": 80,
        "beep_count": 7,
        "volume": 1.0,
        "description": "EEW Alert - Moderate Shaking Expected",
        "label": "緊急地震速報（警報）"
    },
    "level3": {
        "type": "beep_sequence",
        "pattern": "rapid_beeps",
        "frequency": 1400,
        "beep_duration_ms": 250,
        "interval_ms": 60,
        "beep_count": 10,
        "volume": 1.0,
        "description": "EEW Alert - Strong/Severe Shaking Expected",
        "label": "緊急地震速報（警報）"
    }
}

def get_eew_alert_level(magnitude, distance_km):
    """Determine EEW alert level based on magnitude and distance"""
    # Estimate shaking intensity at distance
    # MMI decreases roughly 1 unit per 2x distance
    if magnitude >= 7.5:
        if distance_km < 30:
            return "level3"
        elif distance_km < 60:
            return "level2"
        else:
            return "level1"
    elif magnitude >= 6.5:
        if distance_km < 40:
            return "level3"
        elif distance_km < 80:
            return "level2"
        else:
            return "level1"
    elif magnitude >= 5.0:
        if distance_km < 50:
            return "level2"
        else:
            return "level1"
    return None

def calculate_wave_arrivals(epicenter_lat, epicenter_lon, depth_km):
    """
    Calculate P-wave and S-wave arrival times to major global cities (compact version)
    
    Args:
        epicenter_lat: Earthquake latitude
        epicenter_lon: Earthquake longitude
        depth_km: Earthquake depth
    
    Returns:
        Dictionary with arrival times and estimated intensities
    """
    import math
    
    # Global major cities - compact format (lat, lon)
    CITIES = {
        # Asia-Pacific
        "Tokyo": (35.68, 139.65), "Sydney": (-33.87, 151.21), "Bangkok": (13.73, 100.49),
        "Manila": (14.60, 120.98), "Singapore": (1.35, 103.82), "Hong Kong": (22.40, 114.11),
        "Seoul": (37.57, 126.98), "Jakarta": (-6.20, 106.80), "Mumbai": (19.08, 72.88),
        # Europe
        "London": (51.51, -0.13), "Paris": (48.86, 2.35), "Berlin": (52.52, 13.41),
        "Rome": (41.90, 12.50), "Madrid": (40.42, -3.70),
        # Americas
        "New York": (40.71, -74.01), "Los Angeles": (34.05, -118.24), "Mexico City": (19.43, -99.13),
        "Toronto": (43.65, -79.38), "São Paulo": (-23.55, -46.63),
        # Middle East/Africa
        "Dubai": (25.20, 55.27), "Cairo": (30.04, 31.24), "Johannesburg": (-26.20, 28.05)
    }
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # km
        lat1_r, lat2_r = map(math.radians, [lat1, lat2])
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dLon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    arrivals = {}
    for city, (lat, lon) in CITIES.items():
        dist_km = haversine(epicenter_lat, epicenter_lon, lat, lon)
        total_dist = math.sqrt(dist_km**2 + depth_km**2)
        p_time = total_dist / 6.0
        s_time = total_dist / 3.5
        dist_mi = dist_km * 0.621371
        
        arrivals[city] = {
            "distance": f"{dist_km:.0f}km / {dist_mi:.0f}mi",
            "countdown": max(0, round(s_time - 2, 1))
        }
    
    return arrivals

def get_alert_level(magnitude):
    """Determine alert level based on magnitude"""
    if magnitude >= 7.0:
        return "critical"
    elif magnitude >= 6.0:
        return "high"
    elif magnitude >= 5.0:
        return "moderate"
    elif magnitude >= 4.0:
        return "low"
    return None

def get_tsunami_alert_level(warning_level_str):
    """Convert tsunami warning level to alert key"""
    level_map = {
        "MAJOR_WARNING": "major_warning",
        "WARNING": "warning",
        "ADVISORY": "advisory",
        "NO_WARNING": None
    }
    return level_map.get(warning_level_str, None)

def generate_sound_data(frequency, duration_ms):
    """Generate sound data for web audio (return frequency and duration for client to play)"""
    return {
        "frequency": frequency,
        "duration_ms": duration_ms,
        "type": "sine"
    }


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    """Serve static files (JS, CSS, etc)"""
    if os.path.exists(os.path.join(".", filename)):
        return send_from_directory(".", filename)
    return jsonify({"error": "Not found"}), 404

@app.route("/proxy/stations/iris")
def iris_stations():
    url = (
        "https://service.iris.edu/fdsnws/station/1/query"
        "?level=station"
        "&format=text"
        "&nodata=404"
    )

    headers = {
        "User-Agent": "OpenSeismo-Lite/1.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=25)
        return Response(
            r.text,
            status=r.status_code,
            content_type="text/plain"
        )
    except Exception as e:
        return Response(str(e), status=502, content_type="text/plain")


@app.route("/proxy/stations/geofon")
def geofon_stations():
    url = (
        "https://geofon.gfz-potsdam.de/fdsnws/station/1/query"
        "?level=station"
        "&format=text"
        "&nodata=404"
    )

    headers = {
        "User-Agent": "OpenSeismo-Lite/1.0"
    }

    try:
        r = requests.get(url, headers=headers, timeout=25)
        return Response(
            r.text,
            status=r.status_code,
            content_type="text/plain"
        )
    except Exception as e:
        return Response(str(e), status=502, content_type="text/plain")


@app.route("/api/tsunami/evaluate", methods=["POST"])
def evaluate_tsunami():
    """
    Evaluate tsunami risk for an earthquake
    Expected JSON: {
        "magnitude": float,
        "depth_km": float,
        "latitude": float,
        "longitude": float,
        "time": string (ISO format)
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['magnitude', 'depth_km', 'latitude', 'longitude']):
            return jsonify({"error": "Missing required fields"}), 400
        
        result = TsunamiWarningSystem.evaluate_earthquake(
            magnitude=data['magnitude'],
            depth_km=data['depth_km'],
            latitude=data['latitude'],
            longitude=data['longitude']
        )
        
        # Add metadata
        result['time'] = data.get('time', '')
        result['analysis_time'] = __import__('datetime').datetime.utcnow().isoformat()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tsunami/info")
def tsunami_info():
    """Get tsunami warning system information and thresholds"""
    info = {
        "system": "JMA-inspired Tsunami Warning System",
        "warning_levels": {
            "MAJOR_WARNING": {
                "description": "Major tsunami warning - expect destructive waves",
                "wave_height_threshold_m": 3.0,
                "color": "#DC2626"
            },
            "WARNING": {
                "description": "Tsunami warning - dangerous waves expected",
                "wave_height_threshold_m": 1.0,
                "color": "#EA580C"
            },
            "ADVISORY": {
                "description": "Tsunami advisory - minor waves may occur",
                "wave_height_threshold_m": 0.5,
                "color": "#F59E0B"
            },
            "NO_WARNING": {
                "description": "No tsunami threat detected",
                "wave_height_threshold_m": 0.0,
                "color": "#10B981"
            }
        },
        "monitored_regions": [
            "Japan", "Indonesia", "Philippines", "New Zealand",
            "US West Coast", "Chile", "Thailand"
        ],
        "minimum_magnitude_for_warning": 6.5,
        "note": "This is an educational tsunami warning system and NOT an official EEW/TWS system"
    }
    return jsonify(info), 200


@app.route("/api/intensity/mmi-shindo", methods=["POST"])
def calculate_intensity():
    """
    Calculate MMI and Shindo intensities for an earthquake
    Expected JSON: {
        "magnitude": float,
        "depth_km": float,
        "latitude": float,
        "longitude": float,
        "distance_km": float (optional, default 0.1)
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['magnitude', 'depth_km', 'latitude', 'longitude']):
            return jsonify({"error": "Missing required fields: magnitude, depth_km, latitude, longitude"}), 400
        
        magnitude = data['magnitude']
        depth_km = data['depth_km']
        latitude = data['latitude']
        longitude = data['longitude']
        distance_km = data.get('distance_km', 0.1)
        
        # Classify fault type
        fault_type, fault_zone_info = IntensityCalculator.classify_fault_type(latitude, longitude, depth_km)
        
        # Calculate intensities
        mmi = IntensityCalculator.calculate_mmi(magnitude, depth_km, distance_km, fault_type)
        shindo = IntensityCalculator.calculate_shindo(magnitude, depth_km, distance_km, fault_type)
        
        # Get scale information
        mmi_scale = IntensityCalculator.get_mmi_scale(mmi)
        shindo_scale = IntensityCalculator.get_shindo_scale(shindo)
        
        result = {
            "magnitude": magnitude,
            "depth_km": depth_km,
            "distance_km": distance_km,
            "latitude": latitude,
            "longitude": longitude,
            "fault_type": fault_type.value,
            "fault_zone": {
                "type": fault_zone_info.fault_type.value,
                "color": fault_zone_info.color,
                "description": fault_zone_info.description,
                "typical_depth_range": f"{fault_zone_info.typical_depth_min}-{fault_zone_info.typical_depth_max} km"
            },
            "mmi": {
                "value": round(mmi, 2),
                "scale": mmi_scale.name,
                "description": mmi_scale.description,
                "color": mmi_scale.color,
                "integer": int(round(mmi))
            },
            "shindo": {
                "value": round(shindo, 2),
                "scale": shindo_scale.name,
                "description": shindo_scale.description,
                "color": shindo_scale.color
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/intensity/report", methods=["POST"])
def intensity_report():
    """
    Generate comprehensive intensity report for an earthquake
    Expected JSON: {
        "magnitude": float,
        "depth_km": float,
        "latitude": float,
        "longitude": float
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['magnitude', 'depth_km', 'latitude', 'longitude']):
            return jsonify({"error": "Missing required fields"}), 400
        
        report = IntensityCalculator.get_intensity_report(
            magnitude=data['magnitude'],
            depth_km=data['depth_km'],
            latitude=data['latitude'],
            longitude=data['longitude']
        )
        
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/intensity/grid", methods=["POST"])
def intensity_grid():
    """
    Calculate intensity grid around epicenter
    Expected JSON: {
        "magnitude": float,
        "depth_km": float,
        "latitude": float,
        "longitude": float,
        "grid_size_km": int (optional, default 50),
        "max_distance_km": int (optional, default 500)
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['magnitude', 'depth_km', 'latitude', 'longitude']):
            return jsonify({"error": "Missing required fields"}), 400
        
        grid_points = IntensityCalculator.calculate_intensity_grid(
            magnitude=data['magnitude'],
            depth_km=data['depth_km'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            grid_size_km=data.get('grid_size_km', 50),
            max_distance_km=data.get('max_distance_km', 500)
        )
        
        return jsonify({
            "magnitude": data['magnitude'],
            "depth_km": data['depth_km'],
            "latitude": data['latitude'],
            "longitude": data['longitude'],
            "grid_points": grid_points,
            "point_count": len(grid_points)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/intensity/info")
def intensity_info():
    """Get intensity scale information and descriptions"""
    return jsonify({
        "mmi_scale": {
            "name": "Modified Mercalli Intensity Scale",
            "description": "Measures the effects of earthquakes on the Earth's surface, human beings, buildings, and other structures",
            "range": "I (not felt) to XII (total destruction)",
            "levels": {
                "I": {"value": 1, "description": "Not felt", "color": "#ffffff"},
                "II": {"value": 2, "description": "Weak - Felt indoors", "color": "#ccccff"},
                "III": {"value": 3, "description": "Weak - Felt indoors, vibrations like passing truck", "color": "#99ccff"},
                "IV": {"value": 4, "description": "Light - Indoor objects rattle, felt outdoors", "color": "#66ccff"},
                "V": {"value": 5, "description": "Moderate - Felt by most, some dishes break", "color": "#00ccff"},
                "VI": {"value": 6, "description": "Strong - Felt by all, minor damage", "color": "#ffff00"},
                "VII": {"value": 7, "description": "Very Strong - Considerable damage, everyone runs outside", "color": "#ffcc00"},
                "VIII": {"value": 8, "description": "Severe - Structural damage, partial collapse", "color": "#ff9900"},
                "IX": {"value": 9, "description": "Violent - Considerable damage, ground cracking", "color": "#ff6600"},
                "X": {"value": 10, "description": "Extreme - Most buildings destroyed", "color": "#ff3300"},
                "XI": {"value": 11, "description": "Extreme - Few buildings standing", "color": "#ff0000"},
                "XII": {"value": 12, "description": "Extreme - Total destruction", "color": "#cc0000"}
            }
        },
        "shindo_scale": {
            "name": "Japan Meteorological Agency Shindo Scale",
            "description": "Japanese seismic intensity scale used by the Japan Meteorological Agency",
            "range": "0 (not felt) to 7 (extreme destruction)",
            "levels": {
                "0": {"value": 0, "description": "Not felt", "color": "#ffffff"},
                "1": {"value": 1, "description": "Weak - Felt indoors", "color": "#ccccff"},
                "2": {"value": 2, "description": "Light - Objects rattle", "color": "#66ccff"},
                "3": {"value": 3, "description": "Moderate - Most people frightened", "color": "#00ccff"},
                "4": {"value": 4, "description": "Strong - Most buildings slightly damaged", "color": "#ffff00"},
                "5-": {"value": 5.0, "description": "Strong - Many buildings damaged", "color": "#ffcc00"},
                "5+": {"value": 5.5, "description": "Strong+ - Considerable damage", "color": "#ff9900"},
                "6-": {"value": 6.0, "description": "Very Strong - Many buildings collapse", "color": "#ff6600"},
                "6+": {"value": 6.5, "description": "Very Strong+ - Most buildings collapse", "color": "#ff3300"},
                "7": {"value": 7.0, "description": "Extreme - Total/near total destruction", "color": "#cc0000"}
            }
        },
        "fault_zones": {
            "subduction": {
                "color": "#0066cc",
                "description": "Subduction Zone - High tsunami and magnitude risk",
                "typical_depth": "0-700 km",
                "examples": ["Japan Trench", "Peru-Chile Trench", "Mariana Trench"]
            },
            "transform": {
                "color": "#ff6600",
                "description": "Transform Fault - Strong lateral motion",
                "typical_depth": "0-50 km",
                "examples": ["San Andreas Fault", "Alpine Fault (NZ)"]
            },
            "reverse_thrust": {
                "color": "#cc0000",
                "description": "Reverse-Thrust Fault - Vertical uplift, potential tsunami",
                "typical_depth": "0-300 km",
                "examples": ["Himalayas", "Zagros Mountains"]
            },
            "normal": {
                "color": "#00cc66",
                "description": "Normal Fault - Extensional stress",
                "typical_depth": "0-30 km",
                "examples": ["East African Rift"]
            },
            "divergent": {
                "color": "#66ccff",
                "description": "Divergent Boundary - Seafloor spreading",
                "typical_depth": "0-20 km",
                "examples": ["Mid-Atlantic Ridge", "East Pacific Rise"]
            },
            "convergent": {
                "color": "#9900cc",
                "description": "Convergent Boundary - Compression zone",
                "typical_depth": "0-250 km",
                "examples": ["Alpine Belt"]
            },
            "strike_slip": {
                "color": "#ffcc00",
                "description": "Strike-Slip Fault - Horizontal motion",
                "typical_depth": "0-30 km",
                "examples": ["San Andreas", "Dead Sea Transform"]
            }
        }
    }), 200


@app.route("/api/intensity/agency-summary", methods=["POST"])
def process_agency_summary():
    """
    Process intensity calculations from seismic agency summaries
    Supports USGS, ESMC, CSEM, and JMA agency formats
    
    Expected JSON: {
        "agency": "USGS|ESMC|CSEM|JMA",
        "magnitude": float,
        "depth_km": float,
        "latitude": float,
        "longitude": float,
        "summary": {...}  # Agency-specific summary dict
    }
    
    For USGS:
        - max_mmi_intensity: int or Roman numeral string
        - impact_description: string ("weak", "light", "moderate", etc.)
    
    For ESMC (European Seismic Commission):
        - ems98_intensity: Roman numeral (I-XII)
        - damage_grade: int (1-5)
    
    For CSEM (Swiss):
        - csem_intensity: numeric value
        - felt_reports: count of reports
        - macroseismic_data: optional dict
    
    For JMA (Japan):
        - shindo_scale: numeric (0-7) or string
        - max_shindo_location: string
    """
    try:
        data = request.get_json()
        
        required_fields = ['agency', 'magnitude', 'depth_km', 'latitude', 'longitude', 'summary']
        if not all(k in data for k in required_fields):
            return jsonify({"error": f"Missing required fields: {', '.join(required_fields)}"}), 400
        
        result = AgencySummaryProcessor.process_agency_summary(
            agency_name=data['agency'],
            magnitude=data['magnitude'],
            depth_km=data['depth_km'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            agency_summary=data['summary']
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/intensity/agency-info")
def agency_info():
    """Get information about supported seismic agencies and their intensity scales"""
    return jsonify({
        "supported_agencies": {
            "USGS": {
                "name": "United States Geological Survey",
                "description": "Operates ShakeMap for earthquake early warning and intensity estimation",
                "region": "Primarily USA and global coverage",
                "intensity_scale": "MMI (Modified Mercalli Intensity)",
                "data_fields": ["max_mmi_intensity", "impact_description"]
            },
            "ESMC": {
                "name": "European Seismic Commission",
                "description": "European earthquake monitoring and intensity assessment",
                "region": "Europe and Mediterranean",
                "intensity_scale": "EMS-98 (European Macroseismic Scale)",
                "data_fields": ["ems98_intensity", "damage_grade", "affected_area"]
            },
            "CSEM": {
                "name": "Swiss Seismological Commission",
                "description": "Swiss and Alpine earthquake monitoring",
                "region": "Switzerland and Alpine region",
                "intensity_scale": "Swiss intensity scale (1-12)",
                "data_fields": ["csem_intensity", "felt_reports", "macroseismic_data"]
            },
            "JMA": {
                "name": "Japan Meteorological Agency",
                "description": "Official earthquake and tsunami early warning for Japan",
                "region": "Japan and surrounding regions",
                "intensity_scale": "Shindo Scale (0-7)",
                "data_fields": ["shindo_scale", "max_shindo_location", "estimated_seismic_intensity"]
            }
        },
        "note": "This endpoint allows unified processing of intensity data from multiple agencies"
    }), 200


@app.route("/api/location/search", methods=["GET", "POST"])
def location_search():
    """
    Search for locations by name or coordinates
    Expected parameters:
    - GET: query=<location name or "lat,lon">
    - POST JSON: {"query": "<location name or coordinates>"}
    """
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            query = data.get('query', '').strip()
        else:
            query = request.args.get('query', '').strip()
        
        if not query:
            return jsonify({"error": "Query parameter required"}), 400
        
        result = LocationSearcher.search(query)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/location/info", methods=["POST"])
def location_info():
    """
    Get comprehensive location information
    Expected JSON: {
        "latitude": float,
        "longitude": float
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['latitude', 'longitude']):
            return jsonify({"error": "latitude and longitude required"}), 400
        
        info = LocationSearcher.get_location_info(
            latitude=data['latitude'],
            longitude=data['longitude']
        )
        
        return jsonify(info), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/location/nearby", methods=["POST"])
def location_nearby():
    """
    Find nearby cities and tectonic regions
    Expected JSON: {
        "latitude": float,
        "longitude": float
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['latitude', 'longitude']):
            return jsonify({"error": "latitude and longitude required"}), 400
        
        nearby = LocationSearcher.search_by_coordinates(
            latitude=data['latitude'],
            longitude=data['longitude']
        )
        
        return jsonify(nearby), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/location/suggestions")
def location_suggestions():
    """
    Get list of major cities for autocomplete suggestions
    """
    try:
        suggestions = []
        
        # Add major cities
        for city in LocationSearcher.MAJOR_CITIES:
            suggestions.append({
                'name': city['name'],
                'type': 'city',
                'country': city['country']
            })
        
        # Add tectonic regions
        for region in LocationSearcher.TECTONIC_REGIONS:
            suggestions.append({
                'name': region['name'],
                'type': 'tectonic_region'
            })
        
        return jsonify({
            'suggestions': sorted(suggestions, key=lambda x: x['name']),
            'total_count': len(suggestions)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/earthquakes/live", methods=["GET"])
def get_live_earthquakes():
    """
    Get current live earthquakes with ShakeMax intensities and hexagon grids
    Query parameters:
        - magnitude_filter: Minimum magnitude (default: 4.5)
        - enrich: Whether to include ShakeMax and hexagon data (default: true)
    """
    try:
        magnitude_filter = request.args.get('magnitude_filter', 4.5, type=float)
        enrich = request.args.get('enrich', 'true').lower() == 'true'
        
        earthquakes = LiveEarthquakeDetector.get_live_earthquakes(
            magnitude_filter=magnitude_filter,
            enrich=enrich
        )
        
        return jsonify({
            "status": "success",
            "count": len(earthquakes),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            "earthquakes": earthquakes
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e), "count": 0, "earthquakes": []}), 500


@app.route("/api/earthquakes/live/<eq_id>", methods=["GET"])
def get_earthquake_detail(eq_id):
    """
    Get detailed information for a specific earthquake
    """
    try:
        earthquakes = LiveEarthquakeDetector.get_live_earthquakes(magnitude_filter=0, enrich=True)
        
        for eq in earthquakes:
            if eq['id'] == eq_id:
                return jsonify({
                    "status": "success",
                    "earthquake": eq
                }), 200
        
        return jsonify({"error": "Earthquake not found"}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/earthquakes/shakemax-grid/<eq_id>", methods=["GET"])
def get_shakemax_grid(eq_id):
    """
    Get ShakeMax hexagon grid for a specific earthquake
    Query parameters:
        - grid_radius: Radius in km (default: 300)
        - hex_size: Hexagon size in km (default: 15)
    """
    try:
        earthquakes = LiveEarthquakeDetector.get_live_earthquakes(magnitude_filter=0, enrich=False)
        
        eq = None
        for earthquake in earthquakes:
            if earthquake['id'] == eq_id:
                eq = earthquake
                break
        
        if not eq:
            return jsonify({"error": "Earthquake not found"}), 404
        
        grid_radius = request.args.get('grid_radius', 300, type=int)
        hex_size = request.args.get('hex_size', 15, type=int)
        
        hexagons = LiveEarthquakeDetector.generate_hexagon_grid(
            latitude=eq['latitude'],
            longitude=eq['longitude'],
            magnitude=eq['magnitude'],
            depth_km=eq['depth_km'],
            grid_radius_km=grid_radius,
            hex_size_km=hex_size
        )
        
        return jsonify({
            "status": "success",
            "earthquake_id": eq_id,
            "magnitude": eq['magnitude'],
            "latitude": eq['latitude'],
            "longitude": eq['longitude'],
            "depth_km": eq['depth_km'],
            "hexagon_count": len(hexagons),
            "grid_radius_km": grid_radius,
            "hexagon_size_km": hex_size,
            "hexagons": hexagons
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/earthquakes/shakemax-levels", methods=["GET"])
def get_shakemax_levels():
    """
    Get ShakeMax intensity level definitions for legend display
    """
    try:
        return jsonify({
            "status": "success",
            "levels": LiveEarthquakeDetector.SHAKEMAX_LEVELS
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= MISSING API ENDPOINTS FOR UI =============

@app.route("/api/earthquakes")
def get_earthquakes():
    """Get live earthquakes from USGS with fallback to mock data"""
    try:
        mag_filter = request.args.get('mag_filter', default=0, type=float)
        earthquakes = LiveEarthquakeDetector.get_live_earthquakes(magnitude_filter=mag_filter, enrich=False)
        
        features = []
        for eq in earthquakes:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [eq['longitude'], eq['latitude'], eq['depth_km']]
                },
                "properties": {
                    "id": eq['id'],
                    "mag": eq['magnitude'],
                    "place": eq['place'],
                    "time": int(eq['time_ms']),
                    "url": eq['url'],
                    "felt": eq['felt_reports'],
                    "tsunami": eq['tsunami'],
                    "sources": eq['sources'],
                    "risk_assessment": {
                        "level": "moderate" if eq['magnitude'] < 6 else "high",
                        "score": min(10, int(eq['magnitude'] * 1.5)),
                        "description": "Seismic activity detected"
                    }
                }
            })
        
        # Fallback to mock earthquakes if API returns nothing
        if not features:
            mock_earthquakes = [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [142.47, 38.27, 15]},
                    "properties": {
                        "id": "us1000mock1",
                        "mag": 5.8,
                        "place": "Eastern Honshu, Japan",
                        "time": 1717604400000,
                        "url": "https://earthquake.usgs.gov/earthquakes/events/us1000mock1/",
                        "felt": 2847,
                        "tsunami": True,
                        "sources": "us,jp",
                        "mmi": 7.2,
                        "cdi": 5.8,
                        "alert": "yellow",
                        "status": "reviewed",
                        "risk_assessment": {"level": "high", "score": 8, "description": "Moderate seismic activity"}
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [95.28, 28.45, 32]},
                    "properties": {
                        "id": "us1000mock2",
                        "mag": 5.2,
                        "place": "Nepal-India border region",
                        "time": 1717590000000,
                        "url": "https://earthquake.usgs.gov/earthquakes/events/us1000mock2/",
                        "felt": 845,
                        "tsunami": False,
                        "sources": "us,neic",
                        "mmi": 6.1,
                        "cdi": 5.2,
                        "alert": "green",
                        "status": "reviewed",
                        "risk_assessment": {"level": "moderate", "score": 7, "description": "Moderate seismic activity"}
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-73.98, -30.22, 18]},
                    "properties": {
                        "id": "us1000mock3",
                        "mag": 4.9,
                        "place": "Argentina - Chile border",
                        "time": 1717575600000,
                        "url": "https://earthquake.usgs.gov/earthquakes/events/us1000mock3/",
                        "felt": 234,
                        "tsunami": False,
                        "sources": "us",
                        "mmi": 5.8,
                        "cdi": 4.9,
                        "alert": "green",
                        "status": "reviewed",
                        "risk_assessment": {"level": "moderate", "score": 6, "description": "Moderate seismic activity"}
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-120.47, 34.95, 8]},
                    "properties": {
                        "id": "us1000mock4",
                        "mag": 6.1,
                        "place": "Central California",
                        "time": 1717561200000,
                        "url": "https://earthquake.usgs.gov/earthquakes/events/us1000mock4/",
                        "felt": 5621,
                        "tsunami": False,
                        "sources": "us,ci",
                        "mmi": 7.8,
                        "cdi": 6.1,
                        "alert": "orange",
                        "status": "reviewed",
                        "risk_assessment": {"level": "high", "score": 9, "description": "High seismic activity"}
                    }
                }
            ]
            features = mock_earthquakes
        
        return jsonify({"type": "FeatureCollection", "features": features}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stations")
def get_stations():
    """Get normalized seismic station network data."""
    try:
        network = request.args.get("network")
        country = request.args.get("country")
        region = request.args.get("region")
        status = request.args.get("status")
        channel = request.args.get("channel")
        tag = request.args.get("tag")
        recent_minutes = request.args.get("recent_minutes", type=int)
        active_recent = request.args.get("active_recent", default="").lower() in {"1", "true", "yes", "on"}

        stations = station_manager.filter_stations(
            network=network,
            country=country,
            region=region,
            status=status,
            channel=channel,
            tag=tag,
            recent_minutes=recent_minutes if active_recent else None,
            active_only=active_recent,
        )

        return jsonify({"count": len(stations), "stations": stations}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/volcanoes")
def get_volcanoes():
    """Get active volcano monitoring data"""
    try:
        volcanoes = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [139.4928, 35.3607]},
                    "properties": {"name": "Mount Fuji", "status": "dormant", "alert_level": 1, "last_eruption": "1707"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [122.7597, 5.3521]},
                    "properties": {"name": "Mount Pinatubo", "status": "active", "alert_level": 2, "last_eruption": "1991"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [103.8343, 3.2675]},
                    "properties": {"name": "Mount Merapi", "status": "active", "alert_level": 3, "last_eruption": "2010"}
                }
            ]
        }
        return jsonify(volcanoes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/faults")
def get_faults():
    """Get major fault line data"""
    try:
        faults = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-115.5, 32.5]},
                    "properties": {"name": "San Andreas Fault", "type": "transform", "activity": "high"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [142.5, 38.5]},
                    "properties": {"name": "Japan Trench", "type": "subduction", "activity": "very_high"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [95.5, -4.5]},
                    "properties": {"name": "Sumatra Fault", "type": "strike_slip", "activity": "very_high"}
                }
            ]
        }
        return jsonify(faults), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/disaster-risks")
def get_disaster_risks():
    """Get disaster risk zones"""
    try:
        risks = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [139.7674, 35.6764]},
                    "properties": {"name": "Tokyo High Risk", "risk_level": "high", "hazard": "earthquake"}
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [121.5645, 25.0443]},
                    "properties": {"name": "Taiwan Moderate Risk", "risk_level": "moderate", "hazard": "earthquake"}
                }
            ]
        }
        return jsonify(risks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/safety-summary")
def get_safety_summary():
    """Get overall safety summary"""
    try:
        summary = {
            "summary": [
                {
                    "kind": "Seismic Activity",
                    "risk_level": "moderate",
                    "name": "Global seismic activity elevated",
                    "score": 6,
                    "safety": [
                        "Monitor official earthquake agencies",
                        "Review preparedness plans in seismic zones"
                    ]
                },
                {
                    "kind": "Tsunami Risk",
                    "risk_level": "low",
                    "name": "No active tsunami threats",
                    "score": 2,
                    "safety": [
                        "Coastal monitoring systems operational",
                        "Early warning dissemination ready"
                    ]
                },
                {
                    "kind": "Infrastructure",
                    "risk_level": "moderate",
                    "name": "Standard preparedness recommended",
                    "score": 5,
                    "safety": [
                        "Regular equipment maintenance schedules",
                        "Test emergency protocols quarterly"
                    ]
                }
            ]
        }
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= LIVE UPDATE ENDPOINTS WITH SOUNDS & NOTIFICATIONS =============

@app.route("/api/live-earthquakes/stream")
def live_earthquakes_stream():
    """
    Server-Sent Events (SSE) endpoint for real-time earthquake updates
    Client subscribes and receives live updates with sound alerts and tsunami warnings
    DISABLED: Use /api/earthquakes/new-since endpoint instead to prevent spam
    """
    # This endpoint is disabled to prevent excessive polling and spam
    # Use /api/earthquakes/new-since for polling with manual control
    return jsonify({
        "error": "This endpoint has been disabled to prevent excessive polling",
        "use_instead": "/api/earthquakes/new-since",
        "note": "Call /api/earthquakes/new-since with since_timestamp for live updates"
    }), 200


@app.route("/api/sound-alerts/config")
def sound_alerts_config():
    """
    Get sound alert configuration for all earthquake severity levels
    Clients use this to generate appropriate alert tones
    """
    try:
        return jsonify({
            "sound_alerts": SOUND_ALERTS,
            "supported_alert_types": ["earthquake", "tsunami", "aftershock"],
            "frequency_range": {
                "min_hz": 440,
                "max_hz": 1046,
                "notes": "A4 to C6 musical notes"
            },
            "client_note": "Use Web Audio API to generate sounds. Frequencies and durations provided for sine wave generation."
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tsunami-alerts/config")
def tsunami_alerts_config():
    """
    Get tsunami alert sound configuration
    Clients use this to generate Japanese-style siren alerts
    """
    try:
        return jsonify({
            "tsunami_alerts": TSUNAMI_ALERTS,
            "siren_info": {
                "type": "frequency sweep",
                "description": "Japanese-style tsunami warning siren with rising/falling frequency modulation",
                "frequency_sweep": {
                    "min_hz": 600,
                    "max_hz": 1200,
                    "notes": "Mimics traditional Japanese air raid sirens"
                }
            },
            "client_note": "Use Web Audio API with OscillatorNode frequency modulation. Implement linear frequency sweep from start to end frequency over specified duration."
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/eew-alerts/config")
def eew_alerts_config():
    """
    Get Earthquake Early Warning (EEW) alert configuration
    Clients use this to generate rapid beep sequence alerts (Japanese style)
    """
    try:
        return jsonify({
            "eew_alerts": EEW_ALERTS,
            "eew_info": {
                "type": "rapid beep sequence",
                "description": "Japanese-style Earthquake Early Warning (緊急地震速報) rapid alert beeps",
                "trigger_magnitude": 5.0,
                "purpose": "Alerts user to impending seismic shaking before S-waves arrive (seconds to tens of seconds advance warning)"
            },
            "wave_info": {
                "p_wave_velocity_kms": 6.0,
                "s_wave_velocity_kms": 3.5,
                "notes": "P-waves detected and warning issued ~2s later, giving ~5-30s warning before destructive S-wave arrival"
            },
            "client_note": "Use Web Audio API with rapid beep sequences. Implement beep_count beeps at specified frequency with timing intervals."
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/notifications/send", methods=["POST"])
def send_notification():
    """
    Send browser notifications for earthquake alerts
    Expected JSON: {
        "title": string,
        "body": string,
        "icon": string (optional),
        "sound_enabled": boolean
    }
    """
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['title', 'body']):
            return jsonify({"error": "title and body required"}), 400
        
        notification = {
            "title": data['title'],
            "body": data['body'],
            "icon": data.get('icon', "/static/earthquake-icon.png"),
            "badge": data.get('badge', "/static/earthquake-badge.png"),
            "tag": data.get('tag', 'earthquake-alert'),
            "requireInteraction": True,
            "actions": [
                {"action": "view", "title": "View Details"},
                {"action": "dismiss", "title": "Dismiss"}
            ]
        }
        
        return jsonify({
            "notification": notification,
            "permissions_needed": "notifications",
            "note": "Send this data to Notification API on client side"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/earthquakes/new-since", methods=["POST"])
def get_new_earthquakes():
    """
    Get earthquakes detected since a specific time
    Used for client-side live update polling with fallback to SSE
    
    Expected JSON: {
        "since_timestamp": ISO 8601 timestamp,
        "min_magnitude": float (optional, default 4.0)
    }
    """
    try:
        data = request.get_json()
        
        if 'since_timestamp' not in data:
            return jsonify({"error": "since_timestamp required"}), 400
        
        since_time = datetime.fromisoformat(data['since_timestamp'].replace('Z', '+00:00'))
        min_magnitude = data.get('min_magnitude', 4.0)
        
        all_earthquakes = LiveEarthquakeDetector.get_live_earthquakes(
            magnitude_filter=min_magnitude,
            enrich=True
        )
        
        # Filter for earthquakes detected after since_time
        new_earthquakes = []
        for eq in all_earthquakes:
            eq_time = datetime.fromisoformat(eq.get('time_utc', '').replace('Z', '+00:00')) if eq.get('time_utc') else datetime.utcnow()
            if eq_time > since_time:
                alert_level = get_alert_level(eq['magnitude'])
                eq['alert_level'] = alert_level
                eq['sound_alert'] = SOUND_ALERTS.get(alert_level)
                new_earthquakes.append(eq)
        
        return jsonify({
            "count": len(new_earthquakes),
            "since": since_time.isoformat(),
            "current_time": datetime.utcnow().isoformat(),
            "earthquakes": sorted(new_earthquakes, key=lambda x: x['magnitude'], reverse=True)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alerts/preferences", methods=["GET", "POST"])
def alert_preferences():
    """
    Get or set user preferences for earthquake alerts
    Stores preferences for sound, notifications, magnitude thresholds, etc.
    
    GET: Returns current preferences
    POST: Updates preferences
    """
    try:
        if request.method == "GET":
            # Return default preferences
            return jsonify({
                "sound_enabled": True,
                "notification_enabled": True,
                "min_magnitude_threshold": 4.5,
                "alert_levels": ["low", "moderate", "high", "critical"],
                "sound_volume": 0.7,
                "auto_mute_after_seconds": 60,
                "vibration_enabled": True,
                "region_filter": None
            }), 200
        
        else:  # POST
            data = request.get_json()
            
            # Validate preferences
            valid_prefs = {
                "sound_enabled": bool(data.get('sound_enabled', True)),
                "notification_enabled": bool(data.get('notification_enabled', True)),
                "min_magnitude_threshold": float(data.get('min_magnitude_threshold', 4.5)),
                "alert_levels": data.get('alert_levels', ["low", "moderate", "high", "critical"]),
                "sound_volume": max(0, min(1, float(data.get('sound_volume', 0.7)))),
                "auto_mute_after_seconds": int(data.get('auto_mute_after_seconds', 60)),
                "vibration_enabled": bool(data.get('vibration_enabled', True)),
                "region_filter": data.get('region_filter')
            }
            
            return jsonify({
                "status": "saved",
                "preferences": valid_prefs,
                "note": "Preferences saved on client side (use localStorage in browser)"
            }), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("OpenSeismo Lite running at: http://localhost:5000")
    # CRITICAL: Never use debug=True or use_reloader=True in production builds
    # These cause infinite tab spawning in PyInstaller executables
    app.run(
        host="127.0.0.1", 
        port=5000, 
        debug=False,           # MUST be False
        use_reloader=False,    # MUST be False
        use_debugger=False     # Extra safety
    )
