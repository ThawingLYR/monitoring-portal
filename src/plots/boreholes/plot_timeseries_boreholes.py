from src.plots.figure_models import Figure
import plotly.graph_objects as go
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from pathlib import Path
import pandas as pd

src_root = Path(__file__).resolve().parents[2]
filename = "grayC.txt"
COLOR_PATH = src_root / "utils" / filename
grayC_cm = np.loadtxt(COLOR_PATH)
grayC_cmap = LinearSegmentedColormap.from_list("grayC", grayC_cm)


class PlotTimeseriesBoreholes(Figure):
    def create_figure(self, sensor):
        fig = go.Figure()
        data = sensor.get_data()

        # Resample data to daily mean
        data = data.resample("1D").mean()

        # Change column headings (extract depth from column heading name)
        data = sensor.extract_multi_index(data)["soil_temperature"]

        # Number of depths
        n = len(data.columns)

        # Evenly spaced values between 0 and 0.95, one per depth
        normalized_depths = np.linspace(0.0, 0.95, n)

        # Convert matplotlib rgba floats to plotly rgba string with 0-255 RGB
        colors = []
        for norm in normalized_depths:
            r, g, b, a = grayC_cmap(norm)
            colors.append(
                f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, {a:.3f})"
            )

        # Add data to plot for each depth
        for i, col in enumerate(data.columns):
            hover_template = (
                "Temp: %{y:.2f} °C<br>"
                f"Depth: {col} cm<br>"
                "Date: %{x|%d %b %Y}"
                "<extra></extra>"
            )

            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[col],
                    mode="lines",
                    name=f"{col}cm",
                    showlegend=True,
                    line=dict(
                        color=colors[i],
                        width=2,
                    ),
                    hovertemplate=hover_template,
                )
            )

        # Add titles and labels etc.
        fig.update_layout(
            title=dict(
                text="Time series for all sensor depths",  # f"{sensor.config.name}
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Date",
            yaxis_title="Temperature [°C]",
            xaxis_range=[data.index.min(), data.index.max()],
            legend_title_text="Depth",
            showlegend=True,
        )

        # Add vertical lines
        first_year = data.index.min().year
        last_year = data.index.max().year
        year_starts = [
            pd.Timestamp(year=y, month=1, day=1)
            for y in range(first_year, last_year + 1)
        ]

        vlines = [
            dict(
                type="line",
                x0=dt,
                x1=dt,
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                line=dict(color="lightgrey", width=0.8, dash="dash"),
                layer="below",
            )
            for dt in year_starts
        ]

        # Append to any existing shapes already in layout
        existing_shapes = fig.layout.shapes or ()
        fig.update_layout(shapes=list(existing_shapes) + vlines)

        # Add annotations
        fig.add_annotation(
            text="Data resampled to daily means",
            x=0,
            y=1.10,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="left",
            align="left",
            font=dict(size=12, color="gray"),
            xshift=3,
        )

        return fig
