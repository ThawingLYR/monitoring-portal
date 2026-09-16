"""
Scheduled data collection job.

Fetches the latest observations for every configured station and pre-renders the
figures the Streamlit app displays. The app itself never calls a provider API and
mounts the data and figure volumes read-only, so everything it shows is produced
here.

Run this on a schedule. For Netatmo the interval must match
NETATMO_MAX_AGE_MINUTES, since that source keeps only readings newer than that
window (see src/datasource/netatmo.md).
"""

from loguru import logger

from src.config.config_manager import ConfigManager
from src.plots.aws import all_aws_figures
from src.plots.boreholes import all_boreholes_figures
from src.sensors.aws import SensorAWS
from src.sensors.borehole import SensorBorehole

# from dotenv import load_dotenv

# load_dotenv()

# A single manager is reused throughout: its configuration cache is a class
# attribute that a second instantiation would reset.
config_manager = ConfigManager()


def update_stations(station_type, sensor_class, figures):
    """Updates every station of one type and pre-renders its figures.

    Each station is isolated so that one unreachable provider or malformed
    response cannot abort the run for the remaining stations.

    Args:
        station_type (StationType): The station type to process.
        sensor_class (Type[Sensor]): Sensor class to instantiate per station.
        figures (list[Type[Figure]]): Figure classes to pre-render.
    """
    config_manager.load_config(station_type)
    configs = config_manager.get_stations(station_type)
    logger.info(f"Updating {len(configs)} {station_type} stations.")

    for config in configs:
        try:
            sensor = sensor_class(config=config)
            sensor.update_latest_data()
            for plot in figures:
                sensor.prepare_figure(plot)
        except Exception as error:
            logger.error(
                f"Failed to update {station_type} station {config.sourceID}: {error}"
            )


# Prepare the data for all boreholes and generate the figures
update_stations("boreholes", SensorBorehole, all_boreholes_figures)

# Prepare the data for all aws stations and generate the figures
update_stations("aws", SensorAWS, all_aws_figures)
