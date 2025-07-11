import pandas as pd
from datetime import datetime, timedelta
from logistics import calculate_distance, estimate_co2_savings
import logging

# --- CONFIGURATION ---
INVENTORY_FILE = 'data/mock_inventory.csv'
NGO_FILE = 'data/mock_ngos.csv'

# Category-specific constraints
CATEGORY_CONSTRAINTS = {
    "Meat": {
        "max_distance_km": 50,    # Maximum distance for meat products
        "min_freshness": 20,      # Minimum freshness required
        "min_days": 2            # Minimum days remaining
    },
    "Seafood": {
        "max_distance_km": 50,
        "min_freshness": 20,
        "min_days": 2
    },
    "Dairy": {
        "max_distance_km": 100,
        "min_freshness": 15,
        "min_days": 3
    },
    "Bakery": {
        "max_distance_km": 75,
        "min_freshness": 15,
        "min_days": 1
    },
    "Fruit": {
        "max_distance_km": 150,
        "min_freshness": 10,
        "min_days": 2
    },
    "Vegetable": {
        "max_distance_km": 150,
        "min_freshness": 10,
        "min_days": 2
    },
    "FrozenDessert": {
        "max_distance_km": 200,
        "min_freshness": 5,
        "min_days": 5
    },
    "Pantry": {
        "max_distance_km": 500,
        "min_freshness": 5,
        "min_days": 7
    }
}

# Default constraints for categories not explicitly listed
DEFAULT_CONSTRAINTS = {
    "max_distance_km": 200,
    "min_freshness": 10,
    "min_days": 3
}

# Redistribution thresholds and settings
FRESHNESS_THRESHOLDS = {
    "critical": 10.0,     # Items that need immediate redistribution
    "warning": 20.0,      # Items to plan for redistribution
    "monitor": 30.0       # Items to keep monitoring
}

CATEGORY_PRIORITIES = {
    "Dairy": 1,          # Highest priority (perishable)
    "Meat": 1,
    "Seafood": 1,
    "Bakery": 2,         # High priority
    "Fruit": 2,
    "Vegetable": 2,
    "FrozenDessert": 3,  # Medium priority
    "Pantry": 4          # Low priority (long shelf life)
}

