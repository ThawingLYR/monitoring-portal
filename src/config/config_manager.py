from src.config.config_class import StationConfig, StationType
from pydantic import BaseModel
from datetime import datetime


import os
import json

from loguru import logger


class ConfigFile(BaseModel):
    stations: list[StationConfig] = []
    last_updated: datetime | None = None


class ConfigManager:
    config_dict: dict[str, ConfigFile] = {}
    config_folder: str

    def __init__(self, config_folder: str = "config/"):
        self.config_folder = config_folder

        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)
            logger.warning(
                f"Config folder '{self.config_folder}' does not exist. Created new folder but it is empty and results in not working condiguration. Please add config files for each station type in the folder."
            )

        for station_type in StationType.__args__:
            self.config_dict[station_type] = ConfigFile()

    def load_config(self, station_type: StationType, timeout: int = 3600):
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
        if station_type not in self.config_dict:
            logger.error(f"Invalid station type: {station_type}")
            raise ValueError(f"Invalid station type: {station_type}")

        self.load_config(station_type)

        stations = self.config_dict[station_type].stations
        for key, value in query.items():
            stations = [s for s in stations if getattr(s, key) == value]
        return stations
