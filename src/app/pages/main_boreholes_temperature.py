# Imports
import streamlit as st
from streamlit_folium import st_folium
import folium

from src.app.reusable.folium_basemap import get_folium_basemap

from src.config.config_manager import ConfigManager
from src.sensors.borehole import SensorBorehole
from src.plots.boreholes import all_boreholes_figures

from sources_boreholes_MET import sources_met_boreholes, lookup_by_station_name_met
from sources_boreholes_Tilsig import (
    sources_tilsig_boreholes,
    lookup_by_station_name_tilsig,
)
from src.app.loader.load_boreholes_data_Tilsig_and_MET import (
    load_data_MET,
    load_data_Tilsig,
    MET_data_to_dataframe,
    data_processing_for_plotting,
    Tilsig_data_to_dataframe,
)
from src.app.plots.plot_boreholes_data import (
    plot_tempVStime_shallowest_depth,
    plot_tempVStime_1_shallow_depth,
    plot_annual_trumpet_summer_winter,
    plot_latest_temperatuer_profile_past_same_date,
    plot_iso0_development_all_and_deepest,
    plot_contour_temperature_depths_times,
)


# Functions: put in other script
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False, na_rep="NaN").encode("utf-8-sig")


config_manager = ConfigManager()
config_manager.load_config("boreholes")

# Set page configuration
st.set_page_config(page_title="Ground temperature data visualization", layout="wide")
st.title("Ground temperature data visualization")

m = get_folium_basemap()
# Create markers with popup texts and icons
# icon_ws = folium.Icon(color='blue',icon='cloud')

for i in range(len(sources_met_boreholes)):
    icon_bh = folium.Icon(color="orange", icon="temperature-half", prefix="fa")
    # iframe = folium.IFrame(marker_html[i], width=200, height=110)
    # popup = folium.Popup(iframe)
    marker = f"""<body style="font-family:sans-serif; font-size:0.5em">
    <b>Name</b>: {sources_met_boreholes[i]["name"]}<br>
    <b>Source ID</b>: {sources_met_boreholes[i]["sourceID"]}<br>
    <b>Data</b>: {sources_met_boreholes[i]["type"]}<br>
    <b>Since</b>: {sources_met_boreholes[i]["startDate"]}<br>
    <b>Owner</b>: {sources_met_boreholes[i]["owner"]}
    </body>"""
    html = folium.Html(marker, script=True)
    popup = folium.Popup(html, max_width=500)
    folium.Marker(
        location=sources_met_boreholes[i]["coordinates"],
        popup=popup,
        tooltip=sources_met_boreholes[i]["name"],
        icon=icon_bh,
    ).add_to(m)

