import streamlit as st
from streamlit_folium import st_folium  # st_folium replaces deprecated folium_static
import folium
from folium.plugins import MarkerCluster
import numpy as np
import pandas as pd
import sqlite3
import plotly.express as px
from managers.request_manager import RequestManager
from managers.stop_manager import StopManager
from managers.shape_manager import ShapeManager
from managers.trip_manager import TripManager
from dotenv import load_dotenv
import os

load_dotenv()
api_url = os.getenv("API_URL")
db_path = "database.db"
headers = {"X-Access-Token": os.getenv("API_KEY")}


st.title("Stops Analytics")

"""
Stops Analytics Page: analyze and visualize delays of vehicles at individual stops in Prague.

A third tab, **Stop Throughput Analysis**, lets you explore *average* at‑stop events per hour over a chosen date range.

Users can view stops grouped by name, inspect current vehicle delays at each stop,
and plot stop locations on a map to identify delay hotspots.
"""


st.markdown(
    """
    Use **Overview** to browse all Prague stops on an interactive map and in a sortable table.  
    Switch to **Dwell&nbsp;Time&nbsp;Analysis** for insights into how long vehicles actually remain at each stop.
    Use the **Stop Throughput** tab to analyze average stop throughput per hour over a selected date range.
    """,
    unsafe_allow_html=True,
)
tabs = st.tabs(["Overview", "Dwell Time Analysis", "Stop Throughput"])
overview_tab, dwell_tab = tabs[:2]

with overview_tab:
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

    def is_valid_line(line: str) -> bool:
        if not isinstance(line, str):
            return False
        line = line.strip()
        ln = len(line)
        if ln == 0 or ln > 4:
            return False
        if line[0].isalpha():
            if line[0] not in {"X", "A", "B", "C"}:
                return False
            if line[0] == "X":
                num = line[1:]
                if not num.isdigit():
                    return False
                n = int(num)
                return (1 <= n <= 99) or (100 <= n <= 250) or (901 <= n <= 917)
            
            return ln == 1
        
        if not line.isdigit():
            return False
        n = int(line)
        return (1 <= n <= 99) or (100 <= n <= 250) or (901 <= n <= 917)

    def assign_nearest_parent(df: pd.DataFrame, stops_df: pd.DataFrame) -> list[str]:
        if df.empty:
            return []
        lat0 = df["lat"].to_numpy()
        lon0 = df["lon"].to_numpy()
        p_lat = stops_df["avg_lat"].to_numpy()
        p_lon = stops_df["avg_lon"].to_numpy()
        p_names = stops_df["stop_name"].to_numpy()

        assigned = []
        for y, x in zip(lat0, lon0):
            dlat = p_lat - y
            dlon = p_lon - x
            idx = np.argmin(dlat * dlat + dlon * dlon)
            assigned.append(p_names[idx])
        return assigned
    # --- Initial data display ---
    parents_df = load_parent_stations()
    if parents_df is None or parents_df.empty:
        st.error("Could not load stop information from the local database.")
        st.stop()

    st.subheader("Prague Stops (zone P)")
    try:
        stops_grouped_df = get_stops_grouped_by_name()
    except Exception as exc:
        st.error(f"Failed to read stops from database: {exc}")
        st.stop()

    stops_grouped_df = stops_grouped_df.rename(
        columns={
            "stop_name": "Stop",
            "avg_lat": "Latitude",
            "avg_lon": "Longitude",
            "stop_count": "Number of Platforms",
        }
    )

    if stops_grouped_df.empty:
        st.info("No stops found in the database.")
        st.stop()

    stops_grouped_df["stop_name"] = stops_grouped_df["Stop"]
    stops_grouped_df["avg_lat"] = stops_grouped_df["Latitude"]
    stops_grouped_df["avg_lon"] = stops_grouped_df["Longitude"]
    stops_grouped_df = stops_grouped_df[stops_grouped_df["Stop"].notna()]
    stops_grouped_df["Stop"] = stops_grouped_df["Stop"].astype(str).str.strip()
    stops_grouped_df = stops_grouped_df[~stops_grouped_df["Stop"].str.fullmatch(r"E\d+")]
    display_cols = ["Stop", "Latitude", "Longitude", "Number of Platforms"]
    st.dataframe(stops_grouped_df[display_cols])

    # --- Map: All stops in zone P ---------------------------------------------
    st.markdown("### 🗺️ Map of All Stops Prague")
    station_options = ["ALL STATIONS"] + sorted(stops_grouped_df["Stop"].unique())
    station_choice = st.selectbox("Select a Station to View Individual Platforms", station_options)

    if station_choice == "ALL STATIONS":
        with st.spinner("Rendering map…"):
            center_lat = stops_grouped_df["Latitude"].mean()
            center_lon = stops_grouped_df["Longitude"].mean()

            base_map = folium.Map(location=[center_lat, center_lon], zoom_start=12)
            cluster = MarkerCluster().add_to(base_map)

            
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
                    f"<b>{row.Stop}</b><br/>"
                    f"Number of platforms: {len(platform_dict[row.Stop])}"
                )
                folium.Marker(
                    location=[row.Latitude, row.Longitude],
                    popup=popup_html,
                    icon=folium.Icon(color='green', icon='info-sign')
                ).add_to(cluster)

            st_folium(base_map, width=700, height=450)
    else:
        # Individual station view
        selected_name = station_choice
       
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
            st_folium(base_map, width=700, height=450)
        else:
            st.info(f"No platform data available for {selected_name}.")

    st.markdown("---")

