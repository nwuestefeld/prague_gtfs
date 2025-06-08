import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from managers.request_manager import RequestManager
from managers.trip_manager import TripManager
from managers.shape_manager import ShapeManager
from shapely import wkt
from datetime import datetime, time

# Page setup
st.set_page_config(
    page_title="Delay Dashboard",
    page_icon=" :bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
**Delay Dashboard Overview**  
This page lets you explore delay patterns in Prague's public transport.

You can:
- **Delay Distribution**: View histogram of delays above a threshold.
- **Delay Statistics**: See count, mean, and max delays by vehicle type.
- **Top 10 Delays**: Identify trips with the highest single delays.
- **Pie Chart**: Understand share of total delay per vehicle type.
- **Predictions**: (coming soon) Forecast delays based on historical data.
- **Export Data**: Download filtered delay data as CSV.
""", unsafe_allow_html=True)

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
    
    #no idea why date filtering is not working. 

    query = (
    "SELECT gtfs_trip_id, vehicle_id, route_type, gtfs_route_short_name, "
    "AVG(delay) AS delay, MIN(timestamp) AS first_timestamp "
    "FROM vehicle_positions "
    "WHERE delay IS NOT NULL "
    "AND route_type <> 2 "
    f"AND longitude BETWEEN {minx} AND {maxx} "
    f"AND latitude BETWEEN {miny} AND {maxy} "
    f"AND delay BETWEEN {min_delay} AND 7200 "
    "GROUP BY gtfs_trip_id"
)
    return query

# Initialize df as empty DataFrame
df = pd.DataFrame()

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
                ["All", "tram", "metro", "bus"]
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
                st.code(query)
                columns = ["gtfs_trip_id", "vehicle_id", "route_type", "gtfs_route_short_name", "delay", "first_timestamp"]
                rm = RequestManager()
                df = rm.server_request(query, columns=columns)
                

                #work around
                df['first_timestamp'] = pd.to_datetime(df['first_timestamp'])
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                start_datetime = datetime.combine(start_date.date(), time.min)
                end_datetime = datetime.combine(end_date.date(), time.max)
                df = df[(df['first_timestamp'] >= start_datetime) & (df['first_timestamp'] <= end_datetime)]

                if df is None:
                    st.error("Server request returned None!")
                elif df.empty:
                    st.warning("No data available for the selected filter.")
                else:
                    # Filter by vehicle type if needed
                    if vehicle_type != "All":
                        df = df[df['route_type'] == vehicle_type]

                    # Save filtered df to session state
                    st.session_state["df"] = df.copy()

                    if not df.empty:
                        mean_delay_trip = df.groupby('gtfs_trip_id')['delay'].mean().reset_index()
                        unique_mean_delay = mean_delay_trip['delay'].nunique()
                        st.success(f"{unique_mean_delay} Trips of vehicle type {vehicle_type} have a delay over {min_delay} seconds.")

                        fig, ax = plt.subplots()
                        ax.hist(df['delay'], bins=20, edgecolor='black', color='skyblue')
                        ax.set_title("Distribution of Delays")
                        ax.set_xlabel("Delay (seconds)")
                        ax.set_ylabel("Number of observations")
                        st.pyplot(fig)
                    else:
                        st.success(f"No delay data of vehicle type {vehicle_type} over {min_delay} seconds.")

            st.subheader("Delay Statistics")
            st.write("Mean and maximum delay grouped by vehicle type.")
            if df is not None and not df.empty:
                stats = df.groupby('route_type')['delay'].agg(['count', 'mean', 'max']).round(1)
                stats.columns = ['Count', 'Mean Delay', 'Max Delay']
                st.dataframe(stats)
            else:
                st.info("No statistics available for the current selection.")

    # Use df from session state for further plots and filters
    if "df" in st.session_state and not st.session_state["df"].empty:
        df_session = st.session_state["df"]
        vehicle_types = sorted(df_session['route_type'].dropna().unique())

        with st.form("vehicle_type_form"):
            selected_types = st.multiselect(
                "Select vehicle types to include in the plot:",
                options=vehicle_types,
                default=vehicle_types
            )

            ts_min = pd.to_datetime(df_session['first_timestamp'].min())
            ts_max = pd.to_datetime(df_session['first_timestamp'].max())
            duration = ts_max - ts_min

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
                    filtered_df = df_session[df_session['route_type'].isin(selected_types)].copy()
                    if not filtered_df.empty:
                        filtered_df['first_timestamp'] = pd.to_datetime(filtered_df['first_timestamp'])

                        if selected_interval == "5min":
                            filtered_df['time_bin'] = filtered_df['first_timestamp'].dt.floor("5min")
                        elif selected_interval == "hourly":
                            filtered_df['time_bin'] = filtered_df['first_timestamp'].dt.floor("h")
                        elif selected_interval == "daily":
                            filtered_df['time_bin'] = filtered_df['first_timestamp'].dt.floor("D")

                        show_overall_avg = st.checkbox("Show average over all selected vehicle types", value=True)

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

# Tab 2: Delay Statistics
with tab2:
    st.subheader("Delay Statistics")
    st.write("Delayed Lines per vehicle type.")

    if "df" in st.session_state and not st.session_state["df"].empty:
        df = st.session_state["df"]
        trip_stats = df.groupby(['gtfs_trip_id', 'route_type'])['delay'].agg(['count', 'mean', 'max']).reset_index()
        stats = trip_stats.groupby('route_type')[['count', 'mean', 'max']].agg({
            'count': 'sum',
            'mean': 'mean',
            'max': 'max'
        }).round(1)

        stats.columns = ['Total Observations', 'Avg of Mean Delays', 'Max of Max Delays']
        st.dataframe(stats)
    else:
        st.info("No statistics available for the current selection.")

# Tab 3: Top 10 Delays
with tab3:
    st.subheader("Top 10 Delays")

    if "df" not in st.session_state or st.session_state["df"].empty:
        st.info("No data available to display top delays.")
    else:
        df = st.session_state["df"]
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

    if "df" in st.session_state and not st.session_state["df"].empty:
        df = st.session_state["df"]
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

# Tab 5: Predictions
with tab5:
    st.subheader("Predictions")
    st.write("This page will show predictions of delays based on historical data.")
    st.info("This feature is not implemented yet.")

# Tab 6: Export Data
with tab6:
    st.subheader("Export Data")
    st.write("This page allows you to export the filtered data to a CSV file.")
    if "df" in st.session_state and not st.session_state["df"].empty:
        st.download_button(
            label="Download CSV",
            data=st.session_state["df"].to_csv(index=False),
            file_name="filtered_delays.csv",
            mime="text/csv"
        )
    else:
        st.info("No data to export.")