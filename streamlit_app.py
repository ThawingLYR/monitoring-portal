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


home_page = st.Page("src/app/pages/about.py", title="About", icon=":material/home:")

ground_temperature = st.Page(
    "src/app/pages/main_boreholes_temperature.py",
    title="Ground temperature",
    default=True,
    icon=":material/thermostat:",
)
ground_temperature_new = st.Page(
    "src/app/pages/main_boreholes_temperature_new.py",
    title="Ground temperature new",
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
    "src/app/pages/ground_ice.py",
    title="Ground ice content",
    icon=":material/mode_cool:",
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
            ground_temperature_new,
            ground_water_content,
            weather_stations,
            insar_deformation,
            all_sky_camera,
            time_lapse_cameras,
        ],
        "Static maps": [ground_ice_content, geomorphology],
        "Permafrost-related hazard, vulnerability and risk": [
            risk_modern_buildings,
            risk_cultural_heritage,
        ],
        "Modeling": [landslide_model, weather_model],
        "Instrument status": [instrument_status],
    }
)

pg.run()
