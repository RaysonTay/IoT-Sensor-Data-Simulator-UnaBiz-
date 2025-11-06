import streamlit as st
import pandas as pd
import plotly.express as px
import os
from simulator import Simulator


st.set_page_config(page_title="IoT Sensor Dashboard", layout="wide")

# --------------------------
# 1. Sidebar / Controls
# --------------------------
st.sidebar.title("Controls")

# Load available datasets
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)

location = st.sidebar.selectbox(
    "Select environment:",
    ["Toilet", "Restaurant", "Mall", "Classroom"],
    index=0
)

# Required base files
ammonia_file = os.path.join(output_dir, "ammonia.csv")

# Location-specific people counter file
pc_file = os.path.join(output_dir, f"people_counter_{location.lower()}.csv")

# Generate Data
st.sidebar.markdown("Data Generation")
if st.sidebar.button(f"Generate data for {location}"):
    with st.spinner(f"Running simulator for {location}..."):
        from simulator import Simulator  # simulator now in root
        sim = Simulator(duration_minutes=1440)
        sim.run_all(["ammonia", f"people_counter_{location.lower()}"])
    st.sidebar.success(f"Generated simulation data for {location}")
    st.rerun()

# Load Data
if not (os.path.exists(ammonia_file) and os.path.exists(pc_file)):
    st.sidebar.warning(f"No data found for {location}")
    st.stop()

# Load both datasets
df_ammonia = pd.read_csv(ammonia_file)
df_pc = pd.read_csv(pc_file)

# Convert timestamps
df_ammonia["timestamp"] = pd.to_datetime(df_ammonia["timestamp"])
df_pc["timestamp"] = pd.to_datetime(df_pc["timestamp"])

# Merge both datasets
df = pd.concat([df_ammonia, df_pc], ignore_index=True)
df.sort_values("timestamp", inplace=True)

st.sidebar.success(f"Loaded data for {location} environment.")

# Sensor selection (if multiple types exist)
sensor_types = sorted(df["sensor_type"].dropna().unique())
selected_sensors = st.sidebar.multiselect("Select sensors", sensor_types, default=sensor_types)

# Define discrete periods and their hour ranges
period_labels = ["Night", "Morning", "Afternoon", "Evening"]
period_ranges = {
    "Night": (0, 6),
    "Morning": (6, 12),
    "Afternoon": (12, 18),
    "Evening": (18, 24)
}

# Range select with textual labels (no numeric ticks)
start_label, end_label = st.sidebar.select_slider(
    "Select time period(s)",
    options=period_labels,
    value=("Morning", "Morning"),   # default = Morning only
)

# Ensure order + build the list of selected periods
start_idx = period_labels.index(start_label)
end_idx = period_labels.index(end_label)
if start_idx > end_idx:
    start_idx, end_idx = end_idx, start_idx

selected_periods = period_labels[start_idx:end_idx + 1]

hide_slider_numbers_css = """
<style>
div[data-testid="stSliderTickBarMin"],
div[data-testid="stSliderTickBarMax"] {
    display: none;
}
</style>
"""

st.markdown(hide_slider_numbers_css, unsafe_allow_html=True)

# Combine hours from the selected periods
selected_hours = []
for p in selected_periods:
    lo, hi = period_ranges[p]
    selected_hours.extend(range(lo, hi))

# Filter dataframe
if "timestamp" in df.columns:
    df = df[df["timestamp"].dt.hour.isin(selected_hours)]

# Filter by sensor type
df = df[df["sensor_type"].isin(selected_sensors)]

st.sidebar.markdown("---")
show_anomalies = st.sidebar.checkbox("Highlight anomalies (>100 NH3 ppm or >10 occupancy change)", True)

# --------------------------
# 2. Main Layout
# --------------------------
st.title("UnaBiz IoT Sensor Dashboard")
st.markdown(
    "This dashboard visualizes IoT sensor data generated from the Sensor Data Simulator "
    "or real UnaBiz deployments. It supports multiple sensor types and realistic anomaly detection."
)

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "People Counter", "Ammonia", "Network Health"])

