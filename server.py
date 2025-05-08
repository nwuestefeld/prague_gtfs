
### DO NOT RUN THIS FILE!!!!

### This file is for testing purposes only. 
### It fetches vehicle positions from the Golemio API and stores them in a SQLite database.
### Intend for server use only.


import requests
import time
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
API_URL = "https://api.golemio.cz/v2/public/vehiclepositions"

load_dotenv()
API_KEY = os.getenv("API_KEY")

headers = {
    "X-Access-Token": API_KEY
}


def add_timestamp(data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for feature in data:
        feature["timestamp"] = timestamp
    return data

def create_table():
    conn = sqlite3.connect('vehicle_positions.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vehicle_positions (
                        vehicle_id TEXT,
                        gtfs_trip_id TEXT,
                        route_type TEXT,
                        latitude REAL,
                        longitude REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    conn.commit()
    conn.close()



def get_vehicle_positions():
    try:
        response = requests.get(API_URL, headers=headers)
        response.raise_for_status()  # for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return None


def store_vehicle_positions(data):
    conn = sqlite3.connect('vehicle_positions.db')
    cursor = conn.cursor()

    features = data.get("features", [])
    rows = []
    for feature in features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        coordinates = geometry.get("coordinates", [])
        gtfs_trip_id = properties.get("gtfs_trip_id", "")
        route_type = properties.get("route_type", "")
        vehicle_id = properties.get("vehicle_id", "")
        rows.append((vehicle_id, gtfs_trip_id, route_type, coordinates[1], coordinates[0]))

    # Batch-Insertion for performance
    cursor.executemany('''INSERT INTO vehicle_positions (vehicle_id, gtfs_trip_id, route_type, latitude, longitude)
                          VALUES (?, ?, ?, ?, ?)''', rows)

    conn.commit()
    conn.close()



def main():
    create_table() 

    
    while True:
        print("Fetching Data...")
        data = get_vehicle_positions()
        
        if data:
            store_vehicle_positions(data)
            print("Data Saved.")
        
        time.sleep(30)

if __name__ == "__main__":
    main()   

