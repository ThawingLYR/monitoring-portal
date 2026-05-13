# Imports
import streamlit as st
from streamlit_folium import st_folium

from src.app.reusable.folium_basemap import get_folium_basemap

from src.config.config_manager import ConfigManager
from src.sensors.borehole import SensorBorehole
from src.plots.boreholes import all_boreholes_figures

config_manager = ConfigManager()
config_manager.load_config("boreholes")

# Set page configuration
st.set_page_config(page_title="Ground temperature data visualization", layout="wide")
st.title("Ground temperature data visualization")

m = get_folium_basemap()

for config in config_manager.get_stations("boreholes"):
    config.get_marker().add_to(m)


# call to render Folium map in Streamlit
st_data = st_folium(
    m,
    use_container_width=True,
    height=450,
    returned_objects=["last_object_clicked_tooltip"],
)  # width=1100

# Visualize data?
# if st_data['last_object_clicked_tooltip'] != None:

st.markdown(f"You selected **{st_data['last_object_clicked_tooltip']}**")
if st_data["last_object_clicked_tooltip"] is not None:
    # if st.button(f"Visualizate data of **{st_data['last_object_clicked_tooltip']}**?",type='primary'):

    sensor = SensorBorehole(
        config=config_manager.get_stations(
            "boreholes", query={"name": st_data["last_object_clicked_tooltip"]}
        )[0]
    )

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

    if button_h:
        with st.spinner("Loading new plots"):
            for fig in all_boreholes_figures:
                st.plotly_chart(sensor.load_figure(fig), theme="streamlit")

    elif button_r:
        with st.spinner("Generating plots..."):
            # Create plots in columns
            col2_1, col2_2 = st.columns(2)

            with col2_1:
                "Plots"

            with col2_2:
                "More plots"
