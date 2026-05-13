from src.sensors.sensors_models import Sensor
from src.datasource import DataSource
from datetime import datetime, timedelta, timezone
import pandas as pd
import re
import numpy as np
from loguru import logger


class SensorBorehole(Sensor):
    """
    A specialized sensor class for borehole stations, extending the base `Sensor` class.

    This class handles the fetching and processing of borehole-specific data,
    such as soil temperature measurements at various depths. It ensures that the data
    is properly formatted with depth information extracted from column names.

    Attributes:
        Inherits all attributes from the parent `Sensor` class.
    """

    def fetch_data(self) -> pd.DataFrame:
        try:
            # Initialize the data source based on the provider
            datasource = DataSource.create(config=self.config)

            # Determine the start time for the fetch
            if self.data is None or self.data.data is None:
                # If no data exists, fetch the last 10 years
                start = datetime.now(timezone.utc) - timedelta(days=3650)
            else:
                # Otherwise, fetch from the last recorded timestamp
                start = self.data.data.index.max().compute()

            # Set end time to tomorrow to include the latest data
            end = datetime.now(timezone.utc) + timedelta(days=1)

            # Fetch data from the data source
            df = datasource.get_data(
                start_time=start,
                end_time=end,
                sensors=self.config.sensors,
                variables=["soil_temperature"],
            )

            df = df.T.groupby(level=0).mean().T

            return df

        except Exception as e:
            logger.error(f"Failed to fetch or process borehole data: {e}")
            raise

    def extract_mutli_index(self, df):
        # Extract dimension names (e.g., "depth", "height") from column names
        # Assumes columns are in the format: "{variable}-{dimension}{value}"
        dim_name = [re.sub(r"\d+", "", c.split("-")[1]) for c in df.columns]

        # Validate that all columns have the same dimension
        unique_dims = np.unique(dim_name)
        if len(unique_dims) != 1:
            error_msg = (
                f"Multiple extra dimensions detected in columns: {unique_dims}. "
                "Borehole sensors can only handle a single dimension (e.g., depth)."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Split column names into variable and dimension-value parts
        df.columns = df.columns.str.split("-", expand=True)

        # Extract the variable name (level 0) and numeric value (level 1)
        level0 = df.columns.get_level_values(0)
        level1 = (
            df.columns.get_level_values(1)
            .str.extract(r"(\d+)")[
                0
            ]  # Extract numeric part (e.g., "10" from "depth10")
            .astype(int)  # Convert to integer
        )

        # Reconstruct the DataFrame with a MultiIndex (variable, depth)
        df.columns = pd.MultiIndex.from_arrays(
            [level0, level1],
            names=[
                df.columns.names[0],
                unique_dims[0],
            ],  # Use the single dimension name
        )

        return df
