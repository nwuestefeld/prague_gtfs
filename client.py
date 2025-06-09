import os
import requests
import sqlite3
from dotenv import load_dotenv
import streamlit as st
from managers.route_manager import RouteManager
from managers.stop_manager import StopManager
from managers.trip_manager import TripManager
class Client:
    def __init__(self):
        load_dotenv()
        if "api_key" not in st.session_state:
            raise RuntimeError("API key not set – please set it on the Connections page first.")
        self.api_key = st.session_state["api_key"]
        #self.api_key = os.getenv("API_KEY")
        self.api_url = os.getenv("API_URL")
        self.headers = {"X-Access-Token": self.api_key}
        self.db_path = "database.db"

        self.routemanager = RouteManager(self.api_url, self.db_path, self.headers)
        self.stopmanager = StopManager()
        self.tripmanager = TripManager()

    def run(self):
        self.routemanager.set_routes()
        self.stopmanager.set_stops()
        self.tripmanager.set_trips()


#ToDo: überlegen wie realtime zeug aussehen soll