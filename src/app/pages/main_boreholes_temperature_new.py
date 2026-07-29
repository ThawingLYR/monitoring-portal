# Imports
import streamlit as st
from streamlit_folium import st_folium

from src.app.reusable.folium_basemap import get_folium_basemap
from src.config.config_manager import ConfigManager
from src.sensors.borehole import SensorBorehole
from src.plots.boreholes import all_boreholes_figures

# --- Configuration ---
config_manager = ConfigManager()
config_manager.load_config("boreholes")

# --- Page Setup ---
st.set_page_config(page_title="Ground temperature data visualization", layout="wide")
st.title("Ground temperature data visualization")

# --- Session State ---
if "last_button" not in st.session_state:
    st.session_state.last_button = None
if "last_tooltip" not in st.session_state:
    st.session_state.last_tooltip = None

# --- Map Visualization ---
m = get_folium_basemap()
for config in config_manager.get_stations("boreholes"):
    config.get_marker().add_to(m)

st_data = st_folium(
    m,
    use_container_width=True,
    height=450,
    returned_objects=["last_object_clicked_tooltip"],
)

# --- User Interaction ---
if st_data["last_object_clicked_tooltip"] is not None:
    st.markdown(f"You selected **{st_data['last_object_clicked_tooltip']}**")

    # Update sensor if tooltip changes
    if st_data["last_object_clicked_tooltip"] != st.session_state.last_tooltip:
        st.session_state.last_tooltip = st_data["last_object_clicked_tooltip"]

    sensor = SensorBorehole(
        config=config_manager.get_stations(
            "boreholes", query={"name": st_data["last_object_clicked_tooltip"]}
        )[0]
    )

    # --- Buttons ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        button_h = st.button("Show historic (long-term) data", use_container_width=True)
    with col2:
        button_r = st.button("Show recent (short-term) data", use_container_width=True)
    with col4:
        st.download_button(
            "Press to download data (CSV)",
            sensor.get_csv().encode("utf-8"),
            f"thawinglyr_data_{sensor.config.sourceID}_{sensor.config.name}_{sensor.config.coordinates.latitude:.4f}_{sensor.config.coordinates.longitude:.4f}.csv",
            "text/csv",
            key="download-csv",
        )

    # --- Data Visualization ---
    # If a button is pressed, update the session state
    if button_h:
        st.session_state.last_button = "historic"
    elif button_r:
        st.session_state.last_button = "recent"

    # Render plots based on the last button pressed
    if st.session_state.last_button == "historic":
        col_plot1, col_plot2 = st.columns(2)
        for i, fig in enumerate(all_boreholes_figures):
            with col_plot1 if i % 2 == 0 else col_plot2:
                st.plotly_chart(sensor.load_figure(fig), theme="streamlit")

    elif st.session_state.last_button == "recent":
        with st.spinner("Generating plots..."):
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.write("Plots")
            with col2_2:
                st.write("More plots")
