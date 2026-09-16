from pathlib import Path
import py7zr
from loguru import logger

from src.auth.secrets import get_secret
from src.utils.load_json_file import load_geojson_into_gdf
from src.utils.load_html import load_html_string

project_root = Path(__file__).resolve().parents[2]
ENCRYPED_PATH = project_root / "map_data_source" / "bedrock.7z"
OUTPUT_PATH = project_root / "map_data_source" / "bedrock"

GEOJSON_PATH_POLY = (
    project_root
    / "map_data_source"
    / "bedrock"
    / "interpolated_depth_to_bedrock.geojson"
)
GEOJSON_PROCESSED_PATH_POLY = (
    project_root / "map_data" / "bedrock" / "bedrock_map_Processed.geojson"
)

GEOJSON_PATH_MARK = (
    project_root / "map_data_source" / "bedrock" / "depth_to_bedrock_points.geojson"
)
GEOJSON_PROCESSED_PATH_MARK = (
    project_root / "map_data" / "bedrock" / "bedrock_data_points_Processed.geojson"
)

LEGEND_PROCESSED_PATH = (
    project_root / "map_data" / "bedrock" / "bedrock_map_legend.html"
)


def get_br_poly_gdf():
    # Get ground ice polygons processed data
    gdf = load_geojson_into_gdf(GEOJSON_PROCESSED_PATH_POLY)

    return gdf


def get_br_mark_gdf():
    # Get ground ice markers processed data
    gdf = load_geojson_into_gdf(GEOJSON_PROCESSED_PATH_MARK)

    return gdf


def get_br_legend():
    # Get ground ice map legend
    legend = load_html_string(LEGEND_PROCESSED_PATH)

    return legend


def init_bedrock():

    try:
        GEOJSON_PROCESSED_PATH_POLY.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Path created")
    except Exception as e:
        logger.error(e)

    # Open encrypted file
    password = get_secret("map_bedrock_key")
    with py7zr.SevenZipFile(ENCRYPED_PATH, mode="r", password=password) as a:
        a.extractall(path=OUTPUT_PATH)

    # Get data from its online source (or for now in map_data_source)
    gdf_poly = load_geojson_into_gdf(GEOJSON_PATH_POLY)
    gdf_mark = load_geojson_into_gdf(GEOJSON_PATH_MARK)

    # Add strings to plotting colors
    mapping = {
        1: "0 - 5",
        2: "5 - 10",
        3: "10 - 20",
        4: "20 - 30",
        5: "30 - 40",
        6: "40 - 50",
        7: "50 - 60",
        8: "60 - 70",
    }
    gdf_poly["depth_range"] = gdf_poly["gridcode"].map(mapping)

    # Save gdf as geojson
    gdf_poly.to_file(GEOJSON_PROCESSED_PATH_POLY)
    gdf_mark.to_file(GEOJSON_PROCESSED_PATH_MARK)

    legend_html_br = """
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

    <div id="maplegend" class="maplegend" style="position:absolute; left:10px; top:10px; z-index:10000;">
    <ul class="legend-labels">
        <li><b>Observed depth to bedrock</b></li>
        <li>&ensp;&#9679;&ensp;&thinsp;Depth to bedrock from boreholes</li>
        <li>&ensp;&#43;&ensp;&thinsp;Shallow (&lt;5 m) boreholes not reaching bedrock</li>
        <li>&ensp;&#215;&ensp;&thinsp;Deep (&gt;5 m) boreholes reaching bedrock</li>

        <li style="margin-top:8px;"><b>Interpolated depth to bedrock (m)</b></li>

        <li><span style="background:#829d4c; opacity:0.9; display:inline-block; width:28px; height:16px;"></span> 0 - 5</li>
        <li><span style="background:#a4c16d; opacity:0.9; display:inline-block; width:28px; height:16px;"></span> 5 - 10</li>
        <li><span style="background:#cde6a4; opacity:0.9; display:inline-block; width:28px; height:16px;"></span> 10 - 20</li>
        <li><span style="background:#eaf4b5; opacity:0.9; display:inline-block; width:28px; height:16px;"></span> 20 - 30</li>
        <li><span style="background:#f6ecae; opacity:0.9; display:inline-block; width:28px; height:16px;"></span> 30 - 40</li>
        <li><span style="background:#ecd097; opacity:0.9; display:inline-block; width:28px; height:16px;"></span> 40 - 50</li>
        <li><span style="background:#d3ac6b; opacity:0.9; display:inline-block; width:28px; height:16px;"></span> 50 - 60</li>
        <li><span style="background:#b98c4b; opacity:0.9; display:inline-block; width:28px; height:16px;"></span> 60 - 70</li>
    </ul>
    </div>

    """

    # Save legend to html
    with LEGEND_PROCESSED_PATH.open("w", encoding="utf-8") as f:
        f.write(legend_html_br)

    return


if __name__ == "__main__":
    init_bedrock()
