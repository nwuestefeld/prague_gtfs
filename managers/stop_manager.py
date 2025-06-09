import requests
import sqlite3
import pandas as pd
import streamlit as st	
from scipy.spatial import cKDTree
import numpy as np

class StopManager:

    def __init__(self):
        self.api_url = st.session_state["API_URL"]
        self.db_path = "database.db"
        if "api_key" not in st.session_state:
            raise RuntimeError("API key not set – please set it on the Connections page first.")
        self.headers = {"X-Access-Token": st.session_state["api_key"]}


    def get_all_stops(self):
        all_features = []
        limit = 10000
        offset = 0

        while True:
            url = f"{self.api_url}/stops?limit={limit}&offset={offset}"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                raise Exception(f"Error fetching stops: {response.status_code}")
            data = response.json()
            features = data.get("features", [])
            if not features:
                break
            all_features.extend(features)
            offset += limit

        return all_features

    def create_stop_table(self):
        """Create or replace the 'stops' table in the local SQLite database.

        Drops the existing table and defines columns for stop metadata and coordinates.

        Returns:
            None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS stops")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stops (
                    stop_id TEXT PRIMARY KEY,
                    stop_name TEXT,
                    location_type INTEGER,
                    parent_station TEXT,
                    platform_code TEXT,
                    wheelchair_boarding INTEGER,
                    zone_id TEXT,
                    level_id TEXT,
                    longitude REAL,
                    latitude REAL
                )
            """)
            conn.commit()
            # kein conn.close()

    def set_stops(self):
        """Populate the stops table with API data filtered to zone P.

        Fetches features, filters by 'zone_id' == 'P', and inserts them into the database.

        Returns:
            None
        """
        self.create_stop_table()
        stops = self.get_all_stops()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for stop in stops:
                props = stop["properties"]
                if props.get("zone_id") != "P":
                    continue # Skip stops not in zone P
                coords = stop["geometry"]["coordinates"]
                cursor.execute("""
                    INSERT OR REPLACE INTO stops (
                        stop_id, stop_name, location_type, parent_station, platform_code,
                        wheelchair_boarding, zone_id, level_id, longitude, latitude
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    props.get("stop_id"),
                    props.get("stop_name"),
                    props.get("location_type"),
                    props.get("parent_station"),
                    props.get("platform_code"),
                    props.get("wheelchair_boarding"),
                    props.get("zone_id"),
                    props.get("level_id"),
                    coords[0],
                    coords[1]
                ))
            conn.commit()
            # no conn.close()
    def get_stops(self):
        with sqlite3.connect(self.db_path) as conn:
            stops = pd.read_sql_query("SELECT stop_id, stop_name, longitude, latitude FROM stops WHERE stop_name IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL", conn)
            columns = ["stop_id", "stop_name", "longitude", "latitude"]
            return pd.DataFrame(stops, columns=columns)
    
    def match_nearest_stops(self, vp_df, stops_df, max_distance_meters=100):
            # Convert all lat and long columns to float to avoid type errors
            if vp_df.empty or stops_df.empty:
                st.error("Vehicle positions or stops data is empty. Please ensure the database is populated.")
                return None
            stops_df["latitude"] = stops_df["latitude"].astype(float)
            stops_df["longitude"] = stops_df["longitude"].astype(float)
            vp_df["latitude"] = vp_df["latitude"].astype(float)
            vp_df["longitude"] = vp_df["longitude"].astype(float)

            #convert lat and long to radians for haversine calculation
            stops_df["latitude_rad"] = np.radians(stops_df["latitude"])
            stops_df["longitude_rad"] = np.radians(stops_df["longitude"])
            vp_df["latitude_rad"] = np.radians(vp_df["latitude"])
            vp_df["longitude_rad"] = np.radians(vp_df["longitude"])
            # Create  KDTree for nn search
            stops_tree = cKDTree(stops_df[["latitude_rad", "longitude_rad"]].values)
            distances, indices = stops_tree.query(vp_df[["latitude_rad", "longitude_rad"]].values, distance_upper_bound=max_distance_meters)

            matched_stops = []
            for i, (dist, idx) in enumerate(zip(distances, indices)):
                if idx != len(stops_df):  # Check if idx is valid
                    vp_row = vp_df.iloc[i].to_dict()
                    stop_row = stops_df.iloc[idx].to_dict()
                    vp_row.update({f"matched_{k}": v for k, v in stop_row.items()})
                    vp_row["distance_m"] = dist
                    matched_stops.append(vp_row)
                    matched_stops_df = pd.DataFrame(matched_stops)
            if matched_stops_df.empty:
                st.info("No matching stations found. You might need to refresh the database.")
                return None
            else:
                matched_stops_df.drop(columns=["latitude_rad", "longitude_rad","matched_longitude","matched_latitude", "distance_m","matched_latitude_rad","matched_longitude_rad"], inplace=True)
                matched_stops_df.rename(columns={"matched_stop_id": "stop_id","matched_stop_name": "stop_name"}, inplace=True)    
                #only unique stop trips and bearing combinations, pick the last one
                matched_stops_df = matched_stops_df.drop_duplicates(subset=["gtfs_trip_id", "stop_id", "bearing"], keep="last")
            return matched_stops_df

