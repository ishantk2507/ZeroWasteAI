"""
Zero Waste AI - Route Optimization
"""

from typing import List, Dict, Any
import numpy as np
from backend.utils import calculate_distance, estimate_co2_savings

def calculate_distance_matrix(
    sources: List[Dict[str, float]], 
    destinations: List[Dict[str, float]]
) -> np.ndarray:
    """Calculate distance matrix between sources and destinations."""
    n_sources = len(sources)
    n_destinations = len(destinations)
    distances = np.zeros((n_sources, n_destinations))
    
    for i, source in enumerate(sources):
        for j, dest in enumerate(destinations):
            distances[i, j] = calculate_distance(
                source['latitude'], 
                source['longitude'],
                dest['latitude'], 
                dest['longitude']
            )
    
    return distances

def optimize_routes(
    items: List[Dict[str, Any]], 
    ngos: List[Dict[str, Any]], 
    max_vehicles: int = 3
) -> List[Dict[str, Any]]:
    """
    Optimize delivery routes considering multiple vehicles and constraints.
    Uses a greedy algorithm with environmental impact considerations.
    """
    # Create distance matrix
    sources = [{
        'latitude': item['latitude'],
        'longitude': item['longitude']
    } for item in items]
    
    destinations = [{
        'latitude': ngo['latitude'],
        'longitude': ngo['longitude']
    } for ngo in ngos]
    
    distances = calculate_distance_matrix(sources, destinations)
    
    # Initialize routes
    routes = []
    for _ in range(min(max_vehicles, len(items))):
        routes.append([])
    
    # Track used items and NGOs
    used_items = set()
    used_ngos = set()
    
    # Greedy assignment
    while len(used_items) < len(items):
        best_addition = None
        best_score = float('inf')
        best_route_idx = -1
        
        # Try adding each remaining item to each route
        for i, item in enumerate(items):
            if i in used_items:
                continue
                
            for j, ngo in enumerate(ngos):
                if j in used_ngos:
                    continue
                    
                for route_idx, route in enumerate(routes):
                    # Calculate score (combination of distance and CO2 impact)
                    additional_distance = distances[i, j]
                    co2_impact = estimate_co2_savings(additional_distance)
                    
                    # Score = distance - CO2_savings (lower is better)
                    score = additional_distance - (co2_impact * 0.1)
                    
                    if score < best_score:
                        best_score = score
                        best_addition = (i, j, additional_distance, co2_impact)
                        best_route_idx = route_idx
        
        if best_addition is None:
            break
        
        # Add best assignment to route
        item_idx, ngo_idx, distance, co2 = best_addition
        routes[best_route_idx].append({
            'item': items[item_idx],
            'ngo': ngos[ngo_idx],
            'distance_km': distance,
            'co2_savings_kg': co2
        })
        
        used_items.add(item_idx)
        used_ngos.add(ngo_idx)
    
    # Format output
    optimized_routes = []
    for route_idx, route in enumerate(routes):
        if route:  # Only include non-empty routes
            optimized_routes.append({
                'route_id': f'R{route_idx + 1}',
                'stops': route,
                'total_distance_km': sum(stop['distance_km'] for stop in route),
                'total_co2_savings_kg': sum(stop['co2_savings_kg'] for stop in route)
            })
    
    return optimized_routes

def get_route_statistics(routes: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate statistics for optimized routes."""
    if not routes:
        return {
            'total_distance_km': 0,
            'total_co2_savings_kg': 0,
            'avg_distance_per_route_km': 0,
            'avg_stops_per_route': 0
        }
    
    total_distance = sum(route['total_distance_km'] for route in routes)
    total_co2_savings = sum(route['total_co2_savings_kg'] for route in routes)
    total_stops = sum(len(route['stops']) for route in routes)
    
    return {
        'total_distance_km': round(total_distance, 2),
        'total_co2_savings_kg': round(total_co2_savings, 2),
        'avg_distance_per_route_km': round(total_distance / len(routes), 2),
        'avg_stops_per_route': round(total_stops / len(routes), 2)
    }
