"""
Variable Column Naming Utilities

Data source modules name their columns after the canonical variable they hold,
optionally qualified by the dimension at which it was measured:

    {variable}-{dimension}_{value:05.0f}{unit}

For example `air_temperature-height_above_msl_00002m` (Frost) or
`soil_temperature-depth_below_surface_00010cm` (Tilsig). Sources that measure a
variable at a single, implicit position - such as Netatmo, whose consumer
stations report one outdoor module - emit the bare variable name instead.

These helpers let display code work with either convention, so a single page can
render stations from several providers.
"""

import pandas as pd


def base_variable(column: str) -> str:
    """Returns the canonical variable name of a column.

    Args:
        column (str): A column name, with or without a dimension suffix.

    Returns:
        str: The part before the dimension suffix.

    Example:
        >>> base_variable("air_temperature-height_above_msl_00002m")
        'air_temperature'
        >>> base_variable("air_temperature")
        'air_temperature'
    """
    return column.split("-", 1)[0]


def columns_for_variable(df: pd.DataFrame, variable: str) -> list[str]:
    """Returns the columns of `df` holding the given canonical variable.

    Args:
        df (pd.DataFrame): The frame to inspect.
        variable (str): Canonical variable name, e.g. "air_temperature".

    Returns:
        list[str]: Matching column names, qualified or not. Empty if the variable
            is not present.
    """
    return [column for column in df.columns if base_variable(column) == variable]
