import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime

from loguru import logger


def plot_tempVStime_shallowest_depth(df: pd.DataFrame):
    # Temperature vs. time for shallowest depth: overlaying years

    logger.info("Plotting temperature vs. time for shallowest depth")

    # Add year and day columns for plotting
    df["year"] = df["referenceTime"].dt.year
    df["day_of_year"] = (
        df["referenceTime"].dt.strftime("%j").astype(int)
        + df["referenceTime"].dt.hour / 24.0
    )

    # Select shallowest depth depending on station
    depth_shallow = df["depth"].unique().min()
    df_plot = df[df["depth"] == depth_shallow].copy()
    plot_title = (
        "Near-surface ground temperature (" + str(depth_shallow / 100) + " m depth)"
    )

    # Find number of years and create grayscale colors
    years = sorted(df_plot["year"].dropna().unique())
    latest_year = years[-1]
    greys = [str(g) for g in np.linspace(0.8, 0.2, len(years) - 1)]

    # Set xtick position
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
    month_mids = {month: start + 14 for month, start in month_starts.items()}

    # Create plot
    fig = plt.figure(figsize=(10, 6))
    for year, color in zip(years[:-1], greys):
        group = df_plot[df_plot["year"] == year]
        plt.plot(
            group["day_of_year"],
            group["value"],
            color=color,
            label=str(year),
            linewidth=1,
        )
    latest_group = df_plot[df_plot["year"] == latest_year]
    plt.plot(
        latest_group["day_of_year"],
        latest_group["value"],
        color="dodgerblue",
        label=str(latest_year),
        linewidth=3,
    )
    plt.xticks(list(month_mids.values()), list(month_mids.keys()))
    for day in month_starts.values():
        plt.axvline(x=day, color="lightgrey", linestyle="--", linewidth=0.8)
    plt.axvline(x=365.5, color="lightgrey", linestyle="--", linewidth=0.8)
    plt.title(plot_title)
    plt.xlabel("Month")
    plt.ylabel("Temperature (°C)")
    plt.grid(axis="y")
    plt.legend(title="Year", loc="upper right")
    plt.tight_layout()

    logger.success("Finished plotting temperature vs. time for shallowest depth")

    return fig


def find_closest_int(array, target_value):
    # Finds the integer in an array closest to a given target value

    closest_int = min(array, key=lambda x: abs(x - target_value))

    return closest_int


def plot_tempVStime_1_shallow_depth(df: pd.DataFrame):
    # Temperature vs. time for 1 shallow depth: overlaying years

    logger.info("Plotting temperature vs. time for 1 shallow depth")

    if len(df["depth"].unique()) > 1:
        # Add year and day columns for plotting
        df["year"] = df["referenceTime"].dt.year
        df["day_of_year"] = (
            df["referenceTime"].dt.strftime("%j").astype(int)
            + df["referenceTime"].dt.hour / 24.0
        )

        # Pick 2 meter depth if available, otherwise any other than the shallowest depth, otherwise none
        depth_preferred = 200
        depth_alternative = find_closest_int(df["depth"].unique(), depth_preferred)
        df_plot = df[df["depth"] == depth_alternative].copy()
        plot_title = "Ground temperature (" + str(depth_alternative / 100) + " m depth)"

        # Find number of years and create grayscale colors
        years = sorted(df_plot["year"].dropna().unique())
        latest_year = years[-1]
        greys = [str(g) for g in np.linspace(0.8, 0.2, len(years) - 1)]

        # Set xtick position
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
        month_mids = {month: start + 14 for month, start in month_starts.items()}

        # Create plot
        fig = plt.figure(figsize=(10, 6))
        for year, color in zip(years[:-1], greys):
            group = df_plot[df_plot["year"] == year]
            plt.plot(
                group["day_of_year"],
                group["value"],
                color=color,
                label=str(year),
                linewidth=1,
            )
        latest_group = df_plot[df_plot["year"] == latest_year]
        plt.plot(
            latest_group["day_of_year"],
            latest_group["value"],
            color="dodgerblue",
            label=str(latest_year),
            linewidth=3,
        )
        plt.xticks(list(month_mids.values()), list(month_mids.keys()))
        for day in month_starts.values():
            plt.axvline(x=day, color="lightgrey", linestyle="--", linewidth=0.8)
        plt.axvline(x=365.5, color="lightgrey", linestyle="--", linewidth=0.8)
        plt.title(plot_title)
        plt.xlabel("Month")
        plt.ylabel("Temperature (°C)")
        plt.grid(axis="y")
        plt.legend(title="Year", loc="upper right")
        plt.tight_layout()
        logger.success("Finished plotting temperature vs. time for 1 shallow depth")

    else:
        logger.warning(
            "Not enough data to plot temperature vs. time for 1 shallow depth"
        )
        fig = plt.figure(figsize=(10, 6))

    return fig


