from math import radians, sin, cos, sqrt, atan2
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict

# --- CONFIGURATION ---
EARTH_RADIUS_KM = 6371  # Earth radius for Haversine formula
STANDARD_EMISSION_FACTOR_KG_PER_KM = 0.2  # Assumed CO2 emission for a standard delivery vehicle
INEFFICIENCY_FACTOR = 1.4  # Assume standard routes are 40% less efficient

# Vehicle configurations
VEHICLE_TYPES = {
    "small_ev": {
        "capacity_kg": 500,
        "max_stops": 8,
        "emission_factor": 0.0,  # Electric vehicle
        "speed_kmh": 30
    },
    "medium_ev": {
        "capacity_kg": 1000,
        "max_stops": 12,
        "emission_factor": 0.0,
        "speed_kmh": 25
    },
    "hybrid": {
        "capacity_kg": 2000,
        "max_stops": 15,
        "emission_factor": 0.1,  # Half of standard
        "speed_kmh": 35
    }
}

# Green scoring weights
SCORE_WEIGHTS = {
    "distance_efficiency": 0.3,
    "capacity_utilization": 0.25,
    "emissions_saved": 0.25,
    "time_efficiency": 0.2
}

@dataclass
class DeliveryPoint:
    """Represents a delivery location with its requirements."""
    id: str
    name: str
    latitude: float
    longitude: float
    demand_kg: float
    time_window: Tuple[int, int]  # 24-hour format, e.g., (9, 17)
    priority: int  # 1 (highest) to 5 (lowest)

@dataclass
class Route:
    """Represents a delivery route with its metrics."""
    vehicle_type: str
    stops: List[str]  # List of delivery point IDs
    total_distance: float
    total_time: float
    total_load: float
    emissions_saved: float
    capacity_utilization: float

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

def calculate_distance_matrix(points: List[DeliveryPoint]) -> np.ndarray:
    """
    Calculates the distance matrix between all delivery points.
    
    Args:
        points: List of DeliveryPoint objects
        
    Returns:
        numpy.ndarray: Matrix of distances between all points
    """
    n = len(points)
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            dist = calculate_distance(
                points[i].latitude, points[i].longitude,
                points[j].latitude, points[j].longitude
            )
            matrix[i][j] = dist
            matrix[j][i] = dist
    
    return matrix

def optimize_route(
    depot: DeliveryPoint,
    delivery_points: List[DeliveryPoint],
    vehicle_type: str
) -> Route:
    """
    Implements a greedy algorithm for route optimization.
    
    Args:
        depot: Starting point for the route
        delivery_points: List of delivery locations
        vehicle_type: Type of vehicle to use
        
    Returns:
        Route: Optimized route with metrics
    """
    vehicle = VEHICLE_TYPES[vehicle_type]
    remaining_capacity = vehicle["capacity_kg"]
    current_point = depot
    unvisited = delivery_points.copy()
    route = [depot.id]
    total_distance = 0
    total_time = 0
    total_load = 0

    while unvisited and len(route) < vehicle["max_stops"]:
        # Find nearest point that fits constraints
        best_next = None
        best_distance = float('inf')
        
        for point in unvisited:
            if point.demand_kg <= remaining_capacity:
                dist = calculate_distance(
                    current_point.latitude, current_point.longitude,
                    point.latitude, point.longitude
                )
                # Adjust distance by priority (higher priority = shorter effective distance)
                adjusted_dist = dist * (point.priority / 3.0)
                
                if adjusted_dist < best_distance:
                    best_distance = adjusted_dist
                    best_next = point

        if best_next is None:
            break

        # Add point to route
        route.append(best_next.id)
        total_distance += best_distance
        total_load += best_next.demand_kg
        remaining_capacity -= best_next.demand_kg
        
        # Update time (assuming average speed from vehicle config)
        total_time += (best_distance / vehicle["speed_kmh"]) * 60  # Convert to minutes
        
        current_point = best_next
        unvisited.remove(best_next)

    # Add return to depot
    final_dist = calculate_distance(
        current_point.latitude, current_point.longitude,
        depot.latitude, depot.longitude
    )
    total_distance += final_dist
    total_time += (final_dist / vehicle["speed_kmh"]) * 60

    # Calculate metrics
    emissions_saved = estimate_co2_savings(total_distance)
    capacity_utilization = (total_load / vehicle["capacity_kg"]) * 100

    return Route(
        vehicle_type=vehicle_type,
        stops=route,
        total_distance=round(total_distance, 2),
        total_time=round(total_time, 2),
        total_load=round(total_load, 2),
        emissions_saved=round(emissions_saved, 2),
        capacity_utilization=round(capacity_utilization, 2)
    )

