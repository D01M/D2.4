"""
Live Earthquake Detection System
Fetches real-time earthquake data from USGS and other sources
Provides ShakeMax hexagon calculations and impact assessments
"""

import requests
import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time

class LiveEarthquakeDetector:
    """
    Monitors live earthquake data from USGS and generates ShakeMax intensity hexagons
    """
    
    # USGS API endpoints
    USGS_SIGNIFICANT = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"
    USGS_ALL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
    USGS_4_5_PLUS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson"
    USGS_2_5_PLUS = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson"
    
    # ShakeMax thresholds for hexagon coloring
    SHAKEMAX_LEVELS = [
        {"min": 0, "max": 1, "color": "#ffffff", "label": "No Damage"},
        {"min": 1, "max": 2, "color": "#ccccff", "label": "Very Light"},
        {"min": 2, "max": 3, "color": "#99ccff", "label": "Light"},
        {"min": 3, "max": 4, "color": "#66ccff", "label": "Moderate"},
        {"min": 4, "max": 5, "color": "#00ccff", "label": "Moderate-Strong"},
        {"min": 5, "max": 6, "color": "#ffff00", "label": "Strong"},
        {"min": 6, "max": 7, "color": "#ffcc00", "label": "Very Strong"},
        {"min": 7, "max": 8, "color": "#ff9900", "label": "Severe"},
        {"min": 8, "max": 9, "color": "#ff6600", "label": "Violent"},
        {"min": 9, "max": 10, "color": "#ff3300", "label": "Extreme"},
        {"min": 10, "max": 12, "color": "#cc0000", "label": "Catastrophic"},
    ]
    
    @staticmethod
    def fetch_recent_earthquakes(magnitude_filter=4.5, days_back=30) -> List[Dict]:
        """
        Fetch recent earthquakes from USGS API
        
        Args:
            magnitude_filter: Minimum magnitude to fetch
            days_back: How many days back to search
        
        Returns:
            List of earthquake data with enhanced metadata
        """
        try:
            # Select appropriate feed
            if magnitude_filter >= 4.5:
                url = LiveEarthquakeDetector.USGS_4_5_PLUS
            elif magnitude_filter >= 2.5:
                url = LiveEarthquakeDetector.USGS_2_5_PLUS
            else:
                url = LiveEarthquakeDetector.USGS_ALL
            
            headers = {"User-Agent": "OpenSeismoLite/1.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            earthquakes = []
            cutoff_time = (datetime.utcnow() - timedelta(days=days_back)).timestamp() * 1000
            
            for feature in data.get('features', []):
                props = feature['properties']
                geom = feature['geometry']['coordinates']
                
                # Filter by magnitude and time
                mag = props.get('mag', 0)
                time_ms = props.get('time', 0)
                
                if mag >= magnitude_filter and time_ms >= cutoff_time:
                    eq = {
                        "id": props.get('id', ''),
                        "magnitude": mag,
                        "latitude": geom[1],
                        "longitude": geom[0],
                        "depth_km": geom[2],
                        "time_utc": datetime.utcfromtimestamp(time_ms / 1000).isoformat() + 'Z',
                        "time_ms": time_ms,
                        "place": props.get('place', 'Unknown'),
                        "tsunami": props.get('tsunami', 0),
                        "felt_reports": props.get('felt', 0),
                        "sources": props.get('sources', ''),
                        "url": props.get('url', ''),
                    }
                    earthquakes.append(eq)
            
            # Sort by time (newest first)
            earthquakes.sort(key=lambda x: x['time_ms'], reverse=True)
            return earthquakes
            
        except Exception as e:
            print(f"Error fetching USGS data: {e}")
            return []
    
    @staticmethod
    def calculate_shakemax_intensity(magnitude, depth_km, distance_km, fault_type="unknown"):
        """
        Calculate ShakeMax intensity (0-12 scale)
        Based on combined MMI and Shindo logic
        
        Args:
            magnitude: Earthquake magnitude
            depth_km: Depth in km
            distance_km: Distance in km
            fault_type: Type of fault mechanism
        
        Returns:
            ShakeMax intensity value (0-12)
        """
        from intensity_calculator import IntensityCalculator, FaultType
        
        # Map fault type strings to enum
        fault_map = {
            "subduction": FaultType.SUBDUCTION,
            "transform": FaultType.TRANSFORM,
            "reverse": FaultType.REVERSE_THRUST,
            "normal": FaultType.NORMAL,
            "strike-slip": FaultType.STRIKE_SLIP,
            "unknown": FaultType.UNKNOWN,
        }
        fault = fault_map.get(fault_type.lower(), FaultType.UNKNOWN)
        
        # Calculate intensity using our precise models
        mmi = IntensityCalculator.calculate_mmi(magnitude, depth_km, distance_km, fault)
        shindo = IntensityCalculator.calculate_shindo(magnitude, depth_km, distance_km, fault)
        
        # ShakeMax = average of MMI and Shindo (scaled to 0-12)
        shakemax = (mmi + (shindo * 1.714)) / 2  # Shindo 7 = MMI 12
        return min(12, max(0, shakemax))
    
    @staticmethod
    def generate_hexagon_grid(latitude, longitude, magnitude, depth_km, 
                             grid_radius_km=300, hex_size_km=10) -> List[Dict]:
        """
        Generate hexagonal grid around epicenter with ShakeMax intensities
        
        Args:
            latitude: Epicenter latitude
            longitude: Epicenter longitude
            magnitude: Earthquake magnitude
            depth_km: Depth in km
            grid_radius_km: Maximum radius for hexagon grid
            hex_size_km: Size of each hexagon in km
        
        Returns:
            List of hexagon tiles with intensity data
        """
        from intensity_calculator import IntensityCalculator, FaultType
        
        # Classify fault type
        fault_type, _ = IntensityCalculator.classify_fault_type(latitude, longitude, depth_km)
        
        hexagons = []
        hex_count = 0
        
        # Generate offset grid (approximate hex grid)
        lat_step = hex_size_km / 111.0  # ~111 km per degree latitude
        lon_step = hex_size_km / (111.0 * math.cos(math.radians(latitude)))
        
        lat_offset = int(grid_radius_km / hex_size_km) + 1
        lon_offset = int(grid_radius_km / hex_size_km) + 1
        
        for i in range(-lat_offset, lat_offset + 1):
            for j in range(-lon_offset, lon_offset + 1):
                # Hexagonal offset (alternate rows)
                if i % 2 != 0:
                    lon_adj = lon_step * 0.5
                else:
                    lon_adj = 0
                
                hex_lat = latitude + (i * lat_step)
                hex_lon = longitude + (j * lon_step + lon_adj)
                
                # Calculate distance from epicenter
                distance = math.sqrt(
                    (i * hex_size_km)**2 + (j * hex_size_km)**2
                )
                
                if distance <= grid_radius_km:
                    # Calculate ShakeMax intensity
                    shakemax = LiveEarthquakeDetector.calculate_shakemax_intensity(
                        magnitude, depth_km, distance, fault_type.value
                    )
                    
                    # Get color based on intensity
                    color = LiveEarthquakeDetector._get_shakemax_color(shakemax)
                    level = LiveEarthquakeDetector._get_shakemax_level(shakemax)
                    
                    hexagons.append({
                        "id": f"hex_{hex_count}",
                        "latitude": hex_lat,
                        "longitude": hex_lon,
                        "distance_km": round(distance, 1),
                        "shakemax": round(shakemax, 2),
                        "color": color,
                        "level": level,
                        "intensity_label": level['label'],
                        "size_km": hex_size_km,
                    })
                    hex_count += 1
        
        return hexagons
    
    @staticmethod
    def _get_shakemax_color(intensity):
        """Get hexagon color for ShakeMax intensity"""
        for level in LiveEarthquakeDetector.SHAKEMAX_LEVELS:
            if level['min'] <= intensity < level['max']:
                return level['color']
        return "#cc0000"  # Default red for extreme
    
    @staticmethod
    def _get_shakemax_level(intensity):
        """Get level info for ShakeMax intensity"""
        for level in LiveEarthquakeDetector.SHAKEMAX_LEVELS:
            if level['min'] <= intensity < level['max']:
                return level
        return LiveEarthquakeDetector.SHAKEMAX_LEVELS[-1]
    
    @staticmethod
    def enrich_earthquake_data(eq: Dict) -> Dict:
        """
        Add calculated fields to earthquake data
        
        Args:
            eq: Earthquake dictionary from USGS
        
        Returns:
            Enriched earthquake data with ShakeMax and hexagons
        """
        # Calculate epicenter intensity
        shakemax_epicenter = LiveEarthquakeDetector.calculate_shakemax_intensity(
            eq['magnitude'], 
            eq['depth_km'], 
            0.1  # At epicenter
        )
        
        eq['shakemax_epicenter'] = round(shakemax_epicenter, 2)
        eq['shakemax_color'] = LiveEarthquakeDetector._get_shakemax_color(shakemax_epicenter)
        eq['shakemax_level'] = LiveEarthquakeDetector._get_shakemax_level(shakemax_epicenter)
        
        # Generate hexagon grid
        eq['hexagons'] = LiveEarthquakeDetector.generate_hexagon_grid(
            eq['latitude'],
            eq['longitude'],
            eq['magnitude'],
            eq['depth_km'],
            grid_radius_km=300,
            hex_size_km=15
        )
        
        # Add time ago calculation
        time_obj = datetime.fromisoformat(eq['time_utc'].replace('Z', '+00:00'))
        time_ago = datetime.utcnow() - time_obj.replace(tzinfo=None)
        
        if time_ago.total_seconds() < 60:
            eq['time_ago'] = "Just now"
        elif time_ago.total_seconds() < 3600:
            minutes = int(time_ago.total_seconds() / 60)
            eq['time_ago'] = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif time_ago.total_seconds() < 86400:
            hours = int(time_ago.total_seconds() / 3600)
            eq['time_ago'] = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(time_ago.total_seconds() / 86400)
            eq['time_ago'] = f"{days} day{'s' if days != 1 else ''} ago"
        
        return eq
    
    @staticmethod
    def get_live_earthquakes(magnitude_filter=4.5, enrich=True) -> List[Dict]:
        """
        Get current live earthquakes with optional enrichment
        
        Args:
            magnitude_filter: Minimum magnitude
            enrich: Whether to add ShakeMax and hexagon data
        
        Returns:
            List of earthquake data
        """
        earthquakes = LiveEarthquakeDetector.fetch_recent_earthquakes(magnitude_filter)
        
        if enrich:
            earthquakes = [
                LiveEarthquakeDetector.enrich_earthquake_data(eq) 
                for eq in earthquakes
            ]
        
        return earthquakes
