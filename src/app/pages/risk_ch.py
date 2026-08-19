import streamlit as st
from streamlit import iframe

from src.map.risk_ch_map import RiskCHMap
from src.init.init_ch_map import get_ch_legend
from src.utils.embed_folium_map import embed_folium_map

# Page Setup
st.set_page_config(page_title="Cultural Heritage", layout="wide")
st.title("Cultural Heritage")

# Create map
m = RiskCHMap().get_map()
embed_folium_map(m, height=500)

# Get html legend and display it under the map
legend_html = get_ch_legend()
iframe(legend_html)

# Add context on data
st.header("Background information")
st.markdown(
    """
    **Risk score**  
    This product uses the “footprint” of each cultural heritage asset/feature on Svalbard, based on the dataset from the Norwegian Directorate for Cultural Heritage. The risk was estimated based on hazard scores (geomorphological, InSAR, coastal erosion) and vulnerability scores. The three hazard scores were summed up, then normalised. The final risk estimate corresponds to the product of the normalised hazard score and the vulnerability score.

    **Hazard score**  
    The hazard score is based on geomorphology, InSAR ground deformation, and coastal erosion.

    *Geomorhology*: A hazard score related to erosional process activity and permafrost-related ground movement potential: 1 to 4.  
    *InSAR ground deformation*: A hazard score based on seasonal and interannual ground dynamics: 1: low ground dynamics, 2: low-medium ground dynamics, 3: medium-high ground dynamics, 4: high ground dynamics.
    *Coastal erosion*: A hazard score based on the distance from the coastline: 1: > 30 m, 2: 20-30 m, 3: 10-20 m, 4: 0-10 m.  
    
    **Vulnerability score**  
    The vulnerability score is based on the cultural heritage object type. The structures were categorised in eight classes: 1) high standing structures (4) 2) low standing structures (3) 3) foundations (1) 4) trases (2) 5) in ground installations (1) 6) loose finds (3) 7) mine dumps (1) 8) graves (4). Each class has a vulnerability score from 1 to 4 assigned (in brackets).

    **Data availablilty, acknowledgements, and citation**  
    The permafrost hazard, vulnerability, and risk maps are results of the PermaRICH project. This research has been funded by the Fram Centre project PermaRICH (Advanced Mapping and Monitoring for Assessing Permafrost Thawing Risks for Modern Infrastructure and Cultural Heritage in Svalbard) (Ministry of Climate and Environment, kap. 1474, post 70).

    For more details on the data please see the corresponding article at https://www.nature.com/articles/s41597-026-07568-7 and the data at https://zenodo.org/records/18154592.

    Nicu, I.C., Rouyet, L., Rubensdotter, L. et al. Permafrost-related hazard, vulnerability and risk estimates for cultural heritage and modern buildings in Svalbard. *Sci Data* (2026). https://doi.org/10.1038/s41597-026-07568-7
    """
)
