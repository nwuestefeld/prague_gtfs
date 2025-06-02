import requests
import sqlite3

class ShapeManager:
    def __init__(self, api_url, db_path, headers):
        self.api_url = api_url
        self.db_path = db_path  # Path to the db
        self.headers = headers

    def create_shape_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shape (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shape_id TEXT,
                    shape_dist_traveled REAL,
                    shape_pt_sequence INTEGER,
                    longitude REAL,
                    latitude REAL
                )
            """)
            conn.commit()
            # no commit close! we use with

    def get_shapes(self, shape_id):
        url = f"{self.api_url}/shapes/{shape_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching shapes: {response.status_code}")
