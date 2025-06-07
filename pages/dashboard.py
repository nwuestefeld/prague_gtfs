import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from managers.request_manager import RequestManager
from managers.trip_manager import TripManager
from managers.shape_manager import ShapeManager
from shapely import wkt
# Page setup
st.set_page_config(
    page_title="Delay Dashboard",
    page_icon=" :bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Delay Distribution", 
    "Delay Statistics", 
    "Top 10 Delays", 
    "Pie Chart", 
    "Predictions",
    "Export Data"
])

def make_query(start_date, end_date, min_delay, bbox):
    minx, miny, maxx, maxy = bbox
    return f"""
        SELECT 
            gtfs_trip_id, vehicle_id, route_type, gtfs_route_short_name, 
            AVG(delay) AS mean_delay, MIN(timestamp) AS first_timestamp 
        FROM vehicle_positions 
        WHERE delay IS NOT NULL 
          AND longitude BETWEEN {minx} AND {maxx} 
          AND latitude BETWEEN {miny} AND {maxy} 
          AND delay BETWEEN {min_delay} AND 7200
          AND DATE(timestamp) >= DATE('{start_date}')
          AND DATE(timestamp) <= DATE('{end_date}')
        GROUP BY gtfs_trip_id
    """



# Connect to the SQLite database (default)
#conn = sqlite3.connect("vehicle_positions.db")
##query = """SELECT * FROM vehicle_positions WHERE delay IS NOT NULL AND delay > 60"""
#df = pd.read_sql_query(query, conn)
#conn.close()
df = pd.DataFrame()  # Initialize df as an empty DataFrame
df1 = pd.DataFrame()  # Initialize df1 as an empty DataFrame


# Tab 1: Delay Distribution
with tab1:
    st.subheader("Delay Distribution")
    st.write("This page shows the distribution of delays by vehicle type.")

    # Setup filter form
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
            with st.spinner("Load Data from Server..."):
                minx, miny, maxx, maxy = ShapeManager().set_bounding_box()
                st.success(f"Filters applied: Date Range: {start_date} to {end_date}")
                query = make_query(start_date, end_date, min_delay, (minx, miny, maxx, maxy))
                st.write("Executing query:")
                columns = ["gtfs_trip_id", "vehicle_id","route_type", "gtfs_route_short_name", "delay", "first_timestamp"]
                rm = RequestManager()
                df = rm.server_request(query, columns=columns)
                if vehicle_type != "All":
                    df1 = df1[df1['route_type'] == vehicle_type]

                # Speichere df1 in session_state
                st.session_state["df1"] = df1

                # Anzeigen und Plots
                if df is None:
                    st.error("Server request returned None!")
                elif df.empty:
                    st.warning("No data available for the selected filter.")
                else:
                    if not df1.empty:
                        df1 = df.copy()
                        mean_delay_trip = df1.groupby('gtfs_trip_id')['delay'].mean().reset_index()
                        unique_mean_delay = mean_delay_trip['delay'].nunique()
                        st.success(f"{unique_mean_delay} Trips of vehicle type {vehicle_type} have a delay over {min_delay} seconds.")
                        fig, ax = plt.subplots()
                        ax.hist(df1['delay'], bins=20, edgecolor='black', color='skyblue')
                        ax.set_title("Distribution of Delays")
                        ax.set_xlabel("Delay (seconds)")
                        ax.set_ylabel("Number of observations")
                        st.pyplot(fig)
                    else:
                        st.success(f"No delay data of vehicle type {vehicle_type} over {min_delay} seconds.")

            st.subheader("Delay Statistics")
            st.write("Mean and maximum delay grouped by vehicle type.")
            if not df.empty:
                stats = df.groupby('route_type')['delay'].agg(['count', 'mean', 'max']).round(1)
                stats.columns = ['Count', 'Mean Delay', 'Max Delay']
                st.dataframe(stats)
            else:
                st.info("No statistics available for the current selection.")

    # Zweiter Filter-Form-Block (Fahrzeugtypen-Auswahl für Plot)
    # Verwende df1 aus session_state, falls vorhanden
    if "df1" in st.session_state and not st.session_state["df1"].empty:
        df1 = st.session_state["df1"]
        vehicle_types = sorted(df1['route_type'].dropna().unique())

        with st.form("vehicle_type_form"):
            selected_types = st.multiselect(
                "Select vehicle types to include in the plot:",
                options=vehicle_types,
                default=vehicle_types
            )

            # spanning the time range
            ts_min = pd.to_datetime(df1['first_timestamp'].min())
            ts_max = pd.to_datetime(df1['first_timestamp'].max())
            duration = ts_max - ts_min

            # Intervall-options
            interval_options = []
            if duration >= pd.Timedelta(minutes=5):
                interval_options.append("5min")
            if duration >= pd.Timedelta(hours=1):
                interval_options.append("hourly")
            if duration >= pd.Timedelta(days=1):
                interval_options.append("daily")

            selected_interval = st.selectbox("Select aggregation interval", interval_options)
            apply = st.form_submit_button("Apply")

            if apply:
                if selected_types:
                    filtered_df = df1[df1['route_type'].isin(selected_types)].copy()
                    if not filtered_df.empty:
                        filtered_df['first_timestamp'] = pd.to_datetime(filtered_df['first_timestamp'])

                        # intervall switch
                        if selected_interval == "5min":
                            filtered_df['time_bin'] = filtered_df['first_timestamp'].dt.floor("5min")
                        elif selected_interval == "hourly":
                            filtered_df['time_bin'] = filtered_df['first_timestamp'].dt.floor("h")
                        elif selected_interval == "daily":
                            filtered_df['time_bin'] = filtered_df['first_timestamp'].dt.floor("D")

                        # show avg checkbox
                        show_overall_avg = st.checkbox("Show average over all selected vehicle types", value=True)

                        # delay per intervall and vehicle type
                        delay_by_type = (
                            filtered_df.groupby(['time_bin', 'route_type'])['delay'].mean().reset_index()
                        )

                        fig = px.line(
                            delay_by_type,
                            x='time_bin',
                            y='delay',
                            color='route_type',
                            title=f'Average Delay ({selected_interval}) by Vehicle Type',
                            labels={'time_bin': 'Time', 'delay': 'Average Delay (seconds)', 'route_type': 'Vehicle Type'}
                        )

                        # Durchschnitt über alle Vehicle Types optional hinzufügen
                        if show_overall_avg:
                            delay_overall = (
                                filtered_df.groupby('time_bin')['delay'].mean().reset_index()
                            )
                            fig.add_scatter(
                                x=delay_overall['time_bin'],
                                y=delay_overall['delay'],
                                mode='lines',
                                line=dict(color='black', width=3, dash='dash'),
                                name='Overall Average'
                            )

                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No data available for the selected vehicle types.")
                else:
                    st.warning("Please select at least one vehicle type.")



   # if vehicle_type != "All":
   #     df_filtered = df_filtered[df_filtered['route_type'] == vehicle_type]
   # if max_delay > 0:
   #     df_filtered = df_filtered[df_filtered['delay'] <= max_delay]

 

