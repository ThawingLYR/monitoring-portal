# Imports
import streamlit as st
import folium
from folium.plugins import StripePattern
import base64
import geopandas as gpd
from geopandas import geodataframe
from folium.features import GeoJsonPopup
import json
from pathlib import Path
import pandas as pd

from src.app.reusable.folium_basemap import get_folium_basemap


# --- Functions ---
def load_config(path: Path):
    if not path.exists():
        st.error(f"Config file not found: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_data(path: Path, config_gm: json):
    # Read file
    gdf = gpd.read_file(path)

    # Reproject to WGS84 (lon/lat/h)
    gdf = gdf.to_crs("EPSG:4326")

    # Ignore h coordinate and irrelevant columns
    gdf["geometry"] = gdf["geometry"].force_2d()
    gdf = gdf.drop(columns=["DATO", "OPPHAV", "NOTAT", "Shape_Length", "Shape_Area"])

    # Convert conguration to dataframe and match JORDART to add configuration to GeoPandas GeoDataFrame (gdf)
    df_config_gm = pd.DataFrame(config_gm)
    gdf = gdf.merge(
        df_config_gm[
            ["JORDART", "landform_color", "landform_description_en", "striped"]
        ],
        on="JORDART",
        how="left",
    )

    geojson = gdf.to_json()

    return gdf, geojson


def mapping_config(gdf: geodataframe):

    mapping = (
        gdf.drop_duplicates(subset=["JORDART"])
        .set_index("JORDART")[["landform_color", "landform_description_en", "striped"]]
        .to_dict(orient="index")
    )

    return mapping


def create_map(gdf: geodataframe, geojson: json, mapping: dict):

    # Create map centered near Longyearbyen
    m = get_folium_basemap()
    # m = folium.Map(
    #         location=[78.213578, 15.599462], zoom_start=11, tiles="OpenStreetMap", control_scale=True
    #     )

    # m = folium.Map(
    #     location=[78.213578, 15.599462], zoom_start=11, tiles=None, control_scale=True
    # )

    # # Basemap layers for different zoom levels
    # basemap = folium.FeatureGroup(name="Basemap", overlay=False, show=True)

    # folium.raster_layers.WmsTileLayer(
    #     url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Basiskart_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    #     layers="NP_Basiskart_Svalbard_WMTS_3857",
    #     fmt="image/png",
    #     transparent=False,
    #     version="1.0.0",
    #     attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
    #     name="Basemap low zoom",
    #     min_zoom=0,
    #     max_zoom=12,
    #     overlay=False,
    #     control=True,
    #     show=True,
    # ).add_to(basemap)

    # folium.raster_layers.WmsTileLayer(
    #     url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/FKB_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    #     layers="FKB_Svalbard_WMTS_3857",
    #     fmt="image/png",
    #     transparent=False,
    #     version="1.0.0",
    #     attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a> © 2015 <a href=https://www.npolar.no/en/>Norwegian Polar Insitute</a>",
    #     name="Basemap high zoom",
    #     min_zoom=13,
    #     max_zoom=17,
    #     overlay=False,
    #     control=True,
    #     show=True,
    # ).add_to(basemap)

    # basemap.add_to(m)

    # folium.raster_layers.WmsTileLayer(
    #     url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Ortofoto_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    #     layers="NP_Ortofoto_Svalbard_WMTS_3857",
    #     fmt="image/png",
    #     transparent=False,
    #     version="1.0.0",
    #     attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a>",
    #     name="Orthophoto",
    #     min_zoom=0,
    #     max_zoom=17,
    #     overlay=True,
    #     control=True,
    #     show=False,
    # ).add_to(m)

    # folium.raster_layers.WmsTileLayer(
    #     url="https://geodata.npolar.no/arcgis/rest/services/Basisdata/NP_Satellitt_Svalbard_WMTS_3857/MapServer/tile/{z}/{y}/{x}",
    #     layers="Basisdata_NP_Satellitt_Svalbard_WMTS_3857",
    #     fmt="image/png",
    #     transparent=False,
    #     version="1.0.0",
    #     attr="<a href=https://toposvalbard.npolar.no/> TopoSvalbard</a>",
    #     name="Satellite",
    #     min_zoom=0,
    #     max_zoom=17,
    #     overlay=True,
    #     control=True,
    #     show=False,
    # ).add_to(m)

    # Define polygon style
    striped_jordarts = sorted(
        gdf.loc[gdf["striped"] == "yes", "JORDART"].unique().tolist()
    )
    patterns_dict = {}
    for striped_jordart in striped_jordarts:
        landform_color = mapping.get(striped_jordart, {}).get("landform_color", None)
        pattern = StripePattern(
            angle=45,
            weight=4,
            color="#ffffff",
            space_color=landform_color,
            space_weight=4,
            opacity=1.0,
            space_opacity=1.0,
        )
        patterns_dict[striped_jordart] = pattern
        pattern.add_to(m)

    def style_function(feature):

        if feature["properties"]["JORDART"] in striped_jordarts:
            default_style = {
                "fillOpacity": 0.7,
                "fillColor": feature["properties"]["landform_color"],
                "fillPattern": patterns_dict[feature["properties"]["JORDART"]],
                "color": "black",
                "weight": 0.5,
                "opacity": 1.0,
            }

        else:
            default_style = {
                "fillOpacity": 0.7,
                "fillColor": feature["properties"]["landform_color"],
                "color": "black",
                "weight": 0.5,
                "opacity": 1.0,
            }

        return default_style

    def highlight(feature):
        return {"weight": 3, "color": "#666666", "fillOpacity": 0.85}

    # Define popup and tooltip
    popup = GeoJsonPopup(
        fields=["JORDART", "landform_description_en"],
        aliases=["Jordart:", "Description:"],
        localize=True,
        labels=True,
        style=(
            "background-color: white; color: #333333; font-family: arial; font-size: 1.2em"
        ),
    )

    # Map polygons with defined style
    folium.GeoJson(
        geojson,
        name="Geomorphology",
        style_function=style_function,
        highlight_function=highlight,
        popup=popup,
    ).add_to(m)

    # Add layer control: this method ensures that there is no jumping of zoom levels when switching between basemap and ortographic map
    folium.LayerControl().add_to(m)

    return m


def embed_folium_map(m, height=700):
    # Render HTML from folium map in memory
    html = m.get_root().render()

    try:
        st.iframe(srcdoc=html, height=height)
    except TypeError:
        # Fallback: create a base64 data URL and pass it as src
        b64 = base64.b64encode(html.encode("utf-8")).decode("utf-8")
        data_url = f"data:text/html;base64,{b64}"
        st.iframe(data_url, height=height)


def build_legend_html(mapping: dict, cols: int = 3):
    legend_list = []
    for jordart in sorted(mapping):
        color = mapping[jordart]["landform_color"]
        description = mapping[jordart]["landform_description_en"]
        if mapping[jordart]["striped"] == "yes":
            box_style = f"background: repeating-linear-gradient(45deg, {color}, {color} 5px, white 5px, white 10px);"
        else:
            box_style = f"background:{color};"
        legend_list.append(
            f"<li><span class='colorbox' style='{box_style}'></span>"
            f"<span class='text'>{jordart} {description}</span></li>"
        )
    legend_items = "".join(legend_list)

    legend_html = f"""
    <div class='maplegend'>
      <ul class='legend-labels'>
        {legend_items}
      </ul>
    </div>

    <style>
    .maplegend {{
      background-color: rgba(255,255,255,0.95);
      border-radius: 8px;
      padding: 12px;
      font-size: 14px;
      margin-top: 12px;
      max-width: 100%;
      box-shadow: 0 1px 4px rgba(0,0,0,0.12);
    }}
    .maplegend .legend-labels {{
      margin: 0;
      padding: 0;
      column-count: {cols};
      column-gap: 24px;
    }}
    .maplegend .legend-labels li {{
      list-style: none;
      margin: 0 0 8px 0;
      display: inline-block;
      width: 100%;
      break-inside: avoid;
      -webkit-column-break-inside: avoid;
      -moz-column-break-inside: avoid;
    }}
    .maplegend .legend-labels li > span {{
      display: inline-block;
      vertical-align: top;
    }}
    .maplegend .legend-labels li .colorbox {{
      width: 28px;
      height: 16px;
      margin-right: 8px;
      border: 1px solid rgba(0,0,0,0.08);
      box-sizing: border-box;
      display: inline-block;
      vertical-align: top;
    }}
    .maplegend .legend-labels li .text {{
      display: inline-block;
      max-width: calc(100% - 36px);
      vertical-align: top;
      line-height: 1.2;
      word-wrap: break-word;
    }}
    @media (max-width: 1000px) {{
      .maplegend .legend-labels {{ column-count: 2; }}
    }}
    @media (max-width: 600px) {{
      .maplegend .legend-labels {{ column-count: 1; }}
    }}
    </style>
    """

    return legend_html


# --- Configuration ---

# --- Session State ---
if "last_button" not in st.session_state:
    st.session_state.last_button = None
if "last_tooltip" not in st.session_state:
    st.session_state.last_tooltip = None

# --- Page Setup ---
st.set_page_config(page_title="Geomorphology", layout="wide")
st.title("Geomorphology and surface sediments")

# Load geomorphology data and configurations
HERE = Path(__file__).resolve().parent
CONFIG_PATH = Path(HERE / "geomorphology.json")
config_gm = load_config(CONFIG_PATH)

DATA_PATH = Path(HERE / "LyBQuatMap10k_Rubensdotter_2022_EPSG32633.geojson")
gdf_gm, geojson_gm = load_data(DATA_PATH, config_gm)
mapping_gm = mapping_config(gdf_gm)

# Create map
m = create_map(gdf_gm, geojson_gm, mapping_gm)
embed_folium_map(m, height=500)

# Build legend HTML and display it under the map
legend_html = build_legend_html(mapping_gm, cols=3)
st.markdown(legend_html, unsafe_allow_html=True)

# Add context on data
st.header("Background information")
st.markdown(
    """
    This geomorphology and surface sediments dataset was produced by Rubensdotter (2022) and contains mapped
    landforms for the Longyearbyen area. The polygons represent mapped geomorphological and sediment
    units (from field mapping and remote sensing), and the attribute `JORDART` links to the
    legend above.

    Source: Rubensdotter, 2022 — see the project repository or DOI for full metadata.
    """
)
