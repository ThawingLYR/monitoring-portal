import streamlit as st
from src.config.config_manager import ConfigManager
from src.sensors.aws import SensorAWS

# from datetime import datetime, timedelta, timezone
from src.plots.aws_temp import all_aws_temp_figures


# Configuration
config_manager = ConfigManager()
config_manager.load_config("aws_temp")

# Page setup
st.set_page_config(page_title="ThawingLYR", layout="wide")
st.title("Nedover ski slope weather station")

st.markdown(
    """
    This is a temporary page showing the most recent and last 24 hours observations from the Nedover ski slope weather station.
    
    Note that for now the time is in UTC and not local timezone aware. Standard time: UTC+1 from 25 Oct 2026 to 28 March 2027. Daylight saving time: UTC+2 from 28 March 2027. 
    
    Data updates every 20 minutes.
    """
)

# stations = config_manager.get_stations("aws_temp")
# stations[:] = [
#     s for s in stations
#     if str(getattr(s, "dataProvider", "")).lower() == "tilsig"
# ]
# print(stations)

# Show data
sensor = SensorAWS(
    config=config_manager.get_stations("aws_temp", query={"name": "Nedover"})[0]
)

col1, col2 = st.columns([2, 1])
with col1:
    fig_obj = sensor.load_figure(all_aws_temp_figures[0])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")

    fig_obj = sensor.load_figure(all_aws_temp_figures[1])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")
with col2:
    fig_obj = sensor.load_figure(all_aws_temp_figures[7])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")

    fig_obj = sensor.load_figure(all_aws_temp_figures[8])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")

col1, col2, col3 = st.columns(3)
with col1:
    fig_obj = sensor.load_figure(all_aws_temp_figures[2])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")
with col2:
    fig_obj = sensor.load_figure(all_aws_temp_figures[3])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")
with col3:
    fig_obj = sensor.load_figure(all_aws_temp_figures[9])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")

col1, col2 = st.columns([2, 1])
with col1:
    fig_obj = sensor.load_figure(all_aws_temp_figures[4])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")

    fig_obj = sensor.load_figure(all_aws_temp_figures[5])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")

    fig_obj = sensor.load_figure(all_aws_temp_figures[6])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")
with col2:
    fig_obj = sensor.load_figure(all_aws_temp_figures[10])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")

    fig_obj = sensor.load_figure(all_aws_temp_figures[11])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")

    fig_obj = sensor.load_figure(all_aws_temp_figures[12])
    st.plotly_chart(fig_obj, theme="streamlit", width="stretch")
