from src.plots.figure_models import Figure


import plotly.graph_objects as go


class TestFigure01(Figure):
    name: str = "Test Figure"

    def create_figure(self, sensor):
        fig = go.Figure()
        data = sensor.get_data()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["Variable1"],
                mode="lines+markers",
                name="Line Plot",
            )
        )
        # Update layout
        fig.update_layout(
            title="Sample Line Plot", xaxis_title="X Axis", yaxis_title="Y Axis"
        )

        return fig
