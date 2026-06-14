#!/usr/bin/env python
"""
Location Search Module Test Suite
Tests location search, geocoding, and risk assessment functionality
"""

import json
from location_search import LocationSearcher

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_city_search():
    """Test searching for cities"""
    print_header("City Search Tests")
    
    test_queries = ["Tokyo", "Los Angeles", "Jakarta", "Manila", "Auckland"]
    
    for query in test_queries:
        results = LocationSearcher.search_by_name(query)
        print(f"\n📍 Searching: '{query}'")
        print(f"   Found: {len(results)} results")
        if results:
            top = results[0]
            print(f"   Top result: {top['name']}, {top.get('country', 'N/A')}")
            print(f"   Coordinates: ({top['latitude']}, {top['longitude']})")

def test_tectonic_search():
    """Test searching for tectonic regions"""
    print_header("Tectonic Region Search Tests")
    
    test_queries = ["Japan Trench", "San Andreas", "Peru-Chile"]
    
    for query in test_queries:
        results = LocationSearcher.search_by_name(query)
        print(f"\n🌋 Searching: '{query}'")
        print(f"   Found: {len(results)} results")
        if results:
            top = results[0]
            print(f"   Type: {top.get('type', 'unknown')}")
            print(f"   Coordinates: ({top['latitude']}, {top['longitude']})")

def test_coordinate_parsing():
    """Test coordinate parsing"""
    print_header("Coordinate Parsing Tests")
    
    test_coords = [
        "35.6762, 139.6503",
        "35.6762 139.6503",
        "-33.8688, 151.2093",
        "40.0 -118.5"
    ]
    
    for coord_str in test_coords:
        coords = LocationSearcher.parse_coordinates(coord_str)
        print(f"\nInput: '{coord_str}'")
        if coords:
            print(f"   Parsed: ({coords[0]}, {coords[1]})")
        else:
            print(f"   Failed to parse")

def test_nearest_location():
    """Test finding nearest cities and tectonic regions"""
    print_header("Nearest Location Tests")
    
    test_locations = [
        (35.6762, 139.6503, "Tokyo, Japan"),
        (37.7749, -122.4194, "San Francisco, USA"),
        (-33.8688, 151.2093, "Sydney, Australia"),
        (14.5994, 120.9842, "Manila, Philippines"),
    ]
    
    for lat, lon, label in test_locations:
        nearby = LocationSearcher.search_by_coordinates(lat, lon)
        print(f"\n📍 Location: {label}")
        print(f"   Coordinates: ({lat}, {lon})")
        
        if nearby['nearest_city']:
            city = nearby['nearest_city']
            print(f"   Nearest City: {city['name']} - {city['distance_km']} km away")
        
        if nearby['nearest_tectonic_region']:
            region = nearby['nearest_tectonic_region']
            print(f"   Nearest Tectonic Region: {region['name']} - {region['distance_km']} km away")

def test_location_info():
    """Test getting comprehensive location information"""
    print_header("Location Information Tests")
    
    test_locations = [
        (35.6762, 139.6503, "Tokyo, Japan"),
        (34.6901, 135.1955, "Kobe, Japan"),
        (37.7749, -122.4194, "San Francisco, USA"),
    ]
    
    for lat, lon, label in test_locations:
        info = LocationSearcher.get_location_info(lat, lon)
        print(f"\n📍 Location: {label}")
        print(f"   Coordinates: ({lat}, {lon})")
        
        if info['nearest_city']:
            print(f"   Nearest City: {info['nearest_city']['name']}")
        
        print(f"   In High-Risk Zone: {info['in_high_risk_zone']}")
        if info['high_risk_zones']:
            print(f"   Zones: {', '.join(info['high_risk_zones'])}")
        
        risk = info['earthquake_risk_assessment']
        print(f"   Risk Level: {risk['risk_level']}")
        print(f"   Risk Score: {risk['risk_score']}")
        
        if info['nearby_cities']:
            print(f"   Nearby Cities:")
            for city in info['nearby_cities'][:3]:
                print(f"      - {city['name']}: {city['distance_km']} km")

