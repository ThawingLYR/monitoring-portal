from .plot_isotherm_development_boreholes_base import (
    PlotIsothermDevelopmentBoreholesBase,
)
import plotly.graph_objects as go


class PlotIsothermDevelopmentAllBoreholes(PlotIsothermDevelopmentBoreholesBase):
    def create_figure(self, sensor):
        df_zero, df_zero_deepest = self._prepare_zero_crossing_data(sensor)
        if df_zero is None:
            return go.Figure()

        years = sorted(df_zero["year"].dropna().unique())
        latest_year = years[-1] if years else None
        greys_rgba = self._get_greys_rgba(years)

        month_starts, tickvals, ticktext = self._month_ticks()

        fig = go.Figure()

        # Add data previous years
        for year, color in zip(years[:-1], greys_rgba):
            grp = df_zero[df_zero["year"] == year]
            if grp.empty:
                continue

            dt_strings = grp["referenceTime"].dt.strftime("%d %b %H:%M:%S")

            fig.add_trace(
                go.Scatter(
                    x=grp["day_of_year"],
                    y=(grp["zero_depths"] / 100.0),
                    mode="markers",
                    marker=dict(color=color, size=2),
                    name=str(year),
                    showlegend=True,
                    text=dt_strings,
                    hovertemplate=(
                        "%{text}<br>"
                        "Depth: %{y:.2f} m<br>"
                        "Year: " + str(year) + "<extra></extra>"
                    ),
                )
            )

        # Add data current year
        if latest_year is not None:
            latest_grp = df_zero[df_zero["year"] == latest_year]
            dt_strings = latest_grp["referenceTime"].dt.strftime("%d %b %H:%M:%S")
            fig.add_trace(
                go.Scatter(
                    x=latest_grp["day_of_year"],
                    y=(latest_grp["zero_depths"] / 100.0),
                    mode="markers",
                    marker=dict(color="blue", size=3),
                    name=str(latest_year),
                    showlegend=True,
                    text=dt_strings,
                    hovertemplate=(
                        "%{text}<br>"
                        "Depth: %{y:.2f} m<br>"
                        "Year: " + str(latest_year) + "<extra></extra>"
                    ),
                )
            )

        # Add vertical lines
        vlines = [
            dict(
                type="line",
                x0=d,
                x1=d,
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                line=dict(color="lightgrey", width=0.8, dash="dash"),
            )
            for d in month_starts
        ]
        vlines.append(
            dict(
                type="line",
                x0=365.5,
                x1=365.5,
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                line=dict(color="lightgrey", width=0.8, dash="dash"),
            )
        )

        # Add titles and labels etc.
        fig.update_layout(
            title=dict(text="0 °C isotherm development: all", x=0.5, xanchor="center"),
            showlegend=True,
            xaxis=dict(
                title="Month", tickmode="array", tickvals=tickvals, ticktext=ticktext
            ),
            yaxis=dict(title="Depth [m]", autorange="reversed"),
            legend=dict(title="Year", x=1, y=0, xanchor="right", yanchor="bottom"),
            shapes=vlines,
            margin=dict(l=60, r=20, t=80, b=60),
            width=900,
        )
        fig.update_yaxes(showgrid=True)

        return fig
