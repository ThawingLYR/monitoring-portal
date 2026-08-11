# Imports
import streamlit as st
from streamlit_folium import st_folium

from src.app.reusable.folium_basemap import get_folium_basemap
from src.config.config_manager import ConfigManager
from src.sensors.aws import SensorAWS
from sources_weather_stations_netatmo import metrics


def select_metric(metric: str):
    st.session_state.selected_metric = metric


def metric_button(label: str, metric: str, key: str):
    return st.button(
        label,
        key=key,
        on_click=select_metric,
        args=(metric,),
        type=("primary" if st.session_state.selected_metric == metric else "secondary"),
        use_container_width=True,
    )


# --- Configuration ---
config_manager = ConfigManager()
config_manager.load_config("aws")

# --- Page Setup ---
st.set_page_config(page_title="NETATMO weather stations", layout="wide")
st.title("NETATMO weather stations")

# --- Session State ---
if "selected_metric" not in st.session_state:
    st.session_state.selected_metric = "temp"
if "last_tooltip" not in st.session_state:
    st.session_state.last_tooltip = None

# --- Map Visualization ---
m = get_folium_basemap()
for config in config_manager.get_stations("aws", {"dataProvider": "netatmo"}):
    config.get_marker().add_to(m)


colT, colWS, colWG, colR60, colR24, colH, colp = st.columns(7)

with colT:
    metric_button(
        "Temperature",
        "temp",
        "btn_T",
    )
with colWG:
    metric_button(
        "Wind gust",
        "wind_g",
        "btn_wg",
    )
with colWS:
    metric_button(
        "Wind strength",
        "wind_s",
        "btn_ws",
    )
with colR60:
    metric_button(
        "Rain 60min",
        "rain_60",
        "btn_r60",
    )
with colR24:
    metric_button(
        "Rain 24h",
        "rain_24",
        "btn_r24",
    )
with colH:
    metric_button(
        "Humidity",
        "hum",
        "btn_h",
    )
with colp:
    metric_button(
        "Pressure",
        "p",
        "btn_p",
    )

# setting the right dict
selected_metric_data = metrics[st.session_state.selected_metric]
# text over map
st.markdown(
    f"**{selected_metric_data['infotext']}**",
)

map_col, legend_col = st.columns([9, 1])

with map_col:
    # call to render Folium map in Streamlit
    st_data = st_folium(
        m,
        use_container_width=True,
        height=450,
        returned_objects=["last_object_clicked_popup", "last_object_clicked_tooltip"],
    )  # width=1100


# --- User Interaction ---
if st_data["last_object_clicked_tooltip"] is not None:
    st.markdown(f"You selected **{st_data['last_object_clicked_tooltip']}**")

    # Update sensor if tooltip changes
    if st_data["last_object_clicked_tooltip"] != st.session_state.last_tooltip:
        st.session_state.last_tooltip = st_data["last_object_clicked_tooltip"]

    sensor = SensorAWS(
        config=config_manager.get_stations(
            "aws", query={"name": st_data["last_object_clicked_tooltip"]}
        )[0]
    )
