import streamlit as st
from streamlit_folium import folium_static
import folium
import pandas as pd
import sqlite3
from managers.request_manager import RequestManager

# Page layout
st.set_page_config(page_title="Stops Analytics", page_icon="🚏", layout="wide")
st.title("Stops Analytics")
st.write("Delays of vehicles at stops (state_position = 'at_stop').")

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

@st.cache_data
def load_stops_grouped_by_name():
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
from folium.plugins import MarkerCluster
import numpy as np

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
stops_grouped_df = load_stops_grouped_by_name()
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

parent_list = ["All"] + [
    f"{row.parent_id} ({row.parent_name})" for row in parents_df.itertuples()
]
selected_parent = st.selectbox("Choose the parent stop", parent_list)

st.markdown("""
Please select a parent station group. After clicking the button, the current delays of vehicles
at the stops in this group will be displayed.
""")

if st.button("Load delays"):
    # Determine selected parent_id
    parent_id = None if selected_parent == "All" else selected_parent.split(" ")[0]

    # Query remote DB
    base_query = """
    SELECT
      vehicle_id,
      gtfs_trip_id,
      route_type,
      gtfs_route_short_name,
      delay,
      timestamp,
      latitude,
      longitude
    FROM vehicle_positions
    WHERE state_position = 'at_stop'
    ORDER BY delay DESC
    LIMIT 100;
    """
    rm = RequestManager()
    columns = [
        "vehicle_id", "gtfs_trip_id", "route_type", "gtfs_route_short_name",
        "delay", "timestamp", "latitude", "longitude"
    ]
    vp_df = rm.server_request(base_query, columns=columns)

    if vp_df is None or vp_df.empty:
        st.info("No data returned from remote vehicle_positions DB (or no delays).")
    else:
        # Nearest parent assignment
        def assign_nearest_parent(vp_df, parents_df):
            import numpy as np
            lat0 = vp_df["latitude"].to_numpy()
            lon0 = vp_df["longitude"].to_numpy()
            parent_lats = parents_df["avg_lat"].to_numpy()
            parent_lons = parents_df["avg_lon"].to_numpy()
            parent_ids = parents_df["parent_id"].to_numpy()
            parent_names = parents_df["parent_name"].to_numpy()

            assigned_parent_id = []
            assigned_parent_name = []
            for y0, x0 in zip(lat0, lon0):
                dlat = parent_lats - y0
                dlon = parent_lons - x0
                dist2 = dlat * dlat + dlon * dlon
                idx = np.argmin(dist2)
                assigned_parent_id.append(parent_ids[idx])
                assigned_parent_name.append(parent_names[idx])

            result = vp_df.copy()
            result["parent_id"] = assigned_parent_id
            result["parent_name"] = assigned_parent_name
            return result

        vp_with_parents = assign_nearest_parent(vp_df, parents_df)

        if parent_id:
            vp_with_parents = vp_with_parents[vp_with_parents["parent_id"] == parent_id]

        if vp_with_parents.empty:
            st.info("No delays found for the selected parent station.")
        else:
            st.success(f"{len(vp_with_parents)} records found.")

            # Delay Details
            with st.expander("Delay Details"):
                display_cols = [
                    "vehicle_id", "gtfs_trip_id", "route_type", "gtfs_route_short_name",
                    "delay", "timestamp", "latitude", "longitude", "parent_id", "parent_name"
                ]
                st.dataframe(vp_with_parents[display_cols])

    with st.expander("Map of Delays"):
        st.subheader("🗺️ Stop Locations on Map")
        stops_grouped_df = load_stops_grouped_by_name()

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
