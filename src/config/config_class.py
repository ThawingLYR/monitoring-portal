"""
Station Configuration Models Module

This module defines the data models for station configurations, including:
- Station types and data providers (as Literal types).
- Position, markers, sensors, and full station configuration classes.
- Helper methods for generating map markers and popups for visualization.

Dependencies:
    - pydantic: For data validation and settings management.
    - folium: For map visualization (Icon, Marker, Popup, Html).
    - typing: For type hints (Dict, Literal).
    - datetime: For handling dates.
"""

from pydantic import BaseModel
from typing import Dict, Literal
from folium import Icon, Marker, Popup, Html
from datetime import datetime

# Define all possible types of stations.
StationType = Literal["boreholes", "aws"]

# Define all the data providers.
DataProvider = Literal["frost", "tilsig"]


class StationPosition(BaseModel):
    """
    Represents the geographic coordinates of a station.

    Attributes:
        latitude (float): The latitude of the station.
        longitude (float): The longitude of the station.
    """

    latitude: float
    longitude: float


class StationMarkers(BaseModel):
    """
    Defines the visual appearance of a station marker on a map.

    Attributes:
        color (str): The color of the marker. Defaults to "white".
        icon (str): The icon to display on the marker. Defaults to "cloud".
    """

    color: str = "white"
    icon: str = "cloud"


class StationSensors(BaseModel):
    """
    Represents a sensor associated with a station.

    Attributes:
        sensorID (str): Unique identifier for the sensor.
        startDate (datetime): The date when the sensor started recording data.
        endDate (datetime | None): The date when the sensor stopped recording data, if applicable.
        depth (Dict[int, float] | None): A dictionary mapping depth levels to values, if applicable.
    """

    sensorID: str
    startDate: datetime
    endDate: datetime | None = None
    depth: Dict[int, float] | None = None


class StationConfig(BaseModel):
    """
    Represents the configuration of a station, including its metadata, position, markers, and sensors.

    Attributes:
        sourceID (str): Unique identifier for the station's data source.
        name (str): Human-readable name of the station.
        startDate (str): The date when the station started operation (as a string).
        coordinates (StationPosition): Geographic coordinates of the station.
        sourceType (StationType): The type of the station (e.g., "boreholes", "aws").
        type (str): The type of data the station collects.
        owner (str): The owner of the station. Defaults to "Unknown".
        marker (StationMarkers): Visual marker settings for the station on a map.
        dataProvider (DataProvider): The provider of the station's data. Defaults to "frost".
        sensors (list[StationSensors]): List of sensors associated with the station.
    """

    sourceID: str
    name: str
    startDate: str
    coordinates: StationPosition
    sourceType: StationType
    type: str
    owner: str = "Unknown"
    marker: StationMarkers = StationMarkers()
    dataProvider: DataProvider = "frost"
    sensors: list[StationSensors] = []

    def get_icon(self) -> Icon:
        """
        Generates a folium `Icon` object for the station's marker.

        Returns:
            Icon: A folium Icon configured with the station's marker color and icon.
        """
        return Icon(color=self.marker.color, icon=self.marker.icon)

    def get_popup_html(self) -> str:
        """
        Generates HTML content for the station's popup on a map.

        Returns:
            str: HTML string containing station details (name, source ID, data type, start date, owner).
        """
        return f"""<body style="font-family:sans-serif; font-size:0.5em">
        <b>Name</b>: {self.name}<br>
        <b>Source ID</b>: {self.sourceID}<br>
        <b>Data</b>: {self.type}<br>
        <b>Since</b>: {self.startDate}<br>
        <b>Owner</b>: {self.owner}
        </body>"""

    def get_marker(self) -> Marker:
        """
        Generates a folium `Marker` object for the station.

        The marker is configured with:
        - The station's coordinates as its location.
        - A popup containing the station's details (HTML).
        - A tooltip displaying the station's name.
        - An icon based on the station's marker settings.

        Returns:
            Marker: A folium Marker ready to be added to a map.
        """
        return Marker(
            location=(self.coordinates.latitude, self.coordinates.longitude),
            popup=Popup(html=Html(self.get_popup_html()), max_width=500),
            tooltip=self.name,
            icon=self.get_icon(),
        )
