import streamlit as st

from loguru import logger

if "env_loaded" not in st.session_state:
    try:
        from dotenv import load_dotenv
        import os

        if os.path.exists(".env"):
            load_dotenv()
            logger.success("Environment variables loaded from .env file")
        else:
            logger.warning(
                ".env file not found, skipping .env loading and defaulting to system environment variables or streamlit secrets"
            )
    except ImportError:
        logger.info("python-dotenv not installed, skipping .env loading")
        pass

    st.session_state.env_loaded = True


home_page = st.Page(
    "src/app/pages/about.py", default=True, title="About", icon=":material/home:"
)

ground_temperature = st.Page(
    "src/app/pages/main_boreholes_temperature.py",
    title="Ground temperature",
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
    title="InSAR ground deformation",
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
    "src/app/pages/ground_ice.py",
    title="Ground ice content",
    icon=":material/mode_cool:",
)
bedrock = st.Page(
    "src/app/pages/bedrock.py", title="Bedrock depth", icon=":material/elevation:"
)
geomorphology = st.Page(
    "src/app/pages/geomorphology.py", title="Geomorphology", icon=":material/landscape:"
)


risk_modern_buildings = st.Page(
    "src/app/pages/risk_mb.py", title="Modern buildings", icon=":material/house:"
)

risk_cultural_heritage = st.Page(
    "src/app/pages/risk_ch.py", title="Cultural Heritage", icon=":material/cabin:"
)

landslide_model = st.Page(
    "src/app/pages/landslide_model.py",
    title="Landslide model",
    icon=":material/landslide:",
)
weather_model = st.Page(
    "src/app/pages/weather_model.py",
    title="Weather model",
    icon=":material/rainy:",
)

instrument_status = st.Page(
    "src/app/pages/instrument_status.py",
    title="Instrument status",
    icon=":material/battery_alert:",
)

pg = st.navigation(
    {
        "": [home_page],
        "Live observations": [
            ground_temperature,
            ground_water_content,
            weather_stations,
            # all_sky_camera,
            time_lapse_cameras,
        ],
        "Static maps": [ground_ice_content, bedrock, geomorphology, insar_deformation],
        "Permafrost-related hazard, vulnerability and risk": [
            risk_modern_buildings,
            risk_cultural_heritage,
        ],
        "Modeling": [landslide_model, weather_model],
        "Instrument status": [instrument_status],
    }
)

pg.run()
