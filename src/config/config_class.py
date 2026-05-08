from pydantic import BaseModel
from typing import Dict, Literal

from folium import Icon, Marker, Popup, Html

from datetime import datetime


# Define all possible type of stations.
StationType = Literal["boreholes", "aws"]

# Define all the data providers
DataProvider = Literal["frost", "tilsig"]


class StationPosition(BaseModel):
    latitude: float
    longitude: float


class StationMarkers(BaseModel):
    color: str = "white"
    icon: str = "cloud"


class StationSensors(BaseModel):
    sensorID: str
    startDate: datetime
    endDate: datetime | None = None
    depth: Dict[int, float] | None = None


class StationConfig(BaseModel):
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

    def get_icon(self):
        return Icon(color=self.marker.color, icon=self.marker.icon)

    def get_popup_html(self):
        return f"""<body style="font-family:sans-serif; font-size:0.5em">
        <b>Name</b>: {self.name}<br>
        <b>Source ID</b>: {self.sourceID}<br>
        <b>Data</b>: {self.type}<br>
        <b>Since</b>: {self.startDate}<br>
        <b>Owner</b>: {self.owner}
        </body>"""

    def get_marker(self):
        return Marker(
            location=(self.coordinates.latitude, self.coordinates.longitude),
            popup=Popup(html=Html(self.get_popup_html()), max_width=500),
            tooltip=self.name,
            icon=self.get_icon(),
        )
