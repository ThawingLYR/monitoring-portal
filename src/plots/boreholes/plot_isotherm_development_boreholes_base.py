from src.plots.figure_models import Figure
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re


class PlotIsothermDevelopmentBoreholesBase(Figure):
    def _prepare_zero_crossing_data(self, sensor):
        """
        Returns (df_zero_all, df_zero_deepest)
        where df_zero_all: one row per zero crossing with columns:
            referenceTime, zero_depths (cm), year, day_of_year
        and df_zero_deepest: one row per timestamp with only the deepest zero crossing.
        """

        # Get data
        df = sensor.get_data()
        if df.empty:
            return go.Figure(), go.Figure()

        # Ensure datetime index
        df.index = pd.to_datetime(df.index)

        # Select soil temperature columns
        st_cols = [c for c in df.columns if c.startswith("soil_temperature")]
        if len(st_cols) == 0:
            return go.Figure(), go.Figure()

        df_st = df[st_cols].copy()

        # Coerce columns to numeric so invalid values become NaN floats
        df_st = df_st.apply(pd.to_numeric, errors="coerce")

        # Parse depth in cm from column names
        def parse_depth_cm(colname):
            m = re.search(r"_(\d{5}|\d+?)cm$", colname)
            if not m:
                m = re.search(r"(\d+)cm", colname)
            if m:
                return int(m.group(1))
            nums = re.findall(r"\d+", colname)
            return int(nums[-1]) if nums else np.nan

        depth_map = {c: parse_depth_cm(c) for c in st_cols}

        # Melt to long format
        df_long = df_st.reset_index().melt(
            id_vars=df_st.reset_index().columns[0],
            value_vars=st_cols,
            var_name="col",
            value_name="value",
        )
        df_long = df_long.rename(columns={df_long.columns[0]: "referenceTime"})
        df_long["referenceTime"] = pd.to_datetime(df_long["referenceTime"])

        # Add numeric depth (cm) and sort for each timestamp
        df_long["depth_cm"] = df_long["col"].map(depth_map).astype(float)

        # Find all zero crossings for one timestamp (DataFrame group)
        def find_all_zero_crossings(group):
            g = group.sort_values("depth_cm")
            depths = g["depth_cm"].values
            temps = g["value"].values

            zero_depths = []
            exact_zeros = g.loc[g["value"] == 0, "depth_cm"].tolist()
            zero_depths.extend(exact_zeros)

            for i in range(len(temps) - 1):
                t1, t2 = temps[i], temps[i + 1]
                if pd.isna(t1) or pd.isna(t2):
                    continue

                # ensure numeric before doing arithmetic (they should be floats after coercion)
                try:
                    f1 = float(t1)
                    f2 = float(t2)
                except TypeError, ValueError:
                    continue

                if (f1 > 0 and f2 < 0) or (f1 < 0 and f2 > 0):
                    d1, d2 = float(depths[i]), float(depths[i + 1])
                    # linear interpolation for zero crossing depth
                    zero_depth = d1 + (0.0 - f1) * (d2 - d1) / (f2 - f1)
                    zero_depths.append(zero_depth)

            if zero_depths:
                zero_depths = sorted(zero_depths, reverse=True)
            else:
                zero_depths = []

            return pd.Series({"zero_depths": zero_depths if zero_depths else np.nan})

        # Group by timestamp and compute zero crossings
        df_zero = (
            df_long.groupby("referenceTime")
            .apply(find_all_zero_crossings)
            .reset_index()
        )

        # Build year and day_of_year with fractional day (hour fraction) for plotting
        df_zero["year"] = df_zero["referenceTime"].dt.year
        df_zero["day_of_year"] = (
            df_zero["referenceTime"].dt.strftime("%j").astype(int)
            + df_zero["referenceTime"].dt.hour / 24.0
        )

        # Explode list of zero_depths to one row per crossing and drop NaNs
        df_zero = df_zero.explode("zero_depths").dropna(subset=["zero_depths"])
        if df_zero.empty:
            return go.Figure(), go.Figure()

        df_zero["zero_depths"] = df_zero["zero_depths"].astype(float)

        # Deepest crossing per timestamp
        df_zero_deepest = (
            df_zero.copy()
            .sort_values("zero_depths", ascending=False)
            .drop_duplicates(subset="referenceTime", keep="first")
            .sort_values("referenceTime", ascending=True)
        )

        return df_zero, df_zero_deepest

    def _get_greys_rgba(self, years):
        # Return list of rgba strings for len(years)-1 past years
        n_years = max(0, len(years))
        if n_years > 0:
            grey_samples = plt.cm.Greys(np.linspace(0.2, 0.8, n_years))
            greys_rgba = [
                f"rgba({int(c[0] * 255)}, {int(c[1] * 255)}, {int(c[2] * 255)}, 1.0)"
                for c in grey_samples
            ]
        else:
            greys_rgba = []
        return greys_rgba

    def _month_ticks(self):
        month_starts = {
            "Jan": 1,
            "Feb": 32,
            "Mar": 61,
            "Apr": 92,
            "May": 122,
            "Jun": 153,
            "Jul": 183,
            "Aug": 214,
            "Sep": 245,
            "Oct": 275,
            "Nov": 306,
            "Dec": 336,
        }
        tickvals = [v + 14 for v in month_starts.values()]
        ticktext = list(month_starts.keys())
        return list(month_starts.values()), tickvals, ticktext
