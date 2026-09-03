from src.plots.figure_models import Figure
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
import datetime
from pathlib import Path
import re

src_root = Path(__file__).resolve().parents[2]
filename = "vik.txt"
COLOR_PATH = src_root / "utils" / filename
vik_cm = np.loadtxt(COLOR_PATH)
vik_cmap = LinearSegmentedColormap.from_list("vik", vik_cm)


class PlotContourDiscreteTemperatureDepthsTimesBoreholes(Figure):
    def create_figure(self, sensor):
        # Get data
        df_wide = sensor.get_data()
        if df_wide is None or df_wide.empty:
            return go.Figure()

        # Resample to daily mean so missing days are explicit
        df_wide = df_wide.resample("1D").mean()
        df_wide.index = pd.to_datetime(df_wide.index)

        # Soil temperature columns
        st_cols = [c for c in df_wide.columns if c.startswith("soil_temperature")]
        if len(st_cols) == 0:
            return go.Figure()

        # Ensure the soil temperature columns are numeric (non-numeric -> NaN)
        df_wide[st_cols] = df_wide[st_cols].apply(pd.to_numeric, errors="coerce")

        # Helper to parse depth in cm from column name
        def parse_depth_cm(colname: str):
            m = re.search(r"_(\d{5}|\d+?)cm$", colname)
            if not m:
                m = re.search(r"(\d+)cm", colname)
            if m:
                return int(m.group(1))
            nums = re.findall(r"\d+", colname)
            return int(nums[-1]) if nums else np.nan

        depth_map = {c: parse_depth_cm(c) for c in st_cols}

        # Melt to long format
        df_long = (
            df_wide[st_cols]
            .reset_index()
            .melt(
                id_vars=df_wide.reset_index().columns[0],
                value_vars=st_cols,
                var_name="col",
                value_name="value",
            )
        )
        df_long = df_long.rename(columns={df_long.columns[0]: "referenceTime"})
        df_long["referenceTime"] = pd.to_datetime(df_long["referenceTime"])
        df_long["depth_cm"] = df_long["col"].map(depth_map).astype(float)

        # Keep only rows with numeric depth and non-null values
        df_long = df_long.dropna(subset=["depth_cm", "value"])
        if df_long.empty:
            return go.Figure()

        # Unique depths and sanity check
        depths_cm = np.sort(df_long["depth_cm"].unique())
        if len(depths_cm) <= 1:
            return go.Figure()

        # Pivot to time x depth and reindex to full daily index to preserve gaps
        pivot = (
            df_long.set_index(["referenceTime", "depth_cm"])["value"]
            .unstack(level=-1)
            .reindex(columns=depths_cm)
        )
        full_index = pd.date_range(
            start=df_wide.index.min(), end=df_wide.index.max(), freq="D"
        )
        pivot = pivot.reindex(index=full_index, columns=depths_cm)

        time_index = pd.Index(full_index, name="referenceTime")
        depth_index = pd.Index(depths_cm, name="depth_cm")

        Z_raw = pivot.values

        # Interpolate along depth for each day while preserve NaN rows
        n_depths_fine = max(150, len(depth_index) * 10)
        depths_cm_fine = np.linspace(
            depth_index.min(), depth_index.max(), n_depths_fine
        )
        Y_m = depths_cm_fine / 100.0

        Z_smooth = np.full((len(time_index), n_depths_fine), np.nan, dtype=float)
        depth_vals = np.asarray(depth_index.values)

        for i_row in range(len(time_index)):
            row = Z_raw[i_row, :]
            ix_valid = np.isfinite(row)
            n_valid = ix_valid.sum()
            if n_valid == 0:
                continue
            elif n_valid == 1:
                Z_smooth[i_row, :] = row[ix_valid][0]
            else:
                Z_smooth[i_row, :] = np.interp(
                    depths_cm_fine,
                    depth_vals[ix_valid],
                    row[ix_valid],
                    left=np.nan,
                    right=np.nan,
                )

        # Optional depth-only smoothing if scipy available
        try:
            from scipy.ndimage import gaussian_filter1d

            sigma = 1.0
            if sigma > 0:
                for i_row in range(Z_smooth.shape[0]):
                    if np.isfinite(Z_smooth[i_row]).any():
                        valid = np.isfinite(Z_smooth[i_row])
                        if valid.all():
                            Z_smooth[i_row] = gaussian_filter1d(
                                Z_smooth[i_row], sigma=sigma, mode="nearest"
                            )
                        else:
                            orig_valid = np.isfinite(Z_raw[i_row, :])
                            xp = depth_vals[orig_valid]
                            fp = Z_raw[i_row, orig_valid]
                            if xp.size >= 2:
                                filled = np.interp(
                                    depths_cm_fine, xp, fp, left=np.nan, right=np.nan
                                )
                                finite_mask = np.isfinite(filled)
                                if finite_mask.any():
                                    tmp = filled.copy()
                                    finite_idx = np.where(finite_mask)[0]
                                    leftmost, rightmost = finite_idx[0], finite_idx[-1]
                                    tmp[:leftmost] = tmp[leftmost]
                                    tmp[rightmost + 1 :] = tmp[rightmost]
                                    smoothed = gaussian_filter1d(
                                        tmp, sigma=sigma, mode="nearest"
                                    )
                                    smoothed[:leftmost] = np.nan
                                    smoothed[rightmost + 1 :] = np.nan
                                    Z_smooth[i_row] = smoothed
        except Exception:
            pass

        # Discrete binning and colors
        level_edges = np.array(
            [-25, -20, -15, -10, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 10, 15, 20, 25]
        )
        bins = level_edges
        n_categories = len(bins) - 1

        # Bin centers
        bin_centers = 0.5 * (bins[:-1] + bins[1:])

        # Sample colormap at normalized positions between vmin and vmax
        vmin, vmax = bins.min(), bins.max()
        pos = (bin_centers - vmin) / (vmax - vmin)
        mpl_rgba = [vik_cmap(p) for p in pos]

        # Convert to Plotly rgba strings
        plotly_colors = [
            f"rgba({int(c[0] * 255)}, {int(c[1] * 255)}, {int(c[2] * 255)}, 1.0)"
            for c in mpl_rgba
        ]

        plotly_colors[8] = "rgba(232, 237, 240, 1.0)"

        # build discrete colorscale
        colorscale = []
        for i, color in enumerate(plotly_colors):
            colorscale.append([i / n_categories, color])
            colorscale.append([(i + 1) / n_categories, color])

        # Compute category indices
        Z_flat = Z_smooth
        with np.errstate(invalid="ignore"):
            Z_inds = np.searchsorted(bins, Z_smooth, side="right") - 1

        # Clamp to valid category range and make float so NaNs preserved
        Z_inds = np.clip(Z_inds, 0, n_categories - 1).astype(float)
        Z_inds[np.isnan(Z_flat)] = np.nan

        # Colorbar ticks at bin edges
        tick_vals_edges = list(range(n_categories + 1))
        tick_text_edges = [str(int(v)) for v in level_edges]

        colorbar_kwargs = dict(
            title=dict(text="Temperature [°C]", side="right", font=dict(size=14)),
            tickmode="array",
            tickvals=tick_vals_edges,
            ticktext=tick_text_edges,
            thickness=18,
            len=1.0,
            outlinewidth=0,
            ticks="outside",
            ticklen=4,
            tickfont=dict(size=10),
        )

        # Create heatmap with z domain
        heatmap_discrete = go.Heatmap(
            x=time_index,
            y=Y_m,
            z=Z_inds.T,
            colorscale=colorscale,
            colorbar=colorbar_kwargs,
            zmin=0,
            zmax=n_categories,
            hoverinfo="skip",
            showscale=True,
        )
        # Transparent hover layer
        heatmap_hover = go.Heatmap(
            x=time_index,
            y=Y_m,
            z=Z_smooth.T,
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False,
            hovertemplate=(
                "Temp: %{z:.2f} °C<br>"
                "Depth: %{y:.2f} m<br>"
                "Date: %{x|%d %b %Y}<extra></extra>"
            ),
        )

        fig = go.Figure(data=[heatmap_discrete, heatmap_hover])

        # xticks at July 1 of each year
        first_year = int(pd.to_datetime(time_index[0]).year)
        last_year = int(pd.to_datetime(time_index[-1]).year)
        years = np.arange(first_year, last_year + 1)
        years_dt = [datetime.datetime(y, 7, 1) for y in years]
        years_str = [str(y) for y in years]

        # Vertical dashed lines
        vlines = []
        for y in years[1:]:
            dt = datetime.datetime(y, 1, 1)
            vlines.append(
                dict(
                    type="line",
                    x0=dt,
                    x1=dt,
                    y0=0,
                    y1=1,
                    xref="x",
                    yref="paper",
                    line=dict(color="black", dash="dash", width=0.8),
                )
            )

        fig.update_layout(
            title=dict(
                text="Contour plot of ground temperature with depth",
                x=0.5,
                xanchor="center",
            ),
            xaxis=dict(
                title="Year", tickmode="array", tickvals=years_dt, ticktext=years_str
            ),
            yaxis=dict(title="Depth [m]", autorange="reversed"),
            shapes=vlines,
            margin=dict(l=60, r=20, t=80, b=80),
            width=900,
            height=500,
        )

        fig.update_yaxes(showgrid=True)

        # Add annotation
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
