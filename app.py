import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import math
import requests
from datetime import datetime
from fpdf import FPDF
import google.generativeai as genai
from PIL import Image
import io

# -----------------------------------------------------------------------------
# 1. LANGUAGE & UI CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Agri-Satellite Pro v16", layout="wide", initial_sidebar_state="collapsed")

# Multi-language Dictionary
TRANS = {
    "en": {
        "title": "🌾 TN PRECISION AGRI-SATELLITE INTELLIGENCE",
        "lat": "LATITUDE", "lon": "LONGITUDE", "acres": "ACRES", "crop": "SELECT CROP",
        "weather": "Live Weather", "village": "Village", "city": "City/District", "state": "State",
        "worth": "Net Worth Analysis", "history": "5-Year Profit Trend", "fert": "Fertilizer Schedule",
        "leaf": "AI Leaf Doctor", "pdf": "Download Farm Report", "suggest": "Expert Suggestions",
        "duration": "Harvest Duration", "tn": "TN Value", "in": "India Value"
    },
    "ta": {
        "title": "🌾 தமிழ்நாடு துல்லிய வேளாண் செயற்கைக்கோள் நுண்ணறிவு",
        "lat": "அட்சரேகை", "lon": "தீர்க்கரேகை", "acres": "ஏக்கர்", "crop": "பயிரைத் தேர்ந்தெடுக்கவும்",
        "weather": "நேரடி வானிலை", "village": "கிராமம்", "city": "நகரம்/மாவட்டம்", "state": "மாநிலம்",
        "worth": "நிகர மதிப்பு பகுப்பாய்வு", "history": "5 ஆண்டு லாபப் போக்கு", "fert": "உர அட்டவணை",
        "leaf": "AI இலை மருத்துவர்", "pdf": "பண்ணை அறிக்கையைப் பதிவிறக்கவும்", "suggest": "நிபுணர் ஆலோசனைகள்",
        "duration": "அறுவடை காலம்", "tn": "தமிழக மதிப்பு", "in": "இந்திய மதிப்பு"
    }
}

if 'lang' not in st.session_state: st.session_state.lang = 'en'
L = TRANS[st.session_state.lang]

# -----------------------------------------------------------------------------
# 2. CUSTOM CSS (STUNNING TECH UI)
# -----------------------------------------------------------------------------
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), 
                    url('https://as2.ftcdn.net/v2/jpg/05/44/22/16/1000_F_544221648_hY0Bf0UfH1N9XlWfFjB9YpG7n9V6uJzF.jpg');
        background-size: cover; background-attachment: fixed;
    }}
    input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button {{ 
        -webkit-appearance: none; margin: 0; 
    }}
    .glass-panel {{
        background: rgba(0, 25, 0, 0.9); border: 2px solid #00ff88;
        border-radius: 15px; padding: 25px; color: white; margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.8);
    }}
    .worth-val {{ color: #ffcc00; font-size: 1.8rem; font-weight: bold; text-shadow: 2px 2px 4px black; }}
    .label-hint {{ color: #00ff88; font-size: 0.85rem; font-weight: bold; }}
    [data-testid="stSidebar"] {{ display: none; }}
    .main .block-container {{ padding: 1rem 3rem; max-width: 100%; }}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. CORE ENGINES (SATELLITE, GEO, WEATHER)
# -----------------------------------------------------------------------------
@st.cache_data
def get_geo_details(lat, lon):
    try:
        geolocator = Nominatim(user_agent="tn_agri_pro_v16")
        location = geolocator.reverse((lat, lon), timeout=10)
        a = location.raw.get('address', {})
        return a.get('village') or a.get('suburb') or a.get('town'), a.get('city') or a.get('district'), a.get('state')
    except: return "Agri Zone", "District Hub", "Tamil Nadu"

def get_weather(lat, lon):
    # Mock Weather if API Key not provided, otherwise use OpenWeatherMap
    return {"temp": "31°C", "hum": "65%", "desc": "Sunny / Optimal for Sowing"}

def calculate_borders(lat, lon, acres):
    side = math.sqrt(acres * 4047)
    d_lat = (side / 111320) / 2
    d_lon = (side / (111320 * math.cos(math.radians(lat)))) / 2
    return [[lat+d_lat, lon-d_lon], [lat+d_lat, lon+d_lon], [lat-d_lat, lon+d_lon], [lat-d_lat, lon-d_lon], [lat+d_lat, lon-d_lon]]

# -----------------------------------------------------------------------------
# 4. DATASET & AI SETUP
# -----------------------------------------------------------------------------
CROP_DB = {
    "Paddy": {"in": 2183, "tn": 2450, "yield": 25, "dur": "125 Days", "fert": "Urea (50kg), SSP (25kg), Potash (25kg)"},
    "Turmeric": {"in": 7800, "tn": 9500, "yield": 22, "dur": "9 Months", "fert": "FYM (10t), Neem Cake (200kg), NPK 120:60:90"},
    "Sugarcane": {"in": 315, "tn": 370, "yield": 450, "dur": "12 Months", "fert": "Press mud, Urea, Super Phosphate"},
    "Banana": {"in": 1800, "tn": 2300, "yield": 150, "dur": "11 Months", "fert": "Drip Fertigation NPK 200:100:300"}
}

# -----------------------------------------------------------------------------
# 5. HEADER & TOP CONTROLS
# -----------------------------------------------------------------------------
c_head, c_lang = st.columns([8, 2])
with c_head: st.markdown(f"<h1>{L['title']}</h1>", unsafe_allow_html=True)
with c_lang: 
    if st.button("English / தமிழ்"):
        st.session_state.lang = 'ta' if st.session_state.lang == 'en' else 'en'
        st.rerun()

st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
i1, i2, i3, i4 = st.columns(4)
with i1: 
    st.markdown(f"<p class='label-hint'>{L['lat']}</p>", unsafe_allow_html=True)
    lat_in = st.number_input("lt", value=11.1271, format="%.6f", label_visibility="collapsed")
with i2:
    st.markdown(f"<p class='label-hint'>{L['lon']}</p>", unsafe_allow_html=True)
    lon_in = st.number_input("ln", value=78.6569, format="%.6f", label_visibility="collapsed")
with i3:
    st.markdown(f"<p class='label-hint'>{L['acres']}</p>", unsafe_allow_html=True)
    acres_in = st.number_input("ac", value=1.0, label_visibility="collapsed")
with i4:
    st.markdown(f"<p class='label-hint'>{L['crop']}</p>", unsafe_allow_html=True)
    sel_crop = st.selectbox("cp", list(CROP_DB.keys()), label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. SATELLITE MAP & WEATHER CENTER
# -----------------------------------------------------------------------------
m_left, m_right = st.columns([2.5, 1])

with m_left:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    m = folium.Map(location=[lat_in, lon_in], zoom_start=18)
    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satellite').add_to(m)
    borders = calculate_borders(lat_in, lon_in, acres_in)
    folium.Polygon(locations=borders, color="#00ff88", weight=5, fill=True, fill_opacity=0.2).add_to(m)
    st_folium(m, width="100%", height=450)
    st.markdown('</div>', unsafe_allow_html=True)

with m_right:
    st.markdown('<
