"""
main.py: Entry point for the Streamlit GTFS application.

Defines the main() function that renders the welcome page, description,
and a button to refresh static GTFS data via the Client manager.
"""
from client import Client
import streamlit as st

def main():
    """Render the GTFS App main page with navigation and data refresh.

    Displays:
        - The application title and sidebar navigation info.
        - An introduction to functionality and usage.
        - A 'Refresh Data' button to update static GTFS tables via Client.

    Args:
        None

    Returns:
        None
    """
    st.title("Welcome to the GTFS App!")
    st.sidebar.info("Navigate using the sidebar.")
    st.markdown("""
    **Welcome to the Prague GTFS Dashboard!**  
    This application allows you to explore both static and real-time GTFS data for the Prague public transport system.

    **What you can do here:**
    - **Refresh Data**: Update your local static GTFS database (routes, stops, trips).
    - **Navigate**: Use the sidebar to switch between Dashboard, Map, Stops, and Connections pages.
    - **Realtime Insights**: View up-to-date delay information for trams, metro, buses, trolleybuses, and funicular.

    Make sure to set your API key and upload your PEM key on the **Connections** page before using realtime features.
    """, unsafe_allow_html=True)

    if st.button("Refresh Data"):
        client = Client()
        with st.spinner("Loading data..."):
            client.run()
        st.success("Your database is up to date!")

if __name__ == "__main__":
    main()