def plot_annual_trumpet_summer_winter(df: pd.DataFrame):
    # Annual trumpet curves for the summer and winter seasons

    logger.info("Plotting annual trumpet curves for the summer and winter seasons")

    # Initialize empty season column
    df["season"] = None

    # Add month column for plotting
    df["month"] = df["referenceTime"].dt.month

    # Create masks
    summer_mask = df["month"].between(5, 9)  # May-Sep
    winter_mask_start = df["month"] >= 10  # Oct–Dec
    winter_mask_end = df["month"] <= 4  # Jan–Apr

    # Vectorized season assignment
    df.loc[summer_mask, "season"] = "summer " + df.loc[summer_mask, "year"].astype(str)
    df.loc[winter_mask_start, "season"] = (
        "winter "
        + df.loc[winter_mask_start, "year"].astype(str)
        + "-"
        + (df.loc[winter_mask_start, "year"] + 1).astype(str)
    )
    df.loc[winter_mask_end, "season"] = (
        "winter "
        + (df.loc[winter_mask_end, "year"] - 1).astype(str)
        + "-"
        + df.loc[winter_mask_end, "year"].astype(str)
    )

    # Separate winters and summers
    df_winter = df[df["season"].str.startswith("winter")]
    df_summer = df[df["season"].str.startswith("summer")]

    # Min temps per depth per winter season
    winter_min = df_winter.groupby(["season", "depth"])["value"].min().unstack(level=0)

    # Max temps per depth per summer season
    summer_max = df_summer.groupby(["season", "depth"])["value"].max().unstack(level=0)

    # Combine winters and summers horizontally (axis=1)
    df_trumpet = pd.concat([winter_min, summer_max], axis=1)

    # Separate winter and summer columns
    winter_cols = [col for col in df_trumpet.columns if col.startswith("winter")]
    summer_cols = [col for col in df_trumpet.columns if col.startswith("summer")]
    winter_cols = winter_cols[::-1]
    summer_cols = summer_cols[::-1]

    # Create plot legend items
    winter_cols_legend = winter_cols.copy()
    summer_cols_legend = summer_cols.copy()

    if (
        df["season"][0].startswith("summer")
        and df["referenceTime"][0].strftime("%d-%m-%Y")
        != "01-05-" + df["referenceTime"][0].strftime("%Y") + ""
    ):
        summer_cols_legend[-1] = (
            summer_cols_legend[-1]
            + " (starts "
            + df["referenceTime"][0].strftime("%d-%m-%Y")
            + ")"
        )
    elif (
        df["season"][0].startswith("winter")
        and df["referenceTime"][0].strftime("%d-%m-%Y")
        != "01-10-" + df["referenceTime"][0].strftime("%Y") + ""
    ):
        winter_cols_legend[-1] = (
            winter_cols_legend[-1]
            + " (starts "
            + df["referenceTime"][0].strftime("%d-%m-%Y")
            + ")"
        )

    legend_trumpet = winter_cols_legend + summer_cols_legend

    # Get depth values (index)
    depths = df_trumpet.index

    # Create color maps
    winter_cmap = plt.get_cmap("Blues_r", 5)
    summer_cmap = plt.get_cmap("Reds_r", 5)

    fig = plt.figure(figsize=(10, 6))
    for i, col in enumerate(winter_cols):
        temps = df_trumpet[col]
        plt.plot(temps, depths / 100, label=col, color=winter_cmap(i), linewidth=2)
    for i, col in enumerate(summer_cols):
        temps = df_trumpet[col]
        plt.plot(temps, depths / 100, label=col, color=summer_cmap(i), linewidth=2)
    plt.gca().invert_yaxis()
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Depth (m)")
    plt.title(
        "Seasonal winter (Oct.-Apr,) min. and summer (May-Sept.) max. temperatures with depth"
    )
    plt.legend(legend_trumpet, loc="best", title="Seasons")
    plt.axvline(x=0, color="black", linestyle="--", linewidth=1)
    plt.grid(True)
    plt.tight_layout()

    logger.success(
        "Finished plotting annual trumpet curves for the summer and winter seasons"
    )

    return fig


