import requests
import os
from dotenv import load_dotenv
import os
import sqlite3

class RouteManager:
    def __init__(self, api_url, db_path, headers):
        self.api_url = api_url 
        self.connection = sqlite3.connect(db_path)
        self.headers = headers

    def get_routes(self):
        url = f"{self.api_url}/routes"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching routes: {response.status_code}")       
    
    def create_route_table(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                route_id TEXT PRIMARY KEY,
                agency_id TEXT,
                route_short_name TEXT,
                route_long_name TEXT,
                route_desc TEXT,
                route_type INTEGER,
                is_night BOOLEAN,
                is_regional BOOLEAN,
                is_substitute_transport BOOLEAN,
                route_color TEXT,
                route_text_color TEXT,
                route_url TEXT,
                last_modify TEXT
            )
            """)
        self.connection.commit()



    def set_routes(self):
        routes = self.get_routes()
        cursor = self.connection.cursor()
        route_table = self.create_route_table()
        for route in routes:
            cursor.execute("""
                    INSERT OR REPLACE INTO routes (
                        route_id, agency_id, route_short_name, route_long_name,
                        route_desc, route_type, is_night, is_regional, 
                        is_substitute_transport, route_color, route_text_color, 
                        route_url, last_modify
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                route.get("route_id"),
                route.get("agency_id"),
                route.get("route_short_name"),
                route.get("route_long_name"),
                route.get("route_desc", ""),  # Default to empty string if None
                route.get("route_type"),
                route.get("is_night", False),  # Default to False if None
                route.get("is_regional", False),  # Default to False if None
                route.get("is_substitute_transport", False),  # Default to False
                route.get("route_color"),
                route.get("route_text_color"),
                route.get("route_url"),
                route.get("last_modify", "Unknown")  # Default to 'Unknown' if None
                ))
        self.connection.commit()