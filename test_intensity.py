#!/usr/bin/env python
"""
OpenSeismo Lite - Intensity Calculator Test Suite
Tests MMI and Shindo calculations with real earthquake scenarios
"""

import json
from intensity_calculator import (
    IntensityCalculator, 
    FaultType, 
    MMIScale, 
    ShindoScale,
    FAULT_ZONES
)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_scenario(name, magnitude, depth_km, latitude, longitude, distances=None):
    """Test a specific earthquake scenario"""
    print_section(name)
    print(f"Magnitude: {magnitude}")
    print(f"Depth: {depth_km} km")
    print(f"Location: ({latitude}°, {longitude}°)")
    
    # Classify fault type
    fault_type, fault_zone = IntensityCalculator.classify_fault_type(
        latitude, longitude, depth_km
    )
    
    print(f"\nFault Classification:")
    print(f"  Type: {fault_type.value}")
    print(f"  Color: {fault_zone.color}")
    print(f"  Description: {fault_zone.description}")
    print(f"  Typical Depth: {fault_zone.typical_depth_min}-{fault_zone.typical_depth_max} km")
    
    # Test at epicenter
    if distances is None:
        distances = [0.1, 10, 50, 100, 200]
    
    print(f"\nIntensity by Distance:")
    print(f"{'Distance (km)':<15} {'MMI':<8} {'MMI Scale':<15} {'Shindo':<8} {'Shindo Scale':<12}")
    print("-" * 70)
    
    for dist in distances:
        mmi = IntensityCalculator.calculate_mmi(magnitude, depth_km, dist, fault_type)
        shindo = IntensityCalculator.calculate_shindo(magnitude, depth_km, dist, fault_type)
        
        mmi_scale = IntensityCalculator.get_mmi_scale(mmi)
        shindo_scale = IntensityCalculator.get_shindo_scale(shindo)
        
        print(f"{dist:<15.1f} {mmi:<8.2f} {mmi_scale.name:<15} {shindo:<8.2f} {shindo_scale.name:<12}")

