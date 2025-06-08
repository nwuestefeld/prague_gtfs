import requests
import sqlite3

class StopManager:
    """Manage GTFS stops: fetch from API, filter by zone P, and store in SQLite.

    Attributes:
        api_url (str): Base URL for the GTFS API.
        db_path (str): Path to the local SQLite database file.
        headers (dict): HTTP headers for authentication.
    """
    def __init__(self, api_url, db_path, headers):
        """Initialize the StopManager.

        Args:
            api_url (str): The GTFS API base URL.
            db_path (str): SQLite database file path.
            headers (dict): HTTP headers including the API key.
        """
        self.api_url = api_url
        self.db_path = db_path
        self.headers = headers

    def get_stops(self):
        """Fetch all stops from the API with pagination.

        Retrieves up to 10,000 features per request until no more are returned.

        Returns:
            list: A list of stop feature dictionaries.

        Raises:
            Exception: If an HTTP request returns a non-200 status.
        """
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
