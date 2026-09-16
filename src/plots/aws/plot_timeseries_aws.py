"""
AWS Time Series Figure

Renders the recent history of an automatic weather station as stacked panels
sharing a time axis.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.plots.figure_models import Figure
from src.utils.variable_columns import columns_for_variable

# How each variable is condensed when resampling. State variables are averaged;
# gusts are maxima, and averaging them would erase the peak that makes them
# interesting. The rainfall variables are *rolling accumulations* already, so they
# are also reduced with max - summing them would count the same rain many times.
AGGREGATIONS: dict[str, str] = {
    "air_temperature": "mean",
    "relative_humidity": "mean",
    "air_pressure": "mean",
    "wind_speed": "mean",
    "wind_speed_of_gust": "max",
    "rainfall_amount_wrt_60min": "max",
    "rainfall_amount_wrt_24h": "max",
}

# Panels, in display order. Variables absent from a station are skipped, and a
# panel with no data at all is not drawn, so a station without a wind module
# yields a shorter figure rather than empty axes.
PANELS: list[dict] = [
    {
        "axis_title": "Temperature [°C]",
        "primary": [("air_temperature", "Air temperature", "lines")],
        "secondary": [],
    },
    {
        "axis_title": "Humidity [%]",
        "secondary_axis_title": "Pressure [hPa]",
        "primary": [("relative_humidity", "Relative humidity", "lines")],
        "secondary": [("air_pressure", "Air pressure", "lines")],
    },
    {
        "axis_title": "Wind [m/s]",
        "primary": [
            ("wind_speed", "Wind speed", "lines"),
            ("wind_speed_of_gust", "Wind gust", "lines"),
        ],
        "secondary": [],
    },
    {
        "axis_title": "Rain [mm]",
        "primary": [("rainfall_amount_wrt_60min", "Rain (60 min)", "bar")],
        "secondary": [],
    },
]


class PlotTimeseriesAWS(Figure):
    """Stacked time series of the variables an AWS station reports.

    Attributes:
        name (str): Display name of the figure.
        resample_rule (str): Pandas offset alias used to condense the raw data.
        window_days (int): Number of days of history shown.
    """

    name: str = "AWS time series"
    resample_rule: str = "1h"
    window_days: int = 30

    def create_figure(self, sensor) -> go.Figure:
        """Builds the figure for one station.

        Args:
            sensor (Sensor): The sensor whose stored data is plotted.

        Returns:
            go.Figure: The stacked time series, or an empty figure carrying an
                explanatory title when the station has no data yet.
        """
        data = sensor.get_data()
        if data is None or data.empty:
            return self._empty_figure(f"{sensor.config.name}: no data recorded yet")

        data = data.sort_index()
        window_start = data.index.max() - pd.Timedelta(days=self.window_days)
        data = data[data.index >= window_start]

        aggregated = self._aggregate(data)
        panels = self._select_panels(aggregated)
        if not panels:
            return self._empty_figure(
                f"{sensor.config.name}: no plottable variables recorded"
            )

        figure = make_subplots(
            rows=len(panels),
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            specs=[[{"secondary_y": bool(panel["secondary"])}] for panel in panels],
        )

        for row, panel in enumerate(panels, start=1):
            for column, label, mode in panel["primary"]:
                self._add_trace(figure, aggregated[column], label, mode, row, False)
            for column, label, mode in panel["secondary"]:
                self._add_trace(figure, aggregated[column], label, mode, row, True)

            figure.update_yaxes(
                title_text=panel["axis_title"], row=row, col=1, secondary_y=False
            )
            if panel["secondary"]:
                figure.update_yaxes(
                    title_text=panel.get("secondary_axis_title", ""),
                    row=row,
                    col=1,
                    secondary_y=True,
                )

        figure.update_xaxes(title_text="Time [UTC]", row=len(panels), col=1)
        figure.update_layout(
            title=f"{sensor.config.name} weather station time series",
            height=220 * len(panels) + 120,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        return figure

    def _aggregate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Condenses the raw frame onto a regular time axis.

        The stored frame is sparse: providers write one row per hardware module,
        so each row carries only that module's columns. Resampling skips missing
        values per column, which fills the gaps without inventing data. Forward
        filling the raw frame first would instead smear a stale wind reading
        across every temperature row.

        Args:
            data (pd.DataFrame): The raw stored observations.

        Returns:
            pd.DataFrame: One column per known variable, on a regular time axis.
        """
        aggregated = pd.DataFrame()
        resampler = data.resample(self.resample_rule)

        for variable, how in AGGREGATIONS.items():
            for column in columns_for_variable(data, variable):
                series = resampler[column].agg(how)
                if series.notna().any():
                    aggregated[variable] = series

        return aggregated

    @staticmethod
    def _select_panels(aggregated: pd.DataFrame) -> list[dict]:
        """Keeps the panels that have at least one populated series.

        Args:
            aggregated (pd.DataFrame): The condensed observations.

        Returns:
            list[dict]: Panel definitions restricted to available variables.
        """
        panels = []
        for panel in PANELS:
            primary = [s for s in panel["primary"] if s[0] in aggregated.columns]
            secondary = [s for s in panel["secondary"] if s[0] in aggregated.columns]
            if primary or secondary:
                panels.append({**panel, "primary": primary, "secondary": secondary})
        return panels

    @staticmethod
    def _add_trace(
        figure: go.Figure,
        series: pd.Series,
        label: str,
        mode: str,
        row: int,
        secondary_y: bool,
    ) -> None:
        """Adds one series to a panel.

        Args:
            figure (go.Figure): The figure under construction.
            series (pd.Series): The values to plot.
            label (str): Legend entry.
            mode (str): Either "bar" or a Plotly scatter mode such as "lines".
            row (int): Subplot row, 1-indexed.
            secondary_y (bool): Whether to attach the trace to the right-hand axis.
        """
        if mode == "bar":
            trace = go.Bar(x=series.index, y=series, name=label)
        else:
            trace = go.Scatter(x=series.index, y=series, mode=mode, name=label)
        figure.add_trace(trace, row=row, col=1, secondary_y=secondary_y)

    @staticmethod
    def _empty_figure(title: str) -> go.Figure:
        """Builds a placeholder figure for a station with nothing to show.

        Args:
            title (str): Title explaining why the figure is empty.

        Returns:
            go.Figure: An empty figure carrying the message.
        """
        figure = go.Figure()
        figure.update_layout(title=title, xaxis_title="Time [UTC]")
        return figure
