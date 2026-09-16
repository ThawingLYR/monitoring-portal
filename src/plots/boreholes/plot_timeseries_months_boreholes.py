from src.plots.figure_models import Figure
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class PlotTimeseriesMonthsBoreholes(Figure):
    def create_figure(self, sensor):
        fig = go.Figure()
        data = sensor.get_data()
        data = data.resample("1D").mean()

        # Extract soil temperature data
        data = sensor.extract_multi_index(data)["soil_temperature"]

        # Get the shallowest depth (closest to surface)
        shallowest_depth = min(data.columns.astype(int))
        shallowest_data = data[shallowest_depth]

        # Convert index to datetime if not already
        shallowest_data.index = pd.to_datetime(shallowest_data.index)

        # Extract year, month, and day of year for grouping
        shallowest_data = shallowest_data.to_frame(name="temperature")
        shallowest_data["year"] = shallowest_data.index.year
        shallowest_data["month"] = shallowest_data.index.month
        shallowest_data["day_of_year"] = shallowest_data.index.dayofyear

        # Get current year
        current_year = shallowest_data["year"].max()

        # Group by year and day of year, then take the mean temperature for each
        grouped_data = (
            shallowest_data.groupby(["year", "day_of_year"])["temperature"]
            .mean()
            .reset_index()
        )

        # Set linestyle
        years = grouped_data["year"].unique()
        n_years = len(years)
        colorscale = plt.cm.Greys(np.linspace(0.2, 0.8, n_years))

        for i, year in enumerate(years):
            year_data = grouped_data[grouped_data["year"] == year]

            # Build hovertext
            origin = pd.Timestamp(f"{year}-01-01")
            dates = pd.to_datetime(
                year_data["day_of_year"] - 1, unit="D", origin=origin
            )
            hovertext = [
                (
                    f"Temp: {temp:.2f} °C<br>"
                    f"Day of year: {d.strftime('%d %b')}<br>"
                    f"Year: {year}"
                )
                for d, temp in zip(dates, year_data["temperature"])
            ]

            # Set linestyle
            color = (
                "blue"
                if year == current_year
                else f"rgba({colorscale[i][0]}, {colorscale[i][1]}, {colorscale[i][2]}, 1.0)"
            )
            width = 2 if year == current_year else 1

            # Plot each year as a line
            fig.add_trace(
                go.Scatter(
                    x=year_data["day_of_year"],
                    y=year_data["temperature"],
                    mode="lines",
                    name=f"{year}",
                    line=dict(color=color, width=width),
                    showlegend=True,
                    text=hovertext,
                    hovertemplate="%{text}<extra></extra>",
                )
            )

        # Add titles and labels etc.
        fig.update_layout(
            title=dict(
                text="Surface temperature by day of year",  # f"{sensor.config.name}
                x=0.5,
                xanchor="center",
            ),
            showlegend=True,
            xaxis_title="Day of Year",
            yaxis_title="Temperature [°C]",
            xaxis=dict(
                tickmode="array",
                tickvals=[1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366],
                ticktext=[
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                    "",
                ],
            ),
            legend_title_text="Year",
        )

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
