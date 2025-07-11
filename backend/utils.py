"""
Zero Waste AI - Backend Utilities
"""

from math import radians, sin, cos, sqrt, atan2
from typing import Tuple

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth using Haversine formula.
    Returns distance in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Earth's radius in kilometers
    radius = 6371
    
    return radius * c

def estimate_co2_savings(distance_km: float) -> float:
    """
    Estimate CO2 emissions savings in kg for a given distance.
    Based on average truck emissions of 0.25 kg CO2 per km.
    """
    return distance_km * 0.25

def calculate_environmental_conditions(
    base_temp: float,
    base_humidity: float,
    time_factor: float,
    equipment_quality: float
) -> Tuple[float, float]:
    """
    Calculate actual temperature and humidity based on various factors.
    
    Args:
        base_temp: Base temperature in Celsius
        base_humidity: Base humidity percentage
        time_factor: Time-based adjustment factor (0-1)
        equipment_quality: Quality of storage equipment (0-1)
        
    Returns:
        Tuple of (actual_temperature, actual_humidity)
    """
    # Temperature variation
    temp_variation = (1 - equipment_quality) * 5  # Up to 5°C variation
    actual_temp = base_temp + (temp_variation * (1 - time_factor))
    
    # Humidity variation
    humidity_variation = (1 - equipment_quality) * 15  # Up to 15% variation
    actual_humidity = base_humidity + (humidity_variation * (1 - time_factor))
    
    # Ensure values are within reasonable bounds
    actual_temp = max(-30, min(40, actual_temp))
    actual_humidity = max(0, min(100, actual_humidity))
    
    return actual_temp, actual_humidity
