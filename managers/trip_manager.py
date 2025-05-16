import requests
import sqlite3

class TripManager:
    def __init__(self, api_url, db_path, headers):
        self.api_url = api_url
        self.db_path = db_path  # Pfad zur DB, keine Connection mehr
        self.headers = headers

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
            conn.close()

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
            conn.close()
