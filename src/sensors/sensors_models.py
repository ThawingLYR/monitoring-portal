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

from pydantic import BaseModel, ConfigDict, model_validator
import dask.dataframe as dd
import pandas as pd
from datetime import datetime
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
        self.data_folder = os.path.join(
            os.getenv("DATA_DIR", "data/"), self.config.sourceType, self.config.sourceID
        )
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            logger.info(
                f"Created folder for sensor data: {self.data_folder}. No data file exists yet."
            )

        self.figure_folder = os.path.join(
            os.getenv("FIG_DIR", "figure/"),
            self.config.sourceType,
            self.config.sourceID,
        )
        if not os.path.exists(self.figure_folder):
            os.makedirs(self.figure_folder)
            logger.info(
                f"Created folder for sensor figures: {self.data_folder}. No data file exists yet."
            )

        if os.listdir(self.data_folder):
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

    def update_data(self, new_data: pd.DataFrame) -> None:
        """
        Updates the sensor's data with new observations, writing each month's data to a separate Parquet file.

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
        """
        if not isinstance(new_data.index, pd.DatetimeIndex):
            if "timestamp" in new_data.columns:
                new_data = new_data.set_index("timestamp")
            else:
                raise ValueError(
                    "new_data must have a datetime index or 'timestamp' column."
                )

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
                        raise ValueError(
                            f"Header mismatch for {month_str}. "
                            f"Missing in existing: {missing_in_existing}. "
                            f"Missing in new: {missing_in_new}."
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
        file_name = (
            f"{self.config.sourceType}_{self.config.sourceID}_{figure_maker_name}.json"
        )
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
