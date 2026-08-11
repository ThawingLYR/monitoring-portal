from src.datasource.datasource_model import DataSource
from src.config.config_class import StationConfig
from src.utils.utc_managment import make_utc
from src.config.config_class import StationSensors
from src.auth.secret_manager import LocalSecretManager
from sources_weather_stations_netatmo import rename_dic

from requests import Session, post

from typing import Any, Dict
from pandas import DataFrame, to_datetime
from datetime import datetime, timedelta, UTC

import pandas as pd
import numpy as np
import re

from src.auth.secrets import get_secret

from loguru import logger


@DataSource.register("netatmo")
class NetatmoDataSource(DataSource):
    def __init__(self, config=StationConfig):
        super().__init__()
        self.provider = "netatmo"
        self.config = config

    def get_data(
        self,
        **kwargs,
    ) -> DataFrame:

        endpoint = "https://api.netatmo.com/api/getpublicdata"

        # two data sets to download all data, since netatmo api just supplies one of multiple stations,
        # if area to big and mulitple are overlapping
        lyr_coords = [78.226902, 15.689416, 78.216516, 15.590670]
        big_area_coords = [78.25, 16.3, 78.15, 15.3]
        coords = [lyr_coords, big_area_coords]
        df: DataFrame = pd.DataFrame()  # Initialize an empty DataFrame

        for lat_ne, lon_ne, lat_sw, lon_sw in coords:
            logger.info(
                f"Requesting data for NETATMO area {lat_ne}/{lon_ne} and {lat_sw}/{lon_sw}"
            )
            parameters = {
                "lat_ne": lat_ne,
                "lon_ne": lon_ne,
                "lat_sw": lat_sw,
                "lon_sw": lon_sw,
                "required_data": "temperature",
                "filter": False,
            }
            r = self.session.get(endpoint, params=parameters)

            data_2_check = r.json()
            if data_2_check.get("status", None) != "ok":
                logger.error(
                    f"Error fetching data from NETATMO API for coordinates {lat_ne}/{lon_ne} and {lat_sw}/{lon_sw}: {data_2_check.get('error', {}).get('message', 'No error message provided')}"
                )
            else:
                df: DataFrame = self._format_data(data_2_check)
                if not df.empty:
                    break

        if df.empty:
            raise ValueError(
                f"No valid data returned from NETATMO API for Sensor {self.config.sourceID}."
            )

        return df

    def _get_session(self) -> Session:

        # Define the NETATMO API endpoint and credentials
        endpoint = "https://api.netatmo.com/oauth2/token"
        client_id = get_secret("netatmo_client_id")
        client_secret = get_secret("netatmo_client_secret")

        # handling the refresh token
        secret_manager = LocalSecretManager(secret_file="./secrets/secrets.enc")
        refresh_token = secret_manager.get_encrypted_secret(
            "netatmo_refresh_token",
            default=get_secret("netatmo_first_refresh_token"),
            create=True,
        )

        # Define the data and headers for the token request
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        r = post(endpoint, data=data)
        # Check if request succeeded and retrieve token
        if r.status_code == 200:
            token_data = r.json()
            access_token = token_data["access_token"]
        else:
            raise Exception(f"Authentication failed with status code {r.status_code}")

        secret_manager.update_secret(
            "netatmo_refresh_token", token_data["refresh_token"]
        )

        session = Session()
        session.headers.update(
            {
                "accept": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
        )

        return session

    def _format_data(self, data: Dict[str, Any]) -> DataFrame:

        def __get_res_time(sensor_data: Dict[str, Any]) -> pd.Timestamp | None:
            for key in ("wind_timeutc", "rain_timeutc"):
                if key in sensor_data:
                    return (
                        pd.to_datetime(int(sensor_data[key]), unit="s")
                        .tz_localize("UTC")
                        .round("min")
                    )
            return None

        mac_address = self._get_MacAdress()
        measurements = []  # storage of the single measurement DataFrames
        for entry in data.get("body", []):
            _id = entry.get("_id")
            if _id != mac_address:
                continue  # Skip entries that don't match the desired MacAdress
            longitude, latitude = entry.get("place", {}).get("location", [None, None])
            # checking if the station has moved, if so log a warning, should be a warning if
            # moved more than 10 meters (if I remember correctly)
            if round(latitude, 6) != round(
                self.config.coordinates.latitude, 6
            ) or round(longitude, 6) != round(self.config.coordinates.longitude, 6):
                logger.warning(
                    f"Station {self.config.sourceID} may have changed location (from {self.config.coordinates.latitude}, {self.config.coordinates.longitude} to {latitude}, {longitude})."
                )

            measures = entry.get("measures", {})
            # all times get rounded to the nearest minute
            for sensor, sensor_data in measures.items():
                # if sensor_data contains "type" and "res", it's either
                # the indoor preassure sensor or the outdoor temperature sensor
                # with humidity
                if "type" in sensor_data and "res" in sensor_data:
                    res_time = int(
                        list(sensor_data.get("res", {"00000": []}).keys())[0]
                    )  # Extract timestamp
                    res_values = sensor_data.get("res", {})[
                        str(res_time)
                    ]  # Sensor readings

                    for i in range(len(sensor_data.get("type", []))):
                        measurements.append(
                            pd.DataFrame(
                                res_values[i],
                                index=[
                                    pd.to_datetime(
                                        res_time,
                                        unit="s",
                                    )
                                    .tz_localize("UTC")
                                    .round("min")
                                ],
                                columns=[sensor_data["type"][i]],
                            )
                        )
                # the wind and rain sensor always start with this Mac address
                # and have a slightly different structure, so they are handled separately
                elif sensor.startswith("06:00:00") or sensor.startswith("05:00:00"):
                    res_time = __get_res_time(sensor_data)
                    if res_time is None:
                        continue  # Skip this sensor if no valid timestamp
                    for name in sensor_data.keys():
                        if name not in ["wind_timeutc", "rain_timeutc", "rain_live"]:
                            measurements.append(
                                pd.DataFrame(
                                    [sensor_data[name]],
                                    index=[res_time],
                                    columns=[name],
                                )
                            )
            break  # Exit after processing the first matching station

        df: pd.DataFrame = pd.DataFrame()  # Initialize an empty DataFrame
        if measurements:
            df = pd.concat(
                measurements, axis=1
            )  # concatenate all measurement DataFrames into a single DataFrame
            df.rename(rename_dic, axis=1, inplace=True)
            if len(df.columns) > len(rename_dic):
                logger.warning(
                    f"Some columns in the DataFrame for {self.config.sourceID} were not renamed. Columns: {df.columns}"
                )
            df.sort_index(inplace=True)
            # removing data that is older than 15 minutes, since the crone job is in that interval
            df = df[df.index > datetime.now(UTC) - timedelta(minutes=15)]
            if df.empty:
                logger.warning(
                    f"No recent data (last 15 minutes) available for station {self.config.sourceID}."
                )

        return df

    def _get_MacAdress(self) -> str:
        """
        Extracts the MacAdress from the station's sourceID.

        Returns:
            str: The extracted MacAdress.
        """
        match: re.Match[str] | None = re.search(
            r"(?i)\b((?:[0-9A-F]{2}(?::|-)){5}[0-9A-F]{2}|[0-9A-F]{12})_(\d+)\b",
            self.config.sourceID,
        )
        if match:
            return match.group(1)  # Return the MacAdress part of the match
        else:
            logger.warning(
                f"Invalid sourceID format: {self.config.sourceID}. Trying to use the entire sourceID as MacAdress."
            )
            return self.config.sourceID
