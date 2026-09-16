from src.plots.figure_models import Figure
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re


class PlotLatestProfilePastSameDateBoreholes(Figure):
    def create_figure(self, sensor):
        df_wide = sensor.get_data()
        if df_wide.empty:
            return go.Figure()

        # Ensure index is datetime
        df_wide.index = pd.to_datetime(df_wide.index)

        # Select soil temperature columns
        st_cols = [c for c in df_wide.columns if c.startswith("soil_temperature")]
        if len(st_cols) == 0:
            return go.Figure()

        df_st = df_wide[st_cols].copy()

        # Helper to parse depth in cm from column names
        def parse_depth_cm(colname):
            m = re.search(r"_(\d{5}|\d+?)cm$", colname)
            if not m:
                m = re.search(r"(\d+)cm", colname)
            if m:
                return int(m.group(1))
            nums = re.findall(r"\d+", colname)
            return int(nums[-1]) if nums else np.nan

        depth_map = {c: parse_depth_cm(c) for c in st_cols}

        # Melt to long form with referenceTime column
        df_long = df_st.reset_index().melt(
            id_vars=df_st.reset_index().columns[0],
            value_vars=st_cols,
            var_name="col",
            value_name="value",
        )
        df_long = df_long.rename(columns={df_long.columns[0]: "referenceTime"})
        df_long["referenceTime"] = pd.to_datetime(df_long["referenceTime"])

        # Add depth (cm), date, year, month, day columns
        df_long["depth_cm"] = df_long["col"].map(depth_map).astype(float)
        df_long["date"] = df_long["referenceTime"].dt.date
        df_long["year"] = df_long["referenceTime"].dt.year
        df_long["month"] = df_long["referenceTime"].dt.month
        df_long["day"] = df_long["referenceTime"].dt.day

        # Determine the target month/day from the latest timestamp in the original wide df
        last_ref = df_wide.index.max()
        target_month = last_ref.month
        target_day = last_ref.day

        # Filter rows that match the month/day
        mask_same_md = (df_long["month"] == target_month) & (
            df_long["day"] == target_day
        )
        df_same_md = df_long[mask_same_md].copy()
        if df_same_md.empty:
            return go.Figure()

        # Compute daily average per date and depth (group by date and depth)
        df_same_md["date"] = pd.to_datetime(df_same_md["date"])
        df_daily_avg = (
            df_same_md.groupby(["date", "depth_cm"])["value"].mean().reset_index()
        )

        # Extract years sorted and determine current (latest) year
        df_daily_avg["year"] = df_daily_avg["date"].dt.year
        years = sorted(df_daily_avg["year"].unique())
        if len(years) == 0:
            return go.Figure()
        current_year = years[-1]
        n_years = len(years)

        # Create greyscale array
        colorscale = plt.cm.Greys(np.linspace(0.2, 0.8, n_years))

        # Build Plotly figure
        fig = go.Figure()

        # Plot each year
        for i, year in enumerate(years):
            group = df_daily_avg[df_daily_avg["year"] == year].sort_values("depth_cm")
            if year == current_year:
                color = "blue"
                width = 3
            else:
                c = colorscale[i]
                r, g, b = c[0], c[1], c[2]
                color = f"rgba({int(r * 255)}, {int(g * 255)}, {int(b * 255)}, {1.0})"
                width = 1

            fig.add_trace(
                go.Scatter(
                    x=group["value"],
                    y=(group["depth_cm"] / 100.0),
                    mode="lines",
                    name=str(year),
                    line=dict(color=color, width=width),
                    showlegend=True,
                    hovertemplate="Temp: %{x:.2f} °C<br>Depth: %{y:.2f} m<br>Year: "
                    + str(year),
                )
            )

        # Layout and styling
        legend_title = f"{target_day:02d} {pd.Timestamp(year=2000, month=target_month, day=1).strftime('%b')} in year"

        # Add titles and labels etc.
        fig.update_layout(
            title=dict(
                text=f"Temperature profile for {target_day:02d} {pd.Timestamp(year=2000, month=target_month, day=1).strftime('%b')}",
                x=0.5,
                xanchor="center",
            ),
            showlegend=True,
            xaxis_title="Temperature [°C]",
            yaxis_title="Depth [m]",
            legend_title_text=legend_title,
            legend=dict(
                traceorder="normal", x=1, y=0, xanchor="right", yanchor="bottom"
            ),
            yaxis=dict(autorange="reversed"),
            shapes=[
                dict(
                    type="line",
                    x0=0,
                    x1=0,
                    y0=0,
                    y1=1,
                    xref="x",
                    yref="paper",
                    line=dict(color="black", width=1, dash="dash"),
                )
            ],
            margin=dict(l=60, r=20, t=80, b=60),
            width=900,
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
