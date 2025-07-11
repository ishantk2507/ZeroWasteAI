import os
import random
import csv
from datetime import datetime, timedelta
from faker import Faker

# --- CONFIGURATION ---

# Ensure the output directory exists
os.makedirs("data", exist_ok=True)

# Initialize Faker for generating mock data
Faker.seed(42)
fake = Faker('en_IN')

# Define locations with approximate latitude and longitude for logistics simulation
LOCATIONS = {
    "Delhi": {"lat": 28.7041, "lon": 77.1025, "stores": ["DEL-01", "DEL-02"]},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777, "stores": ["MUM-01", "MUM-02", "MUM-03"]},
    "Bangalore": {"lat": 12.9716, "lon": 77.5946, "stores": ["BLR-01", "BLR-02"]},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639, "stores": ["KOL-01"]},
    "Chennai": {"lat": 13.0827, "lon": 80.2707, "stores": ["CHE-01", "CHE-02"]}
}

# Define product profiles (category, storage type, ideal ranges, shelf life)
PRODUCT_PROFILES = [
    {"product": "Apple", "category": "Fruit", "storage_type": "Refrigerated", "temp_range": (0, 4), "humidity_range": (80, 95), "shelf_life_days": (20, 30)},
    {"product": "Banana", "category": "Fruit", "storage_type": "Ambient", "temp_range": (15, 20), "humidity_range": (60, 75), "shelf_life_days": (3, 7)},
    {"product": "Milk", "category": "Dairy", "storage_type": "Refrigerated", "temp_range": (1, 4), "humidity_range": (85, 95), "shelf_life_days": (10, 15)},
    {"product": "Bread", "category": "Bakery", "storage_type": "Ambient", "temp_range": (20, 25), "humidity_range": (50, 70), "shelf_life_days": (3, 5)},
    {"product": "Chicken", "category": "Meat", "storage_type": "Refrigerated", "temp_range": (0, 4), "humidity_range": (85, 95), "shelf_life_days": (5, 10)},
    {"product": "Fish", "category": "Seafood", "storage_type": "Frozen", "temp_range": (-20, -15), "humidity_range": (75, 85), "shelf_life_days": (30, 60)},
    {"product": "Carrots", "category": "Vegetable", "storage_type": "Refrigerated", "temp_range": (0, 4), "humidity_range": (85, 95), "shelf_life_days": (15, 30)},
    {"product": "Ice Cream", "category": "FrozenDessert", "storage_type": "Frozen", "temp_range": (-25, -18), "humidity_range": (50, 60), "shelf_life_days": (180, 365)},
    {"product": "Canned Beans", "category": "Pantry", "storage_type": "Ambient", "temp_range": (10, 25), "humidity_range": (30, 50), "shelf_life_days": (365, 730)},
    {"product": "Eggs", "category": "Dairy", "storage_type": "Refrigerated", "temp_range": (1, 4), "humidity_range": (80, 85), "shelf_life_days": (21, 30)}
]

# Define seasonal patterns
SEASONS = {
    "Summer": {
        "months": [3, 4, 5],  # March to May in India
        "temp_modifier": 5,
        "humidity_modifier": 15,
        "high_demand": ["Ice Cream", "Banana", "Fish"],
        "low_demand": ["Bread", "Milk"]
    },
    "Monsoon": {
        "months": [6, 7, 8],  # June to August
        "temp_modifier": -2,
        "humidity_modifier": 30,
        "high_demand": ["Bread", "Milk", "Canned Beans"],
        "low_demand": ["Ice Cream"]
    },
    "Winter": {
        "months": [11, 12, 1],  # November to January
        "temp_modifier": -5,
        "humidity_modifier": -20,
        "high_demand": ["Milk", "Bread", "Chicken"],
        "low_demand": ["Ice Cream", "Fish"]
    }
}

# Enhanced store characteristics
STORE_PROFILES = {
    "premium": {
        "equipment_quality": (4, 5),  # Range of possible values
        "temp_variance": 1.5,
        "humidity_variance": 5,
        "storage_capacity": (200, 400),
        "staff_count": (15, 25)
    },
    "standard": {
        "equipment_quality": (3, 4),
        "temp_variance": 2.5,
        "humidity_variance": 8,
        "storage_capacity": (100, 200),
        "staff_count": (8, 15)
    },
    "budget": {
        "equipment_quality": (2, 3),
        "temp_variance": 3.5,
        "humidity_variance": 12,
        "storage_capacity": (50, 100),
        "staff_count": (4, 8)
    }
}

