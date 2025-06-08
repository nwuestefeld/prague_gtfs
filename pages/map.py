import streamlit as st
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium
import sqlite3
import pandas as pd

@st.cache_data
def load_stops():
    with sqlite3.connect("database.db", check_same_thread=False) as conn:
        df = pd.read_sql_query("SELECT * FROM stops", conn)
    conn.close()
    return df


conn = sqlite3.connect("vehicle_positions.db")
query = """SELECT * FROM vehicle_positions WHERE delay IS NOT NULL AND delay > 180 AND route_type <> 2"""

vehicle_type = st.selectbox(
    "Choose vehicle type",
    ["All", "tram", "metro", "bus"]
)

df = pd.read_sql_query(query, conn)
conn.close()
df_filtered = df.copy()

if vehicle_type != "All":
    df_filtered = df_filtered[df_filtered['route_type'] == vehicle_type]

if df_filtered.empty:
    st.warning("No data available for the selected filter.")
else:
    heat_data = [[row['latitude'], row['longitude'], row['delay']] for _, row in df_filtered.iterrows()]

#df_stops = load_stops()

# experimental 
#df_stops['parent_station'] = df_stops['parent_station'].fillna(df_stops['stop_id'])

# grouping
#df_grouped = df_stops.groupby('parent_station').agg({
#    'latitude': 'mean',
#    'longitude': 'mean',
#    'stop_name': 'first', 
#}).reset_index()

center = [50.0755, 14.4378]

m = folium.Map(
    location=center,
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True,         
    zoom_control=True,          
    scrollWheelZoom=True,       
    dragging=True               
)

#marker_cluster = MarkerCluster().add_to(m)

#for idx, row in df_grouped.iterrows():
#    popup_text = f"Station: {row.get('station_id', 'n/a')} <br> Parent: {row['parent_station']} <br>Name: {row['stop_name']}"
#    folium.Marker(
#        location=[row['latitude'], row['longitude']],
#        popup=popup_text,
#        icon=folium.Icon(color='red', icon='train')
#    ).add_to(marker_cluster)

HeatMap(heat_data).add_to(m)

m.save("test_heatmap.html")

st.title("Test Vehicle Heatmap Map")
st.subheader("Vehicle Density Heatmap (Demo)")
st.markdown("""
**Spatial Delay Heatmap**  
Visualize where delays are most severe in Prague (zone P only):

- Select a vehicle type to focus on (tram, metro, bus, etc.).  
- Heatmap intensity shows average delay at each location.  
- Zoom and pan to explore hotspots across the city.  
- Color scale runs from blue (lowest delays) to red (highest delays).  
""", unsafe_allow_html=True)
st.write("Please select a Vehicle Type")
st_folium(m, width=700, height=500)
