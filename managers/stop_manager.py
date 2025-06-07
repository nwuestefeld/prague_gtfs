import requests
import sqlite3

class StopManager:
    def __init__(self, api_url, db_path, headers):
        self.api_url = api_url
        self.db_path = db_path
        self.headers = headers

    def get_stops(self):
        url = f"{self.api_url}/stops"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()["features"]
        else:
            raise Exception(f"Error fetching stops: {response.status_code}")      

    def create_stop_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
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
        self.create_stop_table()
        stops = self.get_stops()
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