# Business hours and peak times
BUSINESS_HOURS = {
    "weekday": {"open": 9, "close": 21, "peaks": [(9, 11), (17, 19)]},
    "weekend": {"open": 10, "close": 22, "peaks": [(11, 13), (16, 20)]}
}

# --- FUNCTION DEFINITIONS ---

def generate_inventory_data(num_rows=500):
    """Generates mock inventory data with realistic patterns and risk factors."""
    inventory_data = []
    current_date = datetime.now()

    for i in range(num_rows):
        # Product selection with seasonal weighting
        season, season_details = get_current_season(current_date)
        if season_details and random.random() < 0.7:  # 70% chance of seasonal influence
            # Prioritize high-demand seasonal products
            seasonal_products = [p for p in PRODUCT_PROFILES if p["product"] in season_details["high_demand"]]
            profile = random.choice(seasonal_products if seasonal_products else PRODUCT_PROFILES)
        else:
            profile = random.choice(PRODUCT_PROFILES)

        # Location and store selection
        location_name = random.choice(list(LOCATIONS.keys()))
        location_details = LOCATIONS[location_name]
        store_id = random.choice(location_details["stores"])
        store_profile = get_store_profile(store_id)

        # Product and store info
        product = profile["product"]
        category = profile["category"]
        storage = profile["storage_type"]
        
        # Add small random offset to lat/lon to simulate different store locations within a city
        lat = location_details["lat"] + random.uniform(-0.05, 0.05)
        lon = location_details["lon"] + random.uniform(-0.05, 0.05)

        # More realistic stock date generation based on product type and store profile
        max_stock_age = 7 if category in ["Bakery", "Dairy"] else 30
        stock_days_ago = int(random.triangular(0, max_stock_age, max_stock_age * 0.3))
        stock_date = current_date - timedelta(days=stock_days_ago)
        
        # Shelf life calculation with store quality influence
        shelf_min, shelf_max = profile["shelf_life_days"]
        quality_modifier = STORE_PROFILES[store_profile]["equipment_quality"][0] / 5.0
        adjusted_shelf_life = int(random.uniform(shelf_min, shelf_max) * quality_modifier)
        expiry_date = stock_date + timedelta(days=adjusted_shelf_life)

        # Generate environmental conditions with seasonal and store quality effects
        temp, hum = generate_environmental_conditions(profile, store_profile, current_date)

        # Calculate sophisticated spoilage risk
        days_on_shelf = (current_date.date() - stock_date.date()).days
        total_risk = calculate_spoilage_risk(profile, temp, hum, days_on_shelf, store_profile)
        
        # Apply demand-based modifications
        demand_modifier = calculate_demand_modifier(current_date, product, store_profile)
        total_risk *= (2 - demand_modifier)  # Higher demand = lower risk due to faster turnover
        
        spoilage_label = 1 if random.random() < total_risk else 0

        inventory_data.append({
            "product_id": f"PROD-{1001 + i}",
            "product_name": product,
            "category": category,
            "stock_date": stock_date.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "storage_type": storage,
            "store_id": store_id,
            "location": location_name,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "temperature_c": temp,
            "humidity_percent": hum,
            "spoilage": spoilage_label
        })
    return inventory_data

def generate_ngo_data(num_ngos=20):
    """Generates mock NGO data for redistribution."""
    ngo_data = []
    categories = [p["category"] for p in PRODUCT_PROFILES]
    
    for i in range(num_ngos):
        name = fake.company() + " Foundation"
        location_name = random.choice(list(LOCATIONS.keys()))
        location_details = LOCATIONS[location_name]
        
        # Add small random offset to lat/lon to simulate different NGO locations
        lat = location_details["lat"] + random.uniform(-0.1, 0.1)
        lon = location_details["lon"] + random.uniform(-0.1, 0.1)

        # Assign accepted categories
        accepted_cats = random.sample(list(set(categories)), k=random.randint(2, 5))
        
        ngo_data.append({
            "ngo_id": f"NGO-{101 + i}",
            "ngo_name": name,
            "location": location_name,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "capacity_kg": random.randint(50, 500),
            "accepted_categories": "|".join(accepted_cats)
        })
    return ngo_data

