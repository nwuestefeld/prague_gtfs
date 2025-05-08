import os
import requests
import sqlite3
from dotenv import load_dotenv
from managers.route_manager import RouteManager
from managers.stop_manager import StopManager
from managers.trip_manager import TripManager
class Client:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API key not found in environment variables.")

        self.api_url = os.getenv("API_URL")
        if not self.api_url:
            raise ValueError("API URL not found in environment variables.")

        self.headers = {"X-Access-Token": self.api_key}

        self.db_path = "database.db"
        self.connection = sqlite3.connect(self.db_path)
     
   

      
        #mange routes
        routemanager = RouteManager(self.api_url, self.db_path, headers=self.headers)
        routemanager.set_routes()
        #manage stops
        stopmanager = StopManager(self.api_url, self.db_path, headers=self.headers)
        stopmanager.set_stops()
        #manage trips
        tripmanager = TripManager(self.api_url, self.db_path, headers=self.headers)
        tripmanager.set_trips()

#ToDo: überlegen wie realtime zeug aussehen soll