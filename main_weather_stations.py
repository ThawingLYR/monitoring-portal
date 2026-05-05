# Imports
import folium.raster_layers
import streamlit as st
import folium
from streamlit_folium import st_folium

from sources_weather_stations_MET import (
    marker_met_html,
    marker_met_coordinates,
    marker_met_tooltip,
)
from sources_weather_stations_Tilsig import (
    marker_tilsig_coordinates,
    marker_tilsig_html,
    marker_tilsig_tooltip,
)
# from load_weather_stations_data_Tilsig_and_MET import *
# from plot_weather_stations_data import *


# Functions: put in other script
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False, na_rep="NaN").encode("utf-8-sig")


# Set page configuration
st.set_page_config(page_title="Weather stations", layout="wide")
st.title("Weather stations")

# Create map centered near Longyearbyen
m = folium.Map(
    location=[78.213578, 15.699462], zoom_start=10, tiles=None
)  # , width=300, height=100)

folium.raster_layers.WmsTileLayer(
    url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Basiskart_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    layers="Basisdata_NP_Basiskart_Svalbard_WMTS_3857",
    fmt="image/png",
    transparent=False,
    version="1.0.0",
    attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
    name="Basemap",
    overlay=False,
    control=True,
    show=True,
).add_to(m)

folium.raster_layers.WmsTileLayer(
    url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Satellitt_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    layers="Basisdata_NP_Satellitt_Svalbard_WMTS_3857",
    fmt="image/png",
    transparent=False,
    version="1.0.0",
    attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
    name="Satellite",
    overlay=False,
    control=True,
    show=False,
).add_to(m)

folium.LayerControl().add_to(m)

# Create markers with popup texts and icons

for i in range(len(marker_met_html)):
    icon_ws = folium.Icon(color="blue", icon="cloud")
    html = folium.Html(marker_met_html[i], script=True)
    popup = folium.Popup(html, max_width=500)
    folium.Marker(
        location=marker_met_coordinates[i],
        popup=popup,
        tooltip=marker_met_tooltip[i],
        icon=icon_ws,
    ).add_to(m)

for i in range(len(marker_tilsig_html)):
    icon_ws2 = folium.Icon(color="darkblue", icon="cloud")
    html = folium.Html(marker_tilsig_html[i], script=True)
    popup = folium.Popup(html, max_width=500)
    folium.Marker(
        location=marker_tilsig_coordinates[i],
        popup=popup,
        tooltip=marker_tilsig_tooltip[i],
        icon=icon_ws2,
    ).add_to(m)

# call to render Folium map in Streamlit
st_data = st_folium(
    m,
    use_container_width=True,
    height=450,
    returned_objects=["last_object_clicked_tooltip"],
)
