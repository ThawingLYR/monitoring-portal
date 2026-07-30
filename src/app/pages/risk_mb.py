import streamlit as st
from streamlit import iframe

from src.map.risk_mb_map import RiskMBMap
from src.init.init_mb_map import get_mb_legend
from src.utils.embed_folium_map import embed_folium_map
from src.init.init_mb_map import init_mb_geojson

# Page Setup
st.set_page_config(page_title="Modern buildings", layout="wide")
st.title("Modern buildings")

# run init
init_mb_geojson()

# Create map
m = RiskMBMap().get_map()
# m.save("map_test.html")
embed_folium_map(m, height=500)

# Get html legend and display it under the map
legend_html = get_mb_legend()
iframe(legend_html)
# st.markdown(legend_html, unsafe_allow_html=True)

# Add context on data
st.header("Background information")
st.markdown(
    """
    PermaRich project information and output
    """
)
