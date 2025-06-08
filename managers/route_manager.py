import requests
import sqlite3
class RouteManager:
    """Manages GTFS route data: fetches from the API and loads into a local SQLite database.

    Attributes:
        api_url (str): Base URL of the GTFS API.
        db_path (str): File path to the SQLite database.
        headers (dict): HTTP headers containing the API authentication token.
    """
    def __init__(self, api_url, db_path, headers):
        """Initialize the RouteManager.

        Args:
            api_url (str): The base URL for GTFS API requests.
            db_path (str): Path to the local SQLite database file.
            headers (dict): HTTP headers for authentication.
        """
        self.api_url = api_url
        self.db_path = db_path  
        self.headers = headers

    def get_routes(self):
        """Fetch all routes from the GTFS API.

        Returns:
            list: A list of route dictionaries on success.

        Raises:
            Exception: If the HTTP response status is not 200.
        """
        url = f"{self.api_url}/routes"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching routes: {response.status_code}")

    def create_route_table(self):
        """Create the 'routes' table in the SQLite database if it does not already exist.

        The table includes fields for route ID, names, type flags, colors, and last modification timestamp.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
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
            conn.commit()
            # dont close her for refresh

    def set_routes(self):
        """Fetch route data and populate the local database.

        Skips any routes with 'route_type' == 2 (trains) and inserts or replaces
        remaining routes into the 'routes' table.
        """
        self.create_route_table()
        routes = self.get_routes()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for route in routes:
                if route.get("route_type") == 2:
                    continue
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
                    route.get("route_desc", ""),
                    route.get("route_type"),
                    route.get("is_night", False),
                    route.get("is_regional", False),
                    route.get("is_substitute_transport", False),
                    route.get("route_color"),
                    route.get("route_text_color"),
                    route.get("route_url"),
                    route.get("last_modify", "Unknown")
                ))
            conn.commit()
