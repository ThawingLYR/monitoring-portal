from src.plots.figure_models import Figure


import plotly.graph_objects as go

import numpy as np

from matplotlib.colors import LinearSegmentedColormap

from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
COLOR_PATH = "grayC.txt"
grayC_cm = np.loadtxt(COLOR_PATH)
grayC_cmap = LinearSegmentedColormap.from_list("grayC", grayC_cm)


class PlotTimeseriesBoreholes(Figure):
    name: str = "Test Figure"

    def create_figure(self, sensor):
        fig = go.Figure()
        data = sensor.get_data()
        data = data.resample("1D").mean()
        data = sensor.extract_mutli_index(data)["soil_temperature"]

        # depths = np.array(data.columns.astype(int).tolist())
        # normalized_depths = (depths - min(depths)) / (max(depths) - min(depths))

        # number of traces (depth series)
        n = len(data.columns)

        # evenly spaced values between 0 and 1, one per trace
        normalized_depths = np.linspace(0.0, 0.95, n)

        # colormap = plt.cm.cool

        # convert matplotlib rgba floats to Plotly rgba string with 0-255 RGB
        colors = []
        for norm in normalized_depths:
            r, g, b, a = grayC_cmap(norm)
            colors.append(
                f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, {a:.3f})"
            )

        for i, col in enumerate(data.columns):
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[col],
                    mode="lines",
                    name=f"{col}cm",
                    line=dict(
                        color=colors[i],
                        width=2,
                    ),
                )
            )
        # Update layout
        fig.update_layout(
            title=f"{sensor.config.name} borehole time series",
            xaxis_title="Time [UTC]",
            yaxis_title="Temperature [°C]",
            xaxis_range=[data.index.min(), data.index.max()],
        )

        fig.add_annotation(
            text="Data resampled to daily means",
            x=0.5,
            y=1.02,
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor="center",
            font=dict(size=12, color="gray"),
        )

        return fig
