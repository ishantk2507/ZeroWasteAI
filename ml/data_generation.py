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

# --- FUNCTION DEFINITIONS ---

def generate_inventory_data(num_rows=500):
    """Generates mock inventory data with spoilage risk factors."""
    inventory_data = []
    current_date = datetime.now().date()

    for i in range(num_rows):
        profile = random.choice(PRODUCT_PROFILES)
        location_name = random.choice(list(LOCATIONS.keys()))
        location_details = LOCATIONS[location_name]

        # Product and store info
        product = profile["product"]
        category = profile["category"]
        storage = profile["storage_type"]
        store_id = random.choice(location_details["stores"])
        
        # Add small random offset to lat/lon to simulate different store locations within a city
        lat = location_details["lat"] + random.uniform(-0.05, 0.05)
        lon = location_details["lon"] + random.uniform(-0.05, 0.05)

        # Random stock date and expiry date based on shelf life
        stock_days_ago = random.randint(0, 30)
        stock_date = current_date - timedelta(days=stock_days_ago)
        shelf_min, shelf_max = profile["shelf_life_days"]
        chosen_life = random.randint(shelf_min, shelf_max)
        expiry_date = stock_date + timedelta(days=chosen_life)

        # Simulate environment conditions with some deviation
        min_temp, max_temp = profile["temp_range"]
        avg_temp = (min_temp + max_temp) / 2
        temp = random.gauss(avg_temp, 3)  # Gaussian distribution around the average
        temp = round(max(min(temp, 50), -30), 1)

        min_hum, max_hum = profile["humidity_range"]
        avg_hum = (min_hum + max_hum) / 2
        hum = random.gauss(avg_hum, 10)
        hum = round(max(min(hum, 100), 0), 1)

        # Simplified spoilage risk calculation
        days_on_shelf = (current_date - stock_date).days
        time_risk = min(days_on_shelf / chosen_life, 1.0)
        
        temp_deviation = max(0, temp - max_temp) + max(0, min_temp - temp)
        temp_risk = min(temp_deviation / 10, 1.0) # Assume 10 degrees deviation is max risk

        # Combine risks and determine spoilage label (probabilistic)
        total_risk = 0.6 * time_risk + 0.4 * temp_risk
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
