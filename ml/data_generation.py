import os
import random
import csv
from datetime import datetime, timedelta
from faker import Faker

# Ensure output directory exists
os.makedirs("data", exist_ok=True)

# Initialize Faker (India locale for variety, if needed)
Faker.seed(42)
fake = Faker('en_IN')

# Define product profiles (category, storage type, ideal ranges, shelf life range)
product_profiles = [
    {"product": "Apple",       "category": "Fruit",      "storage_type": "Refrigerated",
     "temp_range": (0, 4),    "humidity_range": (80, 95),    "shelf_life_days": (20, 30)},
    {"product": "Banana",      "category": "Fruit",      "storage_type": "Ambient",
     "temp_range": (15, 20),  "humidity_range": (60, 75),    "shelf_life_days": (3, 7)},
    {"product": "Milk",        "category": "Dairy",      "storage_type": "Refrigerated",
     "temp_range": (1, 4),    "humidity_range": (85, 95),    "shelf_life_days": (10, 15)},
    {"product": "Bread",       "category": "Bakery",     "storage_type": "Ambient",
     "temp_range": (20, 25),  "humidity_range": (50, 70),    "shelf_life_days": (3, 5)},
    {"product": "Chicken",     "category": "Meat",       "storage_type": "Refrigerated",
     "temp_range": (0, 4),    "humidity_range": (85, 95),    "shelf_life_days": (5, 10)},
    {"product": "Fish",        "category": "Seafood",    "storage_type": "Frozen",
     "temp_range": (-20, -15),"humidity_range": (75, 85),    "shelf_life_days": (30, 60)},
    {"product": "Carrots",     "category": "Vegetable",  "storage_type": "Refrigerated",
     "temp_range": (0, 4),    "humidity_range": (85, 95),    "shelf_life_days": (15, 30)},
    {"product": "Ice Cream",   "category": "FrozenDessert", "storage_type": "Frozen",
     "temp_range": (-25, -18),"humidity_range": (50, 60),    "shelf_life_days": (180, 365)},
    {"product": "Canned Beans","category": "Pantry",     "storage_type": "Ambient",
     "temp_range": (10, 25),  "humidity_range": (30, 50),    "shelf_life_days": (365, 730)},
    {"product": "Eggs",        "category": "Dairy",      "storage_type": "Refrigerated",
     "temp_range": (1, 4),    "humidity_range": (80, 85),    "shelf_life_days": (21, 30)}
]

# Inventory generation
inventory_data = []
num_rows = 300
locations = ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai"]
current_date = datetime.now().date()

for _ in range(num_rows):
    profile = random.choice(product_profiles)
    min_temp, max_temp = profile["temp_range"]
    min_hum, max_hum = profile["humidity_range"]
    
    # Product info
    product = profile["product"]
    category = profile["category"]
    storage = profile["storage_type"]
    
    # Random stock date and expiry date based on shelf life
    stock_days_ago = random.randint(0, 30)
    stock_date = current_date - timedelta(days=stock_days_ago)
    shelf_min, shelf_max = profile["shelf_life_days"]
    chosen_life = random.randint(shelf_min, shelf_max)
    expiry_date = stock_date + timedelta(days=chosen_life)
    
    # Simulate environment conditions
    # Temperature: random Gaussian around midpoint of ideal
    avg_temp = (min_temp + max_temp) / 2
    if storage == "Frozen":
        temp = random.gauss(avg_temp, 2)
    elif storage == "Refrigerated":
        temp = random.gauss(avg_temp, 3)
    else:
        temp = random.gauss(avg_temp, 5)
    temp = max(min(temp, 50), -30)
    
    # Humidity: random Gaussian around midpoint
    avg_hum = (min_hum + max_hum) / 2
    hum = random.gauss(avg_hum, 10)
    hum = max(min(hum, 100), 0)
    
    # Compute spoilage risk factors
    days_on_shelf = (current_date - stock_date).days
    risk_days = min(days_on_shelf / chosen_life, 1)
    temp_diff = 0
    if temp < min_temp:
        temp_diff = min_temp - temp
    elif temp > max_temp:
        temp_diff = temp - max_temp
    temp_span = max(max_temp - min_temp, 1)
    risk_temp = temp_diff / temp_span
    hum_diff = 0
    if hum < min_hum:
        hum_diff = min_hum - hum
    elif hum > max_hum:
        hum_diff = hum - max_hum
    hum_span = max(max_hum - min_hum, 1)
    risk_hum = hum_diff / hum_span
    
    # Combined risk score and label
    risk_score = 0.5*risk_days + 0.25*risk_temp + 0.25*risk_hum
    risk_score = min(risk_score, 1)
    spoilage_label = 1 if random.random() < risk_score else 0
    
    # Assemble row dictionary
    inventory_data.append({
        "product": product,
        "category": category,
        "stock_date": stock_date.isoformat(),
        "storage_type": storage,
        "store_location": random.choice(locations),
        "temperature": round(temp, 1),
        "humidity": round(hum, 1),
        "expiry_date": expiry_date.isoformat(),
        "spoilage": spoilage_label
    })

# Write inventory CSV (consistent column order)
inventory_cols = ["product", "category", "stock_date", "storage_type",
                  "store_location", "temperature", "humidity", "expiry_date", "spoilage"]
with open("data/mock_inventory.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=inventory_cols)
    writer.writeheader()
    for row in inventory_data:
        writer.writerow(row)

# NGO data generation
categories = ["Fruit", "Dairy", "Bakery", "Meat", "Seafood", "Vegetable", "Pantry", "FrozenDessert"]
ngo_data = []
names_used = set()
for _ in range(10):
    prefix = random.choice(["Green", "Helping", "Hope", "Future", "Rainbow", "Sunshine",
                             "Goodwill", "Care", "Unity", "Harbor", "Lighthouse"])
    suffix = random.choice(["Foundation", "Trust", "Alliance", "Association", 
                             "Project", "Initiative", "Organization", "Mission", "Cares"])
    name = f"{prefix} {suffix}"
    # avoid duplicate names
    while name in names_used:
        name = f"{random.choice([prefix,'Green','Helping','Hope','Future'])} {random.choice([suffix,'Foundation','Trust','Alliance'])}"
    names_used.add(name)
    location = random.choice(locations)
    capacity = random.randint(50, 500)
    accepted = random.sample(categories, k=random.randint(2, 4))
    accepted_str = "|".join(accepted)
    ngo_data.append({
        "ngo_name": name,
        "location": location,
        "capacity": capacity,
        "accepted_categories": accepted_str
    })

# Write NGO CSV
ngo_cols = ["ngo_name", "location", "capacity", "accepted_categories"]
with open("data/mock_ngos.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=ngo_cols)
    writer.writeheader()
    for row in ngo_data:
        writer.writerow(row)

