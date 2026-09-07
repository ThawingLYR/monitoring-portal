# Imports
import streamlit as st
from PIL import Image

# Load image
image = Image.open("landslide_example.png")

# Set page configuration
st.set_page_config(page_title="ThawingLYR", layout="wide")
st.title("Landslide model")

st.markdown(
    """
    **Under Development** This page will show the output of a landslide model that identifies areas that are more susceptible to landsliding than others. This is by no means a landslide prediction tool. The model results can be used to aid decision-making on potential area closures. Two methods will be presented here.
    """
)

col2_1, col2_2 = st.columns(2)
with col2_1:
    st.header("Method 1: Complex")
    st.markdown(
        """
        This landslide model is made up from three models: 
        - Thermal model: determining the ground temperature along mountain slopes based on available observations. This model finds the active layer thickness and thereby the amount of unfrozen ground mass. The ground temperature also affects the pore water pressure (next model).
        - Pore water pressure model: determining the pore pressure of the ground based on current (from soil moisture sensors) and forecasted (from weather models) water in the ground, as well as conditions from the thermal model, and ground characteristics from in-situ samples. As pore water pressure increases, the cohesive strength of the ground mass reduces (used in the next model). Water on top of the permafrost can function as lubrication, decreasing the friction between thawed and frozen ground.
        - Geotechnical model: determines the slope failure possiblity, based on output of the two previous models, and utilizing failure criteria.
        This model will run on-demand when the active layer is thawed and the top layer is not frozen, and a certain amount of precipitation is forecasted. See figure on this page to see an example of the landslide model output. The colors represent the probability of sliding.
        """
    )

with col2_2:
    st.header("Method 2: Simple")
    st.markdown(
        """
        This model is based on set thresholds for observed ground temperature, observed ground water content, and forecasted precipitation. This simple model will give an area warning the size of Longyeardalen, and will not be as specific as the landslide model from method 1.

        """
    )
    st.space("medium")
    st.image(image, caption="Example output of complex landslide model (method 1).")
