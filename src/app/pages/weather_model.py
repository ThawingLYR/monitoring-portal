# Imports
import streamlit as st

# Set page configuration
st.set_page_config(page_title="ThawingLYR", layout="wide")
st.title("Weather model (high resolution)")

st.markdown(
    """
    **Under Development** The operational weather model for the high north is the AROME-Arctic model by MET. The geographic resolution is 2.5 kilometres, which is the same as in the model that MET uses to forecast the weather elsewhere in Norway. However, its 2.5 km horizontal grid resolution does not resolve critical fine-scale variations in temperature and precipitation that impact permafrost stability, particularly at the scales of the mountain slopes around Longyearbyen, nor does it capture the steep topography. This project, with MET, works to improve the parameterisation of precipitation, temperature, and wind in a higher resolution (500 m) weather model. With this we can:
    - study the impact of horizontal model resolution is on precipitation forecast accuracy in Svalbard.
    - provide higher resolution data for key weather variables (precipitation, temperature, wind) relevant to permafrost and related landslide phenomena in the Longyeardalen area.
    """
)
