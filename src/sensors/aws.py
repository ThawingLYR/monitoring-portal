from datetime import datetime, timedelta, timezone

import pandas as pd
from loguru import logger

from src.datasource import DataSource
from src.sensors.sensors_models import Sensor

# Canonical variables requested for an automatic weather station. Providers return
# the subset they actually measure; a provider that ignores this list (Netatmo)
# simply returns everything it has.
AWS_VARIABLES = [
    "air_temperature",
    "relative_humidity",
    "air_pressure",
    "wind_speed",
    "wind_from_direction",
    "wind_speed_of_gust",
    "wind_gust_from_direction",
    "rainfall_amount_wrt_60min",
    "rainfall_amount_wrt_24h",
]


class SensorAWS(Sensor):
    """
    A specialized sensor class for AWS stations, extending the base `Sensor` class.

    This class handles the fetching and processing of AWS-specific data,
    such as meteorological measurements. It ensures that the data
    is properly formatted and ready for analysis.

    The class is provider-agnostic: the concrete data source is resolved from
    `config.dataProvider`, so the same sensor serves Netatmo, Frost and Tilsig
    weather stations.

    Attributes:
        Inherits all attributes from the parent `Sensor` class.
    """

    def fetch_data(self) -> pd.DataFrame:
        """Fetches observations not yet stored for this station.

        Returns:
            pd.DataFrame: Observations indexed by timestamp.

        Raises:
            Exception: Re-raises any failure of the underlying data source, after
                logging it. Callers iterating over many stations should catch this
                so one unavailable station does not abort the whole pass.
        """
        try:
            # Initialize the data source based on the provider
            datasource = DataSource.create(config=self.config)

            # Determine the start time for the fetch
            if self.data is None or self.data.data is None:
                # If no data exists, start from the station's commissioning date
                start = self._start_date()
            else:
                # Otherwise, fetch from the last recorded timestamp
                start = self.data.data.index.max().compute()

            # Set end time to tomorrow to include the latest data
            end = datetime.now(timezone.utc) + timedelta(days=1)

            # Fetch data from the data source. Snapshot-only providers such as
            # Netatmo ignore the time range and return their current values.
            df = datasource.get_data(
                start_time=start,
                end_time=end,
                sensors=self.config.sensors,
                variables=AWS_VARIABLES,
            )

            return df

        except Exception as e:
            logger.error(f"Failed to fetch or process AWS data: {e}")
            raise

    def _start_date(self) -> datetime:
        """Resolves the earliest timestamp worth requesting for this station.

        Returns:
            datetime: The configured start date, or ten years ago if it cannot be
                parsed.
        """
        try:
            return pd.to_datetime(self.config.startDate, utc=True).to_pydatetime()
        except ValueError, TypeError:
            logger.warning(
                "Could not parse startDate '{}' for station {}. Defaulting to ten "
                "years of history.",
                self.config.startDate,
                self.config.sourceID,
            )
            return datetime.now(timezone.utc) - timedelta(days=3650)
