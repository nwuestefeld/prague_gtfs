import streamlit as st
import pandas as pd
import sqlite3
from managers.request_manager import RequestManager

# page layout
st.set_page_config(page_title="Stops Analytics", page_icon="🚏", layout="wide")

st.title("Stops Analytics")
st.write("Delays of vehicles at stops (state_position = 'at_stop').")

# 1 Load andgroup by parent_station from database.db
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

parents_df = load_parent_stations()

st.subheader("List of Parent Stations")
if parents_df.empty:
    st.warning("There are no parent stations available in the database.")
else:
    st.dataframe(parents_df[["parent_id", "parent_name", "avg_lat", "avg_lon"]])

st.markdown("---")

# 2 Query for delays where the vehicle is "on_stop"
st.subheader("Vehicle Delays at Stops")

parent_list = ["All"] + [
    f"{row.parent_id} ({row.parent_name})"
    for row in parents_df.itertuples()
]
selected_parent = st.selectbox("Choose the parent stop", parent_list)

st.markdown(
    """
    Please select a parent station group. After clicking the button, the current delays of vehicles
    at the stops in this group will be displayed.
    """
)

if st.button("Load delays"):
    # Determine selected parent_id (e.g., "U1007S1") or None for "All"
    if selected_parent == "All":
        parent_id = None
    else:
        parent_id = selected_parent.split(" ")[0]

    # Remote query: fetch only from vehicle_positions (no JOIN to stops)
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
        "vehicle_id",
        "gtfs_trip_id",
        "route_type",
        "gtfs_route_short_name",
        "delay",
        "timestamp",
        "latitude",
        "longitude"
    ]
    vp_df = rm.server_request(base_query, columns=columns)

    if vp_df is None or vp_df.empty:
        st.info("No data returned from remote vehicle_positions DB (or no delays).")
    else:
        # Local assignment of nearest parent based on coordinates
        parents_coords = parents_df  # contains parent_id, parent_name, avg_lat, avg_lon

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

        vp_with_parents = assign_nearest_parent(vp_df, parents_coords)

        # Filter by selected parent_id if not "All"
        if parent_id:
            vp_with_parents = vp_with_parents[vp_with_parents["parent_id"] == parent_id]

        if vp_with_parents.empty:
            st.info("No delays found for the selected parent station.")
        else:
            st.success(f"{len(vp_with_parents)} records found.")

            st.write("")

            with st.expander("Delay Details"):
                display_cols = [
                    "vehicle_id",
                    "gtfs_trip_id",
                    "route_type",
                    "gtfs_route_short_name",
                    "delay",
                    "timestamp",
                    "latitude",
                    "longitude",
                    "parent_id",
                    "parent_name"
                ]
                st.dataframe(vp_with_parents[display_cols])

            with st.expander("Top 10 Biggest Delays"):
                top10 = vp_with_parents.nlargest(10, "delay")
                st.dataframe(top10[[
                    "parent_name",
                    "gtfs_route_short_name",
                    "delay",
                    "timestamp",
                    "vehicle_id"
                ]])