def plot_latest_temperatuer_profile_past_same_date(df: pd.DataFrame):
    # Latest temperature profile and from past same dates
    logger.info("Plotting latest temperature profile and from past same dates")

    # Find corresponding dates and create temperature daily averages
    last_date_month = df["referenceTime"].iloc[-1].strftime("%m")
    last_date_day = df["referenceTime"].iloc[-1].strftime("%d")
    df_same_day = df[
        (df["referenceTime"].dt.strftime("%m") == last_date_month)
        & (df["referenceTime"].dt.strftime("%d") == last_date_day)
    ].copy()
    df_same_day["date"] = df_same_day["referenceTime"].dt.date
    df_same_day_avg = (
        df_same_day.groupby(["date", "depth"])["value"].mean().reset_index()
    )

    # Find years for plotting and create grayscale colors
    df_same_day_avg["date"] = pd.to_datetime(df_same_day_avg["date"])
    df_same_day_avg["year"] = df_same_day_avg["date"].dt.year
    years = df_same_day_avg["date"].dt.year.unique()
    latest_year = years[-1]

    greys = [str(g) for g in np.linspace(0.8, 0.2, len(years) - 1)]

    # Create plot
    fig = plt.figure(figsize=(10, 6))
    for year, color in zip(years[:-1], greys):
        group = df_same_day_avg[df_same_day_avg["year"] == year]
        plt.plot(
            group["value"],
            group["depth"] / 100,
            color=color,
            label=str(year),
            linewidth=1,
        )
    latest_group = df_same_day_avg[df_same_day_avg["year"] == latest_year]
    plt.plot(
        latest_group["value"],
        latest_group["depth"] / 100,
        color="dodgerblue",
        label=str(latest_year),
        linewidth=3,
    )
    plt.gca().invert_yaxis()
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Depth (m)")
    plt.title("Latest temperature profile (daily average)")
    plt.legend(
        title="" + last_date_day + "-" + last_date_month + " in year", loc="best"
    )
    plt.axvline(x=0, color="black", linestyle="--", linewidth=1)
    plt.grid(True)
    plt.tight_layout()

    logger.success(
        "Finished plotting latest temperature profile and from past same dates"
    )

    return fig


def find_all_zero_crossings(group):
    # Interpolates temperatures to find depths where temperature is 0 °C

    group = group.sort_values("depth")
    depths = group["depth"].values
    temps = group["value"].values

    zero_depths = []

    # Exact 0 °C values
    exact_zeros = group.loc[group["value"] == 0, "depth"].tolist()
    zero_depths.extend(exact_zeros)

    # Interpolate where temperature crosses 0 °C
    for i in range(len(temps) - 1):
        t1, t2 = temps[i], temps[i + 1]
        if (t1 > 0 and t2 < 0) or (t1 < 0 and t2 > 0):
            d1, d2 = depths[i], depths[i + 1]
            zero_depth = d1 + (0 - t1) * (d2 - d1) / (t2 - t1)
            zero_depths.append(zero_depth)

    # Sort with deepest first
    if zero_depths:
        zero_depths = sorted(zero_depths, reverse=True)
    else:
        zero_depths = []

    return pd.Series({"zero_depths": zero_depths if zero_depths else np.nan})