# ======================================================
# Overview Tab
# ======================================================
with tab1:
    st.subheader("System Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Readings", f"{len(df):,}")
    col2.metric("Active Sensors", f"{len(sensor_types)}")
    col3.metric("Average RSSI", f"{df['rssi'].mean():.1f} dBm" if 'rssi' in df else "—")
    col4.metric("Average Battery", f"{df['battery'].mean():.1f}%" if 'battery' in df else "—")

    if "nh3" in df.columns and "ammonia" in selected_sensors and not df[df["sensor_type"].str.contains("ammonia")].empty:
        sub = df[df["sensor_type"].str.contains("ammonia")]
        fig_nh3 = px.line(sub, x="timestamp", y="nh3", color="sensor_type",
                        title="Ammonia (NH₃) Levels Over Time")
        if show_anomalies:
            df_spikes = df[df["nh3"] > 100]
            fig_nh3.add_scatter(x=df_spikes["timestamp"], y=df_spikes["nh3"],
                                mode="markers", marker=dict(color="red", size=8), name="Anomalies")
        st.plotly_chart(fig_nh3, use_container_width=True)

    if "current_occupancy" in df.columns and any("people_counter" in s for s in selected_sensors):
        pc_df = df[df["sensor_type"].str.contains("people_counter", na=False)]
        if not pc_df.empty:
            fig_occ = px.line(pc_df, x="timestamp", y="current_occupancy", color="sensor_type",
                              title="Occupancy (People Counter Sensors)")
            st.plotly_chart(fig_occ, use_container_width=True)

# ======================================================
# People Counter Tab
# ======================================================
with tab2:
    st.subheader("People Counter Metrics")
    pc_df = df[df["sensor_type"].str.contains("people_counter", na=False)]

    if not pc_df.empty:
        pc_df["period_in"] = pd.to_numeric(pc_df["period_in"], errors="coerce")
        pc_df["period_out"] = pd.to_numeric(pc_df["period_out"], errors="coerce")
        if "current_occupancy" in pc_df.columns:
            pc_df["current_occupancy"] = pd.to_numeric(pc_df["current_occupancy"], errors="coerce")

        # Calculate metrics safely
        avg_in = pc_df["period_in"].dropna().mean()
        avg_out = pc_df["period_out"].dropna().mean()
        max_occupancy = (
            pc_df["current_occupancy"].max()
            if "current_occupancy" in pc_df.columns else None
        )
        col1, col2, col3 = st.columns(3)
        col1.metric("Average Inflow", f"{avg_in:.1f}")
        col2.metric("Average Outflow", f"{avg_out:.1f}")
        if max_occupancy is not None:
            col3.metric("Max Occupancy", int(max_occupancy))
        else:
            col3.metric("Max Occupancy", "—")

        fig_inout = px.bar(pc_df, x="timestamp", y=["period_in", "period_out"],
                           title="People Flow (In/Out)", barmode="group")
        st.plotly_chart(fig_inout, use_container_width=True)

        fig_occ2 = px.line(pc_df, x="timestamp", y="current_occupancy",
                           title="Occupancy Over Time")
        st.plotly_chart(fig_occ2, use_container_width=True)
    else:
        st.info("No people counter data available in this dataset.")

# ======================================================
# Ammonia Sensor Tab
# ======================================================
with tab3:
    st.subheader("Ammonia Sensor Metrics")
    nh3_df = df[df["sensor_type"].str.contains("ammonia", na=False)]

    if not nh3_df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Average NH₃", f"{nh3_df['nh3'].mean():.2f} ppm")
        col2.metric("Average Temp", f"{nh3_df['temperature'].mean():.1f} °C")
        col3.metric("Average Humidity", f"{nh3_df['humidity'].mean():.1f} %")

        fig_nh3_2 = px.line(nh3_df, x="timestamp", y="nh3", title="NH₃ Concentration Over Time")
        st.plotly_chart(fig_nh3_2, use_container_width=True)

        fig_temp = px.line(nh3_df, x="timestamp", y=["temperature", "humidity"],
                           title="Temperature and Humidity Trends")
        st.plotly_chart(fig_temp, use_container_width=True)
    else:
        st.info("No ammonia sensor data available in this dataset.")

# ======================================================
# Network Health Tab
# ======================================================
with tab4:
    st.subheader("Network & Device Health")

    if "rssi" in df.columns:
        fig_rssi = px.line(df, x="timestamp", y="rssi", color="sensor_type", title="RSSI Signal Strength")
        st.plotly_chart(fig_rssi, use_container_width=True)

    if "snr" in df.columns:
        fig_snr = px.line(df, x="timestamp", y="snr", color="sensor_type", title="SNR Levels")
        st.plotly_chart(fig_snr, use_container_width=True)

    if "battery" in df.columns:
        fig_batt = px.line(df, x="timestamp", y="battery", color="sensor_type", title="Battery Drain Over Time")
        st.plotly_chart(fig_batt, use_container_width=True)

st.markdown("---")
st.caption("© 2025 UnaBiz Internship Project — Sensor Data Simulator Dashboard by Rayson")
