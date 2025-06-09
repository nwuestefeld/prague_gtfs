import streamlit as st
from streamlit_folium import folium_static
import folium
from folium.plugins import MarkerCluster
import numpy as np
import pandas as pd
import sqlite3
from managers.request_manager import RequestManager
from managers.stop_manager import StopManager
from managers.shape_manager import ShapeManager


# Page layout
st.set_page_config(page_title="Stops Analytics", page_icon="🚏", layout="wide")
st.title("Stops Analytics")
st.write("Delays of vehicles at stops (state_position = 'at_stop').")
st.markdown("""
**Stop-Level Delay Analysis**  
Use this page to explore delay patterns at individual stops in Prague (zone P).

- **Stops grouped by stop_name**: displays all stops aggregated by name with location data.
- **Vehicle Delays at Stops**: select a parent station to view current delays at each platform.
- **Map of Delays**: plot stop locations on an interactive map to identify problem areas.
""", unsafe_allow_html=True)

# --- Load data from database ---
@st.cache_data
def load_parent_stations():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    query = """
    SELECT
      s.parent_station AS parent_id,
      p.stop_name       AS parent_name,
      AVG(s.latitude)   AS avg_lat,
      AVG(s.longitude)  AS avg_lon
    FROM stops AS s
    LEFT JOIN stops AS p
      ON s.parent_station = p.stop_id
    GROUP BY s.parent_station
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data
def load_stops_without_id():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    query = "SELECT stop_name FROM stops WHERE stop_id IS NULL;"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


#for map
@st.cache_data
def get_stops_grouped_by_name():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    query = """
    SELECT
      stop_name,
      AVG(latitude) AS avg_lat,
      AVG(longitude) AS avg_lon,
      COUNT(*) AS stop_count
    FROM stops
    GROUP BY stop_name
    ORDER BY stop_name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def haversine(lat1, lon1, lat2, lon2):
    """
    calc dist
    """
    R = 6371  # radius in km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c
# --- Initial data display ---
parents_df = load_parent_stations()

st.subheader("Stops grouped by stop_name")
stops_grouped_df = get_stops_grouped_by_name()
#remove exits like
#stops_grouped_df = stops_grouped_df[~stops_grouped_df["stop_name"].str.match(r"^E\d+$")]
stops_grouped_df = stops_grouped_df[stops_grouped_df["stop_name"].notna()]
#remove leading and trailing spaces from stop_name
stops_grouped_df["stop_name"] = stops_grouped_df["stop_name"].astype(str).str.strip()
stops_grouped_df = stops_grouped_df[~stops_grouped_df["stop_name"].str.fullmatch(r"E\d+")]
if stops_grouped_df.empty:
    st.warning("No stops found in the database.")
else:
    st.dataframe(stops_grouped_df)

st.markdown("---")

# --- Delays Section ---
st.subheader("Vehicle Delays at Stops")

st.markdown("""
Please select a parent station group. After clicking the button, the current delays of vehicles
at the stops in this group will be displayed.
""")

with st.form("filter_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Select Start date")
        with col2:
            end_date = st.date_input("Select End date")
        with col3:
            min_delay = st.number_input("Min delay: default is 60 Sec, Default is 360 Sec", min_value=60, max_value=3600, value=360)
        submitted = st.form_submit_button("Apply")

if submitted:
    # some checks.
    if start_date > end_date:
        st.error("Start date cannot be after end date.")
    if  start_date > pd.Timestamp.now().date():
        st.error("Start or End date cannot be in the future.")
    else:
        #TODO ensure that no double entries when vehicle is at stop for multiple timestamps
        # that means same trip_id and roungly same  lat and long ->unique trip id and stop combi
        start_date_str = start_date.strftime('%Y-%m-%d') + " 00:00:00"
        end_date_str = end_date.strftime('%Y-%m-%d') + " 23:59:00"
        st.success(f"Selected date range: {start_date_str} to {end_date_str}")
        minx, miny, maxx, maxy = ShapeManager().set_bounding_box()
        base_query = f"""
        SELECT
        vehicle_id,
        gtfs_trip_id,
        route_type,
        gtfs_route_short_name,
        delay,
        bearing,
        timestamp,
        latitude,
        longitude
        FROM vehicle_positions
        WHERE state_position = 'at_stop'
        AND longitude BETWEEN '{minx}' AND '{maxx}'
        AND latitude BETWEEN '{miny}' AND '{maxy}'
        AND route_type <> 2
        AND delay > '{min_delay}'
        AND timestamp BETWEEN '{start_date_str}' AND '{end_date_str}'
        """
        rm = RequestManager()
        columns = [
        "vehicle_id", "gtfs_trip_id", "route_type", "gtfs_route_short_name",
        "delay", "bearing", "timestamp", "latitude", "longitude"
        ]
        with st.spinner("Loading data..."):
            vp_df = rm.server_request(base_query, columns=columns)
            print(vp_df.head())
            if vp_df is None or vp_df.empty:
                st.info("No data returned from remote vehicle_positions DB (or no delays). Please try a different date range or check the database.")
                st.stop()
            else:
                st.success(f"Found vehicles on stops with delays greater than {min_delay} seconds.")

            with st.spinner("Matching Stations with Database"):
                # Match stations with lat and long from on stop vehicle positions
                sm = StopManager()
                stops_df = sm.get_stops()
                if stops_df.empty:
                    st.error("Please ensure that the stops table is populated in the database. You can do this by refreshing the database on the Connections page.")
                    st.stop()
                else:
                    matched_stops = sm.match_nearest_stops(vp_df, stops_df, 100)
                    st.dataframe(matched_stops.head(10), use_container_width=True)





    with st.expander("Map of Delays"):
        st.subheader("🗺️ Stop Locations on Map")
        stops_grouped_df = get_stops_grouped_by_name()

        if stops_grouped_df.empty:
            st.info("No stops found to plot.")
        else:
            center_lat = stops_grouped_df["avg_lat"].mean()
            center_lon = stops_grouped_df["avg_lon"].mean()

            # Distanz berechnen
            stops_grouped_df["distance_to_center"] = haversine(
                stops_grouped_df["avg_lat"], stops_grouped_df["avg_lon"],
                center_lat, center_lon
            )

            # Nur Stops innerhalb 20 km
            stops_near = stops_grouped_df[stops_grouped_df["distance_to_center"] <= 20]

            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

            # MarkerCluster initialisieren
            marker_cluster = MarkerCluster().add_to(m)

            for row in stops_near.itertuples():
                folium.Marker(
                    location=[row.avg_lat, row.avg_lon],
                    popup=f"{row.stop_name} ({row.stop_count} Stops)",
                    icon=folium.Icon(color="blue", icon="info-sign")
                ).add_to(marker_cluster)

            folium_static(m)
