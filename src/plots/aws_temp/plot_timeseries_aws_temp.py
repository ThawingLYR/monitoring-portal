import pandas as pd
import plotly.graph_objects as go
from src.plots.figure_models import Figure


class PlotTimeseriesAWStemp(Figure):
    def create_figure(self, sensor):
        fig = go.Figure()
        data = sensor.get_data()  # expects a DataFrame with DatetimeIndex

        # --- Ensure datetime index ---
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data.index = pd.to_datetime(data.index)

        # --- Determine "now" in the same timezone as the index ---
        if data.index.tz is not None:
            now = pd.Timestamp.now(tz=data.index.tz)
        else:
            now = pd.Timestamp.now(tz=None)

        last24 = now - pd.Timedelta(hours=24)

        # --- Filter to last 24 hours ---
        data_24h = data.loc[data.index >= last24]

        # --- Extract the temperature column ---
        # adjust column name if different
        temp_col = "air_temperature_degC"
        if temp_col not in data_24h.columns:
            # fall back to original data (in case of index-only selection)
            raise KeyError(f"Temperature column '{temp_col}' not found in DataFrame")

        data_temperature = data_24h[temp_col]

        # If empty, add an annotation and return an empty time series
        if data_temperature.empty:
            fig.update_layout(
                title=dict(
                    text="Air temperature time series (no data last 24 h)", x=0.5
                ),
                xaxis_title="Date and time",
                yaxis_title="Temperature [°C]",
            )
            fig.add_annotation(
                text="No data in the last 24 hours",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        # --- Add data to plot ---
        hover_template = (
            "Temp: %{y:.2f} °C<br>Date: %{x|%d %b %Y %H:%M:%S}<extra></extra>"
        )

        fig.add_trace(
            go.Scatter(
                x=data_temperature.index,
                y=data_temperature.values,
                mode="lines",
                name="Air temperature",
                showlegend=True,
                line=dict(width=2),
                hovertemplate=hover_template,
            )
        )

        # --- Add titles and labels etc. ---
        fig.update_layout(
            title=dict(
                text="Air temperature time series (last 24 hours) in UTC",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Date and time",
            yaxis_title="Temperature [°C]",
            # set xaxis_range to the last 24 hours window (or the data extent if narrower)
            xaxis_range=[
                min(last24, data_temperature.index.min()),
                max(now, data_temperature.index.max()),
            ],
            showlegend=False,
            hovermode="x unified",
            margin=dict(l=40, r=20, t=60, b=40),
        )

        return fig
