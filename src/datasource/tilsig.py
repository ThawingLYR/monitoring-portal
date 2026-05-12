from src.datasource.datasource_model import DataSource
from src.config.config_class import StationSensors

from requests import Session, post
from datetime import datetime

from typing import Any, Dict
from pandas import DataFrame

import pandas as pd

from src.auth.secrets import get_secret

from loguru import logger


@DataSource.register("tilsig")
class TilsigDataSource(DataSource):
    def __init__(self):
        super().__init__()
        self.provider = "tilsig"

    def get_data(
        self,
        start_time: datetime,
        end_time: datetime,
        sensors: list[StationSensors],
        variables: list[str],
    ) -> DataFrame:

        assert len(variables) == 1

        endpoint = "https://api.tilsig.com/v1/measurement/raw"

        sensors = self._reduce_sensor_list(
            start_time=start_time, end_time=end_time, sensors=sensors
        )

        dfs = []

        for sensor in sensors:
            periods = self._get_periods(sensor.startDate, sensor.endDate)

            for start, end in periods:
                parameters = {
                    "stationId": "",
                    "deviceId": "",
                    "sensorId": sensor.sensorID,
                    "from": end.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "to": start.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                }
                r = self.session.get(endpoint, params=parameters)

                if r.status_code == 200:
                    dfs.append(
                        self._format_data(
                            r.json(), variable_name=variables[0], sensor=sensor
                        )
                    )
                else:
                    logger.warning(
                        f"Request for Tilsig sensor {sensor.sensorID} between {start} and {end} failled with code {r.status_code}"
                    )
        df = pd.concat(
            dfs,
            axis=0,
            join="outer",  # Keeps all columns, fills missing with NaN
            ignore_index=False,  # Preserves the datetime index
            sort=True,  # Avoids sorting the index
        ).sort_index(axis=1)

        return df

    def _get_session(self) -> Session:

        # Define the Tilsig API endpoint and credentials
        endpoint = "https://api.tilsig.com/v1/authentication/authenticate"
        username = get_secret("tilsig_username")
        password = get_secret("tilsig_password")

        # Define the data and headers for the token request
        data = {
            "username": username,
            "password": password,
        }

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        # Send the token request
        r = post(endpoint, json=data, headers=headers)

        # Check if request succeeded and retrieve token
        if r.status_code == 200:
            token_data = r.json()
            access_token = token_data["token"]
        else:
            logger.error(f"Authentication failed with status code {r.status_code}")
            raise Exception(f"Authentication failed with status code {r.status_code}")

        session = Session()
        session.headers.update(
            {
                "accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
        )

        return session

    def _format_data(
        self, data: Dict[str, Any], variable_name: str, sensor: StationSensors
    ) -> DataFrame:
        df = pd.DataFrame(data)

        df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")

        sequences = df.sequence.unique()

        new_df = pd.concat(
            [
                df[df["sequence"] == seq][["value", "timestamp"]]
                .set_index("timestamp")
                .rename(
                    columns={
                        "value": f"{variable_name}-depth_below_surface_{sensor.depth[seq]:05.0f}cm"
                    }
                )
                for seq in sequences
            ],
            axis=1,
            sort=True,  # Explicitly sort the index
        ).sort_index(axis=1)

        return new_df

    def _reduce_sensor_list(
        self, start_time: datetime, end_time: datetime, sensors: list[StationSensors]
    ) -> list[StationSensors]:
        """
        Filters and adjusts a list of sensors to only include those relevant to the specified time range.
        For each sensor, the `startDate` and `endDate` are clipped to the provided `start_time` and `end_time`.

        Args:
            start_time (datetime): Start of the time range (inclusive).
            end_time (datetime): End of the time range (inclusive).
            sensors (list[StationSensors]): List of sensors to filter and adjust.

        Returns:
            list[StationSensors]: A new list of sensors, where each sensor's date range is clipped to the specified time range.
                                Sensors with no overlap with the time range are excluded.
        """
        new_sensors = []
        for sensor in sensors:
            new_sensor = sensor.model_copy()

            if sensor.startDate < start_time:
                new_sensor.startDate = start_time
            elif sensor.startDate > end_time:
                continue

            if sensor.endDate is None:
                new_sensor.endDate = end_time
            elif sensor.endDate > end_time:
                new_sensor.endDate = end_time
            elif sensor.endDate < start_time:
                continue

            new_sensors.append(new_sensor)

        return new_sensors
