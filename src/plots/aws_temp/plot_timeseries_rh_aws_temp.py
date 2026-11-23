import pandas as pd
import plotly.graph_objects as go
from src.plots.figure_models import Figure


class PlotTimeseriesRhAWStemp(Figure):
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

        # --- Extract the relative humidity column ---
        # adjust column name if different
        rh_col = "relative_humidity"
        if rh_col not in data_24h.columns:
            # fall back to original data (in case of index-only selection)
            raise KeyError(
                f"Relative humidity column '{rh_col}' not found in DataFrame"
            )

        data_rh = data_24h[rh_col]

        # If empty, add an annotation and return an empty time series
        if data_rh.empty:
            fig.update_layout(
                title=dict(
                    text="Relative humidity time series (no data last 24 h)", x=0.5
                ),
                xaxis_title="Date and time",
                yaxis_title="Relative humidity [-]",
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
        hover_template = "RH: %{y:.2f}<br>Date: %{x|%d %b %Y %H:%M:%S}<extra></extra>"

        fig.add_trace(
            go.Scatter(
                x=data_rh.index,
                y=data_rh.values,
                mode="lines",
                name="Relative humidity",
                showlegend=True,
                line=dict(width=2),
                hovertemplate=hover_template,
            )
        )

        # --- Add titles and labels etc. ---
        fig.update_layout(
            title=dict(
                text="Relative humidity time series (last 24 hours) in UTC",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Date and time",
            yaxis_title="Relative humidity [-]",
            # set xaxis_range to the last 24 hours window (or the data extent if narrower)
            xaxis_range=[
                min(last24, data_rh.index.min()),
                max(now, data_rh.index.max()),
            ],
            showlegend=False,
            hovermode="x unified",
            margin=dict(l=40, r=20, t=60, b=40),
        )

        return fig
