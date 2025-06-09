"""
client.py: Defines the Client class to refresh local GTFS databases.

The Client class loads API credentials from Streamlit session state,
and orchestrates fetching static routes, stops, and trips data
into a local SQLite database.
"""
import os
import requests
import sqlite3
from dotenv import load_dotenv
import streamlit as st
from managers.route_manager import RouteManager
from managers.stop_manager import StopManager
from managers.trip_manager import TripManager
class Client:
    """Orchestrates GTFS data refresh by calling individual managers.

    Attributes:
        api_key (str): API key loaded from Streamlit session state.
        api_url (str): Base URL for GTFS API.
        headers (dict): HTTP headers for API requests.
        db_path (str): Local path to the SQLite database file.
        routemanager (RouteManager): Manager for GTFS routes.
        stopmanager (StopManager): Manager for GTFS stops.
        tripmanager (TripManager): Manager for GTFS trips.
    """
    def __init__(self):
        """Initialize the Client.

        Loads environment variables, retrieves API credentials,
        and initializes managers for routes, stops, and trips.
        """
        load_dotenv()
        if "api_key" not in st.session_state:
            st.error("Keys are not set – please go to the 'Connections' page and upload it first.")
            st.stop()
        self.api_key = st.session_state["api_key"]
        #self.api_key = os.getenv("API_KEY")
        self.api_url = st.session_state["api_url"]
        self.headers = {"X-Access-Token": self.api_key}
        self.db_path = "database.db"

        self.routemanager = RouteManager(self.api_url, self.db_path, self.headers)
        self.stopmanager = StopManager()
        self.tripmanager = TripManager()

    def run(self):
        """Run all data managers to refresh local GTFS tables.

        Calls set_routes, set_stops, and set_trips in order to
        update the SQLite database with the latest static GTFS data.
        """
        self.routemanager.set_routes()
        self.stopmanager.set_stops()
        self.tripmanager.set_trips()


#ToDo: überlegen wie realtime zeug aussehen soll