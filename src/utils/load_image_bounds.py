import json
from pathlib import Path


def load_bounds(path: Path):
    """
    Load bounds from a JSON sidecar and return as
    [[lat_min, lon_min], [lat_max, lon_max]].

    Assumes the JSON is either {"image_bounds": [[...],[...]]} or raw [[...],[...]].
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    bounds = data["image_bounds"] if isinstance(data, dict) else data

    # cast to floats and normalize order
    (a_lat, a_lon), (b_lat, b_lon) = map(lambda p: (float(p[0]), float(p[1])), bounds)
    lat_min, lat_max = min(a_lat, b_lat), max(a_lat, b_lat)
    lon_min, lon_max = min(a_lon, b_lon), max(a_lon, b_lon)
    return [[lat_min, lon_min], [lat_max, lon_max]]
