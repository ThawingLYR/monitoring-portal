# Imports
import streamlit as st
from streamlit_folium import st_folium

from src.app.reusable.folium_basemap import get_folium_basemap
from src.config.config_manager import ConfigManager
from src.sensors.aws import SensorAWS

# --- Configuration ---
config_manager = ConfigManager()
config_manager.load_config("aws")

# --- Page Setup ---
st.set_page_config(page_title="NETATMO weather stations", layout="wide")
st.title("NETATMO weather stations")

# --- Session State ---
if "last_tooltip" not in st.session_state:
    st.session_state.last_tooltip = None

# --- Map Visualization ---
m = get_folium_basemap()
for config in config_manager.get_stations("aws", {"dataProvider": "netatmo"}):
    config.marker.color = "darkred"
    config.get_marker().add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(
    m,
    use_container_width=True,
    height=450,
    returned_objects=["last_object_clicked_tooltip"],
)  # width=1100


# --- User Interaction ---
if st_data["last_object_clicked_tooltip"] is not None:
    st.markdown(f"You selected **{st_data['last_object_clicked_tooltip']}**")

    sensor = SensorAWS(
        config=config_manager.get_stations(
            "aws", query={"name": st_data["last_object_clicked_tooltip"]}
        )[0]
    )

    col1, col2, col3, col4 = st.columns(4)
    with col4:
        st.download_button(
            "Press to download data (CSV)",
            sensor.get_csv().encode("utf-8"),
            f"thawinglyr_data_{sensor.config.sourceID}_{sensor.config.name}_{sensor.config.coordinates.latitude:.4f}_{sensor.config.coordinates.longitude:.4f}.csv",
            "text/csv",
            key="download-csv",
        )
