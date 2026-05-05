# Imports
import folium.raster_layers
import streamlit as st
import folium
from folium import Element
from streamlit_folium import st_folium

from sources_boreholes_MET import sources_met_boreholes, lookup_by_station_name_met
from sources_boreholes_Tilsig import (
    sources_tilsig_boreholes,
    lookup_by_station_name_tilsig,
)
from load_boreholes_data_Tilsig_and_MET import (
    load_data_MET,
    load_data_Tilsig,
    MET_data_to_dataframe,
    data_processing_for_plotting,
    Tilsig_data_to_dataframe,
)
from plot_boreholes_data import plot_1, plot_2, plot_3, plot_4, plot_5_6, plot_7_8


# Functions: put in other script
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False, na_rep="NaN").encode("utf-8-sig")


# Set page configuration
st.set_page_config(page_title="Ground temperature data visualization", layout="wide")
st.title("Ground temperature data visualization")

# Create map centered near Longyearbyen
m = folium.Map(
    location=[78.213578, 15.599462], zoom_start=11, tiles=None, control_scale=True
)  # , width=300, height=100)

# Basemap layers for different zoom levels
basemap = folium.FeatureGroup(name="Basemap", overlay=False)

folium.raster_layers.WmsTileLayer(
    url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Basiskart_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    layers="NP_Basiskart_Svalbard_WMTS_3857",
    fmt="image/png",
    transparent=False,
    version="1.0.0",
    attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
    name="Basemap low zoom",
    min_zoom=0,
    max_zoom=12,
    overlay=True,
    show=True,
).add_to(basemap)

folium.raster_layers.WmsTileLayer(
    url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/FKB_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    layers="FKB_Svalbard_WMTS_3857",
    fmt="image/png",
    transparent=False,
    version="1.0.0",
    attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
    name="Basemap high zoom",
    min_zoom=13,
    max_zoom=17,
    overlay=True,
    show=True,
).add_to(basemap)

basemap.add_to(m)

# Orthographic map as overlay
folium.raster_layers.WmsTileLayer(
    url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Ortofoto_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    layers="NP_Ortofoto_Svalbard_WMTS_3857",
    fmt="image/png",
    transparent=False,
    version="1.0.0",
    attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
    name="Orthophoto",
    min_zoom=0,
    max_zoom=17,
    overlay=True,
    control=True,
    show=False,
).add_to(m)

# Add layer control: this method ensures that there is no jumping of zoom levels when switching between basemap and ortographic map
folium.LayerControl().add_to(m)

js = """
<script>
var basemapLayers = [];
var orthoLayer;

// collect layers
map.eachLayer(function(layer){
    if(layer.options && layer.options.name === "Orthophoto"){
        orthoLayer = layer;
    }
    if(layer.options && layer.options.name === "Basemap low zoom"){
        basemapLayers.push(layer);
    }
    if(layer.options && layer.options.name === "Basemap high zoom"){
        basemapLayers.push(layer);
    }
});

// custom control behavior
map.on('overlayadd', function(e){
    if(e.name === "Orthophoto"){
        basemapLayers.forEach(l => map.removeLayer(l));
    }
    if(e.name === "Basemap Low" || e.name === "Basemap high zoom"){
        map.removeLayer(orthoLayer);
    }
});
</script>
"""

m.get_root().html.add_child(Element(js))

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
        # Create plots in columns
        col1_1, col1_2 = st.columns(2)
        fig1 = plot_1(data_df)
        fig2 = plot_2(data_df)
        fig3 = plot_3(data_df)
        fig4 = plot_4(data_df)
        fig5, fig6 = plot_5_6(data_df)
        fig7, fig8 = plot_7_8(data_df)

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
        # Create plots in columns
        col2_1, col2_2 = st.columns(2)
        fig1 = plot_1(data_df)
        fig2 = plot_2(data_df)
        fig3 = plot_3(data_df)
        fig4 = plot_4(data_df)
        fig5, fig6 = plot_5_6(data_df)
        fig7, fig8 = plot_7_8(data_df)

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
        # Create plots in columns
        col2_1, col2_2 = st.columns(2)

        with col2_1:
            "Plots"

        with col2_2:
            "More plots"
