"""
Earthquake Intensity Calculator
Calculates MMI and Shindo intensities based on earthquake parameters
Includes fault type classification and color-coded zones
"""

import math
from enum import Enum
from dataclasses import dataclass

class FaultType(Enum):
    """Tectonic fault types"""
    SUBDUCTION = "Subduction"
    TRANSFORM = "Transform"
    REVERSE_THRUST = "Reverse-Thrust"
    NORMAL = "Normal"
    DIVERGENT = "Divergent"
    CONVERGENT = "Convergent"
    STRIKE_SLIP = "Strike-Slip"
    UNKNOWN = "Unknown"

class MMIScale(Enum):
    """Modified Mercalli Intensity Scale"""
    I = (1, "Not felt", "#ffffff")
    II = (2, "Weak - Felt indoors", "#ccccff")
    III = (3, "Weak - Felt indoors, vibrations like passing truck", "#99ccff")
    IV = (4, "Light - Indoor objects rattle, felt outdoors", "#66ccff")
    V = (5, "Moderate - Felt by most, some dishes break", "#00ccff")
    VI = (6, "Strong - Felt by all, minor damage", "#ffff00")
    VII = (7, "Very Strong - Considerable damage, everyone runs outside", "#ffcc00")
    VIII = (8, "Severe - Structural damage, partial collapse", "#ff9900")
    IX = (9, "Violent - Considerable damage to buildings, ground cracking", "#ff6600")
    X = (10, "Extreme - Most buildings destroyed, ground distorted", "#ff3300")
    XI = (11, "Extreme - Few buildings standing", "#ff0000")
    XII = (12, "Extreme - Total destruction", "#cc0000")

    @property
    def intensity(self):
        return self.value[0]
    
    @property
    def description(self):
        return self.value[1]
    
    @property
    def color(self):
        return self.value[2]

class ShindoScale(Enum):
    """Japan Meteorological Agency Shindo Scale"""
    SHINDO_0 = (0, "Not felt", "#ffffff")
    SHINDO_1 = (1, "Weak - Felt indoors", "#ccccff")
    SHINDO_2 = (2, "Light - Objects rattle", "#66ccff")
    SHINDO_3 = (3, "Moderate - Most people frightened", "#00ccff")
    SHINDO_4 = (4, "Strong - Most buildings slightly damaged", "#ffff00")
    SHINDO_5_MINUS = (5, "Strong - Many buildings damaged, cracks in walls", "#ffcc00")
    SHINDO_5_PLUS = (5.5, "Strong+ - Considerable damage", "#ff9900")
    SHINDO_6_MINUS = (6, "Very Strong - Many buildings collapse", "#ff6600")
    SHINDO_6_PLUS = (6.5, "Very Strong+ - Most buildings collapse", "#ff3300")
    SHINDO_7 = (7, "Extreme - Total or near total destruction", "#cc0000")

    @property
    def intensity(self):
        return self.value[0]
    
    @property
    def description(self):
        return self.value[1]
    
    @property
    def color(self):
        return self.value[2]

@dataclass
class FaultZoneInfo:
    """Information about a fault zone"""
    fault_type: FaultType
    color: str
    description: str
    typical_depth_min: float
    typical_depth_max: float
    magnitude_multiplier: float

