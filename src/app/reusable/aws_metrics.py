"""
AWS Metric Display Metadata

Presentation metadata for the variables an automatic weather station reports:
the button caption, the unit, the map icon, and how fresh a reading must be to
be worth drawing.

This is deliberately separate from `src.config.config_class`, which mirrors the
externally managed station JSON. Nothing here describes a station; it describes
how a measurement is shown, and it is consumed both by the weather station page
and by the figures in `src.plots.aws`.

The metric table, its icons and its wording are ported from the NETATMO
weather station page contributed by PSelleunis (@PSelleunis) in
https://github.com/ThawingLYR/monitoring-portal/pull/44, re-keyed to the canonical
variable names the data sources now store.

Icon names are Font Awesome 6: folium 6.20 bundles Font Awesome 6 without the
version 4 compatibility shims, so version 4 names such as "tint" or "tachometer"
render as empty boxes.
"""

import math
from datetime import timedelta

import pandas as pd
from pydantic import BaseModel

from src.config.config_class import StationConfig


class MetricDisplay(BaseModel):
    """Display metadata for one AWS variable shown on the station map.

    Attributes:
        key (str): Short identifier used for widget keys and session state.
        label (str): Caption of the metric selection button.
        infotext (str): Sentence shown above the map when the metric is selected.
        variable (str): Canonical variable name, as stored by the data sources.
        direction_variable (str | None): Canonical variable holding a bearing in
            degrees, used to rotate the marker glyph. None for scalar metrics.
        unit (str): Unit appended to formatted values.
        legend (str): Caption of the colour scale.
        icon (str): Font Awesome 6 icon name.
        decimals (int): Decimal places used when formatting values.
        max_age (timedelta): Readings older than this are not drawn.
    """

    key: str
    label: str
    infotext: str
    variable: str
    direction_variable: str | None = None
    unit: str
    legend: str
    icon: str
    decimals: int = 1
    max_age: timedelta = timedelta(minutes=20)

    def format_value(self, value: float, direction: float | None = None) -> str:
        """Formats a measured value, and its bearing when the metric has one.

        Args:
            value (float): The measured value.
            direction (float | None): Bearing in degrees, if applicable.

        Returns:
            str: A short human readable representation, e.g. "4.0 m/s | 210deg".

        Example:
            >>> AWS_METRICS["temp"].format_value(-3.25)
            '-3.2 °C'
        """
        text = f"{value:.{self.decimals}f} {self.unit}"
        if direction is not None and not pd.isna(direction):
            text += f" | {math.floor(direction)}°"
        return text

    @property
    def short_legend(self) -> str:
        """The legend without its trailing unit, for use as a popup field label.

        Returns:
            str: e.g. "Wind Gust" for the legend "Wind Gust (m/s)".
        """
        return self.legend.rsplit(" ", 1)[0]


AWS_METRICS: dict[str, MetricDisplay] = {
    "temp": MetricDisplay(
        key="temp",
        label="Temperature",
        infotext="Air temperature, from the most recent reading of each station.",
        variable="air_temperature",
        unit="°C",
        legend="Temperature (°C)",
        icon="temperature-half",
    ),
    "wind_s": MetricDisplay(
        key="wind_s",
        label="Wind strength",
        infotext="Wind speed and direction, from the most recent reading of each station.",
        variable="wind_speed",
        direction_variable="wind_from_direction",
        unit="m/s",
        legend="Wind Strength (m/s)",
        icon="arrow-down",
    ),
    "wind_g": MetricDisplay(
        key="wind_g",
        label="Wind gust",
        infotext="Wind gust and direction, from the most recent reading of each station.",
        variable="wind_speed_of_gust",
        direction_variable="wind_gust_from_direction",
        unit="m/s",
        legend="Wind Gust (m/s)",
        icon="arrow-down",
    ),
    "rain_60": MetricDisplay(
        key="rain_60",
        label="Rain 60min",
        infotext="Rain accumulated over the 60 minutes before the last reading.",
        variable="rainfall_amount_wrt_60min",
        unit="mm",
        legend="Rain (mm)",
        icon="droplet",
        max_age=timedelta(hours=1),
    ),
    "rain_24": MetricDisplay(
        key="rain_24",
        label="Rain 24h",
        infotext="Rain accumulated over the 24 hours before the last reading.",
        variable="rainfall_amount_wrt_24h",
        unit="mm",
        legend="Rain (mm)",
        icon="cloud-rain",
        max_age=timedelta(hours=1),
    ),
    "hum": MetricDisplay(
        key="hum",
        label="Humidity",
        infotext="Relative humidity, from the most recent reading of each station.",
        variable="relative_humidity",
        unit="%",
        legend="Humidity (%)",
        icon="percent",
        decimals=0,
    ),
    "p": MetricDisplay(
        key="p",
        label="Pressure",
        infotext="Air pressure, from the most recent reading of each station.",
        variable="air_pressure",
        unit="hPa",
        legend="Pressure (hPa)",
        icon="gauge-high",
    ),
}

DEFAULT_METRIC = "temp"

# Marker body colour per station owner. Netatmo stations operated by UNIS are
# distinguished from the public consumer stations that are shown alongside them.
OWNER_MARKER_COLOR: dict[str, str] = {"UNIS": "darkred"}
DEFAULT_MARKER_COLOR = "white"

# Label shown in the map legend for owners without a dedicated colour.
OTHER_OWNER_LABEL = "Private/Other organization"


def marker_color_for(config: StationConfig) -> str:
    """Returns the marker body colour for a station.

    Args:
        config (StationConfig): The station to colour.

    Returns:
        str: A Leaflet AwesomeMarkers colour name.
    """
    return OWNER_MARKER_COLOR.get(config.owner, DEFAULT_MARKER_COLOR)


def owner_label_for(config: StationConfig) -> str:
    """Returns the legend label describing a station's owner.

    Args:
        config (StationConfig): The station to label.

    Returns:
        str: The owner name when it has a dedicated colour, a generic label
            otherwise.
    """
    return config.owner if config.owner in OWNER_MARKER_COLOR else OTHER_OWNER_LABEL
