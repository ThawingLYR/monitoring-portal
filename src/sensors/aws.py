from src.sensors.sensors_models import Sensor
from src.datasource import DataSource
from datetime import datetime, timedelta, timezone
import pandas as pd
import re
import numpy as np
from loguru import logger


class SensorAWS(Sensor):
    """
    A specialized sensor class for AWS stations, extending the base `Sensor` class.

    This class handles the fetching and processing of AWS-specific data,
    such as meteorological measurements. It ensures that the data
    is properly formatted and ready for analysis.

    Attributes:
        Inherits all attributes from the parent `Sensor` class.
    """

    def fetch_data(self) -> pd.DataFrame:
        try:
            # Initialize the data source based on the provider
            datasource = DataSource.create(config=self.config)

            # Determine the start time for the fetch
            # if self.data is None or self.data.data is None:
            # If no data exists, fetch the last 10 years
            # start = datetime.now(timezone.utc) - timedelta(days=3650)
            # else:
            #     # Otherwise, fetch from the last recorded timestamp
            #     start = self.data.data.index.max().compute()

            # # Set end time to tomorrow to include the latest data
            # end = datetime.now(timezone.utc) + timedelta(days=1)

            # Fetch data from the data source
            df = datasource.get_data(
                # start_time=start,
                # end_time=end,
                variables=[
                    "air_temperature",
                    "relative_humidity",
                    "air_pressure",
                    "wind_speed",
                    "wind_from_direction",
                    "wind_speed_of_gust",
                    "wind_gust_from_direction",
                    # rain-amount missing
                ],  ## List of variables to update
            )

            # df = df.T.groupby(level=0).mean().T

            return df

        except Exception as e:
            logger.error(f"Failed to fetch or process AWS data: {e}")
            raise
