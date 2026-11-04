from pathlib import Path
import py7zr
from loguru import logger
import rasterio
import numpy as np
import json
from rasterio.warp import (
    calculate_default_transform,
    reproject,
    Resampling,
    transform_bounds,
)
from rasterio.transform import array_bounds
from PIL import Image

from src.auth.secrets import get_secret
from src.utils.load_png_file import load_png_as_data_url
from src.utils.load_image_bounds import load_bounds
from src.utils.load_html import load_html_string

# Path to your GeoTIFF
project_root = Path(__file__).resolve().parents[2]
ENCRYPED_PATH = project_root / "map_data_source" / "LYB_InSAR.7z"
OUTPUT_PATH = project_root / "map_data_source" / "insar"
LEGEND_PROCESSED_PATH = project_root / "map_data" / "insar" / "insar_map_legend.html"

# Datasets: TIF source, processed PNG target, bounds JSON target
DATASETS = [
    {
        "tif": project_root
        / "map_data_source"
        / "insar"
        / "LYB_InSAR_Seasonal_Combined_Asc-Desc.tif",
        "png": project_root
        / "map_data"
        / "insar"
        / "LYB_InSAR_Seasonal_Combined_Asc-Desc_Processed.png",
        "bounds": project_root
        / "map_data"
        / "insar"
        / "imagebounds_LYB_InSAR_Seasonal_Combined_Asc-Desc.json",
    },
    {
        "tif": project_root
        / "map_data_source"
        / "insar"
        / "LYB_InSAR_Interannual_Combined_Asc-Desc.tif",
        "png": project_root
        / "map_data"
        / "insar"
        / "LYB_InSAR_Interannual_Combined_Asc-Desc_Processed.png",
        "bounds": project_root
        / "map_data"
        / "insar"
        / "imagebounds_LYB_InSAR_Interannual_Combined_Asc-Desc.json",
    },
    {
        "tif": project_root
        / "map_data_source"
        / "insar"
        / "LYB_InSAR_Combined_Seasonal-Interannual_Asc-Desc.tif",
        "png": project_root
        / "map_data"
        / "insar"
        / "LYB_InSAR_Combined_Seasonal-Interannual_Asc-Desc_Processed.png",
        "bounds": project_root
        / "map_data"
        / "insar"
        / "imagebounds_LYB_InSAR_Combined_Seasonal-Interannual_Asc-Desc.json",
    },
]


def process_tif_to_png_bounds(
    src_path: Path, png_path: Path, bounds_path: Path, dst_crs: str = "EPSG:3857"
):
    """
    Reproject the first band of src_path to dst_crs, colorize using your mapping,
    save PNG to png_path and bounds (in EPSG:4326) to bounds_path.
    """
    png_path.parent.mkdir(parents=True, exist_ok=True)
    bounds_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(src_path) as src:
        transform3857, width3857, height3857 = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        # NOTE: this creates an array of size (bands, height, width). If very large, consider resampling/downsampling here.
        profile = src.profile.copy()
        profile.update(
            {
                "crs": dst_crs,
                "transform": transform3857,
                "width": width3857,
                "height": height3857,
            }
        )

        dst = np.zeros((src.count, height3857, width3857), dtype=src.dtypes[0])
        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=dst[i - 1],
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform3857,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear,
            )

    # Compute bbox in EPSG:3857 (left, bottom, right, top)
    minx, miny, maxx, maxy = array_bounds(height3857, width3857, transform3857)

    # Transform bbox to EPSG:4326 (lon_min, lat_min, lon_max, lat_max)
    lon_min, lat_min, lon_max, lat_max = transform_bounds(
        dst_crs, "EPSG:4326", minx, miny, maxx, maxy, densify_pts=21
    )

    # Colorize: uses first band (adjust logic if needed)
    band = dst[0]
    h, w = band.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    color_map = {
        1: (248, 223, 124, 200),
        2: (231, 148, 82, 200),
        3: (199, 80, 75, 200),
        4: (91, 48, 35, 200),
    }
    for v, col in color_map.items():
        rgba[band == v] = col

    Image.fromarray(rgba, mode="RGBA").save(png_path, format="PNG")

    image_bounds = [[lat_min, lon_min], [lat_max, lon_max]]
    with bounds_path.open("w", encoding="utf-8") as f:
        json.dump({"image_bounds": image_bounds}, f, ensure_ascii=False, indent=2)


