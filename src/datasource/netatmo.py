"""
Netatmo Data Source Module

This module implements the DataSource interface for the Netatmo `getpublicdata`
API, which exposes the current readings of public personal weather stations
inside a geographic bounding box.

Two characteristics of the Netatmo API drive the design of this module:

- Rotating refresh tokens. Netatmo issues a *single-use* refresh token: every
  authentication consumes the stored token and returns a new one, which must be
  persisted or the integration locks itself out permanently. Persistence is
  delegated to `LocalSecretManager`, and the authenticated session is cached on
  the class so that a cron pass over many stations rotates the token once rather
  than once per station.
- Snapshot-only, area-scoped responses. `getpublicdata` returns the *current*
  reading for *every* public station in a bounding box; it cannot be queried for
  a single station or for a time range. One response therefore serves every
  configured station, so responses are cached per bounding box for a short
  period and filtered per station by MAC address.

Credit:
    The Netatmo integration was contributed by PSelleunis (@PSelleunis) in
    https://github.com/ThawingLYR/monitoring-portal/pull/44. The payload parsing
    in `_format_data`, which untangles the per-module structure and timestamps of
    the `getpublicdata` response, is their work and is kept here essentially as
    written.

Dependencies:
    - requests: For HTTP requests and session management.
    - pandas: For building the resulting DataFrame.
    - loguru: For logging.
    - src.auth.secrets / src.auth.secret_manager: For credential retrieval and
      persistence of the rotating refresh token.
"""

import math
import os
import re
import threading
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar, Dict, List, Tuple

import pandas as pd
from loguru import logger
from pandas import DataFrame
from requests import Session, post

from src.auth.secret_manager import LocalSecretManager
from src.auth.secrets import get_secret
from src.config.config_class import StationConfig, StationSensors
from src.datasource.datasource_model import DataSource

# Default number of minutes of history kept from a response. This should match the
# period of the cron job configured on the server: readings older than one cron
# period have already been stored by the previous pass, and keeping them only
# produces duplicate rows. Override with the NETATMO_MAX_AGE_MINUTES env var.
DEFAULT_MAX_AGE_MINUTES = 15


