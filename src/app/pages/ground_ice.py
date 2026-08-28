import streamlit as st
from streamlit import iframe

from src.map.ground_ice_map import GroundIceMap
from src.init.init_ground_ice_map import get_gi_legend
from src.utils.embed_folium_map import embed_folium_map

# Page Setup
st.set_page_config(page_title="Excess ground ice content", layout="wide")
st.title("Excess ground ice content")

# Create map
m = GroundIceMap().get_map()
embed_folium_map(m, height=500)

# Get html legend and display it under the map
legend_html = get_gi_legend()
iframe(legend_html)

# Add context on data
st.header("Background information")
st.markdown(
    """
    This map shows the excess ground ice content in the top 1 m of the permafrost in Longyeardalen, based on borehole data from 12 locations (white circle markers). The excess ground ice content is then extrapolated based on quaternary geological and geomorphological mapping (blue/purple polygons). 

    Excess ground ice content refers to the amount of ice in permafrost that exceeds the total pore space of the surrounding soil or sediment. This extra water is frozen into distinct ice bodies (i.e., ice wedges, horizontal ice lenses, or layers of pure ice). When the climate warms and permafrost thaws, the solid ice turns into liquid water and drains away, leaving an empty volume that the overlying ground cannot support. This can cause ground collapse, surface subsidence, and the formation of thermokarst landscapes (uneven terrain, water-filled depressions, sinkholes, and landslides) which heavily damages Arctic infrastructure like roads, pipelines, and buildings.

    Till and solifluction material has a medium ground ice content (10-20% EIC) dominating the slopes in the northeast and northwest part of the valley, whereas colluvial material has a low ice content (5-10% EIC) dominating the slopes in the western part. Alluvial deposits have a negligible ice content (0-1% EIC) and only exist in the valley bottom. The highest ground ice content (more than 20% EIC) is mapped in the rock glaciers and moraines in front of the glaciers.

    The developed top permafrost ice map can now be utilised in the work to improve the resilience towards climate change and geohazards in Longyearbyen. 

    Note that the active layer depth in the popups of the borehole locations is from year XXXX.

    For more details on the data please see the corresponding article at https://onlinelibrary.wiley.com/doi/10.1002/ppp.70027.

    K. Tveit and H. Christiansen. Ground Ice Distribution, Cryostratigraphy and Sedimentation in Longyeardalen Valley, Svalbard. *Permafrost and Periglacial Processes*, 37, no. 2 (2026), pp. 185-202, doi: 10.1002/ppp.70027.
    """
)