def plot_iso0_development_all_and_deepest(df):
    # Find 0 °C isotherm

    logger.info("Plotting 0 °C isotherm development: all and only deepest 0 °C")

    # Group and find all zero crossings
    df_isotherm_all = (
        df.groupby("referenceTime")
        .apply(find_all_zero_crossings, include_groups=False)
        .reset_index()
    )

    # Add year and day data for plotting
    df_isotherm_all["year"] = df_isotherm_all["referenceTime"].dt.year
    df_isotherm_all["day_of_year"] = (
        df_isotherm_all["referenceTime"].dt.strftime("%j").astype(int)
        + df_isotherm_all["referenceTime"].dt.hour / 24.0
    )

    # Explode so each depth is a separate row
    df_isotherm_all = df_isotherm_all.explode("zero_depths").dropna(
        subset=["zero_depths"]
    )
    df_isotherm_all["zero_depths"] = df_isotherm_all["zero_depths"].astype(float)

    # Find only deepest zero crossings
    df_isotherm_deepest = (
        df_isotherm_all.copy()
        .sort_values("zero_depths", ascending=False)
        .drop_duplicates(subset="referenceTime", keep="first")
    )
    df_isotherm_deepest = df_isotherm_deepest.sort_values(
        "referenceTime", ascending=True
    )

    # Find number of years and create grayscale colors
    years = sorted(df_isotherm_deepest["year"].dropna().unique())
    latest_year = years[-1]
    greys = [str(g) for g in np.linspace(0.8, 0.2, len(years) - 1)]

    # Set xtick position
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
    month_mids = {month: start + 14 for month, start in month_starts.items()}

    # Create plot: all zero crossings
    fig1 = plt.figure(figsize=(10, 6))
    for year, color in zip(years[:-1], greys):
        group = df_isotherm_all[df_isotherm_all["year"] == year]
        plt.scatter(
            group["day_of_year"],
            group["zero_depths"] / 100,
            color=color,
            label=str(year),
            s=3,
        )
    latest_group = df_isotherm_all[df_isotherm_all["year"] == latest_year]
    plt.scatter(
        latest_group["day_of_year"],
        latest_group["zero_depths"] / 100,
        color="dodgerblue",
        label=str(latest_year),
        s=3,
    )
    plt.xticks(list(month_mids.values()), list(month_mids.keys()))
    plt.gca().invert_yaxis()
    for day in month_starts.values():
        plt.axvline(x=day, color="lightgrey", linestyle="--", linewidth=0.8)
    plt.axvline(x=365.5, color="lightgrey", linestyle="--", linewidth=0.8)
    plt.title("0 °C isotherm development: all 0 °C")
    plt.xlabel("Month")
    plt.ylabel("Depth [m]")
    plt.grid(axis="y")
    plt.legend(title="Year", loc="upper right")
    plt.tight_layout()

    # Create plot: deepest zero crossings
    fig2 = plt.figure(figsize=(10, 6))
    for year, color in zip(years[:-1], greys):
        group = df_isotherm_deepest[df_isotherm_deepest["year"] == year]
        plt.scatter(
            group["day_of_year"],
            group["zero_depths"] / 100,
            color=color,
            label=str(year),
            s=3,
        )
    latest_group = df_isotherm_deepest[df_isotherm_deepest["year"] == latest_year]
    plt.scatter(
        latest_group["day_of_year"],
        latest_group["zero_depths"] / 100,
        color="dodgerblue",
        label=str(latest_year),
        s=3,
    )
    plt.xticks(list(month_mids.values()), list(month_mids.keys()))
    plt.gca().invert_yaxis()
    for day in month_starts.values():
        plt.axvline(x=day, color="lightgrey", linestyle="--", linewidth=0.8)
    plt.axvline(x=365.5, color="lightgrey", linestyle="--", linewidth=0.8)
    plt.title("0 °C isotherm development: only deepest 0 °C")
    plt.xlabel("Month")
    plt.ylabel("Depth [m]")
    plt.grid(axis="y")
    plt.legend(title="Year", loc="upper right")
    plt.tight_layout()

    logger.success(
        "Finished plotting 0 °C isotherm development: all and only deepest 0 °C crossings"
    )

    return fig1, fig2


