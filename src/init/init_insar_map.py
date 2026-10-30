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

# Path to your GeoTIFF
project_root = Path(__file__).resolve().parents[2]
ENCRYPED_PATH = project_root / "map_data_source" / "LYB_InSAR.7z"
OUTPUT_PATH = project_root / "map_data_source" / "insar"
TIF_PATH = (
    project_root
    / "map_data_source"
    / "insar"
    / "LYB_InSAR_Combined_Seasonal-Interannual_Asc-Desc.tif"
)
PNG_PROCESSED_PATH = (
    project_root
    / "map_data"
    / "insar"
    / "LYB_InSAR_Combined_Seasonal-Interannual_Asc-Desc_Processed.png"
)
BOUNDS_PATH = project_root / "map_data" / "insar" / "imagebounds.json"


def get_insar_map():
    # Get
    data_url = load_png_as_data_url(PNG_PROCESSED_PATH)

    return data_url


def get_image_bounds():
    # Get
    image_bounds = load_bounds(BOUNDS_PATH)

    return image_bounds


def init_insar():

    try:
        PNG_PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Path created")
    except Exception as e:
        logger.error(e)

    # Open encrypted file
    password = get_secret("map_insar_key")
    with py7zr.SevenZipFile(ENCRYPED_PATH, mode="r", password=password) as a:
        a.extractall(path=OUTPUT_PATH)

    # Read, transform, and optionally downsample to keep image small
    src_path = TIF_PATH
    dst_crs = "EPSG:3857"

    with rasterio.open(src_path) as src:
        transform3857, width3857, height3857 = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

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

    # Bands and colors
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

    # Save to PNG
    Image.fromarray(rgba, mode="RGBA").save(PNG_PROCESSED_PATH, format="PNG")

    # Save image bounds: [[south, west], [north, east]]
    image_bounds = [[lat_min, lon_min], [lat_max, lon_max]]
    with BOUNDS_PATH.open("w", encoding="utf-8") as f:
        json.dump({"image_bounds": image_bounds}, f, ensure_ascii=False, indent=2)

    return


if __name__ == "__main__":
    init_insar()
