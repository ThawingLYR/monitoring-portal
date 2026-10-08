"""
Sensor Data Management Module

This module defines the base classes and utilities for managing sensor data, including:
- Abstract `Sensor` class for fetching, updating, and retrieving sensor data.
- `SensorData` model for storing and validating sensor data with Dask DataFrames.

Dependencies:
    - pydantic: For data validation and settings management.
    - dask.dataframe: For lazy, out-of-core data processing.
    - pandas: For in-memory data manipulation.
    - loguru: For structured logging.
    - tempfile: For atomic file operations.
    - abc: For abstract base class definitions.
"""

import numpy as np
from pydantic import BaseModel, ConfigDict, model_validator
import dask.dataframe as dd
import pandas as pd
from datetime import datetime, timedelta, timezone
import tempfile
from abc import abstractmethod, ABC
from src.config.config_class import StationConfig
from src.plots.figure_models import Figure
from src.utils.object_name import get_full_class_name
from typing import Optional, Type
import os
import json
from loguru import logger

import plotly.io as pio
import plotly.graph_objects as go


class SensorData(BaseModel):
    """
    Represents the data collected by a sensor, stored as a Dask DataFrame.

    Attributes:
        SensorID (str): Unique identifier for the sensor.
        data (dd.DataFrame | None): A Dask DataFrame containing the sensor data, with timestamps as the index.
        update_time (datetime | None): The time when the data was last updated.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    SensorID: str
    data: Optional[dd.DataFrame] = None
    update_time: Optional[datetime] = None

    @model_validator(mode="after")
    def check_datetime_index(cls, values):
        """
        Validates that the Dask DataFrame has a DatetimeIndex.

        Args:
            values: The SensorData instance being validated.

        Returns:
            SensorData: The validated instance.

        Raises:
            ValueError: If the Dask DataFrame index is not a DatetimeIndex.
        """
        if values.data is not None:
            # Compute the index type (Dask dd.DataFrames are lazy, so we check the meta)
            if not isinstance(values.data.index._meta, pd.DatetimeIndex):
                raise ValueError("The Dask dd.DataFrame index must be a DatetimeIndex.")
        return values


class Sensor(BaseModel, ABC):
    """
    Abstract base class for all sensor types.

    This class provides core functionality for:
    - Initializing sensor data storage.
    - Updating sensor data with new observations.
    - Retrieving data within a specified time range.
    - Fetching new data (to be implemented by subclasses).

    Attributes:
        config (StationConfig): The configuration for the sensor's station.
        data (SensorData | None): The sensor's data, or None if no data is available.
        folder (str | None): Path to the folder where the sensor's data is stored.
    """

    config: StationConfig
    data: SensorData | None = None
    data_folder: str | None = None
    figure_folder: str | None = None

    def __init__(self, **data):
        """
        Initializes the Sensor instance.

        Sets up the data folder for the sensor based on its `sourceType` and `sourceID`.
        If the folder does not exist, it is created. If existing data files are found,
        they are loaded into the `data` attribute.
        """
        super().__init__(**data)
        folder_name = self._path_component(self.config.sourceID)
        self.data_folder = os.path.join(
            os.getenv("DATA_DIR", "data/"), self.config.sourceType, folder_name
        )
        self._ensure_folder(self.data_folder, "data")

        self.figure_folder = os.path.join(
            os.getenv("FIG_DIR", "figure/"),
            self.config.sourceType,
            folder_name,
        )
        self._ensure_folder(self.figure_folder, "figures")

        if os.path.isdir(self.data_folder) and os.listdir(self.data_folder):
            logger.info(
                f"Loading existing data for sensor {self.config.sourceID} from {self.data_folder}."
            )
            self.data = SensorData(
                SensorID=f"{self.config.sourceType}_{self.config.sourceID}",
                data=dd.read_parquet(
                    os.path.join(self.data_folder, "*.parquet"),
                    engine="pyarrow",
                    index_col=0,
                ),
                update_time=datetime.now(),
            )
        else:
            logger.info(
                f"No existing data found for sensor {self.config.sourceID} in {self.data_folder}. Starting with empty data."
            )
            self.data = SensorData(
                SensorID=f"{self.config.sourceType}_{self.config.sourceID}",
                data=None,
                update_time=None,
            )

    @staticmethod
    def _path_component(source_id: str) -> str:
        """
        Makes a sourceID safe to use as a folder name on any platform.

        Netatmo stations are identified by their MAC address, e.g.
        "70:ee:50:1e:00:34_0". Colons are legal in POSIX paths but reserved on
        Windows, so a developer running the collection job locally on Windows
        would otherwise get an opaque OSError. Identifiers that are already safe -
        every borehole and Frost station - are returned unchanged, so this does not
        move any existing data.

        Args:
            source_id (str): The station's source identifier.

        Returns:
            str: The identifier with reserved characters replaced by "-".
        """
        reserved = ':*?"<>|/\\'
        return "".join(
            "-" if character in reserved else character for character in source_id
        )

    @staticmethod
    def _ensure_folder(path: str, kind: str) -> None:
        """
        Creates a folder for the sensor if it does not exist yet.

        The Streamlit container mounts the data and figure volumes read-only, so a
        station the cron job has never written cannot have its folder created there.
        That is an expected condition rather than an error: the sensor simply has no
        data to show.

        Args:
            path (str): The folder to create.
            kind (str): Human readable description used in log messages.
        """
        if os.path.exists(path):
            return
        try:
            os.makedirs(path, exist_ok=True)
            logger.info(
                f"Created folder for sensor {kind}: {path}. No file exists yet."
            )
        except OSError as error:
            logger.warning(
                f"Could not create folder for sensor {kind}: {path} ({error}). "
                "Continuing without it; this is expected on a read-only mount."
            )

    def get_latest_values(
        self, lookback: timedelta = timedelta(hours=24)
    ) -> pd.DataFrame:
        """
        Retrieves the most recent valid value of every variable of the sensor.

        Providers may write one row per hardware module, leaving the columns of the
        other modules empty on that row. The latest value is therefore resolved
        column by column rather than by taking the last row of the DataFrame, which
        would be mostly missing values.

        Args:
            lookback (timedelta): How far back to search for a valid value.
                Defaults to 24 hours.

        Returns:
            pd.DataFrame: One row per variable, indexed by variable name, with the
                columns `value` (float) and `timestamp` (timezone-aware UTC).
                Empty if the sensor has no data in the window.
        """
        # Stored timestamps are timezone-naive UTC (see `update_data`), so the bound
        # must be naive too, and the results are re-localized on the way out.
        start_time = datetime.now(timezone.utc).replace(tzinfo=None) - lookback
        df = self.get_data(start_time=start_time)

        if df is None or df.empty:
            logger.info(
                f"No data in the last {lookback} for sensor {self.config.sourceID}."
            )
            return pd.DataFrame(columns=["value", "timestamp"])

        df = df.sort_index()
        records = {}
        for column in df.columns:
            series = df[column].dropna()
            if series.empty:
                continue
            timestamp = series.index[-1]
            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize("UTC")
            records[column] = {"value": series.iloc[-1], "timestamp": timestamp}

        if not records:
            return pd.DataFrame(columns=["value", "timestamp"])

        return pd.DataFrame.from_dict(records, orient="index")

    def update_data(self, new_data: pd.DataFrame) -> None:
        """
        Updates the sensor's data with new observations, writing each month's data to a separate Parquet file.
        Timezone information is removed before monthly partitioning to avoid warnings.

        Args:
            new_data (pd.DataFrame): New data to add. Must have a datetime index or a 'timestamp' column.

        Raises:
            ValueError: If `new_data` lacks a datetime index or 'timestamp' column.
            ValueError: If there is a header mismatch between existing and new data for any month.
            Exception: If an error occurs during file operations (temp files are cleaned up).

        Notes:
            - Data is partitioned by month (YYYY-MM) and stored as Parquet files.
            - Uses atomic writes (temp file + rename) to prevent corruption.
            - Duplicates are resolved by keeping the last observation for each timestamp.
            - Timezone information is dropped before converting to PeriodIndex to avoid warnings.
        """
        if len(new_data.columns) != len(np.unique(new_data.columns)):
            logger.error("There is duplicated columns in the new data, aborting...")
            return

        if not isinstance(new_data.index, pd.DatetimeIndex):
            if "timestamp" in new_data.columns:
                new_data = new_data.set_index("timestamp")
            else:
                raise ValueError(
                    "new_data must have a datetime index or 'timestamp' column."
                )

        # Remove timezone to avoid warnings when converting to PeriodIndex
        if new_data.index.tz is not None:
            new_data.index = new_data.index.tz_localize(None)

        # Extract unique months from the new data
        months = new_data.index.to_period("M").unique()

        for month in months:
            month_str = month.strftime("%Y-%m")
            file_path = os.path.join(self.data_folder, f"{month_str}.parquet")
            temp_file_path = None

            try:
                # Load existing data for this month (if any)
                if os.path.exists(file_path):
                    existing_data = dd.read_parquet(
                        file_path, engine="pyarrow"
                    ).compute()
                    # Check header compatibility
                    if not set(existing_data.columns) == set(new_data.columns):
                        missing_in_existing = set(new_data.columns) - set(
                            existing_data.columns
                        )
                        missing_in_new = set(existing_data.columns) - set(
                            new_data.columns
                        )

                        # Add missing columns to new_data with NaN
                        for col in missing_in_new:
                            new_data[col] = np.nan
                            logger.warning(
                                f"Missing column {col} in the new data - filling with NaN"
                            )

                        # A variable the station has not reported before is normal
                        # rather than exceptional: a Netatmo station only reports its
                        # wind or rain columns when those modules are awake, so the
                        # first write of a month may well be narrower than the next
                        # one. Widen the stored data instead of refusing the write.
                        for col in missing_in_existing:
                            existing_data[col] = np.nan
                            logger.info(
                                f"New column {col} for {month_str} - backfilling the "
                                "existing rows with NaN"
                            )
                else:
                    existing_data = pd.DataFrame(columns=new_data.columns)

                # Filter new_data for this month
                new_data_for_month = new_data[new_data.index.to_period("M") == month]

                # Combine existing and new data, keeping the last observation for duplicates
                updated_data = pd.concat([existing_data, new_data_for_month])
                updated_data = updated_data[~updated_data.index.duplicated(keep="last")]

                # Atomic write: write to temp file first
                temp_fd, temp_file_path = tempfile.mkstemp(
                    suffix=".parquet", dir=self.data_folder
                )
                os.close(temp_fd)
                updated_data.to_parquet(temp_file_path, engine="pyarrow")

                # Replace the old file with the new one
                if os.path.exists(file_path):
                    os.remove(file_path)
                os.rename(temp_file_path, file_path)

            except Exception as e:
                # Clean up temp file if something went wrong
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                raise e

        # Reload the data into the SensorData object
        self._reload_data()

    def _reload_data(self) -> None:
        """
        Reloads the sensor's data from disk after an update.

        Raises:
            ValueError: If no data files are found after update.
        """
        if os.listdir(self.data_folder):
            self.data.data = dd.read_parquet(
                os.path.join(self.data_folder, "*.parquet"),
                engine="pyarrow",
                index_col=0,
            )
            self.data.update_time = datetime.now()
        else:
            logger.error("No data files found after update. This should not happen.")
            raise ValueError(
                "No data files found after update. This should not happen."
            )

    def get_data(
        self, start_time: datetime = None, end_time: datetime = None
    ) -> Optional[pd.DataFrame]:
        """
        Retrieves the sensor's data within the specified time range.
        If start_time or end_time is not provided, the range is unbounded on that side.

        Args:
            start_time (datetime, optional): Start of the time range (inclusive). Defaults to None.
            end_time (datetime, optional): End of the time range (inclusive). Defaults to None.

        Returns:
            pd.DataFrame | None: The filtered data as a pandas DataFrame, or None if no data is available.
        """
        if self.data is None or self.data.data is None:
            logger.warning(
                f"No data available for sensor {self.config.sourceID} when attempting to retrieve data."
            )
            return None

        # If no time range is provided, return all data
        if start_time is None and end_time is None:
            return self.data.data.compute()

        # If only start_time is provided, filter from start_time to the end
        if start_time is not None and end_time is None:
            return self.data.data.loc[start_time:].compute()

        # If only end_time is provided, filter from the beginning to end_time
        if start_time is None and end_time is not None:
            return self.data.data.loc[:end_time].compute()

        # If both are provided, filter between start_time and end_time
        return self.data.data.loc[start_time:end_time].compute()

    def update_latest_data(self) -> None:
        """
        Fetches the latest data (from the last cached timestamp to now) and updates the sensor's data.
        """
        new_data = self.fetch_data()
        if new_data is not None and not new_data.empty:
            self.update_data(new_data)

    def _get_figure_cache(self, figure_maker_name: str) -> str:
        """
        Generates the file path for caching a figure based on the figure maker's class name.

        Args:
            figure_maker_name (str): The fully qualified class name of the figure maker.

        Returns:
            str: The absolute path to the JSON file where the figure will be cached.

        Example:
            >>> self._get_figure_cache("module.FigureMaker")
            '/path/to/figure_folder/sourceType_sourceID_module.FigureMaker.json'
        """
        source_id = self._path_component(self.config.sourceID)
        file_name = f"{self.config.sourceType}_{source_id}_{figure_maker_name}.json"
        return os.path.join(self.figure_folder, file_name)

    def prepare_figure(self, figure_maker: Type[Figure]) -> None:
        """
        Creates a figure using the provided figure maker, serializes it to JSON, and saves it to disk.

        Args:
            figure_maker (Type[Figure]): A class (not an instance) that inherits from `Figure`.
                                        Must implement `create_figure`.

        Raises:
            FileNotFoundError: If the `figure_folder` does not exist.
            IOError: If there is an issue writing the file (e.g., permissions).
            Exception: If the figure cannot be created or serialized.

        Notes:
            - The figure is cached as a JSON file in `self.figure_folder`.
            - The filename is derived from the figure maker's class name, `sourceType`, and `sourceID`.
        """
        try:
            # Create and serialize the figure
            fm = figure_maker()
            fig_json = fm.create_figure(self).to_json()

            # Get the cache path
            path = self._get_figure_cache(get_full_class_name(figure_maker))

            # Ensure the directory exists
            os.makedirs(self.figure_folder, exist_ok=True)

            # Write the JSON to file
            with open(path, "w") as f:
                f.write(fig_json)

        except FileNotFoundError as e:
            logger.error(f"Figure folder not found: {self.figure_folder}. Error: {e}")
            raise
        except IOError as e:
            logger.error(f"Failed to write figure to {path}. Error: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Failed to prepare figure for {figure_maker.__name__}. Error: {e}"
            )
            raise

    def load_figure(self, figure_maker: Type[Figure]) -> go.Figure:
        """
        Loads a cached figure from disk and deserializes it into a Plotly `Figure` object.

        Args:
            figure_maker (Figure): The class of the figure maker used to originally create the figure.

        Returns:
            plotly.graph_objects.Figure: The deserialized Plotly figure.

        Raises:
            FileNotFoundError: If the cached figure file does not exist.
            json.JSONDecodeError: If the cached file contains invalid JSON.
            Exception: If the figure cannot be deserialized.

        Notes:
            - The filename is derived from the figure maker's class name, `sourceType`, and `sourceID`.
        """
        try:
            path = self._get_figure_cache(get_full_class_name(figure_maker))

            if not os.path.exists(path):
                raise FileNotFoundError(f"Cached figure not found at: {path}")

            with open(path, "r") as f:
                fig_json = f.read()
                fig = pio.from_json(fig_json)

            return fig

        except FileNotFoundError as e:
            logger.error(f"Cached figure not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in cached figure file {path}. Error: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Failed to load figure for {figure_maker.__name__}. Error: {e}"
            )
            raise

    def get_csv(self) -> str:
        """
        Serializes the internal data to a CSV-formatted string with ISO 8601 timestamps.

        Steps:
        1. Retrieves data via `self.get_data()` (assumed to return a pandas DataFrame).
        2. Resets the DataFrame index and renames it to 'timestamp'.
        3. Converts the 'timestamp' column to ISO 8601 format (e.g., '2026-05-13T14:30:00.123Z').
        4. Returns the DataFrame as a CSV string without an index column.

        Returns:
            str: CSV string of the DataFrame with standardized timestamp formatting.

        Example:
            >>> csv_output = obj.get_csv()
            >>> print(csv_output)
            timestamp,value
            2026-05-13T14:30:00.123Z,42
        """
        df = self.get_data()
        df_reset = df.reset_index()
        df_reset = df_reset.rename(columns={"index": "timestamp"})

        # Convert the 'timestamp' column to ISO format
        df_reset["timestamp"] = (
            df_reset["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )

        return df_reset.to_csv(index=False)

    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        """
        Abstract method to fetch new data for the sensor.

        Subclasses must implement this method to define how data is fetched
        (e.g., from an API, database, or file). The returned DataFrame should
        contain data from the last cached timestamp to the present.

        Returns:
            pd.DataFrame: A DataFrame with new sensor data, indexed by timestamp.
        """
        pass
