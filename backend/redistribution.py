"""
Zero Waste AI - Core Redistribution Logic
"""

from typing import Dict, List, Tuple, Any
import pandas as pd
from datetime import datetime
from backend.utils import calculate_distance, estimate_co2_savings

class Redistributor:
    def __init__(self, inventory_file: str, ngo_file: str):
        """Initialize the redistributor with data sources."""
        self.inventory_df = pd.read_csv(inventory_file)
        self.ngos_df = pd.read_csv(ngo_file)
        self.current_date = datetime.now()
        
    def calculate_item_priority(self, item: Dict[str, Any]) -> float:
        """Calculate priority score for an item based on multiple factors."""
        # Base priority from expiry date
        days_until_expiry = (
            pd.to_datetime(item['expiry_date']) - self.current_date
        ).days
        
        expiry_priority = max(0, 1 - (days_until_expiry / 30))
        
        # Priority based on category
        category_weights = {
            'Dairy': 1.0,
            'Meat': 1.0,
            'Seafood': 1.0,
            'Bakery': 0.8,
            'Fruit': 0.8,
            'Vegetable': 0.8,
            'FrozenDessert': 0.6,
            'Pantry': 0.4
        }
        category_priority = category_weights.get(item['category'], 0.5)
        
        # Environmental condition factor
        condition_priority = 0.0
        if item['temperature_c'] > 25 or item['humidity_percent'] > 80:
            condition_priority = 0.5
        
        # Combine factors (weighted sum)
        priority_score = (
            0.5 * expiry_priority +
            0.3 * category_priority +
            0.2 * condition_priority
        )
        
        return min(1.0, priority_score)
    
    def find_compatible_ngos(
        self, 
        item: Dict[str, Any], 
        max_distance: float = 100.0
    ) -> List[Dict[str, Any]]:
        """Find NGOs that can accept the item within constraints."""
        compatible_ngos = []
        
        for _, ngo in self.ngos_df.iterrows():
            # Check category compatibility
            if item['category'] not in ngo['accepted_categories'].split('|'):
                continue
            
            # Calculate distance
            distance = calculate_distance(
                item['latitude'], item['longitude'],
                ngo['latitude'], ngo['longitude']
            )
            
            if distance > max_distance:
                continue
            
            # Calculate match score
            co2_savings = estimate_co2_savings(distance)
            capacity_score = min(1.0, ngo['capacity_kg'] / 100)
            
            match_score = (
                0.4 * (1 - distance / max_distance) +
                0.3 * capacity_score +
                0.3 * co2_savings / 10  # Normalize CO2 savings
            )
            
            compatible_ngos.append({
                'ngo_id': ngo['ngo_id'],
                'ngo_name': ngo['ngo_name'],
                'distance_km': round(distance, 2),
                'co2_savings_kg': round(co2_savings, 2),
                'match_score': round(match_score, 3)
            })
        
        # Sort by match score
        compatible_ngos.sort(key=lambda x: x['match_score'], reverse=True)
        
        return compatible_ngos
    
    def get_redistribution_plan(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Generate a comprehensive redistribution plan."""
        # Add priority scores to inventory
        self.inventory_df['priority_score'] = self.inventory_df.apply(
            self.calculate_item_priority,
            axis=1
        )
        
        # Sort by priority
        prioritized_items = self.inventory_df.sort_values(
            'priority_score', 
            ascending=False
        )
        
        # Generate matches for high-priority items
        high_priority_items = prioritized_items[
            prioritized_items['priority_score'] >= 0.7
        ]
        
        redistribution_plan = []
        for _, item in high_priority_items.iterrows():
            matches = self.find_compatible_ngos(item)
            if matches:
                redistribution_plan.append({
                    'item_id': item['product_id'],
                    'product_name': item['product_name'],
                    'category': item['category'],
                    'priority_score': item['priority_score'],
                    'best_match': matches[0]
                })
        
        # Create summary statistics
        summary = {
            'total_items_to_redistribute': len(redistribution_plan),
            'total_co2_savings': sum(
                item['best_match']['co2_savings_kg'] 
                for item in redistribution_plan
            ),
            'avg_distance': sum(
                item['best_match']['distance_km'] 
                for item in redistribution_plan
            ) / len(redistribution_plan) if redistribution_plan else 0
        }
        
        return pd.DataFrame(redistribution_plan), summary
