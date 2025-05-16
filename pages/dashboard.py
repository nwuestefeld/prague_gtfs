import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Connect to the SQLite database
conn = sqlite3.connect("vehicle_positions.db")
query = """SELECT * FROM vehicle_positions WHERE delay IS NOT NULL AND delay > 60"""
df = pd.read_sql_query(query, conn)
conn.close()

# Page title
st.title("Delay Dashboard")

# Create tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Delay Distribution", 
    "Delay Statistics", 
    "Top 10 Delays", 
    "Pie Chart", 
    "Map"
])

# Tab 1: Delay Distribution
with tab1:
    st.subheader("Delay Distribution")
    st.write("This page shows the distribution of delays by vehicle type.")

    vehicle_type = st.selectbox(
        "Select vehicle type",
        ["All", "tram", "metro", "train", "bus"]
    )

    df_filtered = df.copy()
    if vehicle_type != "All":
        df_filtered = df_filtered[df_filtered['route_type'] == vehicle_type]

    if df_filtered.empty:
        st.warning("No data available for the selected filter.")
    else:
        st.success(f"{len(df_filtered)} observations have a delay over 60 seconds.")
        fig, ax = plt.subplots()
        ax.hist(df_filtered['delay'], bins=20, edgecolor='black', color='skyblue')
        ax.set_title("Distribution of Delays")
        ax.set_xlabel("Delay (seconds)")
        ax.set_ylabel("Number of observations")
        st.pyplot(fig)

# Tab 2: Delay Statistics
with tab2:
    st.subheader("Delay Statistics")
    st.write("Mean and maximum delay grouped by vehicle type.")

    if not df_filtered.empty:
        stats = df_filtered.groupby('route_type')['delay'].agg(['count', 'mean', 'max']).round(1)
        stats.columns = ['Count', 'Mean Delay', 'Max Delay']
        st.dataframe(stats)
    else:
        st.info("No statistics available for the current selection.")

# Tab 3: Top 10 Delays
with tab3:
    st.subheader("Top 10 Delays")

    if not df_filtered.empty:
        top_delays = df_filtered.nlargest(10, 'delay')
        st.dataframe(top_delays[['vehicle_id', 'route_type', 'delay']])
    else:
        st.info("No data available for top 10 delays.")

# Tab 4: Pie Chart
with tab4:
    st.subheader("Delay Distribution by Vehicle Type")
    st.write("This page shows the distribution of delays by vehicle type in a pie chart.")

    if not df_filtered.empty:
    
        delay_by_type = df_filtered.groupby('route_type')['delay'].sum().sort_values(ascending=False)

        fig, ax = plt.subplots()
        ax.pie(
            delay_by_type,
            labels=delay_by_type.index,
            autopct='%1.1f%%',
            startangle=140
        )
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.info("Not enough data available to display a pie chart.")


with tab5:
    st.subheader("PLACEHOLDER")
    st.info("This feature is not implemented yet.")


#TODO: include otp routing, predctions based on boosting

