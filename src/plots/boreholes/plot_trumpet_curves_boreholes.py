from src.plots.figure_models import Figure
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re


class PlotTrumpetCurveBoreholes(Figure):
    def create_figure(self, sensor):
        df_wide = sensor.get_data()

        # Ensure index is datetime
        df_wide.index = pd.to_datetime(df_wide.index)

        # Select only soil_temperature columns
        st_cols = [c for c in df_wide.columns if c.startswith("soil_temperature")]
        if len(st_cols) == 0:
            return go.Figure()

        df_st = df_wide[st_cols].copy()

        # Parse depth from column names
        def parse_depth_cm(colname):
            m = re.search(r"_(\d{5}|\d+?)cm$", colname)
            if not m:
                # try other pattern: digits before 'cm'
                m = re.search(r"(\d+)cm", colname)
            if m:
                return int(m.group(1))
            nums = re.findall(r"\d+", colname)
            return int(nums[-1]) if nums else np.nan

        depth_map = {c: parse_depth_cm(c) for c in st_cols}

        # Change to long format
        df_long = df_st.reset_index().melt(
            id_vars=df_st.reset_index().columns[0],
            value_vars=st_cols,
            var_name="col",
            value_name="value",
        )
        df_long = df_long.rename(columns={df_long.columns[0]: "referenceTime"})
        df_long["referenceTime"] = pd.to_datetime(df_long["referenceTime"])

        # Add depth (cm), year, and month column
        df_long["depth_cm"] = df_long["col"].map(depth_map).astype(float)
        df_long["month"] = df_long["referenceTime"].dt.month
        df_long["year"] = df_long["referenceTime"].dt.year

        # Season assignment: Summer: May (5) - Sep (9), Winter: Oct (10) - Apr (4)
        df_long["season"] = None
        summer_mask = df_long["month"].between(5, 9)
        winter_mask_start = df_long["month"] >= 10
        winter_mask_end = df_long["month"] <= 4

        df_long.loc[summer_mask, "season"] = "summer " + df_long.loc[
            summer_mask, "year"
        ].astype(int).astype(str)
        df_long.loc[winter_mask_start, "season"] = (
            "winter "
            + df_long.loc[winter_mask_start, "year"].astype(int).astype(str)
            + "-"
            + (df_long.loc[winter_mask_start, "year"] + 1).astype(int).astype(str)
        )
        df_long.loc[winter_mask_end, "season"] = (
            "winter "
            + (df_long.loc[winter_mask_end, "year"] - 1).astype(int).astype(str)
            + "-"
            + df_long.loc[winter_mask_end, "year"].astype(int).astype(str)
        )

        # Split for winter and summer
        df_winter = df_long[df_long["season"].str.startswith("winter", na=False)]
        df_summer = df_long[df_long["season"].str.startswith("summer", na=False)]

        # Compute winter minima and summer maxima per (season, depth_cm)
        if not df_winter.empty:
            winter_min = (
                df_winter.groupby(["season", "depth_cm"])["value"]
                .min()
                .unstack(level=0)
            )
        else:
            winter_min = pd.DataFrame(index=sorted(df_long["depth_cm"].unique()))

        if not df_summer.empty:
            summer_max = (
                df_summer.groupby(["season", "depth_cm"])["value"]
                .max()
                .unstack(level=0)
            )
        else:
            summer_max = pd.DataFrame(index=sorted(df_long["depth_cm"].unique()))

        # Combine so columns are seasons
        df_trumpet = pd.concat([winter_min, summer_max], axis=1)

        # Ensure index sorted by depth
        df_trumpet = df_trumpet.sort_index()

        # Collect columns and reverse order to match original plotting
        winter_cols = [
            col for col in df_trumpet.columns if str(col).startswith("winter")
        ]
        summer_cols = [
            col for col in df_trumpet.columns if str(col).startswith("summer")
        ]
        winter_cols = winter_cols[::-1]
        summer_cols = summer_cols[::-1]

        # Legend labels
        winter_cols_legend = [str(c) for c in winter_cols]
        summer_cols_legend = [str(c) for c in summer_cols]

        legend_trumpet = winter_cols_legend + summer_cols_legend

        # Depths (index) in meters
        depths_cm = df_trumpet.index.astype(float)
        depth_m = depths_cm / 100.0

        # Colormaps
        winter_cmap = plt.get_cmap("Blues_r")
        summer_cmap = plt.get_cmap("Reds_r")
        n_winter = len(winter_cols)
        n_summer = len(summer_cols)

        # Create rgba from colormap
        def rgba_from_cmap(cmap, i, n):
            if n <= 1:
                pos = 0.5
            else:
                pos = i / max(1, n - 1)
            delta = 0.12
            if pos <= 0.0:
                pos = min(delta, 1.0)
            elif pos >= 1.0:
                pos = max(1.0 - delta, 0.0)
            color = cmap(pos)
            return f"rgba({int(color[0] * 255)}, {int(color[1] * 255)}, {int(color[2] * 255)}, {color[3]:.3f})"

        fig = go.Figure()

        # Add winter traces
        for i, col in enumerate(winter_cols):
            temps = df_trumpet[col]
            fig.add_trace(
                go.Scatter(
                    x=temps.values,
                    y=depth_m.values,
                    mode="lines",
                    name=str(col),
                    line=dict(color=rgba_from_cmap(winter_cmap, i, n_winter), width=2),
                    hovertemplate=(
                        "Temp: %{x:.2f} °C<br>"
                        "Depth: %{y:.2f} m<br>"
                        "Season: " + str(col) + "<extra></extra>"
                    ),
                )
            )

        # Add summer traces
        for i, col in enumerate(summer_cols):
            temps = df_trumpet[col]
            fig.add_trace(
                go.Scatter(
                    x=temps.values,
                    y=depth_m.values,
                    mode="lines",
                    name=str(col),
                    line=dict(color=rgba_from_cmap(summer_cmap, i, n_summer), width=2),
                    hovertemplate=(
                        "Temp: %{x:.2f} °C<br>"
                        "Depth: %{y:.2f} m<br>"
                        "Season: " + str(col) + "<extra></extra>"
                    ),
                )
            )

        # Add titles and labels etc.
        fig.update_layout(
            title=dict(
                text="Winter min. and summer max. temperature profiles",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Temperature [°C]",
            yaxis_title="Depth [m]",
            legend_title_text="Seasons",
            legend=dict(traceorder="normal"),
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
        )

        # Replace trace names with adjusted legend labels in order (winter then summer)
        for trace, label in zip(fig.data, legend_trumpet):
            trace.name = label

        # Add annotations
        fig.add_annotation(
            text="Winter: Oct. - Apr.<br>Summer: May - Sep.",
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
