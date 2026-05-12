from src.config.config_class import StationConfig, StationType
from src.sensors.sensors_models import SensorData, Sensor

from src.datasource import DataSource

from datetime import datetime, timedelta

import pandas as pd
import re
import numpy as np

from loguru import logger


class SensorBorehole(Sensor):
    """
    Represents a borehole sensor, which is a specific type of sensor associated with borehole stations.

    Inherits from the generic `Sensor` class and can include additional attributes or methods specific to borehole sensors.
    """

    def fetch_data(self) -> pd.DataFrame:

        datasource = DataSource.create(self.config.dataProvider)

        if self.data.data is None:
            start = datetime.now - timedelta(days=3650)
        else:
            start = self.data.data.index.max().compute()

        end = datetime.now + timedelta(days=1)

        df = datasource.get_data(
            start_time=start,
            end_time=end,
            sensors=self.config.sensors,
            variables=["soil_temperature"],
        )

        dim_name = [re.sub(r"\d+", "", c.split("-")[1]) for c in df.columns]

        if len(np.unique(dim_name)) != 1:
            logger.error(
                "Something bad happend in the processing, can not handle mutliple extra dimentions for boreholes"
            )
            raise ValueError(
                "Something bad happend in the processing, can not handle mutliple extra dimentions for boreholes"
            )

        df.columns = df.columns.str.split("-", expand=True)
        level0 = df.columns.get_level_values(0)
        level1 = df.columns.get_level_values(1).str.extract(r"(\d+)")[0].astype(int)

        df.columns = pd.MultiIndex.from_arrays(
            [level0, level1], names=[df.columns.names[0], dim_name[0]]
        )

        return df