def calculate_green_score(route: Route) -> float:
    """
    Calculates a green score for a route based on multiple factors.
    
    Args:
        route: Route object with metrics
        
    Returns:
        float: Green score from 0 to 100
    """
    # Distance efficiency (lower is better)
    max_reasonable_distance = 100  # km
    distance_score = max(0, 100 - (route.total_distance / max_reasonable_distance * 100))
    
    # Capacity utilization (higher is better)
    capacity_score = route.capacity_utilization
    
    # Emissions saved (higher is better)
    emissions_score = min(100, route.emissions_saved * 10)
    
    # Time efficiency (lower is better)
    max_reasonable_time = 480  # 8 hours in minutes
    time_score = max(0, 100 - (route.total_time / max_reasonable_time * 100))
    
    # Weighted combination
    green_score = (
        SCORE_WEIGHTS["distance_efficiency"] * distance_score +
        SCORE_WEIGHTS["capacity_utilization"] * capacity_score +
        SCORE_WEIGHTS["emissions_saved"] * emissions_score +
        SCORE_WEIGHTS["time_efficiency"] * time_score
    )
    
    return round(green_score, 2)

def generate_impact_report(routes: List[Route]) -> Dict:
    """
    Generates a comprehensive impact report for a set of routes.
    
    Args:
        routes: List of Route objects
        
    Returns:
        dict: Impact metrics and statistics
    """
    total_distance = sum(r.total_distance for r in routes)
    total_emissions_saved = sum(r.emissions_saved for r in routes)
    total_items_delivered = sum(len(r.stops) - 1 for r in routes)  # Excluding depot
    avg_capacity_utilization = np.mean([r.capacity_utilization for r in routes])
    
    # Calculate efficiency metrics
    metrics_by_vehicle = defaultdict(lambda: {
        'routes': 0,
        'total_distance': 0,
        'total_emissions_saved': 0,
        'avg_capacity_utilization': 0
    })
    
    for route in routes:
        metrics_by_vehicle[route.vehicle_type]['routes'] += 1
        metrics_by_vehicle[route.vehicle_type]['total_distance'] += route.total_distance
        metrics_by_vehicle[route.vehicle_type]['total_emissions_saved'] += route.emissions_saved
        metrics_by_vehicle[route.vehicle_type]['avg_capacity_utilization'] += route.capacity_utilization

    # Calculate averages
    for vehicle_type in metrics_by_vehicle:
        metrics_by_vehicle[vehicle_type]['avg_capacity_utilization'] /= \
            metrics_by_vehicle[vehicle_type]['routes']

    return {
        "total_metrics": {
            "distance_covered_km": round(total_distance, 2),
            "emissions_saved_kg": round(total_emissions_saved, 2),
            "items_delivered": total_items_delivered,
            "avg_capacity_utilization": round(avg_capacity_utilization, 2)
        },
        "vehicle_metrics": dict(metrics_by_vehicle),
        "estimated_monthly_impact": {
            "co2_savings_kg": round(total_emissions_saved * 30, 2),
            "distance_reduced_km": round((total_distance * INEFFICIENCY_FACTOR - total_distance) * 30, 2),
            "fuel_saved_liters": round(total_distance * 0.1 * 30, 2)  # Assuming 0.1L/km saving
        }
    }

# --- EXAMPLE USAGE ---

if __name__ == "__main__":
    # Create sample delivery points
    depot = DeliveryPoint(
        id="DEPOT-01",
        name="Central Warehouse",
        latitude=28.7041,
        longitude=77.1025,
        demand_kg=0,
        time_window=(8, 20),
        priority=1
    )
    
    delivery_points = [
        DeliveryPoint(
            id=f"NGO-{i+1}",
            name=f"NGO Location {i+1}",
            latitude=28.7041 + np.random.uniform(-0.1, 0.1),
            longitude=77.1025 + np.random.uniform(-0.1, 0.1),
            demand_kg=np.random.uniform(50, 200),
            time_window=(9, 17),
            priority=np.random.randint(1, 5)
        ) for i in range(10)
    ]
    
    # Calculate distance matrix
    print("\nCalculating distance matrix...")
    distance_matrix = calculate_distance_matrix([depot] + delivery_points)
    
    # Optimize route
    print("\nOptimizing route...")
    route = optimize_route(depot, delivery_points, "medium_ev")
    
    # Calculate green score
    green_score = calculate_green_score(route)
    
    # Generate impact report
    impact_report = generate_impact_report([route])
    
    # Print results
    print("\nRoute Details:")
    print(f"Stops: {len(route.stops)}")
    print(f"Total Distance: {route.total_distance:.2f} km")
    print(f"Total Time: {route.total_time:.2f} minutes")
    print(f"Capacity Utilization: {route.capacity_utilization:.2f}%")
    print(f"CO2 Savings: {route.emissions_saved:.2f} kg")
    print(f"Green Score: {green_score}")
    
    print("\nImpact Report:")
    print(f"Total Emissions Saved: {impact_report['total_metrics']['emissions_saved_kg']} kg CO2")
    print(f"Average Capacity Utilization: {impact_report['total_metrics']['avg_capacity_utilization']}%")
    print("\nMonthly Projections:")
    print(f"CO2 Savings: {impact_report['estimated_monthly_impact']['co2_savings_kg']} kg")
    print(f"Distance Reduced: {impact_report['estimated_monthly_impact']['distance_reduced_km']} km")
    print(f"Fuel Saved: {impact_report['estimated_monthly_impact']['fuel_saved_liters']} L")