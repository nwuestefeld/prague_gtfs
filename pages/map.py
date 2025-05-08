import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import sqlite3
import pandas as pd
conn = sqlite3.connect("vehicle_positions.db")

query = """SELECT * FROM vehicle_positions WHERE delay IS NOT NULL AND delay > 60"""

vehicle_type = st.selectbox(
    "Choose vehicle type",
    ["All", "tram", "metro","train","bus"]
)

df = pd.read_sql_query(query, conn)
conn.close()
df_filtered = df.copy()

if vehicle_type != "All":
    df_filtered = df_filtered[df_filtered['route_type'] == vehicle_type]

if df_filtered.empty:
    st.warning("No data available for the selected filter.")
else:
    # Heatmap-Daten: [latitude, longitude, delay]
    heat_data = [[row['latitude'], row['longitude'], row['delay']] for index, row in df_filtered.iterrows()]






center = [50.0755, 14.4378]  # Latitude, Longitude
#basemap
m = folium.Map(
    location=center,
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True,         
    zoom_control=True,          
    scrollWheelZoom=True,       
    dragging=True               
)
#add heatmap overlay to basemap m
heat_data = [[row['latitude'], row['longitude'], row['delay']] for index, row in df_filtered.iterrows()]
HeatMap(heat_data).add_to(m)

m.save("test_heatmap.html")



st.title("Test Vehicle Heatmap Map")
st.subheader("Vehicle Density Heatmap (Demo)")
st.write("Please select a Vehicle Type")
st_folium(m, width=700, height=500)