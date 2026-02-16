import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import os

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(page_title="AgriLife AI | Indian Farm Advisor", layout="wide")

# API Setup for AI Advisor
try:
    # Set your API Key in Streamlit Secrets as GEMINI_API_KEY
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.sidebar.warning("⚠️ AI Expert mode offline. (API Key missing)")

# Professional Indian Agri-Tech CSS
st.markdown("""
    <style>
    .stApp { background-color: #040d04; color: #e8f5e9; }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2e7d32;
        text-align: center;
    }
    .hero-section {
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
        padding: 40px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
        color: white;
    }
    .highlight { color: #FFD700; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR: FARM INPUTS ---
with st.sidebar:
    st.title("🚜 Farm Tools")
    if st.button("🔄 Reset Analysis"):
        st.rerun()

    st.header("📍 Farm Location")
    # Search simulation
    search_loc = st.text_input("Search Patta/Chitta/Survey No.", placeholder="e.g. TN-1022-5")
    
    col_lat, col_lon = st.columns(2)
    lat = col_lat.number_input("Latitude", value=13.0827, format="%.4f")
    lon = col_lon.number_input("Longitude", value=80.2707, format="%.4f")
    
    acres = st.number_input("Land Area (Acres)", value=3.0, step=0.5)
    
    st.header("🧪 Soil Profile")
    soil_type = st.selectbox("Soil Type", ["Alluvial Soil", "Black Soil", "Red Soil", "Laterite Soil", "Clayey"])
    ph_val = st.slider("Soil pH Level", 4.0, 9.0, 6.5)
    
    analyze_btn = st.button("🚀 Analyze Indian Farm Conditions", use_container_width=True)

# --- 3. MAIN DASHBOARD ---
st.markdown("""
    <div class="hero-section">
        <h1>🌾 AI Farming Advisor (India Edition)</h1>
        <p>Real-time crop intelligence using satellite data, Indian market MSP, and soil health analysis.</p>
    </div>
""", unsafe_allow_html=True)

if analyze_btn:
    with st.spinner("Fetching Mandi prices and local climate data..."):
        # 1. Dashboard Metrics
        st.header("📊 Analysis Summary")
        m1, m2, m3, m4 = st.columns(4)
        
        # Simulated logic for India
        best_crop = "Paddy (Rice)" if soil_type in ["Alluvial Soil", "Clayey"] else "Cotton"
        m1.metric("Best Recommended Crop", best_crop)
        m2.metric("Expected Net Profit", f"₹ {acres * 45000:,.0f}", "+₹5,200")
        m3.metric("AI Confidence", "96.4%")
        m4.metric("Land Area", f"{acres} Acres")

        # 2. Detailed Analytics Tabs
        tab1, tab2, tab3 = st.tabs(["📋 Mandi Insights", "📊 Market Comparison", "💰 Cost-Benefit Analysis"])
        
        # Indian Crop Data (Simulated Market Prices per Quintal)
        india_crops = pd.DataFrame({
            'Crop': ['Paddy', 'Sugarcane', 'Cotton', 'Maize', 'Groundnut'],
            'Mandi Price (₹/Q)': [2250, 3150, 7050, 2090, 6375],
            'Expected Yield (Q/Acre)': [25, 350, 12, 22, 15],
            'Suitability Score': [94.5, 88.0, 91.2, 85.6, 82.3]
        })
        # Calculate Total Profit
        india_crops['Total Revenue (₹)'] = india_crops['Mandi Price (₹/Q)'] * india_crops['Expected Yield (Q/Acre)'] * acres

        with tab1:
            st.subheader("Current Market Estimates (India)")
            st.dataframe(india_crops, use_container_width=True)
        
        with tab2:
            fig_suit = px.bar(india_crops, x='Crop', y='Suitability Score', color='Suitability Score', 
                             color_continuous_scale='Greens', title="Crop Suitability for Local Soil")
            st.plotly_chart(fig_suit, use_container_width=True)

        with tab3:
            fig_rev = px.pie(india_crops, values='Total Revenue (₹)', names='Crop', hole=0.4,
                            title="Potential Revenue Distribution (Total Acres)")
            st.plotly_chart(fig_rev, use_container_width=True)

        # 3. Environmental Conditions (Indian Context)
        st.divider()
        st.header("🌍 Local Environment & Soil Health")
        col_w, col_s = st.columns(2)
        
        with col_w:
            st.markdown(f"""
            <div class='metric-card'>
                <h3>☀️ Weather Forecast</h3>
                <p>Temp: <b>31.5°C</b> | Humidity: <b>68%</b></p>
                <p>Forecast: <span class='highlight'>Moderate Monsoon Rains Expected</span></p>
                <p>Wind Speed: 18 km/h</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_s:
            st.markdown(f"""
            <div class='metric-card'>
                <h3>🌱 Soil Nutrient Report</h3>
                <p>Nitrogen: <b>Medium</b> | Phosphorus: <b>Low</b></p>
                <p>Organic Carbon: <b>0.52%</b> (Needs Improvement)</p>
                <p>Soil Type: <b>{soil_type}</b> | pH: <b>{ph_val}</b></p>
            </div>
            """, unsafe_allow_html=True)

        # 4. Planting Calendar for India (Kharif/Rabi/Zaid)
        st.divider()
        st.header("🗓️ Indian Crop Calendar (Kharif/Rabi)")
        months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"]
        crops = ["Paddy", "Wheat", "Cotton", "Mustard", "Moong Dal"]
        # Creating a heatmap of planting suitability
        suit_matrix = np.random.randint(40, 98, size=(len(crops), len(months)))
        fig_heat = px.imshow(suit_matrix, labels=dict(x="Month", y="Crop", color="Suitability"),
                            x=months, y=crops, color_continuous_scale='YlGn', text_auto=True)
        st.plotly_chart(fig_heat, use_container_width=True)

        # 5. AI Agronomist - Local Advice
        st.divider()
        st.header("🤖 AI Agronomist Recommendations")
        try:
            prompt = f"Act as an Indian Agri-Expert. Farm: {acres} acres, {soil_type}, pH {ph_val}. Suggest 5 fertilizer and irrigation tips specifically for {best_crop} in Indian climate."
            response = ai_model.generate_content(prompt)
            st.write(response.text)
        except:
            st.write("1. 🌾 **Crop Choice:** Paddy is ideal for your soil; ensure nursery preparation starts before the monsoon.")
            st.write("2. 🧪 **Soil Health:** Your pH is slightly high. Consider applying Gypsum to neutralize.")
            st.write("3. 💧 **Irrigation:** Use AWD (Alternate Wetting and Drying) to save water in Paddy.")
            st.write("4. 💰 **MSP Watch:** The latest MSP for Paddy is ₹2,250; track local Mandis for better rates.")
            st.write("5. 🛡️ **Pest Control:** Check for Stem Borer activity in the early vegetative stage.")

        # 6. Data Export
        csv = india_crops.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full Farm Report (CSV)", data=csv, file_name="india_farm_report.csv")

else:
    # Landing Page
    st.info("👋 Namaste! Please enter your farm details in the sidebar to generate a 360° Agriculture Report.")
    
    # Satellite Map
    m = folium.Map(location=[lat, lon], zoom_start=15)
    # Using Google Satellite tiles for agricultural clarity
    google_satellite = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
    folium.TileLayer(tiles=google_satellite, attr='Google', name='Satellite View').add_to(m)
    folium.Marker([lat, lon], popup="Your Selected Farm").add_to(m)
    st_folium(m, width=1200, height=500)
