import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

def preprocess_inventory_data(df):
    """Preprocess inventory data for model training."""
    # Calculate days until expiry
    df['expiry_date'] = pd.to_datetime(df['expiry_date'])
    df['stock_date'] = pd.to_datetime(df['stock_date'])
    df['days_until_expiry'] = (df['expiry_date'] - df['stock_date']).dt.days
    
    # Create category encodings
    df['category_code'] = pd.Categorical(df['category']).codes
    
    # Create storage type encodings
    df['storage_type_code'] = pd.Categorical(df['storage_type']).codes
    
    return df

def prepare_features(df):
    """Prepare feature matrix for training."""
    features = [
        'temperature_c', 'humidity_percent', 'days_until_expiry',
        'category_code', 'storage_type_code'
    ]
    
    X = df[features]
    y = df['spoilage']
    
    return X, y

def train_spoilage_model(X_train, y_train):
    """Train the spoilage prediction model."""
    from sklearn.ensemble import RandomForestClassifier
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42
    )
    
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    """Evaluate model performance."""
    from sklearn.metrics import classification_report, confusion_matrix
    
    y_pred = model.predict(X_test)
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    return {
        'accuracy': model.score(X_test, y_test),
        'predictions': y_pred
    }

if __name__ == "__main__":
    # Load data
    inventory_df = pd.read_csv('data/mock_inventory.csv')
    
    # Preprocess data
    processed_df = preprocess_inventory_data(inventory_df)
    
    # Prepare features
    X, y = prepare_features(processed_df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = train_spoilage_model(X_train_scaled, y_train)
    
    # Evaluate model
    results = evaluate_model(model, X_test_scaled, y_test)
    
    # Save model and scaler
    joblib.dump(model, 'ml/models/spoilage_model.joblib')
    joblib.dump(scaler, 'ml/models/scaler.joblib')
    
    print(f"\nModel saved with accuracy: {results['accuracy']:.2f}")
