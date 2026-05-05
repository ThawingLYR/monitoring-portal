# Imports
import folium.raster_layers
import streamlit as st
import folium
from streamlit_folium import st_folium

from sources_boreholes_Tilsig import (
    sources_tilsig,
    marker_tilsig_coordinates,
    marker_tilsig_html,
    marker_tilsig_tooltip,
)
from functions_instrument_status import instrument_status_Tilsig

# Set page configuration
st.set_page_config(page_title="Ground temperature data visualization", layout="wide")
st.title("Ground temperature data visualization")

# Load instrument status data
status = instrument_status_Tilsig(sources_tilsig)

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
