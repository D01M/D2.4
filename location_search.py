"""
Location Search Module
Provides geocoding and location-based earthquake search functionality
"""

import math
from typing import List, Dict, Tuple, Optional

class LocationSearcher:
    """
    Handles location searches, geocoding, and location-based queries
    Supports city names, coordinates, and region searches
    """
    
    # Major cities database (lat, lon, country, population)
    MAJOR_CITIES = [
        # Japan
        {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "magnitude": 10},
        {"name": "Osaka", "lat": 34.6937, "lon": 135.5023, "country": "Japan", "magnitude": 9},
        {"name": "Yokohama", "lat": 35.4437, "lon": 139.6380, "country": "Japan", "magnitude": 9},
        {"name": "Kyoto", "lat": 35.0116, "lon": 135.7681, "country": "Japan", "magnitude": 8},
        {"name": "Kobe", "lat": 34.6901, "lon": 135.1955, "country": "Japan", "magnitude": 8},
        {"name": "Nagoya", "lat": 35.1815, "lon": 136.9066, "country": "Japan", "magnitude": 8},
        {"name": "Sapporo", "lat": 43.0642, "lon": 141.3469, "country": "Japan", "magnitude": 8},
        {"name": "Fukuoka", "lat": 33.5904, "lon": 130.4017, "country": "Japan", "magnitude": 8},
        
        # Indonesia
        {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456, "country": "Indonesia", "magnitude": 9},
        {"name": "Surabaya", "lat": -7.2575, "lon": 112.7521, "country": "Indonesia", "magnitude": 8},
        {"name": "Bandung", "lat": -6.9147, "lon": 107.6098, "country": "Indonesia", "magnitude": 8},
        {"name": "Medan", "lat": 3.5952, "lon": 98.6722, "country": "Indonesia", "magnitude": 8},
        
        # Philippines
        {"name": "Manila", "lat": 14.5994, "lon": 120.9842, "country": "Philippines", "magnitude": 9},
        {"name": "Cebu", "lat": 10.3157, "lon": 123.8854, "country": "Philippines", "magnitude": 8},
        {"name": "Davao", "lat": 7.0731, "lon": 125.6121, "country": "Philippines", "magnitude": 8},
        
        # China
        {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737, "country": "China", "magnitude": 10},
        {"name": "Beijing", "lat": 39.9042, "lon": 116.4074, "country": "China", "magnitude": 10},
        {"name": "Chongqing", "lat": 29.5630, "lon": 106.5516, "country": "China", "magnitude": 9},
        {"name": "Chengdu", "lat": 30.5728, "lon": 104.0668, "country": "China", "magnitude": 8},
        
        # Southeast Asia
        {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "country": "Thailand", "magnitude": 9},
        {"name": "Ho Chi Minh City", "lat": 10.8231, "lon": 106.6297, "country": "Vietnam", "magnitude": 9},
        {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "country": "Singapore", "magnitude": 8},
        
        # South Korea
        {"name": "Seoul", "lat": 37.5665, "lon": 126.9780, "country": "South Korea", "magnitude": 9},
        {"name": "Busan", "lat": 35.1796, "lon": 129.0753, "country": "South Korea", "magnitude": 8},
        
        # New Zealand
        {"name": "Auckland", "lat": -37.7870, "lon": 175.2793, "country": "New Zealand", "magnitude": 8},
        {"name": "Wellington", "lat": -41.2865, "lon": 174.7762, "country": "New Zealand", "magnitude": 8},
        {"name": "Christchurch", "lat": -43.5321, "lon": 172.6362, "country": "New Zealand", "magnitude": 8},
        
        # Australia
        {"name": "Sydney", "lat": -33.8688, "lon": 151.2093, "country": "Australia", "magnitude": 9},
        {"name": "Melbourne", "lat": -37.8136, "lon": 144.9631, "country": "Australia", "magnitude": 9},
        
        # USA West Coast
        {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "country": "United States", "magnitude": 8},
        {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "country": "United States", "magnitude": 9},
        {"name": "Seattle", "lat": 47.6062, "lon": -122.3321, "country": "United States", "magnitude": 8},
        {"name": "Vancouver", "lat": 49.2827, "lon": -123.1207, "country": "Canada", "magnitude": 8},
        
        # South America
        {"name": "Lima", "lat": -12.0464, "lon": -77.0428, "country": "Peru", "magnitude": 8},
        {"name": "Santiago", "lat": -33.8688, "lon": -70.6693, "country": "Chile", "magnitude": 8},
        {"name": "Valparaíso", "lat": -33.0472, "lon": -71.6127, "country": "Chile", "magnitude": 7},
        
        # Middle East
        {"name": "Istanbul", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "magnitude": 9},
        {"name": "Tehran", "lat": 35.6892, "lon": 51.3890, "country": "Iran", "magnitude": 8},
        
        # Europe
        {"name": "Rome", "lat": 41.9028, "lon": 12.4964, "country": "Italy", "magnitude": 8},
        {"name": "Athens", "lat": 37.9838, "lon": 23.7275, "country": "Greece", "magnitude": 8},
    ]
    
    # Tectonic regions for context
    TECTONIC_REGIONS = [
        {"name": "Japan Trench", "lat": 38.0, "lon": 142.0, "radius": 300},
        {"name": "Kuril-Kamchatka", "lat": 53.0, "lon": 160.0, "radius": 400},
        {"name": "Peru-Chile Trench", "lat": -25.0, "lon": -70.0, "radius": 500},
        {"name": "San Andreas Fault", "lat": 36.0, "lon": -120.5, "radius": 300},
        {"name": "Alpine Fault (NZ)", "lat": -43.5, "lon": 171.5, "radius": 200},
        {"name": "Himalayas", "lat": 28.0, "lon": 85.0, "radius": 400},
        {"name": "Mid-Atlantic Ridge", "lat": 0.0, "lon": -25.0, "radius": 300},
    ]
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    @staticmethod
    def search_by_name(query: str) -> List[Dict]:
        """
        Search for locations by name
        Returns matching cities with their coordinates
        """
        query_lower = query.lower()
        results = []
        
        for city in LocationSearcher.MAJOR_CITIES:
            if (query_lower in city['name'].lower() or 
                query_lower in city['country'].lower()):
                results.append({
                    'name': city['name'],
                    'country': city['country'],
                    'latitude': city['lat'],
                    'longitude': city['lon'],
                    'type': 'city',
                    'population_category': city['magnitude']
                })
        
        # Also search tectonic regions
        for region in LocationSearcher.TECTONIC_REGIONS:
            if query_lower in region['name'].lower():
                results.append({
                    'name': region['name'],
                    'latitude': region['lat'],
                    'longitude': region['lon'],
                    'type': 'tectonic_region',
                    'radius_km': region['radius']
                })
        
        # Sort by relevance (exact matches first)
        results.sort(key=lambda x: (
            0 if x['name'].lower() == query_lower else 1,
            x['name']
        ))
        
        return results[:10]  # Return top 10 results
    
    @staticmethod
    def search_by_coordinates(latitude: float, longitude: float) -> Dict:
        """
        Find nearest city/region for given coordinates
        """
        min_distance = float('inf')
        nearest_city = None
        nearest_tectonic = None
        
        # Find nearest city
        for city in LocationSearcher.MAJOR_CITIES:
            distance = LocationSearcher.haversine_distance(
                latitude, longitude, city['lat'], city['lon']
            )
            if distance < min_distance:
                min_distance = distance
                nearest_city = {
                    'name': city['name'],
                    'country': city['country'],
                    'latitude': city['lat'],
                    'longitude': city['lon'],
                    'distance_km': round(distance, 1),
                    'type': 'city'
                }
        
        # Find nearest tectonic region
        min_tectonic_distance = float('inf')
        for region in LocationSearcher.TECTONIC_REGIONS:
            distance = LocationSearcher.haversine_distance(
                latitude, longitude, region['lat'], region['lon']
            )
            if distance < min_tectonic_distance:
                min_tectonic_distance = distance
                nearest_tectonic = {
                    'name': region['name'],
                    'latitude': region['lat'],
                    'longitude': region['lon'],
                    'distance_km': round(distance, 1),
                    'radius_km': region['radius'],
                    'type': 'tectonic_region'
                }
        
        return {
            'query_latitude': latitude,
            'query_longitude': longitude,
            'nearest_city': nearest_city,
            'nearest_tectonic_region': nearest_tectonic
        }
    
    @staticmethod
    def get_location_info(latitude: float, longitude: float) -> Dict:
        """
        Get comprehensive location information
        Includes nearby cities, tectonic context, and risk assessment
        """
        nearby = LocationSearcher.search_by_coordinates(latitude, longitude)
        
        # Find all nearby cities within 500km
        nearby_cities = []
        for city in LocationSearcher.MAJOR_CITIES:
            distance = LocationSearcher.haversine_distance(
                latitude, longitude, city['lat'], city['lon']
            )
            if distance < 500:
                nearby_cities.append({
                    'name': city['name'],
                    'country': city['country'],
                    'distance_km': round(distance, 1),
                    'latitude': city['lat'],
                    'longitude': city['lon']
                })
        
        # Sort by distance
        nearby_cities.sort(key=lambda x: x['distance_km'])
        
        # Check if in high-risk tectonic zones
        in_high_risk_zone = False
        high_risk_zones = []
        
        for region in LocationSearcher.TECTONIC_REGIONS:
            distance = LocationSearcher.haversine_distance(
                latitude, longitude, region['lat'], region['lon']
            )
            if distance < region['radius']:
                in_high_risk_zone = True
                high_risk_zones.append(region['name'])
        
        return {
            'latitude': latitude,
            'longitude': longitude,
            'nearest_city': nearby['nearest_city'],
            'nearest_tectonic_region': nearby['nearest_tectonic_region'],
            'nearby_cities': nearby_cities[:5],  # Top 5 nearest cities
            'in_high_risk_zone': in_high_risk_zone,
            'high_risk_zones': high_risk_zones,
            'earthquake_risk_assessment': get_risk_assessment(latitude, longitude, high_risk_zones)
        }
    
    @staticmethod
    def parse_coordinates(input_string: str) -> Optional[Tuple[float, float]]:
        """
        Parse various coordinate formats
        Supports: "lat,lon", "lat lon", "lat N/S lon E/W"
        """
        try:
            # Try comma-separated
            if ',' in input_string:
                parts = input_string.split(',')
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return (lat, lon)
            
            # Try space-separated
            parts = input_string.split()
            if len(parts) >= 2:
                lat = float(parts[0])
                lon = float(parts[1])
                return (lat, lon)
            
            return None
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def search(query: str) -> Dict:
        """
        Universal search function
        Handles location names, coordinates, and region searches
        """
        query = query.strip()
        
        # Try to parse as coordinates
        coords = LocationSearcher.parse_coordinates(query)
        if coords:
            lat, lon = coords
            return {
                'type': 'coordinates',
                'location_info': LocationSearcher.get_location_info(lat, lon)
            }
        
        # Search by name
        results = LocationSearcher.search_by_name(query)
        
        if results:
            return {
                'type': 'search_results',
                'query': query,
                'results': results,
                'count': len(results)
            }
        
        return {
            'type': 'no_results',
            'query': query,
            'message': f"No locations found matching '{query}'"
        }


def get_risk_assessment(latitude: float, longitude: float, zones: List[str]) -> Dict:
    """
    Assess seismic risk for a location
    """
    risk_level = "Low"
    risk_score = 1.0
    
    high_risk_keywords = ['Subduction', 'Trench', 'Japan', 'Chile', 'Indonesia']
    medium_risk_keywords = ['San Andreas', 'Transform', 'Alpine', 'Himalayas']
    
    zone_text = ' '.join(zones)
    
    if any(keyword in zone_text for keyword in high_risk_keywords):
        risk_level = "Very High"
        risk_score = 4.0
    elif any(keyword in zone_text for keyword in medium_risk_keywords):
        risk_level = "High"
        risk_score = 3.0
    elif zones:
        risk_level = "Moderate"
        risk_score = 2.0
    
    return {
        'risk_level': risk_level,
        'risk_score': risk_score,
        'assessed_zones': zones,
        'recommendation': f"Location in {len(zones)} tectonic zone(s). Monitor official earthquake alerts."
    }
