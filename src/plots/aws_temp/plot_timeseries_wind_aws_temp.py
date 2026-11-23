import pandas as pd
import plotly.graph_objects as go
from src.plots.figure_models import Figure


class PlotTimeserieswindAWStemp(Figure):
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

        # --- Required columns ---
        gust_col = "wind_gust_speed_ms"
        avg_col = "wind_speed_avg_ms"
        missing = [c for c in (gust_col, avg_col) if c not in data_24h.columns]
        if missing:
            raise KeyError(
                f"Missing required column(s) in DataFrame: {', '.join(missing)}"
            )

        gust = data_24h[gust_col]
        avg = data_24h[avg_col]

        # If both empty, return an annotated empty figure
        if gust.empty and avg.empty:
            fig.update_layout(
                title=dict(text="Wind speed time series (no data last 24 h)", x=0.5),
                xaxis_title="Date and time",
                yaxis_title="Wind speed [m/s]",
            )
            fig.add_annotation(
                text="No wind data in the last 24 hours",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        # --- Hover templates ---
        gust_hover = "Gust: %{y:.2f} m/s<br>Date: %{x|%d %b %Y %H:%M:%S}<extra></extra>"
        avg_hover = "Avg: %{y:.2f} m/s<br>Date: %{x|%d %b %Y %H:%M:%S}<extra></extra>"

        # --- Add traces (only add trace if not empty) ---
        if not avg.empty:
            fig.add_trace(
                go.Scatter(
                    x=avg.index,
                    y=avg.values,
                    mode="lines",
                    name="Wind speed (avg.)",
                    line=dict(width=2, color="royalblue"),
                    hovertemplate=avg_hover,
                )
            )

        if not gust.empty:
            fig.add_trace(
                go.Scatter(
                    x=gust.index,
                    y=gust.values,
                    mode="lines",
                    name="Wind gust speed",
                    line=dict(width=1.5, dash="dash", color="firebrick"),
                    hovertemplate=gust_hover,
                )
            )

        # --- Compute x-axis range robustly ---
        x_candidates = [last24]  # ensure the range covers the last-24h window
        if not avg.empty:
            x_candidates.append(avg.index.min())
            x_candidates.append(avg.index.max())
        if not gust.empty:
            x_candidates.append(gust.index.min())
            x_candidates.append(gust.index.max())
        x_candidates.append(now)

        x_min = min(x_candidates)
        x_max = max(x_candidates)

        fig.update_layout(
            title=dict(
                text="Wind speed (avg.) and wind gust speed time series (last 24 hours) in UTC",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Date and time",
            yaxis_title="Wind speed [m/s]",
            xaxis_range=[x_min, x_max],
            hovermode="x unified",
            margin=dict(l=40, r=20, t=60, b=40),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            showlegend=True,
        )

        return fig
