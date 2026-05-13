from src.datasource.datasource_model import DataSource
from src.config.config_class import StationSensors, StationConfig
from src.utils.utc_managment import make_utc
from src.auth.secrets import get_secret

from requests import Session
from datetime import datetime

from typing import Any, Dict
from pandas import DataFrame, to_datetime, concat
from loguru import logger


@DataSource.register("frost")
class FrostDataSource(DataSource):
    def __init__(self, config=StationConfig):
        super().__init__()
        self.provider = "frost"
        self.config = config

    def _get_session(self) -> Session:
        session = Session()

        client_id = get_secret("frost_client_id")
        session.auth = (client_id, "")

        return session

    def _format_data(self, data: Dict[str, Any]) -> DataFrame:
        # Initialize an empty list to store each record as a dictionary
        records = []

        # Iterate over each observation in the data
        for observation in data.get("data", []):
            # Start with the timestamp for each record
            record = {"timestamp": observation.get("referenceTime")}

            # Add each observation element to the record
            for element in observation.get("observations", []):
                level = element.get("level", {})
                level_type = level.get("levelType", "")
                level_value = level.get("value", 0)
                level_unit = level.get("unit", "")

                # Create a descriptive key for the element
                key = (
                    f"{element.get('elementId')}-"
                    f"{level_type}_{level_value:05.0f}{level_unit}"
                )
                record[key] = element.get("value")

            records.append(record)

        # Create a DataFrame and sort columns alphabetically
        df = DataFrame(records).sort_index(axis=1)

        # Convert timestamp to datetime and set as index
        df["timestamp"] = to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        return df

    def get_data(
        self,
        start_time: datetime,
        end_time: datetime,
        sensors: list[StationSensors],
        variables: list[str],
    ) -> DataFrame:

        if len(sensors) != 0:
            raise ValueError("Frost does not support using sensors")

        endpoint = "https://frost.met.no/observations/v0.jsonld"

        start_time = make_utc(start_time)
        end_time = make_utc(end_time)

        periods = self._get_periods(start_time, end_time)

        dfs = []

        for start, end in periods:
            logger.info(
                f"Requesting data for Frost station {self.config.sourceID} between {start} and {end}"
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
                    f"Request for Frost station {self.config.sourceID} between {start} and {end} failled with code {r.status_code}"
                )
                continue

        df = concat(
            dfs,
            axis=0,
            join="outer",  # Keeps all columns, fills missing with NaN
            ignore_index=False,  # Preserves the datetime index
            sort=True,  # Sort the index
        ).sort_index(axis=1)

        return df
