# src/plots/latest_measurements.py
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import ClassVar, Optional, Tuple
from src.plots.figure_models import Figure


class LatestMeasurementFigureBase(Figure):
    """
    Base class that returns a small Plotly figure with:
      Line 1: display name
      Line 2: large bold value + unit
      Line 3: timestamp

    Subclasses should set the class attributes:
      column (str): dataframe column name
      display_name (str): friendly label to show
      unit (str): unit string (optional)
    """

    # Mark these as ClassVar so Pydantic won't treat them as model fields
    column: ClassVar[str] = ""
    display_name: ClassVar[str] = "Variable"
    unit: ClassVar[str] = ""

    def _format_timestamp(self, ts: pd.Timestamp) -> str:
        if ts is None or pd.isna(ts):
            return "—"
        if hasattr(ts, "tz") and ts.tz is not None:
            return ts.strftime("%Y-%m-%d %H:%M:%S %Z")
        return ts.strftime("%Y-%m-%d %H:%M:%S UTC")

    def _format_value(self, val) -> str:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return "No data"
        # default formatting: floats 2 dp, ints raw
        if isinstance(val, float):
            return f"{val:.2f}"
        return str(val)

    def _add_three_lines(
        self,
        fig: go.Figure,
        title: str,
        value: str,
        ts: str,
        x: float = 0.5,
        title_y: float = 0.57,
        value_y: float = 0.46,
        ts_y: float = 0.33,
    ) -> None:
        """
        Helper to add three stacked annotations to fig at horizontal position x.
        y positions are in paper coordinates.
        """
        # Title (smaller)
        fig.add_annotation(
            text=title,
            xref="paper",
            yref="paper",
            x=x,
            y=title_y,
            showarrow=False,
            font=dict(size=30, color="black", family="Arial"),
            align="center",
        )
        # Big value
        fig.add_annotation(
            text=value,
            xref="paper",
            yref="paper",
            x=x,
            y=value_y,
            showarrow=False,
            font=dict(size=40, color="black", family="Arial"),
            align="center",
        )
        # Timestamp (small, gray)
        fig.add_annotation(
            text=ts,
            xref="paper",
            yref="paper",
            x=x,
            y=ts_y,
            showarrow=False,
            font=dict(size=24, color="gray", family="Arial"),
            align="center",
        )

    def _empty_source_figure(self, message: str) -> go.Figure:
        fig = go.Figure()
        # Single centered message
        fig.add_annotation(
            text=self.display_name + "<br>" + message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=30, color="black", family="Arial"),
            align="center",
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            margin=dict(l=8, r=8, t=8, b=8),
        )
        return fig

    def create_figure(self, sensor) -> go.Figure:
        fig = go.Figure()

        data = sensor.get_data()
        if data is None or not isinstance(data, pd.DataFrame):
            return self._empty_source_figure("No data source")

        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            try:
                data.index = pd.to_datetime(data.index)
            except Exception:
                # if coercion fails, still continue; series selection will handle emptiness
                pass

        # If column missing
        if self.column not in data.columns:
            return self._empty_source_figure(f"Column not found ({self.column})")

        # Pick latest non-null
        series = data[self.column].dropna()
        if series.empty:
            return self._empty_source_figure("No data")

        last_idx = series.index.max()
        last_val = series.loc[last_idx]
        try:
            last_ts = pd.to_datetime(last_idx)
        except Exception:
            last_ts = last_idx

        value_str = self._format_value(last_val)
        ts_str = self._format_timestamp(last_ts)
        unit_str = f" {self.unit}" if self.unit else ""

        # Add three annotations centered
        self._add_three_lines(
            fig,
            title=self.display_name,
            value=f"{value_str}{unit_str}",
            ts=ts_str,
            x=0.5,
            title_y=0.57,
            value_y=0.46,
            ts_y=0.33,
        )

        # hide axes and compact margins
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            margin=dict(l=8, r=8, t=8, b=8),
        )
        return fig


# -------------------------
# Per-variable subclasses
# -------------------------
class AirTemperatureFigure(LatestMeasurementFigureBase):
    column: ClassVar[str] = "air_temperature_degC"
    display_name: ClassVar[str] = "Air temperature"
    unit: ClassVar[str] = "°C"


class WindDirectionFigure(LatestMeasurementFigureBase):
    column: ClassVar[str] = "wind_direction_deg"
    display_name: ClassVar[str] = "Wind direction"
    unit: ClassVar[str] = "°"