def plot_contour_temperature_depths_times(df):
    # Contour plot of temperatures for all depths and times

    logger.info("Plotting contour plot of temperatures for all depths and times")

    depths = np.unique(df["depth"])
    if len(depths) > 1:
        # Create datagrids and colorbar
        X, Y = np.meshgrid(np.unique(df["referenceTime"].to_numpy()), depths)
        Z = np.reshape(
            df["value"].to_numpy(), (np.shape(X)[0], np.shape(X)[1]), order="F"
        )

        custom_levels = np.array(
            [-25, -20, -15, -10, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 10, 15, 20, 25]
        )
        custom_levels_ticks = np.array([-20, -15, -10, -5, 0, 5, 10, 15, 20])

        # Set xtick positions and labels
        first_year = int(df["referenceTime"].iloc[0].strftime("%Y"))
        last_year = int(df["referenceTime"].iloc[-1].strftime("%Y"))
        years = np.arange(first_year, last_year + 1)
        years_str = [str(year) for year in years]

        xticks_years = []
        for i in range(len(years)):
            xticks_years.append(datetime.datetime(years[i], 7, 1))

        # Import a scientific colormap
        cm_data = np.loadtxt("vik.txt")
        from matplotlib.colors import LinearSegmentedColormap

        vik_map = LinearSegmentedColormap.from_list("vik", cm_data)

        # Create plot
        fig1 = plt.figure(figsize=(10, 6))
        contour = plt.contourf(X, Y / 100, Z, levels=custom_levels, cmap=vik_map)
        plt.ylabel("Depth (m)")
        plt.title("Contour plot of ground temperature over all depths")
        plt.gca().invert_yaxis()
        plt.tick_params(
            axis="x", which="both", bottom=False, top=False, labelbottom=True
        )
        plt.xticks(xticks_years, years_str)
        for i in range(1, len(years)):
            plt.axvline(
                x=datetime.datetime(years[i], 1, 1),
                color="k",
                linestyle="--",
                linewidth=0.8,
            )
        plt.colorbar(
            contour,
            label="Temperature (°C)",
            ticks=custom_levels_ticks,
            spacing="proportional",
        )

    else:
        fig1 = plt.figure(figsize=(10, 6))

    if (depths > 500).any():
        fig2 = plt.figure(figsize=(10, 6))
        contour = plt.contourf(X, Y / 100, Z, levels=custom_levels, cmap=vik_map)
        plt.ylabel("Depth (m)")
        plt.title("Contour plot of ground temperature up to 5 m depth")
        plt.ylim([depths.min() / 100, 5])
        plt.gca().invert_yaxis()
        plt.tick_params(
            axis="x", which="both", bottom=False, top=False, labelbottom=True
        )
        plt.xticks(xticks_years, years_str)
        for i in range(1, len(years)):
            plt.axvline(
                x=datetime.datetime(years[i], 1, 1),
                color="k",
                linestyle="--",
                linewidth=0.8,
            )
        # plt.colorbar(label='Temperature (°C)')
        plt.colorbar(
            contour,
            label="Temperature (°C)",
            ticks=custom_levels_ticks,
            spacing="proportional",
        )
    else:
        fig2 = plt.figure(figsize=(10, 6))

    logger.success(
        "Finished plotting contour plot of temperatures for all depths and times"
    )

    return fig1, fig2
