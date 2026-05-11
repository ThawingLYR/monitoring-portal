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
from typing import Optional
import os
from loguru import logger


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
    folder: str | None = None

    def __init__(self, **data):
        """
        Initializes the Sensor instance.

        Sets up the data folder for the sensor based on its `sourceType` and `sourceID`.
        If the folder does not exist, it is created. If existing data files are found,
        they are loaded into the `data` attribute.
        """
        super().__init__(**data)
        self.folder = os.path.join(
            os.getenv("DATA_DIR", "data/"), self.config.sourceType, self.config.sourceID
        )
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
            logger.info(
                f"Created folder for sensor data: {self.folder}. No data file exists yet."
            )

        if os.listdir(self.folder):
            logger.info(
                f"Loading existing data for sensor {self.config.sourceID} from {self.folder}."
            )
            self.data = SensorData(
                SensorID=f"{self.config.sourceType}_{self.config.sourceID}",
                data=dd.read_parquet(
                    os.path.join(self.folder, "*.parquet"),
                    engine="pyarrow",
                    index_col=0,
                ),
                update_time=datetime.now(),
            )
        else:
            logger.info(
                f"No existing data found for sensor {self.config.sourceID} in {self.folder}. Starting with empty data."
            )
            self.data = SensorData(
                SensorID=f"{self.config.sourceType}_{self.config.sourceID}",
                data=None,
                update_time=None,
            )

    def update_data(self, new_data: pd.DataFrame) -> None:
        """
        Updates the sensor's data with new observations, writing each date's data to a separate Parquet file.

        Args:
            new_data (pd.DataFrame): New data to add. Must have a datetime index or a 'timestamp' column.

        Raises:
            ValueError: If `new_data` lacks a datetime index or 'timestamp' column.
            ValueError: If there is a header mismatch between existing and new data for any date.
            Exception: If an error occurs during file operations (temp files are cleaned up).

        Notes:
            - Data is partitioned by date (YYYY-MM-DD) and stored as Parquet files.
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

        # Extract unique dates from the new data
        dates = new_data.index.normalize().unique()

        for date in dates:
            date_str = date.strftime("%Y-%m-%d")
            file_path = os.path.join(self.folder, f"{date_str}.parquet")
            temp_file_path = None

            try:
                # Load existing data for this date (if any)
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
                            f"Header mismatch for {date_str}. "
                            f"Missing in existing: {missing_in_existing}. "
                            f"Missing in new: {missing_in_new}."
                        )
                else:
                    existing_data = pd.DataFrame(columns=new_data.columns)

                # Filter new_data for this date
                new_data_for_date = new_data[new_data.index.normalize() == date]

                # Combine existing and new data, keeping the last observation for duplicates
                updated_data = pd.concat([existing_data, new_data_for_date])
                updated_data = updated_data[~updated_data.index.duplicated(keep="last")]

                # Atomic write: write to temp file first
                temp_fd, temp_file_path = tempfile.mkstemp(
                    suffix=".parquet", dir=self.folder
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
        if os.listdir(self.folder):
            self.data.data = dd.read_parquet(
                os.path.join(self.folder, "*.parquet"),
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
        self, start_time: datetime, end_time: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Retrieves the sensor's data within the specified time range.

        Args:
            start_time (datetime): Start of the time range (inclusive).
            end_time (datetime): End of the time range (inclusive).

        Returns:
            pd.DataFrame | None: The filtered data as a pandas DataFrame, or None if no data is available.
        """
        if self.data is None or self.data.data is None:
            logger.warning(
                f"No data available for sensor {self.config.sourceID} when attempting to retrieve data."
            )
            return None

        # Filter data by time range and compute the result
        return self.data.data.loc[start_time:end_time].compute()

    def update_latest_data(self) -> None:
        """
        Fetches the latest data (from the last cached timestamp to now) and updates the sensor's data.
        """
        new_data = self.fetch_data()
        if new_data is not None and not new_data.empty:
            self.update_data(new_data)

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