class RelativeHumidityFigure(LatestMeasurementFigureBase):
    column: ClassVar[str] = "relative_humidity"
    display_name: ClassVar[str] = "Relative humidity"
    unit: ClassVar[str] = "-"


class AtmosphericPressureFigure(LatestMeasurementFigureBase):
    column: ClassVar[str] = "atmospheric_pressure_kPa"
    display_name: ClassVar[str] = "Atmospheric pressure"
    unit: ClassVar[str] = "kPa"


class VaporPressureFigure(LatestMeasurementFigureBase):
    column: ClassVar[str] = "vapor_pressure_kPa"
    display_name: ClassVar[str] = "Vapor pressure"
    unit: ClassVar[str] = "kPa"


# -------------------------
# Combined wind speeds figure
# -------------------------


class WindSpeedsCombinedFigure(LatestMeasurementFigureBase):
    """
    Stacked Avg + Gust blocks using LatestMeasurementFigureBase._add_three_lines.
    """

    avg_col: ClassVar[str] = "wind_speed_avg_ms"
    gust_col: ClassVar[str] = "wind_gust_speed_ms"
    display_name: ClassVar[str] = "Wind speeds"
    unit: ClassVar[str] = "m/s"

    # layout tuning (paper coordinates)
    title_y: ClassVar[float] = 0.92
    # Avg block y-coordinates (title, value, ts)
    avg_title_y: ClassVar[float] = 0.70
    avg_value_y: ClassVar[float] = 0.58
    avg_ts_y: ClassVar[float] = 0.46
    # Gap to next block (you can lower/raise these)
    gust_title_y: ClassVar[float] = 0.34
    gust_value_y: ClassVar[float] = 0.22
    gust_ts_y: ClassVar[float] = 0.10

    # increase height to avoid clipping with large fonts
    fig_height: ClassVar[int] = 420

    def _latest_for_col(
        self, data: pd.DataFrame, col: str
    ) -> Tuple[Optional[str], Optional[str]]:
        if col not in data.columns:
            return None, f"({col})"
        s = data[col].dropna()
        if s.empty:
            return None, "—"
        last_idx = s.index.max()
        last_val = s.loc[last_idx]
        try:
            last_ts = pd.to_datetime(last_idx)
        except Exception:
            last_ts = last_idx
        return self._format_value(last_val), self._format_timestamp(last_ts)

    def create_figure(self, sensor) -> go.Figure:
        fig = go.Figure()
        data = sensor.get_data()
        if data is None or not isinstance(data, pd.DataFrame):
            return self._empty_source_figure("No data source")

        # ensure DateTimeIndex
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            try:
                data.index = pd.to_datetime(data.index)
            except Exception:
                pass

        avg_val, avg_ts = self._latest_for_col(data, self.avg_col)
        gust_val, gust_ts = self._latest_for_col(data, self.gust_col)

        if avg_val is None and gust_val is None:
            return self._empty_source_figure("No wind speed data")

        # Title
        fig.add_annotation(
            text=self.display_name,
            xref="paper",
            yref="paper",
            x=0.5,
            y=self.title_y,
            showarrow=False,
            font=dict(size=30, color="black", family="Arial"),
            align="center",
        )

        unit_str = f" {self.unit}" if self.unit else ""

        # Avg block (centered horizontally) using base helper
        avg_value = avg_val if avg_val is not None else "No data"
        avg_ts_str = avg_ts if avg_ts is not None else "—"
        self._add_three_lines(
            fig,
            title="Avg",
            value=f"{avg_value}{unit_str}" if avg_val is not None else avg_value,
            ts=avg_ts_str,
            x=0.5,
            title_y=self.avg_title_y,
            value_y=self.avg_value_y,
            ts_y=self.avg_ts_y,
        )

        # Gust block (stacked below avg)
        gust_value = gust_val if gust_val is not None else "No data"
        gust_ts_str = gust_ts if gust_ts is not None else "—"
        self._add_three_lines(
            fig,
            title="Gust",
            value=f"{gust_value}{unit_str}" if gust_val is not None else gust_value,
            ts=gust_ts_str,
            x=0.5,
            title_y=self.gust_title_y,
            value_y=self.gust_value_y,
            ts_y=self.gust_ts_y,
        )

        # hide axes and set larger height to accommodate big fonts
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            margin=dict(l=8, r=8, t=8, b=8),
            height=self.fig_height,
        )
        return fig
