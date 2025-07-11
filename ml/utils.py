import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib

def load_models():
    """Load trained models and scalers."""
    try:
        model = joblib.load('ml/models/spoilage_model.joblib')
        scaler = joblib.load('ml/models/scaler.joblib')
        return model, scaler
    except FileNotFoundError:
        print("Models not found. Please run model_training.py first.")
        return None, None

def predict_spoilage_risk(
    model, 
    scaler, 
    temperature, 
    humidity, 
    days_until_expiry,
    category_code,
    storage_type_code
):
    """Predict spoilage risk for given conditions."""
    if model is None or scaler is None:
        return 0.5  # Default risk if models aren't loaded
    
    features = np.array([
        temperature,
        humidity,
        days_until_expiry,
        category_code,
        storage_type_code
    ]).reshape(1, -1)
    
    features_scaled = scaler.transform(features)
    risk_prob = model.predict_proba(features_scaled)[0][1]
    
    return risk_prob

def calculate_category_code(category):
    """Convert category to numeric code."""
    categories = [
        'Dairy', 'Meat', 'Seafood', 'Bakery', 'Fruit',
        'Vegetable', 'FrozenDessert', 'Pantry'
    ]
    return categories.index(category) if category in categories else -1

def calculate_storage_code(storage_type):
    """Convert storage type to numeric code."""
    storage_types = ['Ambient', 'Refrigerated', 'Frozen']
    return storage_types.index(storage_type) if storage_type in storage_types else -1

def analyze_item_risk(item_data):
    """Analyze risk factors for an item."""
    model, scaler = load_models()
    
    risk_prob = predict_spoilage_risk(
        model,
        scaler,
        item_data['temperature_c'],
        item_data['humidity_percent'],
        item_data['days_until_expiry'],
        calculate_category_code(item_data['category']),
        calculate_storage_code(item_data['storage_type'])
    )
    
    risk_factors = {
        'temperature_risk': max(0, abs(item_data['temperature_c'] - 20) / 40),
        'humidity_risk': abs(item_data['humidity_percent'] - 60) / 100,
        'time_risk': max(0, 1 - item_data['days_until_expiry'] / 30),
        'model_risk': risk_prob
    }
    
    return {
        'overall_risk': np.mean(list(risk_factors.values())),
        'risk_factors': risk_factors
    }

def get_risk_recommendation(risk_analysis):
    """Generate recommendations based on risk analysis."""
    overall_risk = risk_analysis['overall_risk']
    factors = risk_analysis['risk_factors']
    
    recommendations = []
    
    if overall_risk > 0.7:
        recommendations.append("URGENT: Immediate redistribution recommended")
    elif overall_risk > 0.5:
        recommendations.append("WARNING: Plan for redistribution within 24 hours")
    elif overall_risk > 0.3:
        recommendations.append("MONITOR: Regular monitoring required")
    
    # Factor-specific recommendations
    if factors['temperature_risk'] > 0.6:
        recommendations.append("Check storage temperature conditions")
    if factors['humidity_risk'] > 0.6:
        recommendations.append("Adjust humidity levels")
    if factors['time_risk'] > 0.6:
        recommendations.append("Prioritize for immediate redistribution")
    
    return recommendations
