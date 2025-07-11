# Zero Waste AI

An AI-powered food waste reduction and redistribution system that connects stores with surplus food to NGOs and organizations that can use it.

## Project Structure

```
zero-waste-ai/
├── ml/                  # Machine Learning Components
│   ├── data_generation.py  # Mock data generation
│   ├── model_training.py   # ML model training
│   └── utils.py           # ML utilities
├── backend/             # Backend Services
│   ├── redistribution.py  # Core redistribution logic
│   ├── routing.py        # Route optimization
│   └── utils.py         # Backend utilities
├── frontend/           # Streamlit Frontend
│   └── app.py         # Main Streamlit application
├── data/              # Data Storage
│   ├── mock_inventory.csv
│   └── mock_ngos.csv
└── requirements.txt
```

## Features

1. **Smart Redistribution Engine**
   - Freshness monitoring and prediction
   - Category-specific handling
   - Priority-based matching

2. **Green Route Optimization**
   - Distance optimization
   - CO2 emission reduction
   - Multi-stop route planning

3. **NGO Matching System**
   - Capacity-aware matching
   - Category specialization
   - Distance-based prioritization

4. **Impact Tracking**
   - CO2 savings calculation
   - Waste reduction metrics
   - Environmental impact scoring

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Generate mock data:
```bash
python ml/data_generation.py
```

4. Run the Streamlit app:
```bash
streamlit run frontend/app.py
```

## Components

### Machine Learning (ml/)
- `data_generation.py`: Generates realistic mock data
- `model_training.py`: Trains predictive models
- `utils.py`: ML utility functions

### Backend (backend/)
- `redistribution.py`: Core redistribution logic
- `routing.py`: Route optimization algorithms
- `utils.py`: Backend utility functions

### Frontend (frontend/)
- `app.py`: Streamlit dashboard application

## Usage

1. Start by generating mock data:
```bash
python ml/data_generation.py
```

2. Train the ML models:
```bash
python ml/model_training.py
```

3. Launch the Streamlit interface:
```bash
streamlit run frontend/app.py
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
