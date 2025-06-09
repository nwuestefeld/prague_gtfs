import requests
import sqlite3
import shapely.wkt as wkt
class ShapeManager:
    """Manage GTFS shape data and geographic operations.

    Attributes:
        wtk (str): Path to the WKT file describing the polygon for filtering.
    """
    def __init__(self):
        """Initialize the ShapeManager.

        Sets the path to the WKT file containing the tariff zone polygon.
        """
        self.wtk = "tariff_zones.wkt"
       # self.api_url = api_url
        #self.db_path = db_path  # Path to the db
        #self.headers = headers


    # not implemented yet
    def create_shape_table(self):
        """Create a local SQLite table to store shape points.

        The table includes fields for shape ID, sequence, and coordinates.

        Args:
            None

        Returns:
            None
        """
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
        """Fetch shape point data for a specific shape ID from the GTFS API.

        Args:
            shape_id (str): The identifier of the shape to retrieve.

        Returns:
            list: The JSON response containing shape point data.

        Raises:
            Exception: If the HTTP response status is not 200.
        """
        url = f"{self.api_url}/shapes/{shape_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error fetching shapes: {response.status_code}")
        

    def set_bounding_box(self):
        """Compute the bounding box from the tariff zone WKT polygon.

        Reads the WKT file, converts it to a geometry, and returns
        its minimum and maximum longitude and latitude values.

        Returns:
            tuple: (minx, miny, maxx, maxy) coordinates of the bounding box.
        """
        with open(self.wtk, "r") as f:
            wkt_polygon = f.read().strip()
        polygon_geom = wkt.loads(wkt_polygon)
        minx, miny, maxx, maxy = polygon_geom.bounds
        return minx, miny, maxx, maxy
