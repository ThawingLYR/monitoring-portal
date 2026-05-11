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


class Sensor(BaseModel, ABC):
    config: StationConfig
    data: SensorData | None = None
    folder: str | None = None

    def __init__(self, **data):
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

    def update_data(self, new_data: pd.DataFrame):
        """
        Updates the sensor's data with new data, writing only the relevant date's file.
        Assumes new_data has a datetime index or a 'timestamp' column.
        Performs header compatibility check and atomic writing.
        """
        if not isinstance(new_data.index, pd.DatetimeIndex):
            if "timestamp" in new_data.columns:
                new_data = new_data.set_index("timestamp")
            else:
                raise ValueError(
                    "new_data must have a datetime index or 'timestamp' column."
                )

        # Extract dates from the new data
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

                # Combine existing and new data
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

        # Update the SensorData object
        self.data.update_time = datetime.now()
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

    def get_data(self, start_time: datetime, end_time: datetime) -> SensorData | None:
        """
        Retrieves the current data stored in the sensor with optionnal filterinf by time range.

        Returns:
            SensorData | None: The current sensor data, or None if no data is available.
        """
        if self.data is None or self.data.data is None:
            logger.warning(
                f"No data available for sensor {self.config.sourceID} when attempting to retrieve data."
            )
            return None

        # Filter data by time range if specified
        return self.data.data.loc[start_time:end_time].compute()

    def update_latest_data(self):
        self.update_data(self.fetch_data)

    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        """
        Abstract method to fetch new data for the sensor. This method should be implemented by subclasses to define how data is fetched for specific sensor types.
        This method should return a dataframe with the data from the latest cached datapoint to now
        """
        pass


class SensorData(BaseModel):
    """
    Represents the data collected by a sensor.

    Attributes:
        sensorID (str): Unique identifier for the sensor.
        data (Daskdd.DataFrame): A Dask dd.DataFrame containing the sensor data, with timestamps as the index.
        update_time (datetime): The time when the data was last updated.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    SensorID: str
    data: Optional[dd.DataFrame] = None
    update_time: Optional[datetime] = None

    @model_validator(mode="after")
    def check_datetime_index(cls, values):
        if values.data is not None:
            # Compute the index type (Dask dd.DataFrames are lazy, so we need to check the meta)
            if not isinstance(values.data.index._meta, pd.DatetimeIndex):
                raise ValueError("The Dask dd.DataFrame index must be a DatetimeIndex.")
        return values
