from src.config.config_manager import ConfigManager
from src.sensors.borehole import SensorBorehole

from src.plots.boreholes import all_boreholes_figures

from dotenv import load_dotenv

load_dotenv()

# Prepare the data for all boreholes and generate the figures
config_manager = ConfigManager()
config_manager.load_config("boreholes")
configs = config_manager.get_stations("boreholes")
for config in configs:
    sensor = SensorBorehole(config=config)
    sensor.update_latest_data()
    for plot in all_boreholes_figures:
        sensor.prepare_figure(plot)