def test_historical_earthquakes():
    """Test with real historical earthquake scenarios"""
    print("\n\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "INTENSITY CALCULATOR TEST SUITE" + " "*22 + "║")
    print("║" + " "*68 + "║")
    print("║" + " "*10 + "Testing MMI and Shindo with Historical Scenarios" + " "*9 + "║")
    print("╚" + "="*68 + "╝")
    
    # 2011 Japan (Tohoku) - Subduction
    test_scenario(
        "2011 Tōhoku Earthquake (Japan) - M9.1 Subduction",
        magnitude=9.1,
        depth_km=24,
        latitude=38.3,
        longitude=142.4,
        distances=[0.1, 30, 100, 200, 300]
    )
    
    # 1995 Kobe - Strike-slip (Near surface)
    test_scenario(
        "1995 Kobe Earthquake (Japan) - M7.3 Strike-Slip",
        magnitude=7.3,
        depth_km=16,
        latitude=34.6,
        longitude=135.0,
        distances=[0.1, 10, 50, 100, 200]
    )
    
    # 2010 Chile - Subduction
    test_scenario(
        "2010 Chilean Earthquake - M8.8 Subduction",
        magnitude=8.8,
        depth_km=35,
        latitude=-35.9,
        longitude=-72.7,
        distances=[0.1, 50, 100, 300, 500]
    )
    
    # 1906 San Francisco - Transform
    test_scenario(
        "1906 San Francisco - M7.9 Transform Fault",
        magnitude=7.9,
        depth_km=12,
        latitude=37.6,
        longitude=-122.4,
        distances=[0.1, 10, 30, 50, 100]
    )
    
    # Recent Papua New Guinea - Deep Subduction
    test_scenario(
        "2018 Papua New Guinea - M7.5 Deep Subduction",
        magnitude=7.5,
        depth_km=580,
        latitude=-7.3,
        longitude=146.6,
        distances=[0.1, 100, 200, 300, 500]
    )

def print_fault_zones_summary():
    """Print summary of all fault zones"""
    print_section("Tectonic Fault Zone Reference")
    
    print(f"{'Type':<20} {'Color':<10} {'Depth Range':<20} {'Description':<35}")
    print("-" * 85)
    
    for fault_type, zone_info in FAULT_ZONES.items():
        print(f"{zone_info.fault_type.value:<20} {zone_info.color:<10} "
              f"{zone_info.typical_depth_min}-{zone_info.typical_depth_max} km   "
              f"{zone_info.description[:32]:<35}")

def print_intensity_scales_summary():
    """Print summary of intensity scales"""
    print_section("Intensity Scales Reference")
    
    print("\nModified Mercalli Intensity (MMI):")
    print(f"{'Scale':<10} {'Value':<8} {'Description':<45}")
    print("-" * 70)
    for scale in MMIScale:
        print(f"{scale.name:<10} {scale.intensity:<8} {scale.description:<45}")
    
    print("\n\nJapan Meteorological Agency Shindo Scale:")
    print(f"{'Scale':<10} {'Value':<8} {'Description':<45}")
    print("-" * 70)
    for scale in ShindoScale:
        print(f"{scale.name:<10} {scale.intensity:<8.1f} {scale.description:<45}")

def test_intensity_report():
    """Test comprehensive intensity report generation"""
    print_section("Comprehensive Intensity Report Example")
    
    report = IntensityCalculator.get_intensity_report(
        magnitude=7.5,
        depth_km=15,
        latitude=36.0,
        longitude=138.0
    )
    
    print(json.dumps(report, indent=2, default=str))

def test_intensity_grid():
    """Test intensity grid generation"""
    print_section("Intensity Grid Generation Test")
    
    points = IntensityCalculator.calculate_intensity_grid(
        magnitude=7.5,
        depth_km=15,
        latitude=36.0,
        longitude=138.0,
        grid_size_km=100,
        max_distance_km=300
    )
    
    print(f"Generated {len(points)} grid points")
    print(f"\nSample points:")
    print(f"{'Lat':<10} {'Lon':<10} {'Distance':<12} {'MMI':<8} {'Shindo':<8}")
    print("-" * 50)
    
    # Print first 5 and last 5 points
    for point in points[:5] + points[-5:]:
        print(f"{point['latitude']:<10.2f} {point['longitude']:<10.2f} "
              f"{point['distance_km']:<12.1f} {point['mmi']:<8.2f} {point['shindo']:<8.2f}")

def test_depth_variations():
    """Test how depth affects intensity calculations"""
    print_section("Depth Variation Analysis")
    print("Magnitude: 7.5 | Distance: 50 km from epicenter")
    print(f"{'Depth (km)':<15} {'MMI':<8} {'Shindo':<8} {'Effect':<30}")
    print("-" * 70)
    
    base_mmi = None
    depths = [5, 10, 20, 50, 100, 200, 400, 600]
    
    for depth in depths:
        mmi = IntensityCalculator.calculate_mmi(7.5, depth, 50, FaultType.SUBDUCTION)
        shindo = IntensityCalculator.calculate_shindo(7.5, depth, 50, FaultType.SUBDUCTION)
        
        if base_mmi is None:
            base_mmi = mmi
            effect = "Baseline (shallow)"
        else:
            diff = mmi - base_mmi
            effect = f"{diff:+.2f} (Deeper = weaker shaking)"
        
        print(f"{depth:<15} {mmi:<8.2f} {shindo:<8.2f} {effect:<30}")

def test_magnitude_variations():
    """Test how magnitude affects intensity"""
    print_section("Magnitude Variation Analysis")
    print("Depth: 20 km | Distance: 50 km | Fault: Subduction")
    print(f"{'Magnitude':<15} {'MMI':<8} {'Shindo':<8} {'Description':<35}")
    print("-" * 70)
    
    magnitudes = [4.0, 5.0, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
    
    for mag in magnitudes:
        mmi = IntensityCalculator.calculate_mmi(mag, 20, 50, FaultType.SUBDUCTION)
        shindo = IntensityCalculator.calculate_shindo(mag, 20, 50, FaultType.SUBDUCTION)
        
        mmi_scale = IntensityCalculator.get_mmi_scale(mmi)
        
        print(f"{mag:<15.1f} {mmi:<8.2f} {shindo:<8.2f} {mmi_scale.description:<35}")

def test_fault_type_effects():
    """Test how different fault types affect intensity"""
    print_section("Fault Type Effect Analysis")
    print("Magnitude: 7.5 | Depth: 20 km | Distance: 50 km")
    print(f"{'Fault Type':<20} {'MMI':<8} {'Shindo':<8} {'Color':<10}")
    print("-" * 50)
    
    for fault_type in FaultType:
        mmi = IntensityCalculator.calculate_mmi(7.5, 20, 50, fault_type)
        shindo = IntensityCalculator.calculate_shindo(7.5, 20, 50, fault_type)
        
        zone_info = FAULT_ZONES.get(fault_type)
        color = zone_info.color if zone_info else "#000000"
        
        print(f"{fault_type.value:<20} {mmi:<8.2f} {shindo:<8.2f} {color:<10}")

def main():
    """Run all tests"""
    
    # Print reference data
    print_fault_zones_summary()
    print_intensity_scales_summary()
    
    # Run historical earthquake tests
    test_historical_earthquakes()
    
    # Run analysis tests
    test_depth_variations()
    test_magnitude_variations()
    test_fault_type_effects()
    
    # Test advanced features
    test_intensity_report()
    test_intensity_grid()
    
    print("\n" + "="*70)
    print("  All tests completed successfully!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
