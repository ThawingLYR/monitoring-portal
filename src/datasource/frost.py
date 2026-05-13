from src.datasource.datasource_model import DataSource
from src.config.config_class import StationSensors, StationConfig
from src.utils.utc_managment import make_utc
from src.auth.secrets import get_secret

from requests import Session
from datetime import datetime

from typing import Any, Dict, List
from pandas import DataFrame, to_datetime, concat
from loguru import logger


@DataSource.register("frost")
class FrostDataSource(DataSource):
    """A data source class for fetching meteorological observations from the Frost API (MET Norway).

    This class handles authentication, data requests, and formatting of observations
    from the Frost API, which provides access to meteorological and hydrological data.

    Attributes:
        provider (str): The name of the data provider, set to "frost".
        config (StationConfig): Configuration object containing station-specific settings,
            such as the `sourceID` for the Frost API.
        session (Session): A requests Session object for making HTTP requests to the Frost API.
    """

    def __init__(self, config: StationConfig) -> None:
        """Initializes the FrostDataSource with the provided configuration.

        Args:
            config (StationConfig, optional): Configuration object for the station.
                Defaults to StationConfig.
        """
        super().__init__()
        self.provider = "frost"
        self.config = config

    def _get_session(self) -> Session:
        """Creates and configures a requests Session for the Frost API.

        Authenticates the session using the client ID from the secrets manager.

        Returns:
            Session: A configured requests Session with basic authentication.
        """
        session = Session()
        client_id = get_secret("frost_client_id")
        session.auth = (client_id, "")
        return session

    def _format_data(self, data: Dict[str, Any]) -> DataFrame:
        """Formats raw observation data from the Frost API into a structured DataFrame.

        Args:
            data (Dict[str, Any]): Raw JSON response from the Frost API, containing
                a list of observations with timestamps and measured values.

        Returns:
            DataFrame: A pandas DataFrame with timestamps as the index and observation
                elements as columns. Columns are sorted alphabetically.
                Example:
                    | timestamp           | air_temperature-height_above_msl_00002m | precipitation-height_above_msl_00000m |
                    |---------------------|-----------------------------------------|---------------------------------------|
                    | 2023-01-01 00:00:00 | 5.2                                     | 0.0                                   |
        """
        records = []
        for observation in data.get("data", []):
            record = {"timestamp": observation.get("referenceTime")}
            for element in observation.get("observations", []):
                level = element.get("level", {})
                level_type = level.get("levelType", "")
                level_value = level.get("value", 0)
                level_unit = level.get("unit", "")

                # Create a unique key for each observation element
                key = (
                    f"{element.get('elementId')}-"
                    f"{level_type}_{level_value:05.0f}{level_unit}"
                )
                record[key] = element.get("value")
            records.append(record)

        # Create DataFrame, convert timestamp to datetime, and set as index
        df = DataFrame(records).sort_index(axis=1)
        df["timestamp"] = to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df

    def get_data(
        self,
        start_time: datetime,
        end_time: datetime,
        sensors: List[StationSensors],
        variables: List[str],
    ) -> DataFrame:
        """Fetches meteorological observation data for a specified time range and variables.

        Args:
            start_time (datetime): Start of the time range for the data request.
            end_time (datetime): End of the time range for the data request.
            sensors (List[StationSensors]): List of sensor configurations. **Note:** Frost API
                does not support sensor-specific requests, so this parameter is ignored and
                must be empty.
            variables (List[str]): List of variable IDs (e.g., ["air_temperature", "precipitation"])
                to request from the Frost API.

        Returns:
            DataFrame: A concatenated DataFrame containing all observations for the requested
                variables and time range. The index is the timestamp, and columns are the
                observation variables. Missing values are filled with NaN.

        Raises:
            ValueError: If the `sensors` list is not empty, as Frost does not support
                sensor-specific requests.
        """
        if len(sensors) != 0:
            raise ValueError("Frost does not support using sensors")

        endpoint = "https://frost.met.no/observations/v0.jsonld"
        start_time = make_utc(start_time)
        end_time = make_utc(end_time)

        # Split the time range into periods to avoid request timeouts
        periods = self._get_periods(start_time, end_time)
        dfs = []

        for start, end in periods:
            logger.info(
                f"Requesting data for Frost station {self.config.sourceID} "
                f"between {start} and {end}"
            )
            parameters = {
                "sources": self.config.sourceID,
                "elements": ",".join(variables),
                "referencetime": f"{start.isoformat()}/{end.isoformat()}",
            }

            r = self.session.get(endpoint, params=parameters)
            if r.status_code == 200:
                dfs.append(self._format_data(r.json()))
            else:
                logger.warning(
                    f"Request for Frost station {self.config.sourceID} "
                    f"between {start} and {end} failed with code {r.status_code}"
                )
                continue

        # Concatenate all DataFrames and sort by index and columns
        df = concat(
            dfs,
            axis=0,
            join="outer",  # Keeps all columns, fills missing with NaN
            ignore_index=False,  # Preserves the datetime index
            sort=True,  # Sort the index
        ).sort_index(axis=1)

        return df
