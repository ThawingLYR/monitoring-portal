"""
Configuration Manager Module

This module provides classes and utilities for managing station configurations.
It supports loading, caching, and querying station configurations from JSON files,
organized by station type. The `ConfigManager` class handles the lifecycle of these configurations,
including lazy loading, caching, and filtering based on user queries.

Dependencies:
    - pydantic: For data validation and settings management.
    - loguru: For structured logging.
"""

from src.config.config_class import StationConfig, StationType
from pydantic import BaseModel
from datetime import datetime
import os
import json
from loguru import logger


class ConfigFile(BaseModel):
    """
    Represents a configuration file for a specific station type.

    Attributes:
        stations (list[StationConfig]): List of station configurations for this type.
        last_updated (datetime | None): Timestamp of the last time the config was loaded.
    """

    stations: list[StationConfig] = []
    last_updated: datetime | None = None


class ConfigManager:
    """
    Manages the loading, caching, and querying of station configurations.

    The manager organizes configurations by `StationType` and supports:
    - Automatic creation of the config folder if missing.
    - Lazy loading and caching of configurations with a configurable timeout.
    - Filtering stations based on arbitrary attributes.

    Class Attributes:
        config_dict (dict[str, ConfigFile]): Maps station types to their configurations.
        config_folder (str): Path to the directory containing config files.

    Args:
        config_folder (str): Path to the config folder. Defaults to "config/".
    """

    config_dict: dict[str, ConfigFile] = {}
    config_folder: str

    def __init__(self, config_folder: str = "config/"):
        """
        Initializes the ConfigManager.

        Creates the config folder if it does not exist and initializes an empty
        `ConfigFile` for each `StationType`. Logs a warning if the folder is empty.
        """
        self.config_folder = config_folder

        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)
            logger.warning(
                f"Config folder '{self.config_folder}' does not exist. "
                "Created new folder but it is empty and results in non-working configuration. "
                "Please add config files for each station type in the folder."
            )

        for station_type in StationType.__args__:
            self.config_dict[station_type] = ConfigFile()

    def load_config(self, station_type: StationType, timeout: int = 3600) -> None:
        """
        Loads or reloads the configuration for a specific station type if outdated.

        The configuration is cached and only reloaded if:
        - It has never been loaded before.
        - The time since the last load exceeds the `timeout` (in seconds).

        Args:
            station_type (StationType): The type of station to load the config for.
            timeout (int): Maximum age (in seconds) for the cached config. Defaults to 3600 (1 hour).

        Raises:
            ValueError: If the station type is invalid.
            FileNotFoundError: If the config file for the station type is missing.
            Exception: For any other error during loading.

        Notes:
            The config file for each station type must be named `{station_type}.json`
            and located in the `config_folder`.
        """
        if station_type not in self.config_dict:
            logger.error(f"Invalid station type: {station_type}")
            raise ValueError(f"Invalid station type: {station_type}")

        if self.config_dict[station_type].last_updated is not None:
            elapsed_time = (
                datetime.now() - self.config_dict[station_type].last_updated
            ).total_seconds()
            if elapsed_time < timeout:
                return
            else:
                logger.info(
                    f"Config for {station_type} is outdated (last updated {elapsed_time:.2f} seconds ago). Reloading config."
                )

        try:
            path = os.path.join(self.config_folder, f"{station_type}.json")
            with open(path, "r") as f:
                data = json.load(f)
                for station in data:
                    self.config_dict[station_type].stations.append(
                        StationConfig.model_validate_json(json.dumps(station))
                    )
            self.config_dict[station_type].last_updated = datetime.now()
            logger.info(f"Config for {station_type} loaded successfully.")
        except FileNotFoundError:
            logger.error(f"Config file for {station_type} not found.")
            raise
        except Exception as e:
            logger.error(f"Error loading config file for {station_type}: {e}")
            raise

    def get_stations(
        self, station_type: StationType, query: dict = {}
    ) -> list[StationConfig]:
        """
        Retrieves stations of a specific type, optionally filtered by a query.

        Args:
            station_type (StationType): The type of station to query.
            query (dict): A dictionary of attribute-value pairs to filter stations.
                         Only stations with matching attributes are returned.
                         Example: `{"attribute_name": "desired_value"}`.

        Returns:
            list[StationConfig]: A list of station configurations matching the query.

        Raises:
            ValueError: If the station type is invalid.

        Example:
            >>> manager = ConfigManager()
            >>> stations = manager.get_stations(StationType.WEATHER, {"region": "Europe"})
        """
        if station_type not in self.config_dict:
            logger.error(f"Invalid station type: {station_type}")
            raise ValueError(f"Invalid station type: {station_type}")

        self.load_config(station_type)

        stations = self.config_dict[station_type].stations
        for key, value in query.items():
            stations = [s for s in stations if getattr(s, key) == value]
        return stations
