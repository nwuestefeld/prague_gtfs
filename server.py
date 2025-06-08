### DO NOT RUN THIS FILE!!!!

### This file is for server use only!
### It fetches vehicle positions from the Golemio API and stores them in a SQLite database.

"""
server.py

Continuously fetches vehicle position data from the Golemio API, stores it in a SQLite database,
and logs the process.
Intend as gather buffer for delay data.

Prerequisites:
- API_KEY stored in a .env file
- Required libraries: requests, python-dotenv

Usage:
1. Save your API key in the .env file (API_KEY=your_api_key)
2. Run the script: python gather_vehicle_positions.py
3. Stop with CTRL+C

Functions:
- create_table(): Creates the SQLite table if it doesn't exist
- get_vehicle_positions(): Retrieves JSON data from the API
- store_vehicle_positions(data): Stores the data in the database
- main(): Main loop that periodically fetches and saves data

Logging:
- Logs events and errors to 'vehicle_positions.log'


TODO:
- Add Token Authentication
"""

import requests
import time
import sqlite3
import numpy as np
import pandas as pd
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
API_URL = "https://api.golemio.cz/v2/public/vehiclepositions"

load_dotenv()
API_KEY = os.getenv("API_KEY")

headers = {
    "X-Access-Token": API_KEY
}


logging.basicConfig(
    filename='gather.log',            
    level=logging.INFO,               
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

def add_timestamp(data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for feature in data:
        feature["timestamp"] = timestamp
    return data



#todo "gtfs_route_short_name"
def create_table():
    """Create the vehicle_positions table in the local SQLite database if it does not exist.

    The table stores vehicle_id, trip IDs, route types, delays, coordinates, and timestamps.
    """
    conn = sqlite3.connect('vehicle_positions.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vehicle_positions (
                        vehicle_id TEXT,
                        gtfs_trip_id TEXT,
                        route_type TEXT,
                        gtfs_route_short_name TEXT,
                        bearing REAL,
                        delay REAL,
                        latitude REAL,
                        longitude REAL,
                        "state_position" TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()
    logger.info("Database table checked/created.")



def get_vehicle_positions():
    """Fetch real-time vehicle position data from the Golemio API.

    Returns:
        dict or None: JSON response containing features if successful, otherwise None.

    Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
    """
    try:
        response = requests.get(API_URL, headers=headers)
        logger.info("Successfully fetched vehicle positions.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API Error: {e}") #log errors
        return None


def store_vehicle_positions(data):
    """Store vehicle position features into the local SQLite database.

    Args:
        data (dict): JSON response with a 'features' list of vehicle position dicts.

    Returns:
        None
    """
    if not data or "features" not in data:
        print("No data to store.")
        return
    
    #db setup
    conn = sqlite3.connect('vehicle_positions.db')
    cursor = conn.cursor()

    features = data.get("features", [])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for feature in features:

        #get highlevel structure of the data
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        coordinates = geometry.get("coordinates", [None, None])

        rows.append((
            properties.get("vehicle_id", ""),
            properties.get("gtfs_trip_id", ""),
            properties.get("route_type", ""),
            properties.get("gtfs_route_short_name", ""),
            properties.get("bearing", 0),
            properties.get("delay", 0),
            coordinates[1],  # latitude
            coordinates[0],  # longitude
            properties.get("state_position", ""),
            timestamp
        ))

    cursor.executemany('''INSERT INTO vehicle_positions (
                            vehicle_id, gtfs_trip_id, route_type, gtfs_route_short_name, bearing, delay,
                            latitude, longitude, state_position, timestamp)
                          VALUES (?, ?, ?, ?, ?, ?,?, ?, ?, ?)''', rows)

    conn.commit()
    conn.close()
    logger.info(f"Stored {len(rows)} vehicle positions to DB.")


def main():
    """Continuously fetch and store vehicle position data at 30-second intervals.

    Creates the database table if needed, then loops to fetch, store, and log data.
    """
    create_table() 

    
    while True:
        print("Fetching Data...")
        data = get_vehicle_positions()
        logger.info("Fetching data...")
        if data:
            store_vehicle_positions(data)
            print("Data Saved.")
        
        time.sleep(30)

if __name__ == "__main__":
    main()   