def create_legend_insar():
    legend_html = """
    <div class='maplegend'>
        <div class='maplegend-title'>Ground movement from InSAR (hazard score in brackets)</div>
        
    <div class='legend-columns'>
        <div class='legend-col'>
        <div class='legend-title'>Seasonal</div>
        <ul class='legend-list'>
            <li><span class='colorbox' style='background:#F8DF7C;'></span><span class='text'>(1) 0-1 cm/summer</span></li>
            <li><span class='colorbox' style='background:#E79452;'></span><span class='text'>(2) 1-2 cm/summer</span></li>
            <li><span class='colorbox' style='background:#C7504B;'></span><span class='text'>(3) 2-3 cm/summer</span></li>
            <li><span class='colorbox' style='background:#5B3023;'></span><span class='text'>(4) ≥3 cm/summer</span></li>
        </ul>
        </div>

        <div class='legend-col'>
        <div class='legend-title'>Interannual</div>
        <ul class='legend-list'>
            <li><span class='colorbox' style='background:#F8DF7C;'></span><span class='text'>(1) 0-4 mm/yr</span></li>
            <li><span class='colorbox' style='background:#E79452;'></span><span class='text'>(2) 4-8 mm/yr</span></li>
            <li><span class='colorbox' style='background:#C7504B;'></span><span class='text'>(3) 8-12 mm/yr</span></li>
            <li><span class='colorbox' style='background:#5B3023;'></span><span class='text'>(4) ≥12 mm/yr</span></li>
        </ul>
        </div>

        <div class='legend-col'>
        <div class='legend-title'>Combined: seasonal and interannual</div>
        <ul class='legend-list'>
            <li><span class='colorbox' style='background:#F8DF7C;'></span><span class='text'>(1) Low ground dynamics</span></li>
            <li><span class='colorbox' style='background:#E79452;'></span><span class='text'>(2) Low-medium ground dynamics</span></li>
            <li><span class='colorbox' style='background:#C7504B;'></span><span class='text'>(3) Medium-high ground dynamics</span></li>
            <li><span class='colorbox' style='background:#5B3023;'></span><span class='text'>(4) High ground dynamics</span></li>
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

    /* Title for the legend: larger and more space below */
    .maplegend .maplegend-title {
      font-weight: normal;
      font-size: 16px;
      line-height: 1.2;
      margin: 0 0 16px 0;
      color: #222;
      padding-bottom: 0px;
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


def init_insar():
    # Ensure output dirs exist
    for ds in DATASETS:
        ds["png"].parent.mkdir(parents=True, exist_ok=True)
        ds["bounds"].parent.mkdir(parents=True, exist_ok=True)

    # Extract encrypted archive once
    try:
        password = get_secret("map_insar_key")
        with py7zr.SevenZipFile(ENCRYPED_PATH, mode="r", password=password) as a:
            a.extractall(path=OUTPUT_PATH)
        logger.debug("Archive extracted to %s", OUTPUT_PATH)
    except Exception as e:
        logger.error("Failed to extract archive: %s", e)
        raise

    # Process each dataset
    for ds in DATASETS:
        try:
            logger.info("Processing %s", ds["tif"])
            process_tif_to_png_bounds(ds["tif"], ds["png"], ds["bounds"])
        except Exception as e:
            logger.exception("Failed to process %s: %s", ds["tif"], e)

    # Create legend
    create_legend_insar()

    return


# Helper getters
def get_insar_map_Seasonal_Combined():
    return load_png_as_data_url(DATASETS[0]["png"])


def get_image_bounds_Seasonal_Combined():
    return load_bounds(DATASETS[0]["bounds"])


def get_insar_map_Interannual_Combined():
    return load_png_as_data_url(DATASETS[1]["png"])


def get_image_bounds_Interannual_Combined():
    return load_bounds(DATASETS[1]["bounds"])


def get_insar_map_Combined_Seasonal_Interannual():
    return load_png_as_data_url(DATASETS[2]["png"])


def get_image_bounds_Combined_Seasonal_Interannual():
    return load_bounds(DATASETS[2]["bounds"])


def get_insar_legend():
    return load_html_string(LEGEND_PROCESSED_PATH)


if __name__ == "__main__":
    init_insar()
