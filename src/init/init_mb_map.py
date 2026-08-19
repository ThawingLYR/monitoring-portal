from pathlib import Path
from pandas import DataFrame
import py7zr
from loguru import logger

from src.auth.secrets import get_secret
from src.utils.load_json_file import load_json, load_geojson_into_gdf
from src.utils.load_html import load_html_string

project_root = Path(__file__).resolve().parents[2]
ENCRYPED_PATH = project_root / "map_data_source" / "HVR_CH_MB.7z"
OUTPUT_PATH = project_root / "map_data_source" / "risk"
GEOJSON_PATH = project_root / "map_data_source" / "risk" / "MB_LYR.geojson"
JSON_PATH = project_root / "map_data_source" / "risk" / "bygningstypekode.json"
GEOJSON_PROCESSED_PATH = project_root / "map_data" / "risk" / "MB_LYR_Processed.geojson"
LEGEND_PROCESSED_PATH = project_root / "map_data" / "risk" / "mb_map_legend.html"


def get_mb_gdf():
    # Get modern buildings processed data
    gdf = load_geojson_into_gdf(GEOJSON_PROCESSED_PATH)

    return gdf


def get_mb_legend():
    # Get modern buildings map legend
    legend = load_html_string(LEGEND_PROCESSED_PATH)

    return legend


def init_mb_geojson():

    try:
        GEOJSON_PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Path created")
    except Exception as e:
        logger.error(e)

    # Open encrypted file
    password = get_secret("map_risk_key")
    with py7zr.SevenZipFile(ENCRYPED_PATH, mode="r", password=password) as a:
        a.extractall(path=OUTPUT_PATH)

    # Get data from its online source (or for now in map_data_source, for now unzipped and unencrypted)
    gdf = load_geojson_into_gdf(GEOJSON_PATH)
    config = load_json(JSON_PATH)

    # Drop irrelevant columns
    gdf = gdf.drop(columns=["MB_date", "HVR_date"])

    # Convert column type
    gdf["MB_type"] = gdf["MB_type"].astype("int64")

    # Convert conguration to dataframe and match MB_type to add configuration to GeoPandas GeoDataFrame (gdf)
    df_config_risk = DataFrame(config)
    gdf = gdf.merge(
        df_config_risk[["MB_type", "navn"]],
        on="MB_type",
        how="left",
    )

    # Save gdf as geojson
    gdf.to_file(GEOJSON_PROCESSED_PATH)

    # Create legend
    legend_html = """
    <div class='maplegend'>
    <div class='legend-columns'>
        <!-- Risk column (split into two subcolumns) -->
        <div class='legend-col'>
        <div class='legend-title'>Risk score</div>
        <ul class='legend-list split'>
            <li><span class='colorbox' style='background:#FBEC9A;'></span><span class='text'>0</span></li>
            <li><span class='colorbox' style='background:#F4CC68;'></span><span class='text'>1</span></li>
            <li><span class='colorbox' style='background:#ECA855;'></span><span class='text'>2</span></li>
            <li><span class='colorbox' style='background:#E48751;'></span><span class='text'>3</span></li>
            <li><span class='colorbox' style='background:#D2624D;'></span><span class='text'>4</span></li>
            <li><span class='colorbox' style='background:#A54742;'></span><span class='text'>5</span></li>
            <li><span class='colorbox' style='background:#73382F;'></span><span class='text'>6</span></li>
            <li><span class='colorbox' style='background:#422818;'></span><span class='text'>7</span></li>
            <li><span class='colorbox' style='background:#1A1A01;'></span><span class='text'>8</span></li>
        </ul>
        </div>

        <!-- Vulnerability column -->
        <div class='legend-col'>
        <div class='legend-title'>Vulnerability score</div>
        <ul class='legend-list'>
            <li><span class='colorbox' style='background:#FFE599;'></span><span class='text'>0</span></li>
            <li><span class='colorbox' style='background:#C5AE32;'></span><span class='text'>1</span></li>
            <li><span class='colorbox' style='background:#71870B;'></span><span class='text'>2</span></li>
            <li><span class='colorbox' style='background:#3A652A;'></span><span class='text'>3</span></li>
            <li><span class='colorbox' style='background:#00404D;'></span><span class='text'>4</span></li>
        </ul>
        </div>

        <!-- Hazard column -->
        <div class='legend-col'>
        <div class='legend-title'>Hazard score</div>
        <ul class='legend-list'>
            <li><span class='colorbox' style='background:#E6E6F0;'></span><span class='text'>1</span></li>
            <li><span class='colorbox' style='background:#D495B8;'></span><span class='text'>2</span></li>
            <li><span class='colorbox' style='background:#926390;'></span><span class='text'>3</span></li>
            <li><span class='colorbox' style='background:#2E214D;'></span><span class='text'>4</span></li>
        </ul>
        </div>
    </div>
    </div>

    <style>
    .maplegend {
    background-color: rgba(255,255,255,0.95);
    border-radius: 8px;
    padding: 12px;
    font-family: "Source Sans Pro", sans-serif;
    font-size: 14px;
    margin-top: 12px;
    max-width: 100%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12);
    }

    /* Container for the three main columns */
    .maplegend .legend-columns {
    display: flex;
    gap: 20px;
    align-items: flex-start;
    }

    /* Individual column */
    .maplegend .legend-col {
    min-width: 160px;
    flex: 1 1 0;
    }

    /* Column title */
    .maplegend .legend-title {
    font-weight: 700;
    margin-bottom: 8px;
    }

    /* Lists inside each column */
    .maplegend .legend-list {
    margin: 0;
    padding: 0;
    list-style: none;
    }

    /* Special handling for the Risk split column:
    we use CSS columns to create the 2 vertical subcolumns for the list items */
    .maplegend .legend-list.split {
    column-count: 2;       /* split into two subcolumns */
    column-gap: 12px;
    }

    /* Individual legend item */
    .maplegend .legend-list li {
    margin: 0 0 8px 0;
    display: inline-block;
    width: 100%;
    break-inside: avoid;
    -webkit-column-break-inside: avoid;
    -moz-column-break-inside: avoid;
    }

    /* Shared styling for color box and text */
    .maplegend .legend-list li > span {
    display: inline-block;
    vertical-align: top;
    }

    .maplegend .legend-list li .colorbox {
    width: 28px;
    height: 16px;
    margin-right: 8px;
    border: 1px solid rgba(0,0,0,0.08);
    box-sizing: border-box;
    display: inline-block;
    vertical-align: top;
    }

    .maplegend .legend-list li .text {
    display: inline-block;
    max-width: calc(100% - 36px);
    vertical-align: top;
    line-height: 1.2;
    word-wrap: break-word;
    }

    /* Responsive: stack columns on smaller screens */
    @media (max-width: 1000px) {
    .maplegend .legend-columns { flex-direction: row; gap: 12px; }
    .maplegend .legend-col { min-width: 120px; }
    }

    @media (max-width: 700px) {
    .maplegend .legend-columns { flex-direction: column; }
    .maplegend .legend-col { width: 100%; }
    /* For very narrow viewports, make the risk list a single column */
    .maplegend .legend-list.split { column-count: 1; }
    }
    </style>
    """

    # Save legend to html
    with LEGEND_PROCESSED_PATH.open("w", encoding="utf-8") as f:
        f.write(legend_html)

    return


if __name__ == "__main__":
    init_mb_geojson()