def test_universal_search():
    """Test universal search function"""
    print_header("Universal Search Tests")
    
    test_queries = [
        "Tokyo",
        "35.6762, 139.6503",
        "San Andreas",
        "Sydney",
        "34.0522, -118.2437"
    ]
    
    for query in test_queries:
        result = LocationSearcher.search(query)
        print(f"\n🔍 Query: '{query}'")
        print(f"   Type: {result['type']}")
        
        if result['type'] == 'search_results':
            print(f"   Results: {result['count']}")
            if result['results']:
                top = result['results'][0]
                print(f"   Top match: {top['name']}")
        elif result['type'] == 'coordinates':
            info = result['location_info']
            print(f"   Nearest city: {info['nearest_city']['name']}")
            print(f"   Risk level: {info['earthquake_risk_assessment']['risk_level']}")
        else:
            print(f"   Message: {result.get('message', 'N/A')}")

def test_risk_assessment():
    """Test risk assessment for various locations"""
    print_header("Seismic Risk Assessment Tests")
    
    test_locations = [
        (35.6762, 139.6503, "Tokyo (Subduction zone)"),
        (37.6, -120.5, "San Francisco (Transform fault)"),
        (51.5, 0, "London (Stable area)"),
        (-12.0464, -77.0428, "Lima (Subduction zone)"),
    ]
    
    print(f"\n{'Location':<40} {'Risk Level':<15} {'Score':<8}")
    print("-" * 70)
    
    for lat, lon, label in test_locations:
        info = LocationSearcher.get_location_info(lat, lon)
        risk = info['earthquake_risk_assessment']
        print(f"{label:<40} {risk['risk_level']:<15} {risk['risk_score']:<8.1f}")

def test_distance_calculations():
    """Test haversine distance calculations"""
    print_header("Distance Calculation Tests")
    
    test_pairs = [
        ((35.6762, 139.6503), (34.6901, 135.1955), "Tokyo to Kobe"),
        ((37.7749, -122.4194), (34.0522, -118.2437), "San Francisco to Los Angeles"),
        ((0, 0), (1, 1), "Equator 1 degree apart"),
    ]
    
    print(f"\n{'From':<25} {'To':<25} {'Distance (km)':<15}")
    print("-" * 70)
    
    for (lat1, lon1), (lat2, lon2), label in test_pairs:
        distance = LocationSearcher.haversine_distance(lat1, lon1, lat2, lon2)
        print(f"{label:<25} {'':<25} {distance:<15.1f}")

def test_database_stats():
    """Print database statistics"""
    print_header("Database Statistics")
    
    print(f"\nTotal Cities: {len(LocationSearcher.MAJOR_CITIES)}")
    print(f"Total Tectonic Regions: {len(LocationSearcher.TECTONIC_REGIONS)}")
    
    # Count by country
    countries = {}
    for city in LocationSearcher.MAJOR_CITIES:
        country = city['country']
        countries[country] = countries.get(country, 0) + 1
    
    print(f"\nCities by Country:")
    for country in sorted(countries.keys()):
        print(f"  {country}: {countries[country]}")
    
    print(f"\nTectonic Regions:")
    for region in LocationSearcher.TECTONIC_REGIONS:
        print(f"  {region['name']}: {region['lat']}°N, {region['lon']}°E (radius: {region['radius']}km)")

def main():
    """Run all tests"""
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "LOCATION SEARCH MODULE TEST SUITE" + " "*20 + "║")
    print("║" + " "*68 + "║")
    print("║" + " "*10 + "Testing location search and geocoding functionality" + " "*7 + "║")
    print("╚" + "="*68 + "╝")
    
    # Run all tests
    test_database_stats()
    test_city_search()
    test_tectonic_search()
    test_coordinate_parsing()
    test_nearest_location()
    test_distance_calculations()
    test_universal_search()
    test_location_info()
    test_risk_assessment()
    
    print("\n" + "="*70)
    print("  All tests completed successfully!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
