from src.config.config_class import StationConfig, StationType
from src.sensors.sensors_models import SensorData, Sensor

import pandas as pd


class SensorBorehole(Sensor):
    """
    Represents a borehole sensor, which is a specific type of sensor associated with borehole stations.

    Inherits from the generic `Sensor` class and can include additional attributes or methods specific to borehole sensors.
    """

    def fetch_data(self) -> pd.DataFrame:
        pass
