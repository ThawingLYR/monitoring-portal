import streamlit as st

# Set page configuration
st.set_page_config(page_title="ThawingLYR", layout="wide")
st.title("Ground temperature: frost tubes")

st.markdown(
    """
    **Under Development** This page will show ground temperature observations from citizens by reading the thaw depth on frost tubes. This method does not provide the detailed temperature profile as a thermistor string, but it does allow for a direct manual reading of the thaw depth at any time, providing the active layer thickness. A frost tube consists of a colored liquid in a clear tube that is placed vertically into the ground inside a protective tube. The ground thaw depth can be read by pulling the frost tube out of the ground and from a distinct colored ice line as the water freezes, representing the distance from the ground surface down to the current thaw depth within the active layer.

    Currently, six frost tubes are installed in Longyearbyen. Observations can be submitted by scanning the QR code next to the frost tube and filling out the online form.

    This page will also present instructions on how to operate the frost tube, to ensure no unwanted material enters the borehole while reading the thaw depth.
    """
)
