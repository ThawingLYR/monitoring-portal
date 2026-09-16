from pathlib import Path
import py7zr
from loguru import logger

from src.auth.secrets import get_secret
from src.utils.load_json_file import load_geojson_into_gdf
from src.utils.load_html import load_html_string

project_root = Path(__file__).resolve().parents[2]
ENCRYPED_PATH = project_root / "map_data_source" / "groundice.7z"
OUTPUT_PATH = project_root / "map_data_source" / "ground_ice"

GEOJSON_PATH_POLY = (
    project_root / "map_data_source" / "ground_ice" / "excess_ice_map.geojson"
)
GEOJSON_PROCESSED_PATH_POLY = (
    project_root / "map_data" / "ground_ice" / "excess_ice_map_Processed.geojson"
)

GEOJSON_PATH_MARK = (
    project_root / "map_data_source" / "ground_ice" / "excess_ice_data_points.geojson"
)
GEOJSON_PROCESSED_PATH_MARK = (
    project_root
    / "map_data"
    / "ground_ice"
    / "excess_ice_data_points_Processed.geojson"
)

LEGEND_PROCESSED_PATH = (
    project_root / "map_data" / "ground_ice" / "ground_ice_map_legend.html"
)


def get_gi_poly_gdf():
    # Get ground ice polygons processed data
    gdf = load_geojson_into_gdf(GEOJSON_PROCESSED_PATH_POLY)

    return gdf


def get_gi_mark_gdf():
    # Get ground ice markers processed data
    gdf = load_geojson_into_gdf(GEOJSON_PROCESSED_PATH_MARK)

    return gdf


def get_gi_legend():
    # Get ground ice map legend
    legend = load_html_string(LEGEND_PROCESSED_PATH)

    return legend


def init_ground_ice():

    try:
        GEOJSON_PROCESSED_PATH_POLY.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Path created")
    except Exception as e:
        logger.error(e)

    # Open encrypted file
    password = get_secret("map_ground_ice_key")
    with py7zr.SevenZipFile(ENCRYPED_PATH, mode="r", password=password) as a:
        a.extractall(path=OUTPUT_PATH)

    # Get data from its online source (or for now in map_data_source)
    gdf_poly = load_geojson_into_gdf(GEOJSON_PATH_POLY)
    gdf_mark = load_geojson_into_gdf(GEOJSON_PATH_MARK)

    # Add num value to plotting colors
    mapping = {
        "No data": 0,
        "Negligible (0 - 5)": 1,
        "Low (5 - 10)": 2,
        "Medium (10 - 20)": 3,
        "High (>20)": 4,
    }
    gdf_poly["Ground_Ice_Num"] = gdf_poly["Ground_Ice"].map(mapping)

    # Save gdf as geojson
    gdf_poly.to_file(GEOJSON_PROCESSED_PATH_POLY)
    gdf_mark.to_file(GEOJSON_PROCESSED_PATH_MARK)

    legend_html_gi = """
    <style>
    .maplegend {
    background-color: rgba(255,255,255,0.95);
    border-radius: 6px;
    padding: 10px;
    font-family: "Source Sans Pro", sans-serif;
    font-size: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12);
    max-width: 420px;
    min-width: 320px;
    overflow: visible;
    }

    /* Single-column list */
    .maplegend .legend-labels {
    margin: 0;
    padding: 0;
    list-style: none;
    }

    /* Each row: swatch space + text */
    .maplegend .legend-labels li {
    display: flex;
    align-items: center;
    gap: 8px;               /* space between swatch area and text */
    margin: 6px 0;
    width: 100%;
    box-sizing: border-box;
    }

    /* Title */
    .maplegend .legend-labels > b {
    display: block;
    width: 100%;
    margin-bottom: 6px;
    font-weight: 700;
    }

    /* Standard swatch area (rectangular color swatches) */
    .maplegend .legend-labels li span[style] {
    display: inline-block;
    width: 28px;            /* fixed swatch container width */
    height: 16px;
    border-radius: 2px;
    border: 1px solid rgba(0,0,0,0.08);
    box-sizing: border-box;
    flex: 0 0 28px;        /* reserve same space for each row */
    vertical-align: middle;
    }

    /* Explicit swatch element for avg row (same reserved space) */
    .maplegend .legend-labels .swatch {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 16px;
    flex: 0 0 28px;
    box-sizing: border-box;
    }

    /* Draw the small white circle with black stroke centered inside the swatch */
    .maplegend .legend-labels .avg-swatch::after {
    content: "";
    display: block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #fff;       /* white fill */
    border: 1px solid #000; /* black stroke */
    box-sizing: border-box;
    }

    /* Label text: aligned after the 28px swatch-space (same for avg and colors) */
    .maplegend .legend-labels li .text {
    color: #222;
    font-size: 13.5px;
    word-wrap: break-word;
    flex: 1 1 auto;
    }

    /* For the avg row prefer single line on wider displays, but allow wrap on small screens */
    .maplegend .legend-labels li.avg .text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    }

    /* Responsive tweak */
    @media (max-width: 500px) {
    .maplegend { max-width: 95vw; min-width: auto; font-size: 13px; }
    .maplegend .legend-labels li span[style] { width: 24px; height: 12px; flex: 0 0 24px; }
    .maplegend .legend-labels .swatch { width: 24px; height: 12px; flex: 0 0 24px; }
    .maplegend .legend-labels li.avg .text { white-space: normal; } /* allow wrap on narrow screens */
    }
    </style>

    <div id='maplegend' class='maplegend'
        style='position: absolute; z-index: 100000; background-color: rgba(255, 255, 255, 0.8);
                border-radius: 6px; padding: 10px; left: 10px; top: 10px;'>
    <div class='legend-scale'>
        <ul class='legend-labels'>
        <b>Excess Ice Content (EIC) in top 1 m permafrost</b>

        <!-- Average row: explicit swatch (avg-swatch) then text -->
        <li class='avg'>
            <span class='swatch avg-swatch'></span>
            <span class='text'>Average EIC in top 1 m permafrost from boreholes (%)</span>
        </li>

        <!-- Category rows: color span + text span -->
        <li>
            <span style='background: #293467; opacity: 0.7;'></span>
            <span class='text'>High (&gt;20%)</span>
        </li>
        <li>
            <span style='background: #3669AD; opacity: 0.7;'></span>
            <span class='text'>Medium (10 - 20%)</span>
        </li>
        <li>
            <span style='background: #989BE7; opacity: 0.7;'></span>
            <span class='text'>Low (5 - 10%)</span>
        </li>
        <li>
            <span style='background: #D0CCF5; opacity: 0.7;'></span>
            <span class='text'>Negligible (0 - 5%)</span>
        </li>
        <li>
            <span style='background: #808080; opacity: 0.7;'></span>
            <span class='text'>No data</span>
        </li>
        </ul>
    </div>
    </div>
    """

    # Save legend to html
    with LEGEND_PROCESSED_PATH.open("w", encoding="utf-8") as f:
        f.write(legend_html_gi)

    return


if __name__ == "__main__":
    init_ground_ice()