@DataSource.register("netatmo")
class NetatmoDataSource(DataSource):
    """A data source class for fetching current observations from the Netatmo API.

    This class handles OAuth authentication (including rotation of the single-use
    refresh token), retrieval of public station data for the Longyearbyen area, and
    formatting of the response into a structured DataFrame for a single station.

    Attributes:
        provider (str): The name of the data provider, set to "netatmo".
        config (StationConfig): Configuration object for the station. Its `sourceID`
            carries the MAC address of the station, optionally suffixed with a
            module number (e.g. "70:ee:50:1e:00:34_0").
        session (Session): A requests Session carrying the OAuth bearer token.
        max_age (timedelta): Readings older than this are discarded by `_format_data`.

    Note:
        `getpublicdata` returns only the *current* reading of each station, so this
        source cannot backfill history. A time series is accumulated by polling:
        each cron pass appends the latest values to the station's Parquet store.
    """

    # Canonical names for the raw Netatmo measurement keys. Mirrors the naming
    # convention used by the Frost and Tilsig sources.
    RENAME_MAP: ClassVar[Dict[str, str]] = {
        "temperature": "air_temperature",
        "humidity": "relative_humidity",
        "pressure": "air_pressure",
        "rain_60min": "rainfall_amount_wrt_60min",
        "rain_24h": "rainfall_amount_wrt_24h",
        "wind_strength": "wind_speed",
        "wind_angle": "wind_from_direction",
        "gust_strength": "wind_speed_of_gust",
        "gust_angle": "wind_gust_from_direction",
    }

    # Bounding boxes to query, as (lat_ne, lon_ne, lat_sw, lon_sw).
    #
    # Two boxes are needed because Netatmo returns only one station per cluster of
    # overlapping stations when the requested area is large. The tight Longyearbyen
    # box resolves the dense town centre; the wider box catches outlying stations
    # that fall outside it.
    AREAS: ClassVar[Tuple[Tuple[float, float, float, float], ...]] = (
        (78.226902, 15.689416, 78.216516, 15.590670),
        (78.25, 16.3, 78.15, 15.3),
    )

    TOKEN_ENDPOINT: ClassVar[str] = "https://api.netatmo.com/oauth2/token"
    DATA_ENDPOINT: ClassVar[str] = "https://api.netatmo.com/api/getpublicdata"

    # How long a fetched area response may be reused. Short enough that a new cron
    # pass always refetches, long enough that one pass over many stations reuses it.
    RESPONSE_TTL: ClassVar[timedelta] = timedelta(minutes=2)

    # Warn when the station's reported position drifts further than this from the
    # configured coordinates, which usually means the station was physically moved.
    POSITION_TOLERANCE_M: ClassVar[float] = 10.0

    # --- Shared state -------------------------------------------------------
    # Netatmo refresh tokens are single-use: authenticating N times in a row
    # performs N rotations and leaves N-1 tokens dead. The session and the area
    # responses are therefore shared by every instance of this class, guarded by a
    # lock so that two threads cannot rotate the token concurrently.
    _session_lock: ClassVar[threading.Lock] = threading.Lock()
    _shared_session: ClassVar[Session | None] = None
    _session_expiry: ClassVar[datetime | None] = None
    _response_cache: ClassVar[
        Dict[Tuple[float, ...], Tuple[datetime, Dict[str, Any]]]
    ] = {}

    def __init__(self, config: StationConfig = None, max_age: timedelta = None):
        """Initializes the Netatmo data source.

        Args:
            config (StationConfig): Configuration of the station to fetch.
            max_age (timedelta | None): Maximum age of a reading to keep. Defaults to
                the NETATMO_MAX_AGE_MINUTES environment variable, or 15 minutes.
        """
        super().__init__()
        self.provider = "netatmo"
        self.config = config
        self.max_age = max_age if max_age is not None else self._default_max_age()

    @staticmethod
    def _default_max_age() -> timedelta:
        """Reads the retention window from the environment.

        Returns:
            timedelta: The configured window, or 15 minutes if unset or invalid.
        """
        raw = os.getenv("NETATMO_MAX_AGE_MINUTES")
        if raw is None:
            return timedelta(minutes=DEFAULT_MAX_AGE_MINUTES)
        try:
            return timedelta(minutes=float(raw))
        except ValueError:
            logger.warning(
                "Invalid NETATMO_MAX_AGE_MINUTES value '{}'. Falling back to {} minutes.",
                raw,
                DEFAULT_MAX_AGE_MINUTES,
            )
            return timedelta(minutes=DEFAULT_MAX_AGE_MINUTES)

    def get_data(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        sensors: List[StationSensors] = None,
        variables: List[str] = None,
    ) -> DataFrame:
        """Fetches the most recent observations available for this station.

        Args:
            start_time (datetime | None): Ignored. The Netatmo public API only
                returns current values and cannot serve a time range.
            end_time (datetime | None): Ignored, for the same reason.
            sensors (list[StationSensors] | None): Ignored. Netatmo stations are
                addressed by MAC address rather than by sensor.
            variables (list[str] | None): Canonical variable names to keep. When
                None, every variable reported by the station is returned.

        Returns:
            DataFrame: Observations indexed by timezone-aware UTC timestamps, with
                canonical variable names as columns.

        Raises:
            ValueError: If no area response contained data for this station.
        """
        if start_time is not None or end_time is not None:
            logger.debug(
                "Netatmo returns current values only; ignoring the requested time "
                "range ({} to {}) for station {}.",
                start_time,
                end_time,
                self.config.sourceID,
            )

        df: DataFrame = pd.DataFrame()
        answered = False
        for area in self.AREAS:
            payload = self._get_area_data(area)
            if payload is None:
                continue
            answered = True
            df = self._format_data(payload)
            if not df.empty:
                break

        # Distinguish a broken API from a quiet station. A public station that has
        # not reported recently is entirely normal - roughly a quarter of them are
        # silent at any moment - so it must not be raised as an error, or every
        # pass fills the log with failures that need no action.
        if not answered:
            raise ValueError(
                f"No response from the NETATMO API for Sensor {self.config.sourceID}."
            )
        if df.empty:
            logger.info(
                f"Station {self.config.sourceID} reported nothing in the last "
                f"{self.max_age}; nothing to store this pass."
            )
            return df

        if variables:
            keep = [column for column in df.columns if column in set(variables)]
            dropped = set(df.columns) - set(keep)
            if dropped:
                logger.debug(
                    "Dropping variables not requested for {}: {}",
                    self.config.sourceID,
                    sorted(dropped),
                )
            df = df[keep]

        return df

    @classmethod
    def _get_area_data(
        cls, area: Tuple[float, float, float, float]
    ) -> Dict[str, Any] | None:
        """Fetches one bounding box, reusing a recent response when available.

        A single response covers every station in the area, so all configured
        stations of a cron pass share one HTTP request per area.

        Args:
            area (tuple): Bounding box as (lat_ne, lon_ne, lat_sw, lon_sw).

        Returns:
            dict | None: The decoded API payload, or None if the request failed.
        """
        now = datetime.now(UTC)
        cached = cls._response_cache.get(area)
        if cached is not None and now - cached[0] < cls.RESPONSE_TTL:
            logger.debug("Reusing cached NETATMO response for area {}.", area)
            return cached[1]

        lat_ne, lon_ne, lat_sw, lon_sw = area
        logger.info(
            f"Requesting data for NETATMO area {lat_ne}/{lon_ne} and {lat_sw}/{lon_sw}"
        )
        parameters = {
            "lat_ne": lat_ne,
            "lon_ne": lon_ne,
            "lat_sw": lat_sw,
            "lon_sw": lon_sw,
            "required_data": "temperature",
            # Sent as a string: requests would serialise Python False as "False",
            # which the API does not recognise.
            "filter": "false",
        }
        response = cls._get_shared_session().get(cls.DATA_ENDPOINT, params=parameters)
        payload = response.json()

        if payload.get("status", None) != "ok":
            logger.error(
                f"Error fetching data from NETATMO API for coordinates "
                f"{lat_ne}/{lon_ne} and {lat_sw}/{lon_sw}: "
                f"{payload.get('error', {}).get('message', 'No error message provided')}"
            )
            return None

        cls._response_cache[area] = (now, payload)
        return payload

    def _get_session(self) -> Session:
        """Returns an authenticated session shared by all instances.

        Returns:
            Session: A requests Session carrying the OAuth bearer token.
        """
        return self._get_shared_session()

    @classmethod
    def _get_shared_session(cls) -> Session:
        """Returns the shared session, authenticating only when missing or stale.

        Netatmo refresh tokens are single-use, so this must not be called once per
        station: each call rotates the stored token and invalidates the previous one.

        Returns:
            Session: A requests Session carrying the OAuth bearer token.

        Raises:
            Exception: If authentication against the Netatmo token endpoint fails.
        """
        with cls._session_lock:
            now = datetime.now(UTC)
            if (
                cls._shared_session is not None
                and cls._session_expiry is not None
                and now < cls._session_expiry
            ):
                return cls._shared_session

            client_id = get_secret("netatmo_client_id")
            client_secret = get_secret("netatmo_client_secret")

            # The refresh token rotates on every use, so the new one returned below
            # must be written back before the next authentication.
            secret_manager = LocalSecretManager()
            refresh_token = secret_manager.get_encrypted_secret(
                "netatmo_refresh_token",
                default=get_secret("netatmo_first_refresh_token"),
                create=True,
            )

            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }

            r = post(cls.TOKEN_ENDPOINT, data=data)
            if r.status_code != 200:
                raise Exception(
                    f"Authentication failed with status code {r.status_code}"
                )
            token_data = r.json()

            # Persist the rotated token immediately: if this is lost, the previous
            # token is already dead and the integration cannot authenticate again.
            secret_manager.update_secret(
                "netatmo_refresh_token", token_data["refresh_token"]
            )

            session = Session()
            session.headers.update(
                {
                    "accept": "application/json",
                    "Authorization": f"Bearer {token_data['access_token']}",
                }
            )

            # Expire a minute early so a request is never made with a token that
            # lapses in flight.
            lifetime = int(token_data.get("expires_in", 10800))
            cls._shared_session = session
            cls._session_expiry = now + timedelta(seconds=max(lifetime - 60, 60))
            logger.info(
                "Authenticated against NETATMO; access token valid for {} seconds.",
                lifetime,
            )
            return session

    def _format_data(self, data: Dict[str, Any]) -> DataFrame:
        """Extracts this station's measurements from an area response.

        The payload lists every public station in the area. Each station carries
        several modules, and the modules report on *independent* timestamps, so the
        resulting frame is sparse: each row holds the values of a single module and
        is empty elsewhere.

        Args:
            data (Dict[str, Any]): Raw JSON response from `getpublicdata`.

        Returns:
            DataFrame: Measurements indexed by timezone-aware UTC timestamps, with
                canonical variable names as columns. Empty if the station was absent
                from the response or reported nothing recent enough.
                Example:
                    | timestamp                 | air_temperature | wind_speed |
                    |---------------------------|-----------------|------------|
                    | 2026-09-17 09:20:00+00:00 | -3.2            | NaN        |
                    | 2026-09-17 09:22:00+00:00 | NaN             | 4.0        |
        """

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
            self._warn_if_moved(latitude, longitude)

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
            df.rename(self.RENAME_MAP, axis=1, inplace=True)
            unrenamed = set(df.columns) - set(self.RENAME_MAP.values())
            if unrenamed:
                logger.warning(
                    "Unknown NETATMO columns for {} were left unrenamed: {}. "
                    "Consider adding them to RENAME_MAP.",
                    self.config.sourceID,
                    sorted(unrenamed),
                )
            df.sort_index(inplace=True)
            # Drop readings already collected by the previous cron pass.
            df = df[df.index > datetime.now(UTC) - self.max_age]
            if df.empty:
                logger.warning(
                    "No recent data (last {}) available for station {}.",
                    self.max_age,
                    self.config.sourceID,
                )

        return df

    def _warn_if_moved(self, latitude: float | None, longitude: float | None) -> None:
        """Logs a warning when the reported position differs from the configured one.

        Args:
            latitude (float | None): Latitude reported by the API.
            longitude (float | None): Longitude reported by the API.
        """
        if latitude is None or longitude is None:
            return

        configured = self.config.coordinates
        # Equirectangular approximation: accurate well past the tolerance at the
        # latitudes involved, and far cheaper than a great-circle computation.
        metres_per_degree = 111_320.0
        d_lat = (latitude - configured.latitude) * metres_per_degree
        d_lon = (
            (longitude - configured.longitude)
            * metres_per_degree
            * math.cos(math.radians(configured.latitude))
        )
        distance = math.hypot(d_lat, d_lon)

        if distance > self.POSITION_TOLERANCE_M:
            logger.warning(
                f"Station {self.config.sourceID} may have changed location "
                f"(from {configured.latitude}, {configured.longitude} "
                f"to {latitude}, {longitude}; {distance:.0f} m apart)."
            )

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