# Define fault zone characteristics
FAULT_ZONES = {
    FaultType.SUBDUCTION: FaultZoneInfo(
        fault_type=FaultType.SUBDUCTION,
        color="#0066cc",  # Dark Blue
        description="Subduction Zone - High tsunami and magnitude risk",
        typical_depth_min=0,
        typical_depth_max=700,
        magnitude_multiplier=1.3
    ),
    FaultType.TRANSFORM: FaultZoneInfo(
        fault_type=FaultType.TRANSFORM,
        color="#ff6600",  # Orange
        description="Transform Fault - Strong lateral motion",
        typical_depth_min=0,
        typical_depth_max=50,
        magnitude_multiplier=1.0
    ),
    FaultType.REVERSE_THRUST: FaultZoneInfo(
        fault_type=FaultType.REVERSE_THRUST,
        color="#cc0000",  # Red
        description="Reverse-Thrust Fault - Vertical uplift, potential tsunami",
        typical_depth_min=0,
        typical_depth_max=300,
        magnitude_multiplier=1.2
    ),
    FaultType.NORMAL: FaultZoneInfo(
        fault_type=FaultType.NORMAL,
        color="#00cc66",  # Green
        description="Normal Fault - Extensional stress",
        typical_depth_min=0,
        typical_depth_max=30,
        magnitude_multiplier=0.9
    ),
    FaultType.DIVERGENT: FaultZoneInfo(
        fault_type=FaultType.DIVERGENT,
        color="#66ccff",  # Light Blue
        description="Divergent Boundary - Seafloor spreading",
        typical_depth_min=0,
        typical_depth_max=20,
        magnitude_multiplier=0.8
    ),
    FaultType.CONVERGENT: FaultZoneInfo(
        fault_type=FaultType.CONVERGENT,
        color="#9900cc",  # Purple
        description="Convergent Boundary - Compression zone",
        typical_depth_min=0,
        typical_depth_max=250,
        magnitude_multiplier=1.25
    ),
    FaultType.STRIKE_SLIP: FaultZoneInfo(
        fault_type=FaultType.STRIKE_SLIP,
        color="#ffcc00",  # Yellow
        description="Strike-Slip Fault - Horizontal motion",
        typical_depth_min=0,
        typical_depth_max=30,
        magnitude_multiplier=1.0
    ),
}

