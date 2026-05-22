from flask import Flask, Response, send_from_directory, request, jsonify
import requests
import json
from tsunami_warning import TsunamiWarningSystem, format_tsunami_report

app = Flask(__name__, static_folder=".")

@app.route("/")
def index():
    return send_from_directory(".", "index.html.html")

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
