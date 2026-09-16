"""
Map Legend

Builds the station-type legend overlaid on the weather station map.

The legend is taken from the NETATMO weather station page contributed by
PSelleunis (@PSelleunis) in
https://github.com/ThawingLYR/monitoring-portal/pull/44.

Theme note: this HTML is injected into the folium map, which Streamlit renders in
an iframe. Streamlit's theme CSS variables do not reach inside that iframe, and
the background behind the legend is always a light basemap tile. The light
palette below is therefore correct in both the light and the dark app theme, and
should not be "fixed" to follow the Streamlit theme.
"""

from folium import Element, Map


def station_legend_html(entries: dict[str, str]) -> str:
    """Builds a fixed-position legend mapping station categories to marker colours.

    Args:
        entries (dict[str, str]): Legend label to AwesomeMarkers colour name.

    Returns:
        str: The legend HTML, or an empty string when there is nothing to
            distinguish (fewer than two categories).
    """
    if len(entries) < 2:
        return ""

    rows = "".join(
        f"""
    <p style="margin: 0 0 6px 0;">
        <span style="
            display: inline-block;
            width: 12px;
            height: 12px;
            background-color: {color};
            border: 1px solid black;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
        "></span>
        {label}
    </p>"""
        for label, color in entries.items()
    )

    return f"""
<div style="
    position: fixed;
    bottom: 50px;
    left: 5px;
    width: 200px;
    background-color: white;
    border-radius: 4px;
    border: 2px solid grey;
    z-index: 9999;
    font-size: 14px;
    padding: 10px;
    color: black;
">
<p style="margin: 0 0 8px 0;"><b>Station Type</b></p>
{rows}
</div>
"""


def add_station_legend(folium_map: Map, entries: dict[str, str]) -> None:
    """Adds the station-type legend to a map, if there is anything to show.

    Args:
        folium_map (Map): The map to annotate.
        entries (dict[str, str]): Legend label to AwesomeMarkers colour name.
    """
    html = station_legend_html(entries)
    if html:
        folium_map.get_root().html.add_child(Element(html))
