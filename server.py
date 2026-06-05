from flask import Flask, Response, send_from_directory, request, jsonify
import requests
import json
import os
from tsunami_warning import TsunamiWarningSystem, format_tsunami_report
from intensity_calculator import IntensityCalculator, FaultType
from location_search import LocationSearcher
from live_earthquake_detector import LiveEarthquakeDetector

app = Flask(__name__, static_folder="static", static_url_path="/static")

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
    """Get seismic station network data"""
    try:
        # Comprehensive global station network
        stations = [
            {"code": "NII", "name": "Tokyo (NIED)", "network": "JMA", "country": "Japan", "health": "operational", "latency_seconds": 0.2, "noise_level": 12, "signal_quality": "excellent", "coverage_radius_km": 150, "lon": 139.7674, "lat": 35.6764, "arrival": {"distance_km": 450, "distance_deg": 4.2, "p_wave_seconds": 45, "s_wave_seconds": 78, "surface_wave_seconds": 120}},
            {"code": "TAP", "name": "Taipei (CWB)", "network": "CWB", "country": "Taiwan", "health": "operational", "latency_seconds": 0.3, "noise_level": 15, "signal_quality": "excellent", "coverage_radius_km": 120, "lon": 121.5645, "lat": 25.0443, "arrival": {"distance_km": 520, "distance_deg": 4.8, "p_wave_seconds": 52, "s_wave_seconds": 90, "surface_wave_seconds": 140}},
            {"code": "JAK", "name": "Jakarta (BMKG)", "network": "BMKG", "country": "Indonesia", "health": "operational", "latency_seconds": 0.4, "noise_level": 18, "signal_quality": "good", "coverage_radius_km": 100, "lon": 106.8456, "lat": -6.2088},
            {"code": "LAX", "name": "Los Angeles (USGS)", "network": "USGS", "country": "USA", "health": "operational", "latency_seconds": 0.2, "noise_level": 14, "signal_quality": "excellent", "coverage_radius_km": 140, "lon": -118.2437, "lat": 34.0522},
            {"code": "PHL", "name": "Philadelphia (USGS)", "network": "USGS", "country": "USA", "health": "operational", "latency_seconds": 0.2, "noise_level": 16, "signal_quality": "good", "coverage_radius_km": 130, "lon": -75.1652, "lat": 40.2206},
            {"code": "KBL", "name": "Kabul (GSC)", "network": "GSC", "country": "Afghanistan", "health": "operational", "latency_seconds": 0.5, "noise_level": 22, "signal_quality": "fair", "coverage_radius_km": 110, "lon": 69.1761, "lat": 34.5256},
            {"code": "SEO", "name": "Seoul (KMA)", "network": "KMA", "country": "South Korea", "health": "operational", "latency_seconds": 0.2, "noise_level": 11, "signal_quality": "excellent", "coverage_radius_km": 140, "lon": 126.978, "lat": 37.5665},
            {"code": "MNL", "name": "Manila (PHIVOLCS)", "network": "PHIVOLCS", "country": "Philippines", "health": "operational", "latency_seconds": 0.3, "noise_level": 19, "signal_quality": "good", "coverage_radius_km": 115, "lon": 121.0437, "lat": 14.5995},
            {"code": "BNK", "name": "Bangkok (DMR)", "network": "DMR", "country": "Thailand", "health": "operational", "latency_seconds": 0.3, "noise_level": 17, "signal_quality": "good", "coverage_radius_km": 105, "lon": 100.4935, "lat": 13.7563},
            {"code": "KTM", "name": "Kathmandu (NBC)", "network": "NBC", "country": "Nepal", "health": "operational", "latency_seconds": 0.4, "noise_level": 20, "signal_quality": "good", "coverage_radius_km": 120, "lon": 85.3157, "lat": 27.7172},
            {"code": "DEL", "name": "Delhi (IMD)", "network": "IMD", "country": "India", "health": "operational", "latency_seconds": 0.4, "noise_level": 21, "signal_quality": "fair", "coverage_radius_km": 130, "lon": 77.1025, "lat": 28.7041},
            {"code": "IST", "name": "Istanbul (Kandilli)", "network": "TR", "country": "Turkey", "health": "operational", "latency_seconds": 0.3, "noise_level": 16, "signal_quality": "good", "coverage_radius_km": 125, "lon": 29.0469, "lat": 41.0082},
            {"code": "ROM", "name": "Rome (INGV)", "network": "INGV", "country": "Italy", "health": "operational", "latency_seconds": 0.25, "noise_level": 13, "signal_quality": "excellent", "coverage_radius_km": 135, "lon": 12.4964, "lat": 41.9028},
            {"code": "ATE", "name": "Athens (NOA)", "network": "NOA", "country": "Greece", "health": "operational", "latency_seconds": 0.3, "noise_level": 14, "signal_quality": "excellent", "coverage_radius_km": 115, "lon": 23.7275, "lat": 37.9838},
            {"code": "BER", "name": "Berlin (GFZ)", "network": "GFZ", "country": "Germany", "health": "operational", "latency_seconds": 0.25, "noise_level": 10, "signal_quality": "excellent", "coverage_radius_km": 140, "lon": 13.405, "lat": 52.52},
            {"code": "PAR", "name": "Paris (IPGP)", "network": "IPGP", "country": "France", "health": "operational", "latency_seconds": 0.25, "noise_level": 11, "signal_quality": "excellent", "coverage_radius_km": 135, "lon": 2.3522, "lat": 48.8566},
            {"code": "LON", "name": "London (BGS)", "network": "BGS", "country": "UK", "health": "operational", "latency_seconds": 0.2, "noise_level": 12, "signal_quality": "excellent", "coverage_radius_km": 130, "lon": -0.1276, "lat": 51.5074},
            {"code": "MEX", "name": "Mexico City (SSN)", "network": "SSN", "country": "Mexico", "health": "operational", "latency_seconds": 0.3, "noise_level": 18, "signal_quality": "good", "coverage_radius_km": 120, "lon": -99.1332, "lat": 19.4326},
            {"code": "SAL", "name": "Santiago (USACH)", "network": "DGF", "country": "Chile", "health": "operational", "latency_seconds": 0.35, "noise_level": 15, "signal_quality": "good", "coverage_radius_km": 125, "lon": -70.6693, "lat": -33.4489},
            {"code": "SYD", "name": "Sydney (GA)", "network": "GA", "country": "Australia", "health": "operational", "latency_seconds": 0.3, "noise_level": 13, "signal_quality": "excellent", "coverage_radius_km": 130, "lon": 151.2093, "lat": -33.8688},
            {"code": "AKL", "name": "Auckland (GeoNet)", "network": "GeoNet", "country": "New Zealand", "health": "operational", "latency_seconds": 0.3, "noise_level": 12, "signal_quality": "excellent", "coverage_radius_km": 125, "lon": 174.8859, "lat": -37.0082},
            {"code": "MOW", "name": "Moscow (IMGG)", "network": "IMGG", "country": "Russia", "health": "operational", "latency_seconds": 0.4, "noise_level": 17, "signal_quality": "good", "coverage_radius_km": 140, "lon": 37.6173, "lat": 55.7558},
            {"code": "HKG", "name": "Hong Kong (HKO)", "network": "HKO", "country": "Hong Kong", "health": "operational", "latency_seconds": 0.25, "noise_level": 14, "signal_quality": "excellent", "coverage_radius_km": 120, "lon": 114.1733, "lat": 22.3193},
            {"code": "SIN", "name": "Singapore (MOM)", "network": "MOM", "country": "Singapore", "health": "operational", "latency_seconds": 0.2, "noise_level": 13, "signal_quality": "excellent", "coverage_radius_km": 100, "lon": 103.8198, "lat": 1.3521},
            {"code": "BKK", "name": "Bangkok DMR", "network": "DMR2", "country": "Thailand", "health": "operational", "latency_seconds": 0.3, "noise_level": 18, "signal_quality": "good", "coverage_radius_km": 110, "lon": 100.5018, "lat": 13.6920},
        ]
        return jsonify({"stations": stations}), 200
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
