# Weather station map.
#
# The layout - metric selection buttons, value-coloured markers, colour scale and
# station legend - follows the NETATMO page contributed by PSelleunis
# (@PSelleunis) in https://github.com/ThawingLYR/monitoring-portal/pull/44,
# reworked to read from the stored data rather than calling the API directly.

# Imports
import math

import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from loguru import logger
from streamlit_folium import st_folium

from src.app.loader.load_aws_latest import config_manager, load_latest_aws_values
from src.app.reusable.aws_metrics import (
    AWS_METRICS,
    DEFAULT_METRIC,
    marker_color_for,
    owner_label_for,
)
from src.app.reusable.folium_basemap import get_folium_basemap
from src.app.reusable.map_legend import add_station_legend
from src.app.reusable.value_marker import make_value_marker
from src.plots.aws import all_aws_figures
from src.sensors.aws import SensorAWS

# --- Configuration ---
config_manager.load_config("aws")
stations = config_manager.get_stations("aws")
stations_by_id = {config.sourceID: config for config in stations}

# --- Page Setup ---
st.set_page_config(page_title="Weather stations", layout="wide")
st.title("Weather stations")

# --- Session State ---
if "selected_metric" not in st.session_state:
    st.session_state.selected_metric = DEFAULT_METRIC


def select_metric(metric_key: str):
    st.session_state.selected_metric = metric_key


# --- Metric Selection ---
metric_columns = st.columns(len(AWS_METRICS))
for column, metric_option in zip(metric_columns, AWS_METRICS.values()):
    with column:
        st.button(
            metric_option.label,
            key=f"btn_{metric_option.key}",
            on_click=select_metric,
            args=(metric_option.key,),
            type=(
                "primary"
                if st.session_state.selected_metric == metric_option.key
                else "secondary"
            ),
            use_container_width=True,
        )

metric = AWS_METRICS[st.session_state.selected_metric]
st.markdown(f"**{metric.infotext}**")

# --- Data ---
if not stations:
    st.warning("No weather stations are configured.")
    st.stop()

latest = load_latest_aws_values(tuple(sorted(stations_by_id)))

# Which metrics each station reports at all, for the marker popups.
availability = {
    source_id: ", ".join(
        sorted(
            option.label
            for option in AWS_METRICS.values()
            if option.variable in set(rows["variable"])
        )
    )
    for source_id, rows in latest.groupby("sourceID")
}

values = latest[latest["variable"] == metric.variable]
directions = pd.Series(dtype=float)
if metric.direction_variable:
    directions = latest[latest["variable"] == metric.direction_variable].set_index(
        "sourceID"
    )["value"]

# Drop readings too old to represent current conditions.
if not values.empty:
    cutoff = pd.Timestamp.now(tz="UTC") - metric.max_age
    stale = values[values["timestamp"] < cutoff]
    for source_id in stale["sourceID"]:
        logger.info(
            f"Skipping station {source_id}: {metric.variable} reading older than "
            f"{metric.max_age}."
        )
    values = values[values["timestamp"] >= cutoff]

# --- Map Visualization ---
m = get_folium_basemap()
folium.LayerControl().add_to(m)

tooltip_lookup: dict[str, str] = {}
legend_entries: dict[str, str] = {}

if values.empty:
    st.warning(
        f"No station reported {metric.label.lower()} within the last {metric.max_age}. "
        "Showing station positions only."
    )
    for config in stations:
        config.get_marker().add_to(m)
else:
    # Guard against a degenerate scale: a single station, or several agreeing to
    # the nearest unit, would otherwise give vmin == vmax.
    vmin = math.floor(values["value"].min())
    vmax = math.ceil(values["value"].max())
    if vmin == vmax:
        vmax += 1
    metric_cm = cm.linear.viridis.scale(vmin, vmax)
    metric_cm.caption = metric.legend
    metric_cm.add_to(m)

    for row in values.itertuples():
        config = stations_by_id.get(row.sourceID)
        if config is None:
            continue

        color = marker_color_for(config)
        legend_entries[owner_label_for(config)] = color

        marker, tooltip = make_value_marker(
            config=config,
            metric=metric,
            value=row.value,
            timestamp=row.timestamp,
            color=color,
            colormap=metric_cm,
            direction=directions.get(row.sourceID),
            availability=availability.get(row.sourceID, ""),
        )
        marker.add_to(m)
        tooltip_lookup[tooltip] = row.sourceID

add_station_legend(m, legend_entries)

# call to render Folium map in Streamlit
st_data = st_folium(
    m,
    use_container_width=True,
    height=450,
    returned_objects=["last_object_clicked_tooltip"],
)

# --- Data Freshness ---
as_of_column, refresh_column = st.columns([4, 1])
with as_of_column:
    if latest.empty:
        st.caption(
            "No data recorded yet. Data is collected by the scheduled job, not by "
            "this page."
        )
    else:
        st.caption(f"Data as of {latest['timestamp'].max():%Y-%m-%d %H:%M} UTC")
with refresh_column:
    if st.button("Reload from disk", use_container_width=True):
        load_latest_aws_values.clear()
        st.rerun()


# --- User Interaction ---
clicked = st_data["last_object_clicked_tooltip"]
if clicked:
    # The tooltip carries the measured value, so it stops matching as soon as the
    # selected metric changes. Fall back to the station name it starts with.
    source_id = tooltip_lookup.get(clicked)
    if source_id is None:
        name = clicked.split(" — ")[0]
        matches = config_manager.get_stations("aws", query={"name": name})
        source_id = matches[0].sourceID if matches else None

    config = stations_by_id.get(source_id)
    if config is None:
        st.info("Select a station on the map to see its data.")
    else:
        st.markdown(f"You selected **{config.name}**")

        sensor = SensorAWS(config=config)
        station_data = sensor.get_data()

        if station_data is None or station_data.empty:
            st.info("No data recorded yet for this station.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col4:
                st.download_button(
                    "Press to download data (CSV)",
                    sensor.get_csv().encode("utf-8"),
                    f"thawinglyr_data_{sensor.config.sourceID}_{sensor.config.name}_{sensor.config.coordinates.latitude:.4f}_{sensor.config.coordinates.longitude:.4f}.csv",
                    "text/csv",
                    key="download-csv",
                )

            for figure_maker in all_aws_figures:
                try:
                    st.plotly_chart(sensor.load_figure(figure_maker), theme="streamlit")
                except FileNotFoundError, OSError:
                    st.info(
                        "No plot available for this station yet. Figures are "
                        "generated by the scheduled job."
                    )
