import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import custom modules
from backend.engine import RedistributionEngine
from ml.utils import analyze_item_risk, get_risk_recommendation

# Page config
st.set_page_config(
    page_title="Zero Waste AI Dashboard",
    page_icon="🌱",
    layout="wide"
)

# Initialize engine
@st.cache_resource
def get_engine():
    return RedistributionEngine()

engine = get_engine()

# Sidebar
st.sidebar.title("Zero Waste AI")
st.sidebar.markdown("### Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Overview", "Inventory Analysis", "NGO Network", "Route Planning"]
)

# Load data
@st.cache_data
def load_data():
    inventory_df = pd.read_csv('data/mock_inventory.csv')
    ngos_df = pd.read_csv('data/mock_ngos.csv')
    return inventory_df, ngos_df

inventory_df, ngos_df = load_data()

# Overview Page
if page == "Overview":
    st.title("📊 System Overview")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    candidates_df, summary = engine.get_redistribution_candidates()
    
    with col1:
        st.metric(
            "Items Needing Action",
            len(candidates_df),
            f"{summary['urgent_items']} urgent"
        )
    
    with col2:
        st.metric(
            "Active NGO Partners",
            len(ngos_df),
            "🤝"
        )
    
    with col3:
        avg_days = summary.get('avg_days_remaining', 0)
        st.metric(
            "Avg Days Remaining",
            f"{avg_days:.1f}",
            "days"
        )
    
    with col4:
        total_capacity = ngos_df['capacity_kg'].sum()
        st.metric(
            "Total NGO Capacity",
            f"{total_capacity:,.0f}",
            "kg"
        )
    
    # Warning Level Distribution
    st.subheader("Warning Level Distribution")
    warning_counts = pd.Series(summary['by_warning_level'])
    fig = px.pie(
        values=warning_counts.values,
        names=warning_counts.index,
        title="Items by Warning Level",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Category Analysis
    st.subheader("Category Analysis")
    category_counts = pd.Series(summary['by_category'])
    fig = px.bar(
        x=category_counts.index,
        y=category_counts.values,
        title="Items by Category",
        labels={'x': 'Category', 'y': 'Count'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Inventory Analysis Page
elif page == "Inventory Analysis":
    st.title("🔍 Inventory Analysis")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        selected_category = st.selectbox(
            "Filter by Category",
            ['All'] + list(inventory_df['category'].unique())
        )
    
    with col2:
        warning_level = st.selectbox(
            "Filter by Warning Level",
            ['All', 'critical', 'warning', 'monitor', 'good']
        )
    
    # Filter data
    filtered_df = inventory_df.copy()
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # Analyze items
    for _, item in filtered_df.iterrows():
        # Ensure days_until_expiry is present
        if 'days_until_expiry' not in item or pd.isnull(item['days_until_expiry']):
            try:
                stock_date = pd.to_datetime(item['stock_date'])
                expiry_date = pd.to_datetime(item['expiry_date'])
                days_until_expiry = (expiry_date - datetime.now()).days
            except Exception:
                days_until_expiry = None
        else:
            days_until_expiry = item['days_until_expiry']
        
        # Create a copy of item as dict and add days_until_expiry
        item_dict = item.to_dict()
        item_dict['days_until_expiry'] = days_until_expiry
        
        st.subheader(f"{item['product_name']} ({item['category']})")
        
        # Get risk analysis
        risk_analysis = analyze_item_risk(item_dict)
        recommendations = get_risk_recommendation(risk_analysis)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk gauge chart
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_analysis['overall_risk'] * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 30], 'color': "green"},
                        {'range': [30, 70], 'color': "yellow"},
                        {'range': [70, 100], 'color': "red"}
                    ]
                },
                title={'text': "Risk Score"}
            ))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Risk Factors")
            for factor, value in risk_analysis['risk_factors'].items():
                safe_value = min(max(value, 0.0), 1.0)
                st.progress(safe_value)
                st.caption(f"{factor}: {value:.1%}")
        
        st.markdown("### Recommendations")
        for rec in recommendations:
            st.warning(rec)
        
        st.divider()

# NGO Network Page
elif page == "NGO Network":
    st.title("🤝 NGO Network Analysis")
    
    # Map of NGO locations
    st.subheader("NGO Network Distribution")
    fig = px.scatter_mapbox(
        ngos_df,
        lat='latitude',
        lon='longitude',
        hover_name='ngo_name',
        hover_data=['location', 'capacity_kg'],
        color='capacity_kg',
        size='capacity_kg',
        title="NGO Network Map",
        mapbox_style="open-street-map"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # NGO capacity analysis
    st.subheader("NGO Capacity Analysis")
    fig = px.bar(
        ngos_df,
        x='ngo_name',
        y='capacity_kg',
        title="NGO Capacity Distribution",
        labels={'capacity_kg': 'Capacity (kg)', 'ngo_name': 'NGO Name'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Route Planning Page
elif page == "Route Planning":
    st.title("🚚 Route Planning")
    
    # Get redistribution candidates
    candidates_df, _ = engine.get_redistribution_candidates()
    
    if not candidates_df.empty:
        # Select an item for route planning
        selected_item = st.selectbox(
            "Select Item for Route Planning",
            candidates_df['product_name'].unique()
        )
        
        item = candidates_df[candidates_df['product_name'] == selected_item].iloc[0]
        
        # Find best matches
        matches, stats = engine.find_best_matches(item.to_dict())
        
        if matches:
            # Create route map
            locations = pd.DataFrame([
                {
                    'name': 'Source',
                    'latitude': item['latitude'],
                    'longitude': item['longitude'],
                    'type': 'source'
                }
            ] + [
                {
                    'name': match['ngo_name'],
                    'latitude': match['latitude'],
                    'longitude': match['longitude'],
                    'type': 'ngo'
                }
                for match in matches[:3]  # Show top 3 matches
            ])
            
            fig = px.scatter_mapbox(
                locations,
                lat='latitude',
                lon='longitude',
                hover_name='name',
                color='type',
                title="Optimal Route Map",
                mapbox_style="open-street-map"
            )
            
            # Add route lines
            for match in matches[:3]:
                fig.add_trace(go.Scattermapbox(
                    mode="lines",
                    lon=[item['longitude'], match['longitude']],
                    lat=[item['latitude'], match['latitude']],
                    name=f"Route to {match['ngo_name']}",
                    line=dict(width=2)
                ))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display route statistics
            st.subheader("Route Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Distance",
                    f"{stats['avg_distance_km']:.1f} km"
                )
            
            with col2:
                st.metric(
                    "CO2 Savings",
                    f"{stats['total_potential_co2_savings']:.1f} kg"
                )
            
            with col3:
                st.metric(
                    "NGO Matches",
                    stats['total_matches']
                )
            
            # Display match details
            st.subheader("Top NGO Matches")
            for match in matches[:3]:
                with st.expander(f"📍 {match['ngo_name']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Location: {match['location']}")
                        st.write(f"Distance: {match['distance_km']:.1f} km")
                    with col2:
                        st.write(f"Capacity: {match['capacity_kg']} kg")
                        st.write(f"Match Score: {match['match_score']:.2f}")
        else:
            st.warning("No suitable NGO matches found for this item.")
    else:
        st.info("No items currently need redistribution.")
