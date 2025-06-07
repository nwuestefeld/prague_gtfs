from client import Client
import streamlit as st

def main():
    st.title("Welcome to the GTFS App!")
    st.sidebar.info("Navigate using the sidebar.")
    st.write("""
        This Dashboard is designed to help you explore and analyze GTFS data from the Prague public transport system.

        You can:
        - View trip delays in real-time
        - Filter trips and apply various analysis parameters
        - Visualize delays on a map
        - Get insights on stops
        - Export data for further analysis

        Use the sidebar to navigate through the different views and tools.  
             
        The realtime data is automatically updated from the server, ensuring you always have the latest information at your fingertips.
        If you want to refresh the stationary data, click the "Refresh Data" button below.
        
             
        For more information, please refer to the documentation or contact the Admins
        """)

    if st.button("Refresh Data"):
        client = Client()
        with st.spinner("Loading data..."):
            client.run()
        st.success("Your database is up to date!")

if __name__ == "__main__":
    main()