# Tab 2: Delay Statistics
with tab2:
    st.subheader("Delay Statistics")
    st.write("Delayed Lines per  vehicle type.")

    if not df.empty:
        trip_stats = df.groupby(['gtfs_trip_id', 'route_type'])['delay'].agg(['count', 'mean', 'max']).reset_index()
        stats = trip_stats.groupby('route_type')[['count', 'mean', 'max']].agg({
            'count': 'sum',   # sum
            'mean': 'mean',   # avg
            'max': 'max'      # maxs
            }).round(1)

        stats.columns = ['Total Observations', 'Avg of Mean Delays', 'Max of Max Delays']
        st.dataframe(stats)
        st.dataframe(stats)
    else:
        st.info("No statistics available for the current selection.")

# Tab 3: Top 10 Delays
with tab3:
    st.subheader("Placeholder")

    if df.empty:
        st.info("No data available to display top delays.")
    else:
        top_delays = df.groupby('gtfs_trip_id')['delay'].max().reset_index().sort_values(by='delay', ascending=False).head(10)
        top_delay_list = top_delays['gtfs_trip_id'].tolist()
        extra_cols = TripManager().get_infos_by_trip_id(top_delay_list)
        extra_cols = extra_cols.rename(columns={'trip_id': 'gtfs_trip_id'})
        top_delays = top_delays.merge(extra_cols, on='gtfs_trip_id', how='left')
        st.write("Top 10 Delays by Vehicle Type")
        st.dataframe(top_delays)

# Tab 4: Pie Chart
with tab4:
    st.subheader("Delay Distribution by Vehicle Type")
    st.write("This page shows the distribution of delays by vehicle type in a pie chart.")

    if not df.empty:
        count_by_type = df.groupby("route_type")["vehicle_id"].nunique()
        delay_by_type = df.groupby('route_type')['delay'].sum().sort_values(ascending=False)


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
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='filtered_vehicle_positions.csv',
        mime='text/csv'
    )

#TODO: include otp routing (maybe?), predctions based on boosting

