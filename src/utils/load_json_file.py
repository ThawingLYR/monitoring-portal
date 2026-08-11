import json
from pathlib import Path
from loguru import logger
import geopandas as gpd


def load_json(path: Path):
    """Load and parse a JSON file from the given path.

    If the file does not exist this logs an error and returns an empty dict.
    If the file exists but contains invalid JSON, the JSONDecodeError is
    propagated.

    Args:
        path: Path to the JSON file.

    Returns:
        A dict containing the parsed JSON data, or an empty dict if the file
        does not exist.

    Raises:
        json.JSONDecodeError: If the file exists but contains invalid JSON.
    """
    if not path.exists():
        logger.error(
            "json file not found in {path}",
        )
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_geojson_into_gdf(path: Path):
    """Load a GeoJSON file into a GeoDataFrame.

    If the file does not exist this logs an error and returns an empty
    GeoDataFrame. If the file exists but is unreadable or not valid GeoJSON,
    the underlying exception from geopandas/fiona will be propagated.

    Args:
        path: Path to the GeoJSON file.

    Returns:
        geopandas.GeoDataFrame: The loaded GeoDataFrame, or an empty
        GeoDataFrame if the file was not found.

    Raises:
        fiona.errors.FionaValueError, OSError, etc.: Errors raised by geopandas
        when the file exists but cannot be read or parsed.
    """
    if not path.exists():
        logger.error(
            "geojson file not found in {path}",
        )
        return gpd.GeoDataFrame()
    return gpd.read_file(path)
