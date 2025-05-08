import requests
import os
from dotenv import load_dotenv
import os
import sqlite3

class StopManager:
    def __init__(self, api_url, db_path, headers):
        self.api_url = api_url 
        self.connection = sqlite3.connect(db_path)
        self.headers = headers

    def get_stops(self):
        url = f"{self.api_url}/stops"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()["features"]
        else:
            raise Exception(f"Error fetching stops: {response.status_code}")      
        
    def create_stop_table(self):
        cursor = self.connection.cursor()
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
        self.connection.commit()
    
    def set_stops(self):
        self.create_stop_table()
        stops = self.get_stops()
        cursor = self.connection.cursor()
        
        for stop in stops:
            props = stop["properties"]
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
        self.connection.commit()
        self.connection.close()


