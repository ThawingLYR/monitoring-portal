import streamlit as st
from streamlit import iframe

from src.map.risk_mb_map import RiskMBMap
from src.init.init_risk_map import get_mb_legend
from src.utils.embed_folium_map import embed_folium_map

# Page Setup
st.set_page_config(page_title="Modern buildings", layout="wide")
st.title("Modern buildings")

# Create map
m = RiskMBMap().get_map()
embed_folium_map(m, height=500)

# Get html legend and display it under the map
legend_html = get_mb_legend()
iframe(legend_html)

# Add context on data
st.header("Background information")
st.markdown(
    """
    **Risk score**  
    This product uses the “footprint” of each modern buildings in Longyearbyen, based on the dataset from the Longyearbyen Community Council (Longyearbyen Lokalstyre). The risk was estimated based on hazard scores (geomorphological, InSAR, coastal erosion) and vulnerability scores. The three hazard scores were summed up, then normalised. The final risk estimate corresponds to the product of the normalised hazard score and the vulnerability score.

    **Hazard score**  
    The hazard score is based on geomorphology, InSAR ground deformation, and coastal erosion.

    *Geomorhology*: A hazard score related to erosional process activity and permafrost-related ground movement potential: 1 to 4.  
    *InSAR ground deformation*: A hazard score based on seasonal and interannual ground dynamics: 1: low ground dynamics, 2: low-medium ground dynamics, 3: medium-high ground dynamics, 4: high ground dynamics.
    *Coastal erosion*: A hazard score based on the distance from the coastline: 1: > 30 m, 2: 20-30 m, 3: 10-20 m, 4: 0-10 m.  
    
    **Vulnerability score**  
    The vulnerability score is based on the building type/usage and the interpretation in term of occupancy and exposure of local population. The buildings were categorised in four classes: 1) buildings little occupied, even during the day (e.g., storage facility, garage); 2) buildings only occupied during the day (e.g., offices, restaurants, shops), or with low occupancy rate during the night (e.g., cabins); 3) buildings occupied day and night (e.g., regular residence, hotels/lodges), or with special cultural/societal value not directly connected to human life (e.g., museum collection); 4) buildings of high community relevance (e.g., hospital, school/kindergarten, facilities used for emergency, evacuation, water and energy management)

    **Data availablilty, acknowledgements, and citation**  
    The permafrost hazard, vulnerability, and risk maps are results of the PermaRICH project. This research has been funded by the Fram Centre project PermaRICH (Advanced Mapping and Monitoring for Assessing Permafrost Thawing Risks for Modern Infrastructure and Cultural Heritage in Svalbard) (Ministry of Climate and Environment, kap. 1474, post 70).

    For more details on the data please see the corresponding article at https://www.nature.com/articles/s41597-026-07568-7 and the data at https://zenodo.org/records/18154592.

    Nicu, I.C., Rouyet, L., Rubensdotter, L. et al. Permafrost-related hazard, vulnerability and risk estimates for cultural heritage and modern buildings in Svalbard. *Sci Data* (2026). https://doi.org/10.1038/s41597-026-07568-7
    """
)
