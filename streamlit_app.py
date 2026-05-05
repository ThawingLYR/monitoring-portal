import streamlit as st

from loguru import logger

try:
    from dotenv import load_dotenv

    load_dotenv()
    logger.info("Environment variables loaded from .env file")
except ImportError:
    logger.warning("python-dotenv not installed, skipping .env loading")
    pass


home_page = st.Page("src/app/pages/about.py", title="About", icon=":material/home:")

ground_temperature = st.Page(
    "src/app/pages/main_boreholes_temperature.py",
    title="Ground temperature",
    default=True,
    icon=":material/thermostat:",
)
ground_water_content = st.Page(
    "src/app/pages/borehole_ground_water_content.py",
    title="Ground water content",
    icon=":material/water_drop:",
)
weather_stations = st.Page(
    "src/app/pages/main_weather_stations.py",
    title="Weather stations",
    icon=":material/cloud:",
)
insar_deformation = st.Page(
    "src/app/pages/insar_deformation.py",
    title="InSAR deformation",
    icon=":material/satellite_alt:",
)
all_sky_camera = st.Page(
    "src/app/pages/all_sky_camera.py", title="All-sky camera", icon=":material/360:"
)
time_lapse_cameras = st.Page(
    "src/app/pages/time_lapse_cameras.py",
    title="Time-lapse cameras",
    icon=":material/photo_camera:",
)

ground_ice_content = st.Page(
    "src/app/pages/ground_ice_content.py",
    title="Ground ice content",
    icon=":material/mode_cool:",
)
geomorphology = st.Page(
    "src/app/pages/geomorphology.py", title="Geomorphology", icon=":material/landscape:"
)

landslide_model = st.Page(
    "src/app/pages/landslide_model.py",
    title="Landslide model",
    icon=":material/landslide:",
)
weather_model = st.Page(
    "src/app/pages/weather_model.py",
    title="Weather model (high resolution)",
    icon=":material/rainy:",
)

instrument_status = st.Page(
    "src/app/pages/instrument_status.py",
    title="Boreholes status",
    icon=":material/battery_alert:",
)

pg = st.navigation(
    {
        "": [home_page],
        "Observations": [
            ground_temperature,
            ground_water_content,
            weather_stations,
            insar_deformation,
            all_sky_camera,
            time_lapse_cameras,
        ],
        "Static maps": [ground_ice_content, geomorphology],
        "Modeling": [landslide_model, weather_model],
        "Instrument status": [instrument_status],
    }
)

pg.run()
