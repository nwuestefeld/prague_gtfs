import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

#Page setup
st.set_page_config(
    page_title="Delay Dashboard",
    page_icon=" :bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Page title
#st.title("Delay Dashboard")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Delay Distribution", 
    "Delay Statistics", 
    "Top 10 Delays", 
    "Pie Chart", 
    "Predictions",
    "Export Data"
])


# Connect to the SQLite database (default)
conn = sqlite3.connect("vehicle_positions.db")
query = """SELECT * FROM vehicle_positions WHERE delay IS NOT NULL AND delay > 60"""
df = pd.read_sql_query(query, conn)
conn.close()


# Tab 1: Delay Distribution
with tab1:
    st.subheader("Delay Distribution")
    st.write("This page shows the distribution of delays by vehicle type.")



    #setup form for filtering
    st.write("Filter the data by vehicle type and date range.")
    with st.form("filter_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            vehicle_type = st.selectbox(
                "Select vehicle type",
                ["All", "tram", "metro", "train", "bus"]
            )
        with col2:
            start_date = st.date_input("Select Start date")
        with col3:
            end_date = st.date_input("Select End date")
        with col4:
            min_delay = st.number_input("Min delay: default is 60 Sec", min_value=0, max_value=3600, value=60)
        submitted = st.form_submit_button("Apply")

    if submitted:
        if start_date > end_date:
            st.error("Start date must be before end date.")
        else:
            st.success(f"Filters applied: Vehicle Type: {vehicle_type}, Date Range: {start_date} to {end_date}")
            query = "SELECT * FROM vehicle_positions WHERE delay IS NOT NULL"
            if vehicle_type != "All":
                query += f" AND route_type = '{vehicle_type}'"
            if min_delay > 0:
                query += f" AND delay BETWEEN {min_delay} AND 7200"
    #send query to db
    
    conn = sqlite3.connect("vehicle_positions.db")
    query = """SELECT * FROM vehicle_positions WHERE delay IS NOT NULL AND delay > 60"""
    df = pd.read_sql_query(query, conn)
    conn.close()

    df_filtered = df.copy()
   # if vehicle_type != "All":
   #     df_filtered = df_filtered[df_filtered['route_type'] == vehicle_type]
   # if max_delay > 0:
   #     df_filtered = df_filtered[df_filtered['delay'] <= max_delay]

    if df_filtered.empty:
        st.warning("No data available for the selected filter.")
    else:
        st.success(f"{len(df_filtered)} observations of vehicle type {vehicle_type} have a delay over {min_delay} seconds.")
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
        #only get the largest degree for each vehicle (have repeated measures)

        idx = df.groupby('vehicle_id')['delay'].idxmax()
        df_max_delays = df.loc[idx].reset_index(drop=True)
        top_delays = df_max_delays.nlargest(10, 'delay')
        st.dataframe(top_delays[['gtfs_route_short_name','vehicle_id', 'route_type',  'delay', 'timestamp']])
    else:
        st.info("No data available for top 10 delays.")

# Tab 4: Pie Chart
with tab4:
    st.subheader("Delay Distribution by Vehicle Type")
    st.write("This page shows the distribution of delays by vehicle type in a pie chart.")

    if not df_filtered.empty:
        count_by_type = df_filtered.groupby("route_type")["vehicle_id"].nunique()
        delay_by_type = df_filtered.groupby('route_type')['delay'].sum().sort_values(ascending=False)


        pie_df = pd.DataFrame({
            "route_type": delay_by_type.index,
            "total_delay": delay_by_type.values,
            "unique_vehicles": count_by_type.reindex(delay_by_type.index).values
        })

        fig = px.pie(
            pie_df,
            names="route_type",
            values="total_delay",
            title="Total Delay by Vehicle Type",
            hover_data=["unique_vehicles"]
        )
        fig.update_traces(textinfo="percent+label")

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data available to display a pie chart.")


with tab5:
    st.subheader("Predictions")
    st.write("This page will show predictions of delays based on historical data.")
    st.info("This feature is not implemented yet.")

with tab6:
    st.subheader("Export Data")
    st.write("This page allows you to export the filtered data to a CSV file.")
    st.download_button(
        label="Download CSV",
        data=df_filtered.to_csv(index=False).encode('utf-8'),
        file_name='filtered_vehicle_positions.csv',
        mime='text/csv'
    )

#TODO: include otp routing (maybe?), predctions based on boosting

