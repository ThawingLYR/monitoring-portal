from src.datasource.datasource_model import DataSource
from src.config.config_class import StationSensors, StationConfig
from src.utils.utc_managment import make_utc

from src.auth.secret_manager import LocalSecretManager

from requests import Session, post

from pandas import DataFrame

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
        start_time,
        end_time,
        sensors: list[StationSensors],
        variables: list[str],
    ) -> DataFrame:

        assert len(variables) == 1

        endpoint = "https://api.netatmo.com/api/getpublicdata"

        # just here for later implementation
        start_time = make_utc(start_time)
        end_time = make_utc(end_time)

        # two data sets to download all data, since netatmo api just supplies one of multiple stations,
        # if area to big and mulitple are overlapping
        lyr_coords = [78.226902, 15.689416, 78.216516, 15.590670]
        big_area_coords = [78.25, 16.3, 78.15, 15.3]
        coords = [lyr_coords, big_area_coords]

        data = {}
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
            if status := data_2_check.get("status", None) != "ok":
                logger.error(
                    f"Error fetching data from NETATMO API for coordinates {coords[i]}: {data_2_check.get('error', {}).get('message', 'No error message provided')}"
                )
            else:
                data[i] = data_2_check
            i += 1

        return None

    def _get_session(self) -> Session:

        # Define the NETATMO API endpoint and credentials
        endpoint = "https://api.netatmo.com/oauth2/token"
        client_id = get_secret("netatmo_client_id")
        client_secret = get_secret("netatmo_client_secret")

        # handling the refresh token
        secret_manager = LocalSecretManager()
        refresh_token = secret_manager.get_secret("netatmo_refresh_token")

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
