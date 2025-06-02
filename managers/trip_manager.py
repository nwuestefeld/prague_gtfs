import requests
import sqlite3
import os
from dotenv import load_dotenv
import pandas as pd

class TripManager:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("API_KEY")
        self.api_url = os.getenv("API_URL")
        self.headers = {"X-Access-Token": self.api_key}
        self.db_path = "database.db"

    def create_trip_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    trip_id TEXT PRIMARY KEY,
                    route_id TEXT,
                    service_id TEXT,
                    trip_headsign TEXT,
                    direction_id INTEGER,
                    block_id TEXT,
                    shape_id TEXT,
                    wheelchair_accessible INTEGER,
                    bikes_allowed INTEGER,
                    exceptional INTEGER,
                    last_modify TEXT
                )
            """)
            conn.commit()
            # kein conn.close()

    def get_trips(self):
        url = f"{self.api_url}/trips"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching trips: {response.status_code}")

    def set_trips(self):
        self.create_trip_table()
        trips = self.get_trips()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for trip in trips:
                cursor.execute("""
                    INSERT OR REPLACE INTO trips (
                        trip_id, route_id, service_id, trip_headsign, direction_id,
                        block_id, shape_id, wheelchair_accessible, bikes_allowed,
                        exceptional, last_modify
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trip.get("trip_id"),
                    trip.get("route_id"),
                    trip.get("service_id"),
                    trip.get("trip_headsign"),
                    trip.get("direction_id"),
                    trip.get("block_id"),
                    trip.get("shape_id"),
                    trip.get("wheelchair_accessible"),
                    trip.get("bikes_allowed"),
                    trip.get("exceptional"),
                    trip.get("last_modify")
                ))
            conn.commit()
            # kein conn.close()

    def get_infos_by_trip_id(self, trip_ids):
        if not trip_ids:
            return pd.DataFrame()  

        placeholders = ",".join("?" for _ in trip_ids)  #  "?, ?, ?"
        query = f"""
            SELECT
                trips.trip_id,
                trips.shape_id,
                routes.route_short_name,
                routes.route_long_name,
                routes.route_color
            FROM trips
            LEFT JOIN routes ON trips.route_id = routes.route_id
            WHERE trips.trip_id IN ({placeholders})
        """

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, trip_ids)
            rows = cursor.fetchall()

        columns = ["trip_id", "shape_id", "route_short_name", "route_long_name", "route_color"]
        df = pd.DataFrame(rows, columns=columns)
        return df
