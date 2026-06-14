"""
Tsunami Warning System Module (JMA-inspired)
Calculates tsunami warnings based on earthquake parameters
"""

import math
from datetime import datetime, timedelta
from enum import Enum


class TsunamiWarningLevel(Enum):
    """Tsunami warning severity levels"""
    NO_WARNING = 0
    ADVISORY = 1
    WARNING = 2
    MAJOR_WARNING = 3


class TsunamiWarningSystem:
    """
    JMA-inspired tsunami warning system
    Issues warnings based on earthquake magnitude, depth, and proximity to coast
    """

    # Coastal regions and their approximate boundaries (lat, lon, radius_km)
    COASTAL_REGIONS = {
        "Pacific": {
            "regions": [
                {"name": "Japan", "lat": 36.0, "lon": 138.0, "radius": 200},
                {"name": "Indonesia", "lat": -2.0, "lon": 113.0, "radius": 250},
                {"name": "Philippines", "lat": 12.0, "lon": 122.0, "radius": 200},
                {"name": "New Zealand", "lat": -41.0, "lon": 174.0, "radius": 200},
                {"name": "US West Coast", "lat": 40.0, "lon": -125.0, "radius": 200},
                {"name": "Chile", "lat": -30.0, "lon": -72.0, "radius": 200},
                {"name": "Thailand", "lat": 8.0, "lon": 100.5, "radius": 150},
            ]
        }
    }

    # Wave height thresholds (in meters)
    WAVE_HEIGHT_THRESHOLDS = {
        TsunamiWarningLevel.NO_WARNING: 0.0,
        TsunamiWarningLevel.ADVISORY: 0.5,
        TsunamiWarningLevel.WARNING: 1.0,
        TsunamiWarningLevel.MAJOR_WARNING: 3.0,
    }

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate distance between two points in km using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates (degrees)
            lat2, lon2: Second point coordinates (degrees)
        
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat/2)**2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    @staticmethod
    def estimate_wave_height(magnitude, depth_km, distance_to_coast_km):
        """
        Estimate tsunami wave height based on earthquake parameters
        Uses empirical relationships from tsunami science
        
        Args:
            magnitude: Earthquake magnitude
            depth_km: Earthquake depth in kilometers
            distance_to_coast_km: Distance to nearest coast in kilometers
        
        Returns:
            Estimated wave height in meters
        """
        if magnitude < 6.5:
            return 0.0

        # Wave height decreases with distance from epicenter and depth
        depth_factor = max(0.1, 1.0 - (depth_km / 700.0))

        # Distance attenuation (wave spreads over larger area)
        distance_factor = max(0.1, 1.0 / (1.0 + (distance_to_coast_km / 200.0)))

        # Magnitude-dependent base wave height
        base_height = (magnitude - 6.5) * 0.8 + 0.5

        estimated_height = base_height * depth_factor * distance_factor

        return max(0.0, estimated_height)

    @staticmethod
    def calculate_arrival_time(distance_to_coast_km):
        """
        Estimate tsunami wave arrival time in minutes
        Average tsunami speed ~800 km/h
        
        Args:
            distance_to_coast_km: Distance to coast in kilometers
        
        Returns:
            Estimated arrival time in minutes
        """
        if distance_to_coast_km <= 0:
            return 0

        speed_kmh = 800
        time_hours = distance_to_coast_km / speed_kmh
        time_minutes = time_hours * 60

        return max(1, int(time_minutes))

    @classmethod
    def get_warning_level(cls, wave_height):
        """
        Determine warning level from wave height
        
        Args:
            wave_height: Estimated wave height in meters
        
        Returns:
            TsunamiWarningLevel enum value
        """
        for level, threshold in sorted(
            cls.WAVE_HEIGHT_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if wave_height >= threshold:
                return level
        return TsunamiWarningLevel.NO_WARNING

    @classmethod
    def evaluate_earthquake(cls, magnitude, depth_km, latitude, longitude):
        """
        Evaluate tsunami risk for an earthquake
        
        Args:
            magnitude: Earthquake magnitude
            depth_km: Earthquake depth in kilometers
            latitude: Earthquake latitude
            longitude: Earthquake longitude
        
        Returns:
            Dictionary with tsunami warning information
        """
        # Find closest coastal region
        min_distance = float('inf')
        closest_region = None

        for region_group in cls.COASTAL_REGIONS.values():
            for region in region_group['regions']:
                distance = cls.haversine_distance(
                    latitude, longitude, region['lat'], region['lon']
                )
                if distance < region['radius'] and distance < min_distance:
                    min_distance = distance
                    closest_region = region

        # Estimate wave height
        wave_height = cls.estimate_wave_height(magnitude, depth_km, min_distance)
        warning_level = cls.get_warning_level(wave_height)
        arrival_time = cls.calculate_arrival_time(min_distance)

        result = {
            "magnitude": magnitude,
            "depth_km": depth_km,
            "latitude": latitude,
            "longitude": longitude,
            "wave_height_m": round(wave_height, 2),
            "warning_level": warning_level.name,
            "warning_value": warning_level.value,
        }

        if closest_region:
            result["nearest_coastal_region"] = closest_region['name']
            result["distance_to_coast_km"] = round(min_distance, 1)
            result["estimated_arrival_minutes"] = arrival_time

        return result


def format_tsunami_report(evaluation):
    """
    Format tsunami evaluation into human-readable report
    
    Args:
        evaluation: Dictionary from TsunamiWarningSystem.evaluate_earthquake
    
    Returns:
        Formatted report string
    """
    report = [
        "=" * 60,
        "TSUNAMI WARNING EVALUATION",
        "=" * 60,
        f"Magnitude: {evaluation['magnitude']}",
        f"Depth: {evaluation['depth_km']} km",
        f"Location: ({evaluation['latitude']:.2f}°, {evaluation['longitude']:.2f}°)",
    ]

    if 'nearest_coastal_region' in evaluation:
        report.append(f"Nearest Region: {evaluation['nearest_coastal_region']}")
        report.append(f"Distance to Coast: {evaluation['distance_to_coast_km']} km")
        report.append(
            f"Estimated Arrival: {evaluation['estimated_arrival_minutes']} minutes"
        )

    report.extend([
        "",
        f"Estimated Wave Height: {evaluation['wave_height_m']} m",
        f"Warning Level: {evaluation['warning_level']}",
        "=" * 60,
    ])

    return "\n".join(report)

    """
    JMA-inspired tsunami warning system
    Issues warnings based on earthquake magnitude, depth, and proximity to coast
    """
    
    # Coastal regions and their approximate boundaries (lat, lon, radius_km)
    COASTAL_REGIONS = {
        "Pacific": {
            "regions": [
                {"name": "Japan", "lat": 36.0, "lon": 138.0, "radius": 200},
                {"name": "Indonesia", "lat": -2.0, "lon": 113.0, "radius": 250},
                {"name": "Philippines", "lat": 12.0, "lon": 122.0, "radius": 200},
                {"name": "New Zealand", "lat": -41.0, "lon": 174.0, "radius": 200},
                {"name": "US West Coast", "lat": 40.0, "lon": -125.0, "radius": 200},
                {"name": "Chile", "lat": -30.0, "lon": -72.0, "radius": 200},
                {"name": "Thailand", "lat": 8.0, "lon": 100.5, "radius": 150},
            ]
        }
    }
    
    # Wave height thresholds (in meters)
    WAVE_HEIGHT_THRESHOLDS = {
        TsunamiWarningLevel.NO_WARNING: 0.0,
        TsunamiWarningLevel.ADVISORY: 0.5,
        TsunamiWarningLevel.WARNING: 1.0,
        TsunamiWarningLevel.MAJOR_WARNING: 3.0,
    }
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    @staticmethod
    def estimate_wave_height(magnitude, depth_km, distance_to_coast_km):
        """
        Estimate tsunami wave height based on earthquake parameters
        Uses empirical relationships from tsunami science
        """
        if magnitude < 6.5:
            return 0.0
        
        # Wave height decreases with distance from epicenter
        # and depth of earthquake
        depth_factor = max(0.1, 1.0 - (depth_km / 700.0))
        
        # Distance attenuation (wave spreads over larger area)
        distance_factor = max(0.1, 1.0 / (1.0 + (distance_to_coast_km / 200.0)))
        
        # Magnitude-dependent base wave height
        base_height = (magnitude - 6.5) * 0.8 + 0.5
        
        estimated_height = base_height * depth_factor * distance_factor
        
        return max(0.0, estimated_height)
    
    @staticmethod
    def calculate_arrival_time(distance_to_coast_km):
        """
        Estimate tsunami wave arrival time in minutes
        Average tsunami speed ~800 km/h
        """
        if distance_to_coast_km <= 0:
            return 0
        
        speed_kmh = 800
        time_hours = distance_to_coast_km / speed_kmh
        time_minutes = time_hours * 60
        
        return max(1, int(time_minutes))
    
    @classmethod
    def get_warning_level(cls, wave_height):
        """Determine warning level based on estimated wave height"""
        thresholds = [
            (cls.WAVE_HEIGHT_THRESHOLDS[TsunamiWarningLevel.MAJOR_WARNING], TsunamiWarningLevel.MAJOR_WARNING),
            (cls.WAVE_HEIGHT_THRESHOLDS[TsunamiWarningLevel.WARNING], TsunamiWarningLevel.WARNING),
            (cls.WAVE_HEIGHT_THRESHOLDS[TsunamiWarningLevel.ADVISORY], TsunamiWarningLevel.ADVISORY),
            (0.0, TsunamiWarningLevel.NO_WARNING),
        ]
        
        for threshold, level in thresholds:
            if wave_height >= threshold:
                return level
        
        return TsunamiWarningLevel.NO_WARNING
    
    @classmethod
    def evaluate_earthquake(cls, magnitude, depth_km, latitude, longitude):
        """
        Evaluate an earthquake for tsunami risk
        Returns warning information for affected regions
        """
        if magnitude < 6.5:
            return {
                "has_risk": False,
                "warnings": [],
                "note": f"Magnitude {magnitude} - Below tsunami threshold"
            }
        
        warnings = []
        
        # Check all coastal regions
        for region_type, region_data in cls.COASTAL_REGIONS.items():
            for region in region_data["regions"]:
                distance = cls.haversine_distance(
                    latitude, longitude,
                    region["lat"], region["lon"]
                )
                
                # Only warn if within alert radius (roughly 3x region radius)
                if distance <= region["radius"] * 3:
                    wave_height = cls.estimate_wave_height(
                        magnitude,
                        depth_km,
                        distance - region["radius"]
                    )
                    
                    warning_level = cls.get_warning_level(wave_height)
                    
                    if warning_level != TsunamiWarningLevel.NO_WARNING:
                        arrival_time = cls.calculate_arrival_time(distance)
                        
                        warnings.append({
                            "region": region["name"],
                            "distance_km": round(distance, 1),
                            "wave_height_m": round(wave_height, 2),
                            "warning_level": warning_level.name,
                            "warning_level_value": warning_level.value,
                            "arrival_time_minutes": arrival_time,
                            "arrival_time_formatted": f"{arrival_time // 60}h {arrival_time % 60}m" if arrival_time >= 60 else f"{arrival_time}m",
                        })
        
        return {
            "has_risk": len(warnings) > 0,
            "warnings": sorted(warnings, key=lambda x: x["warning_level_value"], reverse=True),
            "magnitude": magnitude,
            "depth_km": depth_km,
            "epicenter": {"lat": latitude, "lon": longitude}
        }
    
    @classmethod
    def get_warning_color(cls, warning_level_str):
        """Get color for warning visualization"""
        colors = {
            "MAJOR_WARNING": "#DC2626",      # Red
            "WARNING": "#EA580C",              # Orange-red
            "ADVISORY": "#F59E0B",             # Amber
            "NO_WARNING": "#10B981",           # Green
        }
        return colors.get(warning_level_str, "#6B7280")
    
    @classmethod
    def get_warning_description(cls, warning_level_str):
        """Get human-readable description"""
        descriptions = {
            "MAJOR_WARNING": "🚨 MAJOR TSUNAMI WARNING - Expect destructive waves",
            "WARNING": "⚠️ TSUNAMI WARNING - Dangerous waves expected",
            "ADVISORY": "ℹ️ TSUNAMI ADVISORY - Minor waves may occur",
            "NO_WARNING": "✓ No tsunami threat detected",
        }
        return descriptions.get(warning_level_str, "Unknown")


def format_tsunami_report(earthquake_data):
    """
    Format earthquake data into a tsunami warning report
    
    Args:
        earthquake_data: dict with 'magnitude', 'depth', 'lat', 'lon', 'time'
    
    Returns:
        dict: Formatted tsunami warning report
    """
    mag = earthquake_data.get('magnitude', 0)
    depth = earthquake_data.get('depth', 0)
    lat = earthquake_data.get('latitude', 0)
    lon = earthquake_data.get('longitude', 0)
    time = earthquake_data.get('time', '')
    
    result = TsunamiWarningSystem.evaluate_earthquake(mag, depth, lat, lon)
    
    # Add metadata
    result['earthquake_time'] = time
    result['analysis_time'] = datetime.utcnow().isoformat()
    
    return result
