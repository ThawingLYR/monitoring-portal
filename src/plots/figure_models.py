"""
Figure Base Class Module

This module defines the abstract base class for creating figures from station and sensor data.
Subclasses must implement the `create_figure` method to generate specific visualizations.
"""

from pydantic import BaseModel
from abc import abstractmethod, ABC
from src.sensors.sensors_models import Sensor
from plotly.graph_objects import Figure as goFigure


class Figure(BaseModel, ABC):
    """
    Abstract base class for generating figures from station and sensor data.

    This class serves as a template for all figure-generating classes.
    Subclasses must implement the `create_figure` method to define how the figure is created.

    Attributes:
        name (str | None): Optional name for the figure. Defaults to None.
    """

    name: str | None = None

    @abstractmethod
    def create_figure(self, sensor: Sensor) -> goFigure:
        """
        Abstract method to create a figure based on the provided station configuration and sensor data.

        Subclasses must implement this method to define the specific visualization logic.

        The subclass naming must be such than there is no duplicate.

        Args:
            config (StationConfig): The configuration of the station associated with the figure.
            data (SensorData): The sensor data to be visualized in the figure.

        Returns:
            The type of the returned figure should be a Plotly go.Figure.
        """
        pass