MATCHING_WEIGHTS = {
    "distance": 0.4,     # Closer NGOs preferred
    "capacity": 0.3,     # NGOs with more capacity preferred
    "category_focus": 0.3 # NGOs specializing in fewer categories preferred
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- CORE FUNCTIONS ---

def calculate_freshness(stock_date_str, expiry_date_str, category=None):
    """
    Calculates the freshness of an item as a percentage (0-100) with category-specific adjustments.

    Args:
        stock_date_str (str): The date the item was stocked (ISO format).
        expiry_date_str (str): The date the item expires (ISO format).
        category (str, optional): The product category for specific adjustments.

    Returns:
        tuple: (freshness_score, warning_level, days_remaining)
            - freshness_score: float from 0 to 100
            - warning_level: str ('critical', 'warning', 'monitor', or 'good')
            - days_remaining: int, number of days until expiry
    """
    stock_date = datetime.fromisoformat(stock_date_str).date()
    expiry_date = datetime.fromisoformat(expiry_date_str).date()
    current_date = datetime.now().date()

    if current_date >= expiry_date:
        return 0.0, 'critical', 0

    total_shelf_life = (expiry_date - stock_date).days
    days_remaining = (expiry_date - current_date).days

    if total_shelf_life <= 0:
        return 0.0, 'critical', 0

    # Base freshness calculation
    freshness_score = (days_remaining / total_shelf_life) * 100
    
    # Category-specific adjustments
    if category:
        priority = CATEGORY_PRIORITIES.get(category, 3)
        if priority == 1:  # High-priority perishables
            freshness_score *= 0.9  # Reduce freshness faster
        elif priority == 4:  # Low-priority non-perishables
            freshness_score *= 1.1  # Reduce freshness slower
    
    # Ensure score stays within bounds
    freshness_score = max(0, min(freshness_score, 100))
    
    # Determine warning level
    if freshness_score <= FRESHNESS_THRESHOLDS['critical']:
        warning_level = 'critical'
    elif freshness_score <= FRESHNESS_THRESHOLDS['warning']:
        warning_level = 'warning'
    elif freshness_score <= FRESHNESS_THRESHOLDS['monitor']:
        warning_level = 'monitor'
    else:
        warning_level = 'good'
    
    return freshness_score, warning_level, days_remaining

def find_best_matches(item, ngos_df):
    """
    Finds the best NGO matches for a given item using a sophisticated matching algorithm.

    Args:
        item (pd.Series): A pandas Series object representing the item to redistribute.
        ngos_df (pd.DataFrame): A DataFrame containing all NGO data.

    Returns:
        tuple: (matches, stats)
            - matches: list of matched NGOs with scores and details
            - stats: dict containing matching statistics and recommendations
    """
    logger.info(f"Finding matches for {item['product_name']} (ID: {item['product_id']})")
    
    # Get category-specific constraints
    constraints = CATEGORY_CONSTRAINTS.get(item['category'], DEFAULT_CONSTRAINTS)
    
    # Check if item meets minimum redistribution criteria
    freshness_score, warning_level, days_remaining = calculate_freshness(
        item['stock_date'], 
        item['expiry_date'],
        item['category']
    )
    
    if (freshness_score < constraints['min_freshness'] or 
        days_remaining < constraints['min_days']):
        logger.warning(
            f"Item {item['product_id']} does not meet minimum criteria for redistribution: "
            f"freshness={freshness_score:.1f}%, days_remaining={days_remaining}"
        )
        return [], {
            "status": "not_redistributable",
            "reason": "below_minimum_criteria",
            "details": {
                "freshness": freshness_score,
                "days_remaining": days_remaining,
                "min_freshness_required": constraints['min_freshness'],
                "min_days_required": constraints['min_days']
            }
        }
    
    # 1. Filter NGOs that accept the item's category
    compatible_ngos = ngos_df[ngos_df['accepted_categories'].str.contains(item['category'])]

    if compatible_ngos.empty:
        logger.warning(f"No compatible NGOs found for category: {item['category']}")
        return [], {"status": "no_matches", "reason": "category_incompatible"}

    # 2. Calculate comprehensive matching scores
    matches = []
    total_capacity = 0
    max_distance = constraints['max_distance_km']
    
    for _, ngo in compatible_ngos.iterrows():
        # Calculate base metrics
        dist = calculate_distance(
            item['latitude'], item['longitude'],
            ngo['latitude'], ngo['longitude']
        )
        
        # Skip NGOs that are too far away
        if dist > max_distance:
            continue
            
        co2_saved = estimate_co2_savings(dist)
        
        # Calculate specialized scores
        # Distance score now considers category-specific max distance
        distance_score = 1 - (dist / max_distance)
        
        # Improved capacity scoring
        # Consider both absolute capacity and available capacity percentage
        min_required_capacity = 10  # Minimum kg capacity needed
        capacity_score = min(1.0, (ngo['capacity_kg'] - min_required_capacity) / 200)
        
        # Calculate category focus score with diminishing returns
        category_count = len(ngo['accepted_categories'].split('|'))
        category_focus_score = 1 / (1 + 0.2 * category_count)  # Steeper penalty for too many categories
        
        # Additional scoring factors
        urgency_multiplier = 1.2 if warning_level == 'critical' else 1.0
        
        # Weighted combination of scores with urgency multiplier
        match_score = urgency_multiplier * (
            MATCHING_WEIGHTS['distance'] * distance_score +
            MATCHING_WEIGHTS['capacity'] * capacity_score +
            MATCHING_WEIGHTS['category_focus'] * category_focus_score
        )

        ngo_match = ngo.to_dict()
        ngo_match.update({
            'distance_km': round(dist, 2),
            'co2_savings_kg': round(co2_saved, 2),
            'match_score': round(match_score, 4),
            'distance_score': round(distance_score, 4),
            'capacity_score': round(capacity_score, 4),
            'category_focus_score': round(category_focus_score, 4)
        })
        matches.append(ngo_match)
        total_capacity += ngo['capacity_kg']

    # 3. Sort matches by score in descending order
    matches.sort(key=lambda x: x['match_score'], reverse=True)

    # 4. Calculate matching statistics
    stats = {
        "status": "matches_found",
        "total_matches": len(matches),
        "total_capacity_kg": total_capacity,
        "avg_distance_km": sum(m['distance_km'] for m in matches) / len(matches),
        "total_potential_co2_savings": sum(m['co2_savings_kg'] for m in matches),
        "recommendation": "proceed" if len(matches) > 0 else "expand_search"
    }

    # Add time-sensitivity based recommendations
    freshness_score, warning_level, days_remaining = calculate_freshness(
        item['stock_date'], 
        item['expiry_date'],
        item['category']
    )
    
    stats.update({
        "item_freshness": round(freshness_score, 2),
        "warning_level": warning_level,
        "days_remaining": days_remaining,
        "urgency": "high" if warning_level in ['critical', 'warning'] else "medium"
    })

    logger.info(f"Found {len(matches)} potential matches for {item['product_name']}")
    return matches, stats

# --- MAIN CLASS (ENGINE) ---

class RedistributionEngine:
    def __init__(self):
        """Initializes the engine by loading the datasets and setting up monitoring."""
        logger.info("Initializing Redistribution Engine...")
        self.stats = {
            "total_items_processed": 0,
            "successful_matches": 0,
            "items_by_warning_level": {
                "critical": 0,
                "warning": 0,
                "monitor": 0,
                "good": 0
            },
            "items_by_category": {}
        }
        
        try:
            self.inventory_df = pd.read_csv(INVENTORY_FILE)
            self.ngos_df = pd.read_csv(NGO_FILE)
            self._initialize_monitoring()
            logger.info("Datasets loaded successfully.")
        except FileNotFoundError as e:
            logger.error(f"Error loading data: {e}")
            logger.error("Please ensure mock data has been generated by running `ml/data_generation.py`")
            self.inventory_df = pd.DataFrame()
            self.ngos_df = pd.DataFrame()

    def _initialize_monitoring(self):
        """Sets up initial monitoring statistics."""
        if not self.inventory_df.empty:
            # Initialize category statistics
            for category in self.inventory_df['category'].unique():
                self.stats["items_by_category"][category] = {
                    "total": 0,
                    "needs_redistribution": 0,
                    "successfully_matched": 0
                }

    def get_redistribution_candidates(self, warning_level='warning'):
        """
        Identifies items needing redistribution based on warning level.
        
        Args:
            warning_level (str): Minimum warning level to consider ('critical', 'warning', or 'monitor')
        
        Returns:
            tuple: (candidates_df, summary)
                - candidates_df: DataFrame of items needing redistribution
                - summary: Dict with analysis and recommendations
        """
        if self.inventory_df.empty:
            return pd.DataFrame(), {"status": "no_data"}

        # Calculate freshness and warning levels for all items
        self.inventory_df[['freshness', 'warning_level', 'days_remaining']] = self.inventory_df.apply(
            lambda row: calculate_freshness(row['stock_date'], row['expiry_date'], row['category']),
            axis=1,
            result_type='expand'
        )

        # Map warning levels to numerical values for filtering
        warning_priorities = {
            'critical': 0,
            'warning': 1,
            'monitor': 2,
            'good': 3
        }
        
        threshold_priority = warning_priorities[warning_level]
        
        # Filter and sort candidates
        candidates = self.inventory_df[
            self.inventory_df['warning_level'].map(warning_priorities) <= threshold_priority
        ].copy()
        
        candidates = candidates.sort_values(
            by=['warning_level', 'freshness'],
            key=lambda x: x.map(warning_priorities) if x.name == 'warning_level' else x,
            ascending=[True, True]
        )

        # Generate summary statistics
        summary = {
            "total_candidates": len(candidates),
            "by_warning_level": candidates['warning_level'].value_counts().to_dict(),
            "by_category": candidates['category'].value_counts().to_dict(),
            "avg_days_remaining": candidates['days_remaining'].mean(),
            "urgent_items": len(candidates[candidates['warning_level'] == 'critical']),
            "recommendation": self._generate_redistribution_recommendation(candidates)
        }

        return candidates, summary

    def _generate_redistribution_recommendation(self, candidates_df):
        """Generates strategic recommendations based on candidate analysis."""
        if candidates_df.empty:
            return "No items currently need redistribution"
            
        urgent_count = len(candidates_df[candidates_df['warning_level'] == 'critical'])
        total_count = len(candidates_df)
        
        if urgent_count > 0:
            return f"URGENT: {urgent_count} items need immediate redistribution"
        elif total_count > 10:
            return "Consider batch redistribution to optimize logistics"
        else:
            return "Monitor items and plan ahead for redistribution"

    def run_engine_for_item(self, product_id):
        """
        Runs comprehensive redistribution analysis for a single product.
        
        Args:
            product_id (str): The ID of the product to process.
            
        Returns:
            dict: Complete analysis including:
                - item_details: Dict of item information
                - matches: List of matched NGOs
                - stats: Matching statistics and recommendations
                - historic_data: Any relevant historical data
        """
        try:
            item = self.inventory_df[self.inventory_df['product_id'] == product_id].iloc[0]
        except (IndexError, KeyError):
            logger.error(f"Product ID {product_id} not found in inventory")
            return {"status": "error", "message": "Product not found"}
        
        # Get freshness analysis
        freshness_score, warning_level, days_remaining = calculate_freshness(
            item['stock_date'], 
            item['expiry_date'],
            item['category']
        )
        
        if warning_level == 'good':
            logger.info(f"Item {product_id} has adequate freshness ({freshness_score:.2f}%)")
            return {
                "status": "no_action_needed",
                "item_details": item.to_dict(),
                "analysis": {
                    "freshness_score": freshness_score,
                    "warning_level": warning_level,
                    "days_remaining": days_remaining
                }
            }
        
        # Find and analyze matches
        matches, match_stats = find_best_matches(item, self.ngos_df)
        
        # Update monitoring stats
        self.stats["total_items_processed"] += 1
        self.stats["items_by_warning_level"][warning_level] += 1
        self.stats["successful_matches"] += 1 if matches else 0
        
        category_stats = self.stats["items_by_category"].get(item['category'], {"total": 0, "needs_redistribution": 0, "successfully_matched": 0})
        category_stats["total"] += 1
        category_stats["needs_redistribution"] += 1
        if matches:
            category_stats["successfully_matched"] += 1
        self.stats["items_by_category"][item['category']] = category_stats

        return {
            "status": "success",
            "item_details": item.to_dict(),
            "matches": matches,
            "stats": match_stats,
            "monitoring": {
                "freshness_score": freshness_score,
                "warning_level": warning_level,
                "days_remaining": days_remaining
            }
        }

# --- EXAMPLE USAGE ---

if __name__ == '__main__':
    engine = RedistributionEngine()

    # Example 1: Get all items that are candidates for redistribution
    print("\n--- Finding redistribution candidates ---")
    candidates_df, summary = engine.get_redistribution_candidates(warning_level='warning')
    
    print(f"\nRedistribution Summary:")
    print(f"Total candidates: {summary['total_candidates']}")
    print(f"By warning level: {summary['by_warning_level']}")
    print(f"Average days remaining: {summary['avg_days_remaining']:.1f}")
    print(f"Recommendation: {summary['recommendation']}")
    
    if not candidates_df.empty:
        print("\nTop candidates:")
        print(candidates_df[['product_id', 'product_name', 'category', 'warning_level', 'freshness', 'days_remaining']].head())

    # Example 2: Run the engine for a specific item from the candidates list
    if not candidates_df.empty:
        sample_item_id = candidates_df.iloc[0]['product_id']
        print(f"\n--- Running engine for a sample item: {sample_item_id} ---")
        
        result = engine.run_engine_for_item(sample_item_id)
        
        if result['status'] == 'success':
            item_details = result['item_details']
            matches = result['matches']
            stats = result['stats']
            
            print(f"\nItem Analysis:")
            print(f"Product: {item_details['product_name']} ({item_details['category']})")
            print(f"Warning Level: {result['monitoring']['warning_level']}")
            print(f"Freshness: {result['monitoring']['freshness_score']:.1f}%")
            print(f"Days Remaining: {result['monitoring']['days_remaining']}")
            
            if matches:
                print(f"\nTop 3 NGO matches:")
                for match in matches[:3]:
                    print(
                        f"  - NGO: {match['ngo_name']} ({match['location']})"
                        f"\n    Distance: {match['distance_km']} km"
                        f" | CO2 Saved: {match['co2_savings_kg']} kg"
                        f" | Capacity: {match['capacity_kg']} kg"
                        f"\n    Match Score: {match['match_score']:.3f}"
                        f" (Distance: {match['distance_score']:.2f},"
                        f" Capacity: {match['capacity_score']:.2f},"
                        f" Category Focus: {match['category_focus_score']:.2f})"
                    )
                
                print(f"\nMatching Statistics:")
                print(f"Total matches found: {stats['total_matches']}")
                print(f"Average distance: {stats['avg_distance_km']:.1f} km")
                print(f"Total potential CO2 savings: {stats['total_potential_co2_savings']:.1f} kg")
            else:
                print("No compatible NGOs found for this item.")
        else:
            print(f"Status: {result['status']}")
            if 'message' in result:
                print(f"Message: {result['message']}")