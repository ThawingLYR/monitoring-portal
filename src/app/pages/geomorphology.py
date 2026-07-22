# Imports
import streamlit as st

from src.map.geomorphology_map import GeomorphologyMap
from src.init.init_geomorph_map import get_geomorph_legend
from src.utils.embed_folium_map import embed_folium_map

# --- Page Setup ---
st.set_page_config(page_title="Geomorphology", layout="wide")
st.title("Geomorphology and surface sediments")

# Create map
m = GeomorphologyMap().get_map()
embed_folium_map(m, height=500)

# Get html legend and display it under the map
legend_html = get_geomorph_legend()
st.markdown(legend_html, unsafe_allow_html=True)

# Add context on data
st.header("Background information")
st.markdown(
    """
    This geomorphology and surface sediments dataset was produced by Rubensdotter (2022) and contains mapped
    landforms for the Longyearbyen area. The polygons represent mapped geomorphological and sediment
    units (from field mapping and remote sensing), and the attribute `JORDART` links to the
    legend above.

    Source: Rubensdotter, 2022 — unpublished data as of now (July 2026).
    """
)
