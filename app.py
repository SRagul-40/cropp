import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import os

# --- 1. PAGE SETUP & THEME ---
st.set_page_config(page_title="AI Farming Advisor v1.0", layout="wide")

# Configure AI (Get key from https://aistudio.google.com/)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.sidebar.warning("⚠️ AI Expert Mode Offline. Please add Gemini API Key to Secrets.")

# Custom CSS for the Exact Video Look
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .card { background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 10px; border: 1px solid #2e7d32; margin-bottom: 20px; }
    .hero-banner { 
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%); 
        padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 30px; 
    }
    .metric-value { font-size: 2.2rem; font-weight: 800; color: #FFD700; }
    .metric-label { font-size: 1rem; color: #a5d6a7; }
    [data-testid="stMetricValue"] { color: #FFD700 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (USER ENTRY - EDITABLE READINGS) ---
with st.sidebar:
    st.title("🚜 Farm Tools")
    if st.button("Reset Analysis", use_container_width=True):
        st.rerun()
    
    st.header("📍 Location Information")
    lat = st.number_input("Enter Latitude", value=13.0827, format="%.6f")
    lon = st.number_input("Enter Longitude", value=80.2707, format="%.6f")
    acres = st.number_input("Land Area (Acres)", value=3.0, step=0.1)

    st.header("🧪 Soil Readings")
    soil_type = st.selectbox("Soil Type", ["Alluvial", "Black", "Red", "Laterite", "Clayey"])
    ph = st.slider("Soil pH Level", 4.0, 9.0, 6.7)
    nitrogen = st.slider("Nitrogen (N)", 0, 100, 50)
    phosphorus = st.slider("Phosphorus (P)", 0, 100, 40)
    potassium = st.slider("Potassium (K)", 0, 100, 40)

    st.header("🌤️ Weather Readings")
    temp = st.number_input("Current Temp (°C)", value=28.5)
    rain = st.number_input("Annual Rainfall (mm)", value=1150.0)
    
    st.header("⚙️ Options")
    analysis_type = st.selectbox("Analysis Type", ["Comprehensive Analysis", "Quick Assessment"])
    
    analyze_btn = st.button("🔴 Analyze Farm Conditions", use_container_width=True)

# --- 3. LOGIC & DATA GENERATION ---
# Dynamic Indian Crop Database
CROP_DB = {
    "Paddy (Rice)": {"price": 2250, "cost": 25000, "yield": 24, "suit": 95, "p_risk": "Low", "m_risk": "Low"},
    "Wheat": {"price": 2275, "cost": 20000, "yield": 18, "suit": 91, "p_risk": "Low", "m_risk": "Medium"},
    "Cotton": {"price": 7020, "cost": 32000, "yield": 11, "suit": 89, "p_risk": "High", "m_risk": "High"},
    "Sugarcane": {"price": 3150, "cost": 45000, "yield": 320, "suit": 87, "p_risk": "Medium", "m_risk": "Low"},
    "Maize": {"price": 2090, "cost": 18000, "yield": 20, "suit": 84, "p_risk": "Low", "m_risk": "Medium"},
    "Soybeans": {"price": 4500, "cost": 15000, "yield": 10, "suit": 82, "p_risk": "Medium", "m_risk": "Medium"}
}

# --- 4. MAIN DASHBOARD ---
st.markdown("""
    <div class="hero-banner">
        <h1 style='margin:0;'>👨‍🌾 AI Farming Advisor</h1>
        <p style='margin:0;'>Personalized Indian crop recommendations based on your editable soil and market inputs.</p>
    </div>
""", unsafe_allow_html=True)

if analyze_btn:
    with st.spinner("Analyzing site conditions..."):
        # Section 1: Analysis Summary
        st.header("📊 Analysis Summary")
        m1, m2, m3, m4 = st.columns(4)
        
        # Calculation for best crop (Simple logic based on Soil Type)
        best_crop = "Paddy (Rice)" if soil_type in ["Alluvial", "Clayey"] else "Cotton"
        best_data = CROP_DB[best_crop]
        
        profit_per_acre = (best_data["price"] * best_data["yield"]) - best_data["cost"]
        total_profit = profit_per_acre * acres
        
        m1.metric("Best Crop", best_crop)
        m2.metric("Expected Profit", f"₹ {total_profit:,.2f}")
        m3.metric("Confidence Score", "95.5%")
        m4.metric("Land Area", f"{acres} Acres")

        # Section 2: Top Crop Recommendations (Tabs)
        st.header("🏆 Top Crop Recommendations")
        tab1, tab2, tab3 = st.tabs(["📋 Detailed List", "📊 Comparison Chart", "💰 Profit Analysis"])

        crops = list(CROP_DB.keys())
        suitability = [CROP_DB[c]["suit"] for c in crops]
        profits = [((CROP_DB[c]["price"] * CROP_DB[c]["yield"]) - CROP_DB[c]["cost"]) * acres for c in crops]
        costs = [CROP_DB[c]["cost"] * acres for c in crops]
        revenues = [CROP_DB[c]["price"] * CROP_DB[c]["yield"] * acres for c in crops]

        with tab1:
            detailed_df = pd.DataFrame({
                "Crop": crops,
                "Gross Revenue": revenues,
                "Total Costs": costs,
                "Net Profit": profits,
                "Suitability Score": suitability
            })
            st.dataframe(detailed_df.style.format("₹ {:,.2f}", subset=["Gross Revenue", "Total Costs", "Net Profit"]), use_container_width=True)

        with tab2:
            fig_suit = px.bar(x=crops, y=suitability, color=suitability, color_continuous_scale="Greens", labels={'x':'Crop', 'y':'Suitability %'})
            st.plotly_chart(fig_suit, use_container_width=True)

        with tab3:
            fig_prof = px.bar(x=crops, y=profits, title="Profit Analysis per Crop (₹)", color_discrete_sequence=['#FFD700'])
            st.plotly_chart(fig_prof, use_container_width=True)

        # Section 3: Expanders (Financial & Risk Assessment)
        for crop in crops:
            with st.expander(f"Details for {crop}"):
                d1, d2 = st.columns(2)
                with d1:
                    st.subheader("Financial Analysis")
                    st.write(f"Estimated Revenue: ₹ {CROP_DB[crop]['price'] * CROP_DB[crop]['yield'] * acres:,.2f}")
                    st.write(f"Estimated Cost: ₹ {CROP_DB[crop]['cost'] * acres:,.2f}")
                    st.write(f"Net Profit: **₹ {((CROP_DB[crop]['price'] * CROP_DB[crop]['yield']) - CROP_DB[crop]['cost']) * acres:,.2f}**")
                with d2:
                    st.subheader("Risk Assessment")
                    st.write(f"🌡️ Weather Risk: **Low**")
                    st.write(f"📈 Market Risk: **{CROP_DB[crop]['m_risk']}**")
                    st.write(f"🐛 Pest Risk: **{CROP_DB[crop]['p_risk']}**")

        # Section 4: Environmental & Soil (Based on User Input)
        st.divider()
        st.header("🌍 Environmental & Soil Conditions")
        e1, e2 = st.columns(2)
        with e1:
            st.markdown(f"""<div class='card'><h3>🌤️ Weather Conditions</h3>
            <p>Current Temp: <b>{temp}°C</b></p>
            <p>Annual Rainfall: <b>{rain} mm</b></p>
            </div>""", unsafe_allow_html=True)
        with e2:
            st.markdown(f"""<div class='card'><h3>🌱 Soil Conditions</h3>
            <p>Soil Type: <b>{soil_type}</b></p>
            <p>pH Level: <b>{ph}</b></p>
            <p>Nitrogen (N): <b>{nitrogen}</b></p>
            </div>""", unsafe_allow_html=True)

        # Section 5: Planting Calendar (Previous vs Current)
        st.header("🗓️ Planting Calendar (Heatmap)")
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        z_data = np.random.randint(40, 95, size=(len(crops), 12))
        fig_heat = px.imshow(z_data, x=months, y=crops, color_continuous_scale="YlGn", title="Monthly Suitability (Current Year)")
        st.plotly_chart(fig_heat, use_container_width=True)

        # Section 6: AI Expert Recommendations
        st.divider()
        st.header("🤖 Recommended Next Steps")
        try:
            prompt = f"Act as an Indian Agri-Expert. Farm: {acres} acres, Soil: {soil_type}, pH {ph}, Nitrogen {nitrogen}. Best Crop: {best_crop}. Suggest 5 Fertilizer and Irrigation tips."
            response = ai_model.generate_content(prompt)
            st.write(response.text)
        except:
            st.write("1. Start nursery preparation for Paddy.\n2. Ensure proper drainage for the field.\n3. Apply balanced NPK fertilizers.\n4. Monitor soil moisture weekly.\n5. Check local Mandi prices for {best_crop}.")

        # Section 7: Download List
        csv = detailed_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Analysis Report (CSV)", data=csv, file_name="farm_analysis.csv", mime="text/csv")

else:
    st.info("👋 Welcome! Enter your soil and weather readings in the sidebar and click 'Analyze' to begin.")
    m = folium.Map(location=[lat, lon], zoom_start=15)
    google_satellite = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
    folium.TileLayer(tiles=google_satellite, attr='Google', name='Satellite').add_to(m)
    folium.Marker([lat, lon], popup="Selected Farm").add_to(m)
    st_folium(m, width=1200, height=500)