class IntensityCalculator:
    """
    Calculates earthquake intensities based on magnitude, depth, and location
    Provides MMI and Shindo scale values with fault type classification
    """
    
    # Known tectonic zones with fault types (lat, lon, radius_km, fault_type)
    TECTONIC_ZONES = [
        # Subduction zones
        {"name": "Japan Trench", "lat": 38.0, "lon": 142.0, "radius": 300, "fault": FaultType.SUBDUCTION},
        {"name": "Kuril-Kamchatka", "lat": 53.0, "lon": 160.0, "radius": 400, "fault": FaultType.SUBDUCTION},
        {"name": "Peru-Chile", "lat": -25.0, "lon": -70.0, "radius": 500, "fault": FaultType.SUBDUCTION},
        {"name": "Tonga-Kermadec", "lat": -18.0, "lon": 175.0, "radius": 400, "fault": FaultType.SUBDUCTION},
        {"name": "Mariana", "lat": 15.0, "lon": 145.0, "radius": 300, "fault": FaultType.SUBDUCTION},
        {"name": "Indonesia", "lat": -2.0, "lon": 115.0, "radius": 350, "fault": FaultType.SUBDUCTION},
        {"name": "Cascadia", "lat": 45.0, "lon": -124.0, "radius": 300, "fault": FaultType.SUBDUCTION},
        
        # Transform faults
        {"name": "San Andreas", "lat": 36.0, "lon": -120.5, "radius": 300, "fault": FaultType.TRANSFORM},
        {"name": "Alpine Fault NZ", "lat": -43.5, "lon": 171.5, "radius": 200, "fault": FaultType.TRANSFORM},
        {"name": "Dead Sea", "lat": 31.5, "lon": 35.5, "radius": 200, "fault": FaultType.TRANSFORM},
        
        # Mid-ocean ridges (divergent)
        {"name": "Mid-Atlantic Ridge", "lat": 0.0, "lon": -25.0, "radius": 300, "fault": FaultType.DIVERGENT},
        {"name": "East Pacific Rise", "lat": 0.0, "lon": -110.0, "radius": 300, "fault": FaultType.DIVERGENT},
        {"name": "Indian Ocean Ridge", "lat": -15.0, "lon": 65.0, "radius": 300, "fault": FaultType.DIVERGENT},
        
        # Reverse-thrust faults
        {"name": "Hindu Kush", "lat": 35.0, "lon": 70.0, "radius": 200, "fault": FaultType.REVERSE_THRUST},
        {"name": "Himalayas", "lat": 28.0, "lon": 85.0, "radius": 400, "fault": FaultType.REVERSE_THRUST},
        {"name": "Zagros", "lat": 30.0, "lon": 52.0, "radius": 300, "fault": FaultType.REVERSE_THRUST},
    ]
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km"""
        R = 6371  # Earth's radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    @staticmethod
    def classify_fault_type(latitude, longitude, depth_km):
        """
        Classify fault type based on location
        Returns FaultType and zone information
        """
        min_distance = float('inf')
        closest_zone = None
        
        for zone in IntensityCalculator.TECTONIC_ZONES:
            distance = IntensityCalculator.haversine_distance(
                latitude, longitude, zone['lat'], zone['lon']
            )
            
            if distance < zone['radius'] and distance < min_distance:
                min_distance = distance
                closest_zone = zone
        
        if closest_zone:
            fault_type = closest_zone['fault']
            return fault_type, FAULT_ZONES[fault_type]
        
        # Default classification based on depth
        if depth_km > 200:
            return FaultType.SUBDUCTION, FAULT_ZONES[FaultType.SUBDUCTION]
        elif depth_km < 20:
            return FaultType.STRIKE_SLIP, FAULT_ZONES[FaultType.STRIKE_SLIP]
        else:
            return FaultType.REVERSE_THRUST, FAULT_ZONES[FaultType.REVERSE_THRUST]
    
    @staticmethod
    def calculate_mmi(magnitude, depth_km, distance_km, fault_type=FaultType.UNKNOWN):
        """
        Calculate Modified Mercalli Intensity (MMI) at a given distance
        Based on Wald et al. (1999) empirical relationships with accurate depth handling
        
        Args:
            magnitude: Earthquake magnitude (Mw)
            depth_km: Depth of earthquake in km
            distance_km: Horizontal distance from epicenter in km
            fault_type: Type of fault (optional, for adjustments)
        
        Returns:
            MMI value (1-12)
        """
        if distance_km <= 0:
            distance_km = 0.1
        if depth_km < 0:
            depth_km = 0
        
        # Calculate hypocentral distance properly (Rh = sqrt(R^2 + h^2))
        # where R is horizontal distance and h is depth
        hypocentral_distance = math.sqrt(distance_km**2 + depth_km**2)
        
        # Wald et al. (1999) refined coefficients for crustal earthquakes
        # MMI = c1 + c2*Mw - c3*log10(Rh) - c4*Rh
        # These are the standard coefficients from the 1999 paper
        if fault_type == FaultType.SUBDUCTION:
            # Subduction zone coefficients (tend to produce more shaking)
            c1 = 5.11
            c2 = 0.826
            c3 = 2.329
            c4 = 0.0019
        elif fault_type == FaultType.REVERSE_THRUST:
            # Reverse faults (high-angle thrust)
            c1 = 5.30
            c2 = 0.830
            c3 = 2.536
            c4 = 0.0030
        elif fault_type == FaultType.TRANSFORM or fault_type == FaultType.STRIKE_SLIP:
            # Strike-slip faults (lower energy radiation)
            c1 = 4.40
            c2 = 0.952
            c3 = 2.150
            c4 = 0.0000
        else:
            # Default coefficients (crustal)
            c1 = 4.80
            c2 = 1.010
            c3 = 2.283
            c4 = 0.0090
        
        # Main MMI calculation using hypocentral distance
        mmi = c1 + c2*magnitude - c3*math.log10(hypocentral_distance + 1) - c4*hypocentral_distance
        
        # Depth-dependent correction factor
        # Deeper earthquakes produce less shaking at given distance
        # but the effect is already partially in hypocentral distance
        # Apply additional correction for very shallow earthquakes
        if depth_km < 10:
            depth_correction = 0.5  # Shallow earthquakes are more damaging
            mmi += depth_correction
        elif depth_km > 100:
            depth_correction = -0.3  # Deeper earthquakes radiate less efficiently
            mmi += depth_correction
        
        # Directivity effect for nearby epicentral distances
        if distance_km < 30 and fault_type == FaultType.STRIKE_SLIP:
            mmi += 0.5  # Strike-slip can have stronger directivity effects
        
        # Clamp MMI between 1 and 12
        mmi = max(1, min(12, mmi))
        return mmi
    
    @staticmethod
    def calculate_shindo(magnitude, depth_km, distance_km, fault_type=FaultType.UNKNOWN):
        """
        Calculate Japan Meteorological Agency (JMA) Shindo intensity
        Using empirically-calibrated relationships from seismic networks
        
        Args:
            magnitude: Earthquake magnitude (Mw)
            depth_km: Depth of earthquake in km
            distance_km: Horizontal distance from epicenter in km
            fault_type: Type of fault (optional, for adjustments)
        
        Returns:
            Shindo value (0-7)
        """
        if distance_km <= 0:
            distance_km = 0.1
        if depth_km < 0:
            depth_km = 0
        
        # Calculate hypocentral distance
        hypocentral_distance = math.sqrt(distance_km**2 + depth_km**2)
        
        # JMA-based attenuation relationships for different fault types
        # Shindo = a + b*M - c*log10(Rh) + d*depth_factor
        
        if fault_type == FaultType.SUBDUCTION:
            # Subduction earthquakes (more efficient wave propagation)
            a = 1.48
            b = 0.78
            c = 1.71
            depth_factor = 0.15 * (1.0 - min(depth_km / 700.0, 1.0))  # Maximum at 0 km, minimum at 700 km
        elif fault_type == FaultType.REVERSE_THRUST:
            # Reverse-fault earthquakes
            a = 1.32
            b = 0.75
            c = 1.60
            depth_factor = 0.10 * (1.0 - min(depth_km / 300.0, 1.0))
        elif fault_type == FaultType.STRIKE_SLIP or fault_type == FaultType.TRANSFORM:
            # Strike-slip earthquakes (lower energy radiation)
            a = 0.95
            b = 0.82
            c = 1.50
            depth_factor = 0.08 * (1.0 - min(depth_km / 50.0, 1.0))
        elif fault_type == FaultType.NORMAL:
            # Normal fault earthquakes (low stress drop)
            a = 0.85
            b = 0.70
            c = 1.45
            depth_factor = 0.06 * (1.0 - min(depth_km / 40.0, 1.0))
        else:
            # Default (crustal earthquakes)
            a = 1.10
            b = 0.76
            c = 1.60
            depth_factor = 0.12 * (1.0 - min(depth_km / 100.0, 1.0))
        
        # Calculate base Shindo
        shindo = a + b*magnitude - c*math.log10(hypocentral_distance + 1) + depth_factor
        
        # Additional depth adjustments for very shallow earthquakes
        # Shallow earthquakes produce disproportionately higher intensity
        if depth_km <= 15:
            shindo += 0.5
        elif depth_km <= 30:
            shindo += 0.3
        elif depth_km <= 50:
            shindo += 0.1
        
        # Directivity enhancement for nearby distances
        if distance_km < 25 and fault_type in [FaultType.STRIKE_SLIP, FaultType.TRANSFORM]:
            shindo += 0.6  # Enhanced for strike-slip directivity
        
        # Frequency content adjustment
        # Very shallow earthquakes have more high-frequency content
        if depth_km < 5:
            shindo += 0.3
        
        # Clamp between 0 and 7
        shindo = max(0, min(7, shindo))
        return shindo
    
    @staticmethod
    def get_mmi_scale(mmi_value):
        """Get MMI scale enum from numeric value"""
        mmi_value = round(mmi_value)
        mmi_map = {
            1: MMIScale.I, 2: MMIScale.II, 3: MMIScale.III, 4: MMIScale.IV,
            5: MMIScale.V, 6: MMIScale.VI, 7: MMIScale.VII, 8: MMIScale.VIII,
            9: MMIScale.IX, 10: MMIScale.X, 11: MMIScale.XI, 12: MMIScale.XII
        }
        return mmi_map.get(mmi_value, MMIScale.V)
    
    @staticmethod
    def get_shindo_scale(shindo_value):
        """Get Shindo scale enum from numeric value"""
        if shindo_value < 1:
            return ShindoScale.SHINDO_0
        elif shindo_value < 2:
            return ShindoScale.SHINDO_1
        elif shindo_value < 3:
            return ShindoScale.SHINDO_2
        elif shindo_value < 4:
            return ShindoScale.SHINDO_3
        elif shindo_value < 5:
            return ShindoScale.SHINDO_4
        elif shindo_value < 5.5:
            return ShindoScale.SHINDO_5_MINUS
        elif shindo_value < 6:
            return ShindoScale.SHINDO_5_PLUS
        elif shindo_value < 6.5:
            return ShindoScale.SHINDO_6_MINUS
        elif shindo_value < 7:
            return ShindoScale.SHINDO_6_PLUS
        else:
            return ShindoScale.SHINDO_7
    
    @staticmethod
    def calculate_intensity_grid(magnitude, depth_km, latitude, longitude, grid_size_km=50, max_distance_km=500):
        """
        Calculate intensity values across a grid around the epicenter
        Useful for generating heatmaps
        
        Returns:
            List of points with intensity data
        """
        fault_type, _ = IntensityCalculator.classify_fault_type(latitude, longitude, depth_km)
        
        points = []
        steps = int(max_distance_km / grid_size_km)
        
        for i in range(-steps, steps + 1):
            for j in range(-steps, steps + 1):
                # Calculate approximate coordinates (rough approximation)
                # In reality, should use proper geodetic calculations
                lat_offset = (i * grid_size_km) / 111.0  # ~111 km per degree latitude
                lon_offset = (j * grid_size_km) / (111.0 * math.cos(math.radians(latitude)))
                
                point_lat = latitude + lat_offset
                point_lon = longitude + lon_offset
                
                distance = math.sqrt((i*grid_size_km)**2 + (j*grid_size_km)**2)
                
                if distance <= max_distance_km:
                    mmi = IntensityCalculator.calculate_mmi(magnitude, depth_km, distance, fault_type)
                    shindo = IntensityCalculator.calculate_shindo(magnitude, depth_km, distance, fault_type)
                    
                    mmi_scale = IntensityCalculator.get_mmi_scale(mmi)
                    shindo_scale = IntensityCalculator.get_shindo_scale(shindo)
                    
                    points.append({
                        "latitude": point_lat,
                        "longitude": point_lon,
                        "distance_km": distance,
                        "mmi": mmi,
                        "mmi_scale": mmi_scale.name,
                        "mmi_color": mmi_scale.color,
                        "shindo": shindo,
                        "shindo_scale": shindo_scale.name,
                        "shindo_color": shindo_scale.color
                    })
        
        return points
    
    @staticmethod
    def get_intensity_report(magnitude, depth_km, latitude, longitude):
        """
        Generate a comprehensive intensity report for an earthquake
        
        Returns:
            Dictionary with fault info, MMI/Shindo scales, and recommendations
        """
        fault_type, fault_zone_info = IntensityCalculator.classify_fault_type(
            latitude, longitude, depth_km
        )
        
        # Calculate intensities at epicenter
        mmi_epicenter = IntensityCalculator.calculate_mmi(magnitude, depth_km, 0.1, fault_type)
        shindo_epicenter = IntensityCalculator.calculate_shindo(magnitude, depth_km, 0.1, fault_type)
        
        # Calculate intensities at various distances
        distances = [10, 50, 100, 200]
        intensity_profile = []
        
        for dist in distances:
            mmi = IntensityCalculator.calculate_mmi(magnitude, depth_km, dist, fault_type)
            shindo = IntensityCalculator.calculate_shindo(magnitude, depth_km, dist, fault_type)
            mmi_scale = IntensityCalculator.get_mmi_scale(mmi)
            shindo_scale = IntensityCalculator.get_shindo_scale(shindo)
            
            intensity_profile.append({
                "distance_km": dist,
                "mmi": round(mmi, 2),
                "mmi_description": mmi_scale.description,
                "shindo": round(shindo, 2),
                "shindo_description": shindo_scale.description,
            })
        
        mmi_scale_epicenter = IntensityCalculator.get_mmi_scale(mmi_epicenter)
        shindo_scale_epicenter = IntensityCalculator.get_shindo_scale(shindo_epicenter)
        
        return {
            "magnitude": magnitude,
            "depth_km": depth_km,
            "latitude": latitude,
            "longitude": longitude,
            "fault_type": fault_type.value,
            "fault_zone_color": fault_zone_info.color,
            "fault_zone_description": fault_zone_info.description,
            "epicenter_intensities": {
                "mmi": round(mmi_epicenter, 2),
                "mmi_scale": mmi_scale_epicenter.name,
                "mmi_description": mmi_scale_epicenter.description,
                "mmi_color": mmi_scale_epicenter.color,
                "shindo": round(shindo_epicenter, 2),
                "shindo_scale": shindo_scale_epicenter.name,
                "shindo_description": shindo_scale_epicenter.description,
                "shindo_color": shindo_scale_epicenter.color,
            },
            "intensity_profile": intensity_profile,
            "recommendations": get_intensity_recommendations(mmi_epicenter, shindo_epicenter, fault_type)
        }

class AgencySummaryProcessor:
    """
    Processes intensity calculations from generalized summaries
    from multiple seismic agencies: USGS, ESMC, CSEM, JMA
    
    This module decouples intensity logic from agency-specific formats,
    allowing unified MMI/Shindo calculations regardless of data source.
    """
    
    # Mapping of agency summary intensities to standardized values
    USGS_SHAKEMAP_INTENSITY_MAP = {
        "not_felt": 1,
        "weak": 3,
        "light": 4,
        "moderate": 5,
        "strong": 6,
        "very_strong": 7,
        "severe": 8,
        "violent": 9,
        "extreme": 10,
    }
    
    # European Seismic Commission (ESMC) EMS-98 to MMI mapping
    ESMC_EMS98_TO_MMI = {
        "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
        "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
        "XI": 11, "XII": 12
    }
    
    # CSEM (Swiss Seismological Commission) intensity mappings
    CSEM_INTENSITY_MAP = {
        0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6,
        6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 11: 12
    }
    
    # JMA Shindo scale (already native)
    JMA_SHINDO_NUMERIC = {
        "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
        "5minus": 5.0, "5plus": 5.5, 
        "6minus": 6.0, "6plus": 6.5,
        "7": 7.0
    }
    
    @staticmethod
    def process_usgs_summary(magnitude, depth_km, latitude, longitude, agency_summary):
        """
        Process USGS ShakeMap summary to calculate MMI and Shindo
        
        Args:
            magnitude: Earthquake magnitude
            depth_km: Depth in km
            latitude: Latitude of epicenter
            longitude: Longitude of epicenter
            agency_summary: Dict with keys like:
                - 'max_mmi_intensity': integer or string (I-XII)
                - 'impact_description': string (e.g., "moderate", "severe")
                - 'estimated_intensity_region': string
        
        Returns:
            Dict with calculated MMI and Shindo values
        """
        fault_type, _ = IntensityCalculator.classify_fault_type(latitude, longitude, depth_km)
        
        # Extract max intensity from summary
        mmi_value = 5  # Default
        if 'max_mmi_intensity' in agency_summary:
            val = agency_summary['max_mmi_intensity']
            if isinstance(val, int):
                mmi_value = val
            elif isinstance(val, str):
                # Handle Roman numerals or English names
                if val.upper() in AgencySummaryProcessor.ESMC_EMS98_TO_MMI:
                    mmi_value = AgencySummaryProcessor.ESMC_EMS98_TO_MMI[val.upper()]
        
        if 'impact_description' in agency_summary:
            desc = agency_summary['impact_description'].lower()
            if desc in AgencySummaryProcessor.USGS_SHAKEMAP_INTENSITY_MAP:
                mmi_value = AgencySummaryProcessor.USGS_SHAKEMAP_INTENSITY_MAP[desc]
        
        # Calculate Shindo from MMI
        shindo_value = IntensityCalculator.calculate_shindo(magnitude, depth_km, 0.1, fault_type)
        
        return {
            "source_agency": "USGS",
            "magnitude": magnitude,
            "depth_km": depth_km,
            "mmi": round(mmi_value, 2),
            "mmi_scale": IntensityCalculator.get_mmi_scale(mmi_value).name,
            "shindo": round(shindo_value, 2),
            "shindo_scale": IntensityCalculator.get_shindo_scale(shindo_value).name,
            "fault_type": fault_type.value,
            "summary": agency_summary
        }
    
    @staticmethod
    def process_esmc_summary(magnitude, depth_km, latitude, longitude, agency_summary):
        """
        Process ESMC (European Seismic Commission) EMS-98 summary
        
        Args:
            magnitude: Earthquake magnitude
            depth_km: Depth in km
            latitude: Latitude of epicenter
            longitude: Longitude of epicenter
            agency_summary: Dict with keys like:
                - 'ems98_intensity': Roman numeral string (I-XII)
                - 'damage_grade': integer (1-5)
                - 'affected_area': string
        
        Returns:
            Dict with calculated MMI and Shindo values
        """
        fault_type, _ = IntensityCalculator.classify_fault_type(latitude, longitude, depth_km)
        
        mmi_value = 5  # Default
        
        # Parse EMS-98 intensity
        if 'ems98_intensity' in agency_summary:
            ems_val = agency_summary['ems98_intensity'].upper()
            if ems_val in AgencySummaryProcessor.ESMC_EMS98_TO_MMI:
                mmi_value = AgencySummaryProcessor.ESMC_EMS98_TO_MMI[ems_val]
        
        # Map damage grade to MMI
        if 'damage_grade' in agency_summary:
            damage = agency_summary['damage_grade']
            if damage == 5:
                mmi_value = max(mmi_value, 10)  # Heavy damage maps to MMI X+
            elif damage == 4:
                mmi_value = max(mmi_value, 8)
            elif damage == 3:
                mmi_value = max(mmi_value, 6)
            elif damage == 2:
                mmi_value = max(mmi_value, 4)
        
        shindo_value = IntensityCalculator.calculate_shindo(magnitude, depth_km, 0.1, fault_type)
        
        return {
            "source_agency": "ESMC",
            "magnitude": magnitude,
            "depth_km": depth_km,
            "mmi": round(mmi_value, 2),
            "mmi_scale": IntensityCalculator.get_mmi_scale(mmi_value).name,
            "shindo": round(shindo_value, 2),
            "shindo_scale": IntensityCalculator.get_shindo_scale(shindo_value).name,
            "fault_type": fault_type.value,
            "summary": agency_summary
        }
    
    @staticmethod
    def process_csem_summary(magnitude, depth_km, latitude, longitude, agency_summary):
        """
        Process CSEM (Swiss Seismological Commission) intensity summary
        
        Args:
            magnitude: Earthquake magnitude
            depth_km: Depth in km
            latitude: Latitude of epicenter
            longitude: Longitude of epicenter
            agency_summary: Dict with keys like:
                - 'csem_intensity': numeric intensity value
                - 'felt_reports': count of felt reports
                - 'macroseismic_data': dict of location intensities
        
        Returns:
            Dict with calculated MMI and Shindo values
        """
        fault_type, _ = IntensityCalculator.classify_fault_type(latitude, longitude, depth_km)
        
        mmi_value = 5  # Default
        
        if 'csem_intensity' in agency_summary:
            csem_int = agency_summary['csem_intensity']
            if csem_int in AgencySummaryProcessor.CSEM_INTENSITY_MAP:
                mmi_value = AgencySummaryProcessor.CSEM_INTENSITY_MAP[csem_int]
        
        # Use felt report count as confidence indicator
        felt_count = agency_summary.get('felt_reports', 0)
        if felt_count > 1000:
            # High confidence in intensity from many reports
            pass
        elif felt_count < 10 and 'macroseismic_data' not in agency_summary:
            # Low confidence - use calculated values instead
            mmi_value = IntensityCalculator.calculate_mmi(magnitude, depth_km, 0.1, fault_type)
        
        shindo_value = IntensityCalculator.calculate_shindo(magnitude, depth_km, 0.1, fault_type)
        
        return {
            "source_agency": "CSEM",
            "magnitude": magnitude,
            "depth_km": depth_km,
            "mmi": round(mmi_value, 2),
            "mmi_scale": IntensityCalculator.get_mmi_scale(mmi_value).name,
            "shindo": round(shindo_value, 2),
            "shindo_scale": IntensityCalculator.get_shindo_scale(shindo_value).name,
            "fault_type": fault_type.value,
            "felt_reports": felt_count,
            "summary": agency_summary
        }
    
    @staticmethod
    def process_jma_summary(magnitude, depth_km, latitude, longitude, agency_summary):
        """
        Process JMA (Japan Meteorological Agency) Shindo intensity summary
        
        Args:
            magnitude: Earthquake magnitude
            depth_km: Depth in km
            latitude: Latitude of epicenter
            longitude: Longitude of epicenter
            agency_summary: Dict with keys like:
                - 'shindo_scale': numeric or string (0-7)
                - 'max_shindo_location': string (prefecture name)
                - 'estimated_seismic_intensity': string
        
        Returns:
            Dict with calculated MMI and Shindo values
        """
        fault_type, _ = IntensityCalculator.classify_fault_type(latitude, longitude, depth_km)
        
        shindo_value = 3  # Default
        
        # Parse JMA Shindo scale
        if 'shindo_scale' in agency_summary:
            shindo_key = agency_summary['shindo_scale']
            if isinstance(shindo_key, (int, float)):
                shindo_value = float(shindo_key)
            elif isinstance(shindo_key, str):
                shindo_lower = shindo_key.lower().replace(" ", "")
                if shindo_lower in AgencySummaryProcessor.JMA_SHINDO_NUMERIC:
                    shindo_value = AgencySummaryProcessor.JMA_SHINDO_NUMERIC[shindo_lower]
        
        # Calculate MMI from Shindo (reverse mapping)
        # Approximate relationship: MMI ≈ Shindo * 1.4 + 0.5
        mmi_value = shindo_value * 1.4 + 0.5
        mmi_value = max(1, min(12, mmi_value))  # Clamp to valid range
        
        return {
            "source_agency": "JMA",
            "magnitude": magnitude,
            "depth_km": depth_km,
            "mmi": round(mmi_value, 2),
            "mmi_scale": IntensityCalculator.get_mmi_scale(mmi_value).name,
            "shindo": round(shindo_value, 2),
            "shindo_scale": IntensityCalculator.get_shindo_scale(shindo_value).name,
            "fault_type": fault_type.value,
            "summary": agency_summary
        }
    
    @staticmethod
    def process_agency_summary(agency_name, magnitude, depth_km, latitude, longitude, agency_summary):
        """
        Unified processor for any agency summary
        Routes to appropriate agency processor
        
        Args:
            agency_name: Name of seismic agency (USGS, ESMC, CSEM, JMA)
            magnitude: Earthquake magnitude
            depth_km: Depth in km
            latitude: Latitude of epicenter
            longitude: Longitude of epicenter
            agency_summary: Agency-specific summary dict
        
        Returns:
            Standardized dict with MMI/Shindo calculations
        """
        agency_name = agency_name.upper().strip()
        
        if agency_name == "USGS":
            return AgencySummaryProcessor.process_usgs_summary(
                magnitude, depth_km, latitude, longitude, agency_summary
            )
        elif agency_name == "ESMC":
            return AgencySummaryProcessor.process_esmc_summary(
                magnitude, depth_km, latitude, longitude, agency_summary
            )
        elif agency_name == "CSEM":
            return AgencySummaryProcessor.process_csem_summary(
                magnitude, depth_km, latitude, longitude, agency_summary
            )
        elif agency_name == "JMA":
            return AgencySummaryProcessor.process_jma_summary(
                magnitude, depth_km, latitude, longitude, agency_summary
            )
        else:
            # Default: use direct calculations
            fault_type, _ = IntensityCalculator.classify_fault_type(latitude, longitude, depth_km)
            mmi = IntensityCalculator.calculate_mmi(magnitude, depth_km, 0.1, fault_type)
            shindo = IntensityCalculator.calculate_shindo(magnitude, depth_km, 0.1, fault_type)
            return {
                "source_agency": agency_name,
                "magnitude": magnitude,
                "depth_km": depth_km,
                "mmi": round(mmi, 2),
                "mmi_scale": IntensityCalculator.get_mmi_scale(mmi).name,
                "shindo": round(shindo, 2),
                "shindo_scale": IntensityCalculator.get_shindo_scale(shindo).name,
                "fault_type": fault_type.value,
                "summary": agency_summary
            }


def get_intensity_recommendations(mmi_value, shindo_value, fault_type):
    """Generate recommendations based on intensity values"""
    recommendations = []
    
    if mmi_value >= 8 or shindo_value >= 6:
        recommendations.append("URGENT: Immediate evacuation recommended")
        recommendations.append("Expect significant structural damage")
    elif mmi_value >= 7 or shindo_value >= 5:
        recommendations.append("HIGH: Seek shelter immediately")
        recommendations.append("Expect moderate to considerable damage")
    elif mmi_value >= 6 or shindo_value >= 4:
        recommendations.append("MODERATE: Move to safe location")
        recommendations.append("Expect minor to moderate damage")
    else:
        recommendations.append("LOW: Remain vigilant for aftershocks")
        recommendations.append("Minimal damage expected")
    
    if fault_type == FaultType.SUBDUCTION:
        recommendations.append("SUBDUCTION ZONE: High tsunami risk - move to higher ground")
    elif fault_type == FaultType.REVERSE_THRUST:
        recommendations.append("REVERSE FAULT: Potential for significant vertical displacement")
    elif fault_type == FaultType.TRANSFORM:
        recommendations.append("TRANSFORM FAULT: Expect strong lateral ground motion")
    
    return recommendations
