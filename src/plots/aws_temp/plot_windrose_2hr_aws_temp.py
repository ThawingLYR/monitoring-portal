import pandas as pd
import numpy as np
import plotly.graph_objects as go
from src.plots.figure_models import Figure


class PlotWindrose2hAWStemp(Figure):
    def create_figure(self, sensor):
        fig = go.Figure()
        data = sensor.get_data()  # expects a DataFrame with DatetimeIndex

        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data.index = pd.to_datetime(data.index)

        # Determine now and last 2h (timezone-aware if index is)
        if data.index.tz is not None:
            now = pd.Timestamp.now(tz=data.index.tz)
        else:
            now = pd.Timestamp.now(tz=None)
        last2 = now - pd.Timedelta(hours=2)

        # Filter to last 2 hours
        data_2h = data.loc[data.index >= last2]

        # Required columns
        speed_col = "wind_speed_avg_ms"
        dir_col = "wind_direction_deg"
        missing = [c for c in (speed_col, dir_col) if c not in data_2h.columns]
        if missing:
            raise KeyError(
                f"Missing required column(s) in DataFrame: {', '.join(missing)}"
            )

        speeds = data_2h[speed_col].dropna()
        dirs = data_2h[dir_col].dropna()

        if speeds.empty or dirs.empty:
            fig.update_layout(
                title=dict(text="Windrose (no data last 2 h)", x=0.5, xanchor="center"),
            )
            fig.add_annotation(
                text="No wind data in the last 2 hours",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        df = pd.DataFrame({speed_col: speeds, dir_col: dirs}).dropna()

        # Speed categories
        speed_bins = [0.0, 5.0, 10.0, 15.0, np.inf]
        speed_labels = ["0-5 m/s", "5-10 m/s", "10-15 m/s", ">15 m/s"]
        df["speed_cat"] = pd.cut(
            df[speed_col], bins=speed_bins, labels=speed_labels, right=False
        )

        # Define sectors by index (0..15), compute center angles and compass labels
        n_sectors = 16
        sector_width = 360.0 / n_sectors  # 22.5

        # normalize directions to [0,360)
        df["dir_norm"] = df[dir_col] % 360.0

        # Compute sector index by rounding to the nearest sector center (0, 22.5, 45, ...)
        # We divide by sector_width and round to nearest integer, then mod by n_sectors.
        df["sector_idx"] = (
            np.round(df["dir_norm"] / sector_width).astype(int) % n_sectors
        )

        # Sector centers (angles) set to multiples of sector_width: 0, 22.5, 45, ...
        sector_centers = [i * sector_width for i in range(n_sectors)]

        # Standard 16-point compass labels starting at North and moving clockwise
        compass_labels = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]

        # Map indices to center angles and labels
        df["sector_center"] = df["sector_idx"].map(lambda i: sector_centers[int(i)])
        df["sector_label"] = df["sector_idx"].map(lambda i: compass_labels[int(i)])

        # Drop any rows that lost category assignment
        df = df.dropna(subset=["speed_cat", "sector_idx"])

        if df.empty:
            fig.update_layout(
                title=dict(
                    text="Windrose (no valid wind records last 2 h)",
                    x=0.5,
                    xanchor="center",
                ),
            )
            fig.add_annotation(
                text="No valid wind speed/direction pairs in the last 2 hours",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        # Aggregate counts by speed_cat and sector_idx (0..15)
        grouped = df.groupby(["speed_cat", "sector_idx"]).size().unstack(fill_value=0)
        # Ensure columns for all sectors exist in order 0..15
        all_sector_idxs = list(range(n_sectors))
        grouped = grouped.reindex(columns=all_sector_idxs, fill_value=0)

        total_count = int(grouped.values.sum())
        if total_count == 0:
            fig.update_layout(
                title=dict(
                    text="Windrose (no valid wind records last 2 h)",
                    x=0.5,
                    xanchor="center",
                ),
            )
            fig.add_annotation(
                text="No valid wind speed/direction pairs in the last 2 hours",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            return fig

        # Convert counts to percentages of total
        grouped_pct = grouped.divide(total_count) * 100.0
        grouped_counts = grouped.astype(int)

        # Theta positions = sector center angles in same order as columns (sector_idx 0..15)
        thetas = [sector_centers[i] for i in all_sector_idxs]

        # Colors for categories
        colors = {
            "0-5 m/s": "rgba(31,119,180,0.8)",
            "5-10 m/s": "rgba(255,127,14,0.8)",
            "10-15 m/s": "rgba(44,160,44,0.8)",
            ">15 m/s": "rgba(214,39,40,0.8)",
        }

        # Add a Barpolar trace per speed category showing percentages
        for cat in speed_labels:
            if cat in grouped_pct.index:
                r_vals = grouped_pct.loc[cat].values.astype(float).tolist()
                count_vals = grouped_counts.loc[cat].values.astype(int).tolist()
            else:
                r_vals = [0.0] * n_sectors
                count_vals = [0] * n_sectors

            # customdata: count, percent, compass label (ordered by sector_idx)
            compass_for_thetas = [compass_labels[i] for i in all_sector_idxs]
            customdata = np.stack([count_vals, r_vals, compass_for_thetas], axis=-1)

            trace = go.Barpolar(
                r=r_vals,
                theta=thetas,
                width=[sector_width * 0.9] * len(thetas),
                name=cat,
                marker_color=colors.get(cat, None),
                opacity=0.85,
                customdata=customdata,
                hovertemplate="Sector: %{customdata[2]}<br>Count: %{customdata[0]}<br>Percent: %{customdata[1]:.2f}%<extra></extra>",
            )
            fig.add_trace(trace)

        max_pct = grouped_pct.values.max()
        radial_range_max = float(np.ceil(max_pct * 1.05)) if max_pct > 0 else 1.0

        fig.update_layout(
            title=dict(
                text="Windrose (last 2 hours)<br>percentages of total records",
                x=0.5,
                xanchor="center",
            ),
            polar=dict(
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,  # keep 0° (North) at top
                    tickmode="array",
                    tickvals=thetas,
                    ticktext=compass_labels,
                ),
                radialaxis=dict(
                    ticksuffix="%",
                    angle=90,
                    range=[0, radial_range_max],
                ),
            ),
            legend=dict(title="Wind speed (avg.)"),
            margin=dict(l=20, r=20, t=80, b=20),
            showlegend=True,
        )

        return fig
