# Imports
import streamlit as st


# Set page configuration
st.set_page_config(page_title="ThawingLYR", layout="wide")
st.title("About")

st.markdown(
    """

    ## Project information

    This portal is developed under the ThawingLYR project.

    **Project objective** The main objective of the ThawingLYR project is to develop the required knowledge base for sustainable management of critical infrastructure, cultural heritage and mountain slopes in the permafrost-based Arctic settlement of Longyearbyen.

    As the Arctic climate warms, thawing permafrost threatens infrastructure, cultural heritage, and mountain slopes. Managing these risks is vital for the safety and sustainability of Arctic communities. ThawingLYR addresses these pressing issues and brings together experts from geoscience, engineering, social sciences, and data science, working closely with local authorities, businesses, and residents. By combining mapping, monitoring, modelling, and local knowledge, we are building an integrated climate and permafrost response system. This online platform will deliver real-time data on permafrost, terrain movement, and weather, as well as tools to predict and manage landslides and other permafrost-related hazards. Ultimately, we will provide practical strategies that strengthen resilience and safeguard Longyearbyen—and other Arctic settlements—for the future.

    **Project funding** ThawingLYR (Thawing Arctic permafrost, emerging risks: managing critical infrastructure, cultural heritage, and mountain slopes under climate change) is a 3-year (2025-2027) research project funded by the Research Council of Norway.

    **Project partners** ThawingLYR is led by the University Centre in Svalbard. Project partners include Nordland Research Institute, Nord University, Norwegian University of Life Sciences, MET Norway, NORSAR, Longyearbyen Lokalstyre, Svalbard Museum, Instanes AS and Tilsig AS.

    ## Platform information

    **Navigation** Use the menubar on the left to navigate between pages. 
    
    **Data** At the bottom of each page you can learn about the data and how to use it. For the live observations, data is recorded every few hours, but data to the portal is fetched once every 24 hours, apart from the instrumentation status page to have the status in real-time.

    **Map layers** For each page that displays a map, you can switch between background maps, and depending on the page also between data layers, by using the map layer button in the top-right corner of the map.

    **Open source** The code behind this portal is open source and can be found on https://github.com/ThawingLYR/monitoring-portal/. Please take note of the license.


    **Scientific colormaps** For the creation of many of the maps and plots we use Scientific Colour Maps by Crameri. See the website https://www.fabiocrameri.ch/colourmaps/ to find the colormaps on Zenodo and the accompanying research articles. These colour maps fairly represent data "The colour gradients are perceptually uniform and ordered to represent data both fairly - without visual distortion - and intuitively" and are universally readable "The colour combinations are readable both by colour-vision deficient and colour-blind people, and even when printed in black & white".

    **Development** Note that the platform is under active development. Any feedback can be submitted to the main developer Maaike Weerdesteijn (maaikew@unis.no). Credits to Louis Pauchet for developing the back-end and to Patrick Selle for developing the private weather stations page.

    """
)