def write_csv(file_path, data, headers):
    """Writes a list of dictionaries to a CSV file."""
    with open(file_path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    print(f"Successfully generated {file_path}")

def get_current_season(date):
    """Determine the current season based on the date."""
    month = date.month
    for season, details in SEASONS.items():
        if month in details["months"]:
            return season, details
    return "Regular", None

def get_store_profile(store_id):
    """Assign store profile based on store ID pattern."""
    if store_id.endswith("01"):  # First stores in each city are premium
        return "premium"
    elif store_id.endswith("02"):  # Second stores are standard
        return "standard"
    return "budget"  # Rest are budget stores

def calculate_demand_modifier(date, product, store_profile):
    """Calculate demand modifier based on various factors."""
    weekday = date.weekday()
    hour = date.hour if isinstance(date, datetime) else 12
    
    # Base modifier
    modifier = 1.0
    
    # Weekend boost
    if weekday >= 5:
        modifier *= 1.3
    
    # Peak hours boost
    business_hours = BUSINESS_HOURS["weekend" if weekday >= 5 else "weekday"]
    for peak_start, peak_end in business_hours["peaks"]:
        if peak_start <= hour <= peak_end:
            modifier *= 1.4
            break
    
    # Seasonal effects
    season, season_details = get_current_season(date)
    if season_details:
        if product in season_details["high_demand"]:
            modifier *= 1.5
        elif product in season_details["low_demand"]:
            modifier *= 0.7
    
    # Store profile effects
    if store_profile == "premium":
        modifier *= 1.2
    elif store_profile == "budget":
        modifier *= 0.8
    
    return modifier

def generate_environmental_conditions(profile, store_profile, date):
    """Generate realistic environmental conditions based on multiple factors."""
    min_temp, max_temp = profile["temp_range"]
    min_hum, max_hum = profile["humidity_range"]
    
    # Get base values
    base_temp = (min_temp + max_temp) / 2
    base_hum = (min_hum + max_hum) / 2
    
    # Apply seasonal modifications
    season, season_details = get_current_season(date)
    if season_details:
        base_temp += season_details["temp_modifier"]
        base_hum += season_details["humidity_modifier"]
    
    # Apply store quality effects
    store_quality = STORE_PROFILES[store_profile]
    temp_variance = store_quality["temp_variance"]
    hum_variance = store_quality["humidity_variance"]
    
    # Generate final values with controlled randomness
    temp = random.gauss(base_temp, temp_variance)
    hum = random.gauss(base_hum, hum_variance)
    
    # Ensure values stay within realistic bounds
    temp = max(min(temp, 50), -30)
    hum = max(min(hum, 100), 0)
    
    return round(temp, 1), round(hum, 1)

def calculate_spoilage_risk(product_profile, temp, humidity, days_on_shelf, store_profile):
    """Calculate sophisticated spoilage risk based on multiple factors."""
    # Base time risk
    shelf_min, shelf_max = product_profile["shelf_life_days"]
    time_risk = days_on_shelf / shelf_max
    
    # Temperature deviation risk
    min_temp, max_temp = product_profile["temp_range"]
    temp_deviation = max(0, temp - max_temp) + max(0, min_temp - temp)
    temp_risk = min(temp_deviation / 10, 1.0)
    
    # Humidity deviation risk
    min_hum, max_hum = product_profile["humidity_range"]
    hum_deviation = max(0, humidity - max_hum) + max(0, min_hum - humidity)
    hum_risk = min(hum_deviation / 20, 1.0)
    
    # Store quality impact
    store_quality = STORE_PROFILES[store_profile]["equipment_quality"][0]
    quality_factor = (6 - store_quality) / 5
    
    # Combine risks with weights
    total_risk = (
        0.35 * time_risk +
        0.25 * temp_risk +
        0.20 * hum_risk +
        0.15 * quality_factor +
        0.05 * random.random()  # Small random factor
    )
    
    return min(1.0, total_risk)

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    # Generate and write inventory data
    inventory_headers = [
        "product_id", "product_name", "category", "stock_date", "expiry_date", 
        "storage_type", "store_id", "location", "latitude", "longitude",
        "temperature_c", "humidity_percent", "spoilage"
    ]
    inventory_data = generate_inventory_data()
    write_csv("data/mock_inventory.csv", inventory_data, inventory_headers)

    # Generate and write NGO data
    ngo_headers = [
        "ngo_id", "ngo_name", "location", "latitude", "longitude", 
        "capacity_kg", "accepted_categories"
    ]
    ngo_data = generate_ngo_data()
    write_csv("data/mock_ngos.csv", ngo_data, ngo_headers)
