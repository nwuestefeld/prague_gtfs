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
from managers.trip_manager import TripManager

# Load environment variables for API access
from dotenv import load_dotenv
import os

load_dotenv()
api_url = os.getenv("API_URL")
db_path = "database.db"
headers = {"X-Access-Token": os.getenv("API_KEY")}


"""
Stops Analytics Page: analyze and visualize delays of vehicles at individual stops in Prague.

Users can view stops grouped by name, inspect current vehicle delays at each stop,
and plot stop locations on a map to identify delay hotspots.
"""

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
    """Load parent station groups with average coordinates.

    Retrieves parent stations from the static stops database and computes
    the average latitude and longitude for each group.

    Returns:
        pandas.DataFrame: Columns ['parent_id', 'parent_name', 'avg_lat', 'avg_lon'].
    """
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
    """Fetch stop names where stop_id is missing in the static database.

    Returns:
        pandas.DataFrame: Single-column DataFrame of stop_name.
    """
    conn = sqlite3.connect("database.db", check_same_thread=False)
    query = "SELECT stop_name FROM stops WHERE stop_id IS NULL;"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


#for map
@st.cache_data

def get_stops_grouped_by_name():
    """Load and group stops by name, computing average coordinates and count.

    Returns:
        pandas.DataFrame: Columns ['stop_name', 'avg_lat', 'avg_lon', 'stop_count'].
    """

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
    """Calculate great-circle distance between two points on Earth.

    Args:
        lat1, lon1, lat2, lon2 (float or array-like): Coordinates in decimal degrees.

    Returns:
        float or array-like: Distance in kilometers.
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

# --- Map: All stops in zone P ---------------------------------------------
st.markdown("### 🗺️ Map of All Stops Prague")
station_options = ["ALL STATIONS"] + sorted(stops_grouped_df["stop_name"].unique())
station_choice = st.selectbox("Select a Station to View Individual Platforms", station_options)

if station_choice == "ALL STATIONS":
    with st.spinner("Rendering map…"):
        center_lat = stops_grouped_df["avg_lat"].mean()
        center_lon = stops_grouped_df["avg_lon"].mean()

        base_map = folium.Map(location=[center_lat, center_lon], zoom_start=12)
        cluster = MarkerCluster().add_to(base_map)

        # complete list of individual platforms for popup details
        all_stops = sqlite3.connect("database.db", check_same_thread=False) \
                         .cursor() \
                         .execute(
                            "SELECT stop_name, stop_id, latitude, longitude "
                            "FROM stops WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
                         ).fetchall()

        from collections import defaultdict
        platform_dict = defaultdict(list)
        for name, sid, lat, lon in all_stops:
            platform_dict[name].append(sid)

        for row in stops_grouped_df.itertuples():
            popup_html = (
                f"<b>{row.stop_name}</b><br/>"
                f"Number of platforms: {len(platform_dict[row.stop_name])}"
            )
            folium.Marker(
                location=[row.avg_lat, row.avg_lon],
                popup=popup_html,
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(cluster)

        folium_static(base_map, width=700, height=450)
else:
    # Individual station view
    selected_name = station_choice
    # fetch individual platform coordinates
    platform_rows = [
        (sid, code, lat, lon) for name, sid, code, lat, lon in sqlite3.connect("database.db", check_same_thread=False)
                            .cursor()
                            .execute(
                                "SELECT stop_name, stop_id, platform_code, latitude, longitude "
                                "FROM stops WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
                            ).fetchall()
        if name == selected_name and code
    ]
    if platform_rows:
        # center on first platform
        _, _, lat0, lon0 = platform_rows[0]
        base_map = folium.Map(location=[lat0, lon0], zoom_start=16)
        for sid, code, lat, lon in platform_rows:
            popup_html = (
                f"<b>{selected_name}</b><br/>"
                f"Platform {code}"
            )
            folium.Marker(
                location=[lat, lon],
                popup=popup_html,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(base_map)
        folium_static(base_map, width=700, height=450)
    else:
        st.info(f"No platform data available for {selected_name}.")

st.markdown("---")

# --- Dwell Time Analysis ---
st.subheader("Dwell Time at Stops")
st.markdown(
    """
    Select a date range and minimum dwell time (in seconds) to find vehicles that
    stayed at stops for at least that duration.
    """
)

with st.form("dwell_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start date")
    with col2:
        end_date = st.date_input("End date")
    with col3:
        min_dwell = st.number_input(
            "Min dwell (sec)", min_value=30, max_value=3600, value=30
        )
    submitted = st.form_submit_button("Run")

if submitted:
    if start_date > end_date:
        st.error("Start date cannot be after end date.")
    elif end_date > pd.Timestamp.now().date():
        st.error("End date cannot be in the future.")
    else:
        sd = start_date.strftime("%Y-%m-%d 00:00:00")
        ed = end_date.strftime("%Y-%m-%d 23:59:59")
        query = f"""
        SELECT
          vehicle_id,
          gtfs_trip_id,
          MIN(timestamp) AS arrival,
          MAX(timestamp) AS departure,
          ROUND(
              strftime('%s', MAX(timestamp)) - strftime('%s', MIN(timestamp)),
              1
          ) AS dwell_seconds
        FROM vehicle_positions
        WHERE state_position = 'at_stop'
          AND timestamp BETWEEN '{sd}' AND '{ed}'
        GROUP BY vehicle_id, gtfs_trip_id
        HAVING dwell_seconds >= {min_dwell}
        ORDER BY dwell_seconds DESC;
        """
        rm = RequestManager()
        cols = ["vehicle_id", "gtfs_trip_id", "arrival", "departure", "dwell_seconds"]
        df_dwell = rm.server_request(query, columns=cols)

        if df_dwell is None or df_dwell.empty:
            st.info("No dwell-time records found for the selection.")
        else:
            st.success(f"Found {len(df_dwell)} records.")
            # enrich with route names
            routes_info = TripManager().get_infos_by_trip_id(df_dwell["gtfs_trip_id"].tolist())
            routes_info = routes_info.rename(columns={"trip_id": "gtfs_trip_id", "route_short_name": "line"})
            # Only display desired columns: Line, Vehicle, Arrival, Departure, Dwell (s)
            df_out = df_dwell.merge(routes_info, on="gtfs_trip_id", how="left")
            df_out = df_out[["line", "vehicle_id", "arrival", "departure", "dwell_seconds"]]
            df_out.columns = ["Line", "Vehicle", "Arrival", "Departure", "Dwell (s)"]
            # Filter out records where line is missing
            df_out = df_out[df_out["Line"].notna()]
            st.dataframe(df_out, use_container_width=True)
