"""
Value-Encoding Map Markers

Builds folium markers whose glyph colour encodes the measured value and whose
rotation encodes a bearing, for the weather station map.

The value-encoded marker design - glyph colour from a colour scale, glyph
rotation from a wind bearing - comes from the NETATMO page contributed by
PSelleunis (@PSelleunis) in
https://github.com/ThawingLYR/monitoring-portal/pull/44.

`StationConfig.get_marker()` is deliberately not reused here. It renders a
station's *configured* appearance, which is static and shared: the configuration
objects live in `ConfigManager.config_dict`, a class attribute shared across
queries and sessions, so writing per-metric styling into them would leak between
renders. The styling below is view state that changes on every metric selection,
so it is kept local to the render.
"""

import pandas as pd
from branca.colormap import ColorMap
from folium import Html, Icon, Marker, Popup

from src.app.reusable.aws_metrics import MetricDisplay
from src.config.config_class import StationConfig


def station_tooltip(
    config: StationConfig,
    metric: MetricDisplay,
    value: float,
    direction: float | None = None,
) -> str:
    """Builds the hover label of a station marker.

    Args:
        config (StationConfig): The station.
        metric (MetricDisplay): The selected metric.
        value (float): The measured value.
        direction (float | None): Bearing in degrees, if applicable.

    Returns:
        str: The station name followed by the formatted value.
    """
    return f"{config.name} — {metric.format_value(value, direction)}"


def make_value_marker(
    config: StationConfig,
    metric: MetricDisplay,
    value: float,
    timestamp: pd.Timestamp,
    color: str,
    colormap: ColorMap,
    direction: float | None = None,
    availability: str = "",
) -> tuple[Marker, str]:
    """Builds a marker whose glyph colour encodes the measured value.

    Args:
        config (StationConfig): Station the marker represents.
        metric (MetricDisplay): Display metadata of the selected metric.
        value (float): Latest value of the metric.
        timestamp (pd.Timestamp): Time of the latest value, in UTC.
        color (str): Colour of the marker body, from the AwesomeMarkers palette.
        colormap (ColorMap): Colour scale applied to `value`.
        direction (float | None): Bearing in degrees used to rotate the glyph.
        availability (str): Human readable list of metrics the station reports.

    Returns:
        tuple[Marker, str]: The marker, and the tooltip text it carries. The
            tooltip is returned so callers can map a click back to the station.
    """
    tooltip = station_tooltip(config, metric, value, direction)

    elevation = (
        f"<b>Elevation</b>: {config.coordinates.elevation:.0f} m<br>"
        if config.coordinates.elevation is not None
        else ""
    )
    popup_html = f"""<body style="font-family:sans-serif; font-size:0.9em">
    <b>Name</b>: {config.name}<br>
    <b>Source ID</b>: {config.sourceID}<br>
    <b>{metric.short_legend}</b>: {metric.format_value(value, direction)}<br>
    <b>Measured</b>: {timestamp:%Y-%m-%d %H:%M} UTC<br>
    {elevation}<b>Owner</b>: {config.owner}<br>
    <b>Data availability</b>: {availability or "unknown"}
    </body>"""

    angle = 0
    if direction is not None and not pd.isna(direction):
        angle = int(direction) % 360

    return (
        Marker(
            location=(config.coordinates.latitude, config.coordinates.longitude),
            tooltip=tooltip,
            popup=Popup(Html(popup_html, script=True), max_width=280),
            icon=Icon(
                color=color,
                icon=metric.icon,
                icon_color=colormap(value),
                angle=angle,
                prefix=config.marker.prefix,
            ),
        ),
        tooltip,
    )
