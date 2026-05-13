from src.plots.figure_models import Figure


import plotly.graph_objects as go
import matplotlib.pyplot as plt

import numpy as np


class PlotTimeseriesBoreholes(Figure):
    name: str = "Test Figure"

    def create_figure(self, sensor):
        fig = go.Figure()
        data = sensor.get_data()
        data = data.resample("1D").mean()

        data = sensor.extract_mutli_index(data)["soil_temperature"]

        depths = np.array(data.columns.astype(int).tolist())
        normalized_depths = (depths - min(depths)) / (max(depths) - min(depths))

        colormap = plt.cm.copper
        colors = [colormap(norm) for norm in normalized_depths]

        for i, col in enumerate(data.columns):
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[col],
                    mode="lines",
                    name=f"{col}cm",
                    line=dict(
                        color=f"rgba({colors[i][0]}, {colors[i][1]}, {colors[i][2]}, {colors[i][3]})",
                        width=2,
                    ),
                )
            )
        # Update layout
        fig.update_layout(
            title="Borehole time series",
            xaxis_title="Time [UTC]",
            yaxis_title="Temperature [°C]",
            xaxis_range=[data.index.min(), data.index.max()],
        )

        return fig
