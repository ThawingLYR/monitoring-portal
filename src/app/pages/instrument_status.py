# Imports
import folium.raster_layers
import streamlit as st
import folium
from streamlit_folium import st_folium

from src.app.reusable.folium_basemap import get_folium_basemap

# from sources_boreholes_Tilsig import
from functions_instrument_status import instrument_status_Tilsig
from sources_weather_stations_Tilsig import (
    sources_tilsig,
    marker_tilsig_coordinates,
    marker_tilsig_html,
    marker_tilsig_tooltip,
)

# Set page configuration
st.set_page_config(page_title="Ground temperature data visualization", layout="wide")
st.title("Ground temperature data visualization")

# Load instrument status data
status = instrument_status_Tilsig(sources_tilsig)

# Create map centered near Longyearbyen
m = get_folium_basemap()

# Create markers with popup texts and icons
for i in range(len(marker_tilsig_html)):
    icon_bh2 = folium.Icon(color="red", icon="temperature-half", prefix="fa")
    html = folium.Html(marker_tilsig_html[i], script=True)
    popup = folium.Popup(html, max_width=500)
    folium.Marker(
        location=marker_tilsig_coordinates[i],
        popup=popup,
        tooltip=marker_tilsig_tooltip[i],
        icon=icon_bh2,
    ).add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(
    m,
    use_container_width=True,
    height=450,
    returned_objects=["last_object_clicked_tooltip"],
)  # width=1100