with dwell_tab:
    # --- Dwell Time Analysis -------------------------------------------------
    st.subheader("Dwell Time at Stops")
    with st.form("dwell_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            start_date = st.date_input("Start", value=pd.Timestamp.now().date())
        with c2:
            end_date = st.date_input("End", value=pd.Timestamp.now().date())
        with c3:
            min_dwell = st.number_input("Min dwell (s)", 60, 3600, 60, step=60)
        run = st.form_submit_button("Run")

    if run:
        if start_date > end_date:
            st.error("Start date > end date")
        elif end_date > pd.Timestamp.now().date():
            st.error("End date ve future")
        else:
            sd = f"{start_date} 00:00:00"
            ed = f"{end_date} 23:59:59"
            q = (
                "SELECT vehicle_id, gtfs_trip_id, route_type, latitude, longitude, timestamp "
                "FROM vehicle_positions "
                "WHERE state_position='at_stop' "
                f"AND timestamp BETWEEN '{sd}' AND '{ed}' "
                "ORDER BY vehicle_id, timestamp"
            )
            with st.spinner("This might take a while"):
                try:
                    if  st.session_state["SERVER_ADDRESS"] is None or st.session_state["API_URL"] is None or st.session_state["api_key"] is None:
                        st.error("Please upload .env file first.")
                        st.stop()
                    rm = RequestManager()
                    cols = ["vehicle_id", "gtfs_trip_id", "route_type", "lat", "lon", "ts"]
                    df = rm.server_request(q, columns=cols)
                except Exception as exc:
                    st.error(f"Unable to retrieve dwell-time data: {exc}")
                    df = pd.DataFrame()

            if df.empty:
                st.info("No data returned for the selected period.")
            else:
                df = df[df["route_type"] != "metro"]

                df["ts"] = pd.to_datetime(df["ts"])
                df[["lat", "lon"]] = df[["lat", "lon"]].astype(float)

                df["prev_lat"] = df.groupby("vehicle_id")["lat"].shift()
                df["prev_lon"] = df.groupby("vehicle_id")["lon"].shift()
                df["prev_ts"] = df.groupby("vehicle_id")["ts"].shift()

                d = haversine(df["lat"], df["lon"], df["prev_lat"], df["prev_lon"])
                dt = (df["ts"] - df["prev_ts"]).dt.total_seconds()

                df["break"] = (
                    (df["vehicle_id"] != df["vehicle_id"].shift()) |
                    (d > 0.15) |                    # > 150 m
                    (dt > 300)                      # > 5 min
                )
                df["group_id"] = df["break"].cumsum()

                agg = (
                    df.groupby("group_id")
                    .agg(
                        vehicle_id=("vehicle_id", "first"),
                        gtfs_trip_id=("gtfs_trip_id", "first"),
                        lat=("lat", "first"),
                        lon=("lon", "first"),
                        arrival=("ts", "first"),
                        departure=("ts", "last")
                    )
                    .reset_index(drop=True)
                )
                agg["dwell_seconds"] = (agg["departure"] - agg["arrival"]).dt.total_seconds()
                agg = agg[agg["dwell_seconds"] >= min_dwell]

                if agg.empty:
                    st.info("No dwell events ≥ threshold")
                else:
                    try:
                        agg["Stop"] = assign_nearest_parent(agg.rename(
                            columns={"lat": "lat", "lon": "lon"}), stops_grouped_df)

                        routes = TripManager().get_infos_by_trip_id(agg["gtfs_trip_id"].tolist())
                        routes = routes.rename(columns={"trip_id": "gtfs_trip_id", "route_short_name": "Line"})
                        out = agg.merge(routes, on="gtfs_trip_id", how="left")
                        out = out[out["Line"].apply(is_valid_line)]
                        out = out[["Stop", "Line", "vehicle_id", "arrival", "departure", "dwell_seconds"]]
                        out.columns = ["Stop", "Line", "Vehicle", "Arrival", "Departure", "Dwell (s)"]

                        st.subheader("Single Dwell Time Events")
                        st.success(f"Found {len(out)} dwell events that meet the criteria")
                        st.dataframe(out, use_container_width=True)

                        # Cumulative Dwell Time per Stop
                        cum = out.groupby("Stop")["Dwell (s)"].sum().reset_index()
                        cum["Dwell (min)"] = cum["Dwell (s)"] / 60
                        cum = cum.sort_values("Dwell (min)", ascending=False)

                        st.subheader("Cumulative Dwell Time per Stop")
                        fig = px.bar(
                            cum,
                            x="Stop",
                            y="Dwell (min)",
                            labels={"Dwell (min)": "Total dwell (min)"},
                            title=""
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("Total dwell minutes accumulated at each stop during the selected period.")

                        st.subheader("Dwell Time Heatmap")
                        with st.spinner("Rendering heatmap…"):
                            center_lat = stops_grouped_df["avg_lat"].mean()
                            center_lon = stops_grouped_df["avg_lon"].mean()
                            m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

                            heat_data = [
                                [
                                    stops_grouped_df.loc[stops_grouped_df["stop_name"] == stop, "avg_lat"].values[0],
                                    stops_grouped_df.loc[stops_grouped_df["stop_name"] == stop, "avg_lon"].values[0],
                                    dwell_min
                                ]
                                for stop, dwell_min in zip(cum["Stop"], cum["Dwell (min)"])
                            ]

                            HeatMap(
                                heat_data,
                                radius=25,   
                                blur=35,     
                                max_zoom=13
                            ).add_to(m)
                            st_folium(m, width=700, height=450)

                        # Average dwell time and event count per stop
                        stats = out.groupby("Stop").agg(
                            avg_dwell_min=("Dwell (s)", lambda x: x.mean() / 60),
                            event_count=("Dwell (s)", "count")
                        ).reset_index()
                        stats = stats.sort_values("avg_dwell_min", ascending=False)
                        st.subheader("Average Dwell Time vs. Event Count")
                        fig2 = px.scatter(
                            stats,
                            x="Stop",
                            y="avg_dwell_min",
                            size="event_count",
                            labels={"avg_dwell_min": "Average dwell (min)", "event_count": "Number of events"},
                            title=""
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                        st.caption("Average dwell per stop; bubble size = number of dwell events.")
                    except Exception as exc:
                        st.error(f"Unable to build visualisations: {exc}")

