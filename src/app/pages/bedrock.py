import streamlit as st
from streamlit import iframe

from src.map.bedrock_map import BedrockMap
from src.init.init_bedrock_map import get_br_legend
from src.utils.embed_folium_map import embed_folium_map

# Page Setup
st.set_page_config(page_title="Bedrock depth", layout="wide")
st.title("Bedrock depth")

# Create map
m = BedrockMap().get_map()
embed_folium_map(m, height=500)

# Get html legend and display it under the map
legend_html = get_br_legend()
iframe(legend_html)

# Add context on data
st.header("Background information")
st.markdown(
    """
    This map shows the depth to bedrock from boreholes and interpolated for Longyeardalen. 
    
    Depth to bedrock has also been determined in 311 older boreholes all in Longyeardalen. At the outlet of the Longyearelva River, a 70-m-deep borehole was drilled without encountering bedrock. Typically, the existing boreholes have been made for specific project purposes such as establishing avalanche defence structures, a ski slope or for buildings. They are very closely spaced, but in different parts of the Longyearbyen area. A few were collected as part of research infrastructure. In the upper part of Longyeardalen, no older boreholes have been made, except for those presented in this paper. The depth to bedrock has been interpolated using the natural neighbour technique. Outcropping bedrock was used in the interpolation together with the depths from the boreholes, and the 70-m-deep borehole at the river outlet was included even though it did not encounter bedrock to give a minimum value at this location.

    The popups at the observation points show ID: assigned during drilling campaign, Reference: reference to the data set, Inclination: the downward angle of an inclined rock layer, fault, or bedding plane measured relative to a horizontal surface, Slope: inclination of the ground surface, (ratio of vertical change (height) to horizontal distance), Elevation: above mean sea level, Reduced Level (RL) of bedrock: *description coming*.

    Note that more data points are coming for the "Shallow (<5 m) boreholes not reaching bedrock" and "Deep (>5 m) boreholes reaching bedrock".

    For more details on the data please see the corresponding article at https://onlinelibrary.wiley.com/doi/10.1002/ppp.70027, also for the references of the borehole data as in the popups at the observation points.

    K. Tveit and H. Christiansen. Ground Ice Distribution, Cryostratigraphy and Sedimentation in Longyeardalen Valley, Svalbard. *Permafrost and Periglacial Processes*, 37, no. 2 (2026), pp. 185-202, doi: 10.1002/ppp.70027.
    """
)
