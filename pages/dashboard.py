import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

conn = sqlite3.connect("vehicle_positions.db")
query = """SELECT * FROM vehicle_positions WHERE delay IS NOT NULL AND delay > 60"""
df = pd.read_sql_query(query, conn)
conn.close()


st.title("Dashboard")
st.write("This is a Dashboard page.")

vehicle_type = st.selectbox(
    "Choose vehicle type",
    ["All", "tram", "metro","train","bus"]
)
df_filtered = df.copy()

if vehicle_type != "All":
    df_filtered = df_filtered[df_filtered['route_type'] == vehicle_type]

if df_filtered.empty:
    st.warning("No data available for the selected filter.")

if not df_filtered.empty:
    st.write(f"Observations with more than 60 sec delay: {len(df_filtered)}")
    fig, ax = plt.subplots()
    ax.hist(df_filtered['delay'], bins=20, edgecolor='black')
    ax.set_title("Distr of Delay")
    ax.set_xlabel("Minutes")
    ax.set_ylabel("Observations")
    st.pyplot(fig)
    


##fetch database stuff
st.subheader("Delay Statistics")

#filter dataframe

#plot top 10 delays
#TODO: connect to static database to get features of interest gtfs_trip_id = trip_id ?
#get trip_id and use in route manager to get route info
st.subheader("Top 10 Delays")
top_delays = df_filtered.nlargest(10, 'delay')
st.dataframe(top_delays[['vehicle_id', 'delay']])