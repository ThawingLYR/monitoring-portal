# Imports
import streamlit as st
import folium
from streamlit_folium import st_folium

from src.app.reusable.folium_basemap import get_folium_basemap
from src.config.config_manager import ConfigManager
from src.sensors.borehole import SensorBorehole
from src.plots.boreholes import (
    all_boreholes_figures,
    PlotTimeseriesBoreholes,
    PlotTimeseriesMonthsBoreholes,
    PlotContourDiscreteTemperatureDepthsTimesBoreholes,
)

# Source IDs for boreholes that only have 1 or 2 sensors
restricted_sourceids = {"SN99843", "SN99857", "SN99874"}

# Configuration
config_manager = ConfigManager()
config_manager.load_config("boreholes")

# Page setup
st.set_page_config(page_title="ThawingLYR", layout="wide")
st.title("Ground temperature")

# Session state
if "last_button" not in st.session_state:
    st.session_state.last_button = None
if "last_tooltip" not in st.session_state:
    st.session_state.last_tooltip = None

# Map visualization
m = get_folium_basemap()
folium.LayerControl().add_to(m)
for config in config_manager.get_stations("boreholes"):
    config.get_marker().add_to(m)

st_data = st_folium(
    m,
    use_container_width=True,
    height=450,
    returned_objects=["last_object_clicked_tooltip"],
)

st.markdown(
    """
    <style>
    /* allow button text to wrap and increase padding for readability */
    .stButton>button, .stDownloadButton>button {
        white-space: normal !important;
        height: auto !important;
        padding: 0.6rem 1rem;
    }
    /* optionally increase min-width to avoid very narrow buttons */
    .stButton>button {
        min-width: 160px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# User interaction
if st_data["last_object_clicked_tooltip"] is not None:
    st.markdown(f"You selected **{st_data['last_object_clicked_tooltip']}**")

    # Update sensor if tooltip changes
    if st_data["last_object_clicked_tooltip"] != st.session_state.last_tooltip:
        st.session_state.last_tooltip = st_data["last_object_clicked_tooltip"]

    sensor = SensorBorehole(
        config=config_manager.get_stations(
            "boreholes", query={"name": st_data["last_object_clicked_tooltip"]}
        )[0]
    )

    # Buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        button_h = st.button("Show historic (long-term) data", use_container_width=True)
    with col2:
        button_r = st.button("Show recent (short-term) data", use_container_width=True)
    with col4:
        st.download_button(
            "Press to download data (CSV)",
            sensor.get_csv().encode("utf-8"),
            f"thawinglyr_data_{sensor.config.sourceID}_{sensor.config.name}_{sensor.config.coordinates.latitude:.4f}_{sensor.config.coordinates.longitude:.4f}.csv",
            "text/csv",
            key="download-csv",
        )

    # Data visualization
    # If a button is pressed, update the session state
    if button_h:
        st.session_state.last_button = "historic"
    elif button_r:
        st.session_state.last_button = "recent"

    # All data
    if st.session_state.last_button == "historic":
        col_plot1, col_plot2 = st.columns(2)

        # Less figures when only 1 or 2 sensor depths available
        if sensor.config.sourceID in restricted_sourceids:
            figures_to_show = [
                PlotTimeseriesBoreholes,
                PlotTimeseriesMonthsBoreholes,
            ]
        else:
            figures_to_show = all_boreholes_figures

        for i, fig_cls in enumerate(figures_to_show):
            # Load the figure
            fig_obj = sensor.load_figure(fig_cls)

            # If this is the heatmap class, render full-width outside the columns
            if fig_cls is PlotContourDiscreteTemperatureDepthsTimesBoreholes:
                st.plotly_chart(fig_obj, theme="streamlit", width="stretch")
                continue

            # Otherwise place in one of the two columns
            target_col = col_plot1 if i % 2 == 0 else col_plot2
            with target_col:
                st.plotly_chart(fig_obj, theme="streamlit")

    # Recent data
    elif st.session_state.last_button == "recent":
        with st.spinner("Generating plots..."):
            st.markdown(
                """
                **Under development** This page will show the recent (short-term) data for ground temperature at the borehole locations.
                """
            )
            # col2_1, col2_2 = st.columns(2)
            # with col2_1:
            # with col2_2:

st.markdown(
    """
    ## Background information

    Click on a borehole marker in the map. 3 buttons will appear:
    - Show historic (long-term) data
    - Show recent (short-term) data
    - Press to download data (CSV)

    The plots are interactive. Cover the pointer over the plot for a menubar with options (symbols) to appear: download plot as PNG, zoom, pan, zoom in, zoom out, autoscale, reset axes, and fullscreen. Click on individual legend items to make the corresponding data (dis)appear in the plot.

    The boreholes, equipped with thermistors strings, measure temperature at different depths, usually every 6 hours, and send data real-time.

    Note that for the trumpet curve the profile can be skewed depending on data availability, e.g., data gaps, or start date of measuring is halfway through the first season.
    """
)
