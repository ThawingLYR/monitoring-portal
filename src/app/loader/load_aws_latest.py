"""
Latest AWS Observation Loader

Reads the most recent value of every variable of every configured weather
station from the Parquet store the cron job writes.

The app never contacts a provider API: it only reads what the cron job has
already stored, and mounts that store read-only. The cost to control here is
therefore disk reads, not requests, which is what the cache below is for.
"""

from datetime import timedelta

import pandas as pd
import streamlit as st
from loguru import logger

from src.config.config_manager import ConfigManager
from src.sensors.aws import SensorAWS
from src.utils.variable_columns import base_variable

# A single, module-level manager shared with the pages that import it.
# `ConfigManager.config_dict` is a class attribute that `__init__` resets, so
# constructing a second manager - in particular inside the cached function below -
# would silently discard the configuration the caller had already loaded.
config_manager = ConfigManager()

LATEST_COLUMNS = ["sourceID", "variable", "column", "value", "timestamp"]


@st.cache_data(ttl=300, show_spinner="Reading latest weather station data")
def load_latest_aws_values(
    source_ids: tuple[str, ...], lookback_hours: int = 24
) -> pd.DataFrame:
    """Loads the latest value of every variable for the given AWS stations.

    Args:
        source_ids (tuple[str, ...]): Source IDs of the stations to read. A tuple
            rather than a list, so Streamlit can hash it into the cache key.
        lookback_hours (int): Size of the window searched for a valid value.

    Returns:
        pd.DataFrame: Long-format frame with the columns `sourceID`, `variable`
            (canonical name), `column` (name as stored, which may carry a
            dimension suffix), `value` and `timestamp` (timezone-aware UTC).
            Stations without recent data contribute no rows.
    """
    config_manager.load_config("aws")
    rows: list[dict] = []

    for source_id in source_ids:
        stations = config_manager.get_stations("aws", {"sourceID": source_id})
        if not stations:
            logger.warning(f"No configuration found for AWS station {source_id}.")
            continue

        try:
            sensor = SensorAWS(config=stations[0])
            latest = sensor.get_latest_values(lookback=timedelta(hours=lookback_hours))
        except Exception as error:
            # One unreadable station must not blank the whole map.
            logger.warning(f"Could not read latest data for {source_id}: {error}")
            continue

        for column, row in latest.iterrows():
            rows.append(
                {
                    "sourceID": source_id,
                    "variable": base_variable(column),
                    "column": column,
                    "value": row["value"],
                    "timestamp": row["timestamp"],
                }
            )

    return pd.DataFrame(rows, columns=LATEST_COLUMNS)
