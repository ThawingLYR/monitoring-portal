import json
from pathlib import Path
from pandas import DataFrame
import py7zr

from src.auth.secrets import get_secret
from src.utils.load_json_file import load_json, load_geojson_into_gdf
from src.utils.load_html import load_html_string

project_root = Path(__file__).resolve().parents[2]
ENCRYPED_PATH = project_root / "map_data_source" / "geomorphology.7z"
OUTPUT_PATH = project_root / "map_data_source"
GEOJSON_PATH = (
    project_root
    / "map_data_source"
    / "geomorphology"
    / "LyBQuatMap10k_Rubensdotter_2022_EPSG32633.geojson"
)
JSON_PATH = project_root / "map_data_source" / "geomorphology" / "geomorphology.json"
GEOJSON_PROCESSED_PATH = (
    project_root
    / "map_data"
    / "geomorphology"
    / "LyBQuatMap10k_Rubensdotter_2022_EPSG32633_Processed.geojson"
)
MAPPING_PROCESSED_PATH = (
    project_root / "map_data" / "geomorphology" / "mapping_dict.json"
)
LEGEND_PROCESSED_PATH = (
    project_root / "map_data" / "geomorphology" / "geomorph_map_legend.html"
)


def get_geomorph_gdf():
    # Get geomoprhology processed data
    gdf = load_geojson_into_gdf(GEOJSON_PROCESSED_PATH)

    return gdf


def get_geomorph_mapping():
    # Get geomorphology mapping dict
    mapping = load_json(MAPPING_PROCESSED_PATH)

    return mapping


def get_geomorph_legend():
    # Get geomorphology map legend
    legend = load_html_string(LEGEND_PROCESSED_PATH)

    return legend


def init_geomorph_geojson():

    # Open encrypted file
    password = get_secret("map_geomorph_key")
    with py7zr.SevenZipFile(ENCRYPED_PATH, mode="r", password=password) as a:
        a.extractall(path=OUTPUT_PATH)

    # Get data from its online source (or for now in map_data_source, for now unzipped and unencrypted)
    gdf = load_geojson_into_gdf(GEOJSON_PATH)

    config = load_json(JSON_PATH)

    ### Processing part
    # Reproject to WGS84 (lon/lat/h)
    gdf = gdf.to_crs("EPSG:4326")

    # Ignore h coordinate and irrelevant columns
    gdf["geometry"] = gdf["geometry"].force_2d()
    gdf = gdf.drop(columns=["DATO", "OPPHAV", "NOTAT", "Shape_Length", "Shape_Area"])

    # Convert conguration to dataframe and match JORDART to add configuration to GeoPandas GeoDataFrame (gdf)
    df_config_gm = DataFrame(config)
    gdf = gdf.merge(
        df_config_gm[
            ["JORDART", "landform_color", "landform_description_en", "striped"]
        ],
        on="JORDART",
        how="left",
    )

    # Create and save mapping dict
    mapping = (
        gdf.drop_duplicates(subset=["JORDART"])
        .set_index("JORDART")[["landform_color", "landform_description_en", "striped"]]
        .to_dict(orient="index")
    )

    with MAPPING_PROCESSED_PATH.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    # Save gdf as geojson
    gdf.to_file(GEOJSON_PROCESSED_PATH)

    # Create legend
    cols = 3
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

    # Save legend to html
    with LEGEND_PROCESSED_PATH.open("w", encoding="utf-8") as f:
        f.write(legend_html)

    return


if __name__ == "__main__":
    init_geomorph_geojson()
