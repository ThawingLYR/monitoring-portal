import streamlit as st

home_page = st.Page("about.py", title="About", icon=":material/home:")

ground_temperature = st.Page(
    "main_boreholes_temperature.py",
    title="Ground temperature",
    default=True,
    icon=":material/thermostat:",
)
ground_water_content = st.Page(
    "borehole_ground_water_content.py",
    title="Ground water content",
    icon=":material/water_drop:",
)
weather_stations = st.Page(
    "main_weather_stations.py", title="Weather stations", icon=":material/cloud:"
)
insar_deformation = st.Page(
    "insar_deformation.py", title="InSAR deformation", icon=":material/satellite_alt:"
)
all_sky_camera = st.Page(
    "all_sky_camera.py", title="All-sky camera", icon=":material/360:"
)
time_lapse_cameras = st.Page(
    "time_lapse_cameras.py", title="Time-lapse cameras", icon=":material/photo_camera:"
)

ground_ice_content = st.Page(
    "ground_ice_content.py", title="Ground ice content", icon=":material/mode_cool:"
)
geomorphology = st.Page(
    "geomorphology.py", title="Geomorphology", icon=":material/landscape:"
)

landslide_model = st.Page(
    "landslide_model.py", title="Landslide model", icon=":material/landslide:"
)
weather_model = st.Page(
    "weather_model.py", title="Weather model (high resolution)", icon=":material/rainy:"
)

instrument_status = st.Page(
    "instrument_status.py", title="Boreholes status", icon=":material/battery_alert:"
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
