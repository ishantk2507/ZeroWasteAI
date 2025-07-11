from math import radians, sin, cos, sqrt, atan2

# --- CONFIGURATION ---
EARTH_RADIUS_KM = 6371  # Earth radius for Haversine formula
STANDARD_EMISSION_FACTOR_KG_PER_KM = 0.2  # Assumed CO2 emission for a standard delivery vehicle
INEFFICIENCY_FACTOR = 1.4  # Assume standard routes are 40% less efficient

# --- GEOSPATIAL AND LOGISTICS FUNCTIONS ---

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two points using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of point 1.
        lat2, lon2: Latitude and longitude of point 2.

    Returns:
        float: Distance in kilometers.
    """
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = EARTH_RADIUS_KM * c
    return distance

def estimate_co2_savings(distance_km):
    """
    Estimates the CO2 savings for a green route compared to a standard route.
    
    Args:
        distance_km (float): The direct distance of the green route.
        
    Returns:
        float: The estimated kilograms of CO2 saved.
    """
    standard_route_distance = distance_km * INEFFICIENCY_FACTOR
    
    co2_standard = standard_route_distance * STANDARD_EMISSION_FACTOR_KG_PER_KM
    co2_green = distance_km * STANDARD_EMISSION_FACTOR_KG_PER_KM
    
    savings = co2_standard - co2_green
    return round(savings, 2)