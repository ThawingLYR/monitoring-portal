# Imports
import streamlit as st
from src.init.init_insar_map import init_insar
from src.map.insar_map import InSARMap
from src.utils.embed_folium_map import embed_folium_map

init_insar()

# Set page configuration
st.set_page_config(page_title="ThawingLYR", layout="wide")
st.title("InSAR deformation")

# Create map
m = InSARMap().get_map()
embed_folium_map(m, height=500)

st.markdown(
    """
**Under Development** This page will show interactive maps of interannual and seasonal ground deformation measured by InSAR (Interferometric Synthetic Aperture Radar). These maps can then be used to identify areas of larger movement and susceptibility to landsliding. Another signal present in this data is the thaw-subsidence and freeze-heave, which can tell us more about active layer processes and ground ice content. For example, see https://doi.org/10.5194/tc-20-1179-202: Wendt, L., Rouyet, L., Christiansen, et al. InSAR sensitivity to active layer ground ice content in Adventdalen, Svalbard. *The Cryosphere*, 20, pp. 1179-1197 (2026) 20. doi: 10.5194/tc-20-1179-2026.

**InSAR background and limitations**

**Data availablilty, acknowledgements, and citation**  
These data are results of InSAR Svalbard (https://www.ngu.no/geologisk-kartlegging/om-insar-svalbard and https://insar-svalbard.ngu.no/) and the PermaRICH project. InSAR Svalbard is a collaboration between NGU (Geological Survey of Norway) and NORCE Research AS, with financial support from the Norwegian Space Agency. The PermaRICH project (Advanced Mapping and Monitoring for Assessing Permafrost Thawing Risks for Modern Infrastructure and Cultural Heritage in Svalbard) has been funded by the Fram Centre (Ministry of Climate and Environment, kap. 1474, post 70).

"""
)
