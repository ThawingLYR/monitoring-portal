from src.config.config_manager import ConfigManager
from src.sensors.borehole import SensorBorehole

from dotenv import load_dotenv

load_dotenv()


config_manager = ConfigManager()
config_manager.load_config("boreholes")
configs = config_manager.get_stations("boreholes", query={"dataProvider": "tilsig"})
for config in configs:
    sensor = SensorBorehole(config=config)
    sensor.update_latest_data()