for i in range(len(sources_tilsig_boreholes)):
    icon_bh2 = folium.Icon(color="red", icon="temperature-half", prefix="fa")
    # iframe = folium.IFrame(marker_html[i], width=200, height=110)
    # popup = folium.Popup(iframe)
    marker = f"""<body style="font-family:sans-serif; font-size:0.5em">
    <b>Name</b>: {sources_tilsig_boreholes[i]["name"]}<br>
    <b>Sensor ID</b>: {sources_tilsig_boreholes[i]["sensorID"]}<br>
    <b>Data</b>: {sources_tilsig_boreholes[i]["type"]}<br>
    <b>Since</b>: {sources_tilsig_boreholes[i]["startDate"]}<br>
    <b>Owner</b>: {sources_tilsig_boreholes[i]["owner"]}
    </body>"""
    html = folium.Html(marker, script=True)
    popup = folium.Popup(html, max_width=500)
    folium.Marker(
        location=sources_tilsig_boreholes[i]["coordinates"],
        popup=popup,
        tooltip=sources_tilsig_boreholes[i]["name"],
        icon=icon_bh2,
    ).add_to(m)

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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        button_h = st.button("Show historic (long-term) data", use_container_width=True)
    with col2:
        button_r = st.button("Show recent (short-term) data", use_container_width=True)
    with col4:
        if any(
            station["name"] == st_data["last_object_clicked_tooltip"]
            for station in sources_met_boreholes
        ):
            # Load data from source
            source = lookup_by_station_name_met.get(
                st_data["last_object_clicked_tooltip"]
            )
            data = load_data_MET(source)

            # Load into Dataframe and convert to CSV
            data_df_pre = MET_data_to_dataframe(data)
            data_df = data_processing_for_plotting(data_df_pre)

        elif any(
            station["name"] == st_data["last_object_clicked_tooltip"]
            for station in sources_tilsig_boreholes
        ):
            # Load data from source
            source = lookup_by_station_name_tilsig.get(
                st_data["last_object_clicked_tooltip"]
            )
            data = load_data_Tilsig(source)

            # Load into Dataframe and convert to CSV
            data_df_pre = Tilsig_data_to_dataframe(data, source)
            data_df = data_processing_for_plotting(data_df_pre)

        csv = convert_df(data_df)

        st.download_button(
            "Press to download data (CSV)",
            csv,
            "file.csv",  # Give other name
            "text/csv",
            key="download-csv",
        )

    if button_h and any(
        station["name"] == st_data["last_object_clicked_tooltip"]
        for station in sources_met_boreholes
    ):
        with st.spinner("Loading new plots"):
            sensor = SensorBorehole(
                config=config_manager.get_stations(
                    "boreholes", query={"name": st_data["last_object_clicked_tooltip"]}
                )[0]
            )
            for fig in all_boreholes_figures:
                st.plotly_chart(sensor.load_figure(fig), theme="streamlit")

        with st.spinner("Generating plots..."):
            # Create plots in columns
            col1_1, col1_2 = st.columns(2)

            fig1 = plot_tempVStime_shallowest_depth(data_df)
            fig2 = plot_tempVStime_1_shallow_depth(data_df)
            fig3 = plot_annual_trumpet_summer_winter(data_df)
            fig4 = plot_latest_temperatuer_profile_past_same_date(data_df)
            fig5, fig6 = plot_iso0_development_all_and_deepest(data_df)
            fig7, fig8 = plot_contour_temperature_depths_times(data_df)

            with col1_1:
                st.pyplot(fig1)

                st.pyplot(fig3)

                st.pyplot(fig5)

                st.pyplot(fig7)

            with col1_2:
                st.pyplot(fig2)

                st.pyplot(fig4)

                st.pyplot(fig6)

                st.pyplot(fig8)

    elif button_r and any(
        station["name"] == st_data["last_object_clicked_tooltip"]
        for station in sources_met_boreholes
    ):
        with st.spinner("Generating plots..."):
            # Create plots in columns
            col2_1, col2_2 = st.columns(2)

            with col2_1:
                "Plots"

            with col2_2:
                "More plots"

    elif button_h and any(
        station["name"] == st_data["last_object_clicked_tooltip"]
        for station in sources_tilsig_boreholes
    ):
        with st.spinner("Generating plots..."):
            # Create plots in columns
            col2_1, col2_2 = st.columns(2)
            fig1 = plot_tempVStime_shallowest_depth(data_df)
            fig2 = plot_tempVStime_1_shallow_depth(data_df)
            fig3 = plot_annual_trumpet_summer_winter(data_df)
            fig4 = plot_latest_temperatuer_profile_past_same_date(data_df)
            fig5, fig6 = plot_iso0_development_all_and_deepest(data_df)
            fig7, fig8 = plot_contour_temperature_depths_times(data_df)

            with col2_1:
                st.pyplot(fig1)

                st.pyplot(fig3)

                st.pyplot(fig5)

                st.pyplot(fig7)

            with col2_2:
                st.pyplot(fig2)

                st.pyplot(fig4)

                st.pyplot(fig6)

                st.pyplot(fig8)

    elif button_r and any(
        station["name"] == st_data["last_object_clicked_tooltip"]
        for station in sources_tilsig_boreholes
    ):
        with st.spinner("Generating plots..."):
            # Create plots in columns
            col2_1, col2_2 = st.columns(2)

            with col2_1:
                "Plots"

            with col2_2:
                "More plots"
