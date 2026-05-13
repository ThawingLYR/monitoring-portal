"""
Data Source Module

This module defines the abstract base class `DataSource` for fetching and formatting data from various providers.
It uses a registry pattern to map `DataProvider` values to concrete implementations of `DataSource`.
"""

from abc import ABC, abstractmethod
from requests import Session
from datetime import datetime, timedelta
from typing import Any, Dict, Type, Optional
from pandas import DataFrame
from src.config.config_class import StationConfig, DataProvider, StationSensors


class DataSource(ABC):
    """
    Abstract base class for data sources.

    This class provides a framework for fetching and formatting data from different providers.
    Subclasses must implement `_get_session`, `_format_data`, and `get_data` methods.
    Uses a registry pattern to dynamically create instances based on the `DataProvider` type.

    Class Attributes:
        session (Session | None): HTTP session for making requests. Initialized in `__init__`.
        config (StationConfig | None): Configuration for the station. Can be set by subclasses.
        provider (DataProvider): The data provider associated with this source (e.g., "frost", "tilsig").
        _registry (Dict[DataProvider, Type["DataSource"]]): Maps provider names to their corresponding `DataSource` subclasses.
    """

    session: Session | None = None
    config: Optional[StationConfig] = None
    provider: DataProvider

    def __init__(self):
        """
        Initializes the `DataSource` instance.
        Sets up the HTTP session by calling `_get_session`.
        """
        self.session = self._get_session()

    # Registry to map provider names to child classes
    _registry: Dict[DataProvider, Type["DataSource"]] = {}

    @classmethod
    def register(cls, provider: DataProvider):
        """
        Decorator to register a `DataSource` subclass for a specific `DataProvider`.

        Args:
            provider (DataProvider): The provider name to register the subclass for.

        Returns:
            Callable: A decorator function that registers the subclass in the `_registry`.

        Example:
            @DataSource.register("frost")
            class FrostDataSource(DataSource):
                ...
        """

        def decorator(child_class: Type["DataSource"]):
            cls._registry[provider] = child_class
            return child_class

        return decorator

    @classmethod
    def create(
        cls, provider: DataProvider = None, config: StationConfig = None
    ) -> "DataSource":
        """
        Creates an instance of the `DataSource` subclass registered for the given provider.

        Args:
            provider (DataProvider): The provider name to create the `DataSource` for.

        Returns:
            DataSource: An instance of the registered `DataSource` subclass.

        Raises:
            ValueError: If no `DataSource` subclass is registered for the given provider.
        """
        if provider is None and config is None:
            raise ValueError(
                "Please specify a provider or a configuration to instanciate a datasource"
            )
        if provider is None:
            provider = config.dataProvider

        if provider not in cls._registry:
            raise ValueError(f"No DataSource registered for provider: {provider}")
        return cls._registry[provider](config=config)

    @abstractmethod
    def _get_session(self) -> Session:
        """
        Abstract method to create and return an HTTP session for the data source.

        Subclasses must implement this method to provide a configured `requests.Session` object.

        Returns:
            Session: A `requests.Session` object for making HTTP requests.
        """
        pass

    @abstractmethod
    def _format_data(self, data: Dict[str, Any]) -> DataFrame:
        """
        Abstract method to format raw data into a pandas DataFrame.

        Subclasses must implement this method to define how raw data (e.g., from an API)
        is converted into a structured DataFrame.

        Args:
            data (Dict[str, Any]): Raw data to be formatted.

        Returns:
            DataFrame: A pandas DataFrame containing the formatted data.
        """
        pass

    @abstractmethod
    def get_data(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        sensors: list[StationSensors] = None,
        variables: list[str] = None,
    ) -> DataFrame:
        """
        Abstract method to fetch data from the source.

        Subclasses must implement this method to define how data is fetched for the given parameters.

        Args:
            start_time (datetime | None): Start of the time range for the data. Defaults to None.
            end_time (datetime | None): End of the time range for the data. Defaults to None.
            sensors (StationSensors | None): Sensors to fetch data for. Defaults to None.
            variables (list[str] | None): List of variables to fetch. Defaults to None.

        Returns:
            DataFrame: A pandas DataFrame containing the fetched and formatted data.
        """
        pass

    def _get_periods(
        self, start_time: datetime, end_time: datetime, max_length: int = 180
    ) -> list[tuple[datetime, datetime]]:
        """
        Splits a time range into a list of contiguous, non-overlapping periods, each with a maximum length of `max_length` days.
        The next period starts **exactly at the end of the previous one** (exclusive), ensuring no gaps or overlaps.

        Args:
            start_time (datetime): Start of the overall time range (inclusive).
            end_time (datetime): End of the overall time range (inclusive).
            max_length (int): Maximum number of days for each period. Defaults to 180 (approximately 6 months).

        Returns:
            list[tuple[datetime, datetime]]: A list of tuples, where each tuple represents a period as (start, end).
                                            The periods are contiguous and cover the entire range without gaps or overlaps.

        Example:
            >>> start = datetime(2023, 1, 1, 12, 0)  # Jan 1, 12:00
            >>> end = datetime(2023, 1, 5, 6, 0)     # Jan 5, 06:00
            >>> _get_periods(start, end, max_length=2)
            [
                (datetime(2023, 1, 1, 12, 0), datetime(2023, 1, 3, 12, 0)),  # Jan 1 12:00 to Jan 3 12:00
                (datetime(2023, 1, 3, 12, 0), datetime(2023, 1, 5, 6, 0))    # Jan 3 12:00 to Jan 5 06:00
            ]

        Notes:
            - The last period may be shorter than `max_length` if the remaining time is less than `max_length`.
            - Each period starts **exactly where the previous one ended**, ensuring no gaps or overlaps.
            - The `end_time` of the last period is **inclusive** (matches the input `end_time`).
        """
        if start_time > end_time:
            raise ValueError("`start_time` must be before or equal to `end_time`.")
        if max_length <= 0:
            raise ValueError("`max_length` must be a positive integer.")

        periods = []
        current_start = start_time

        while current_start < end_time:
            # Calculate the end of the current period
            current_end = current_start + timedelta(days=max_length)

            # Ensure the end does not exceed the provided end_time
            if current_end > end_time:
                current_end = end_time

            periods.append((current_start, current_end))

            # Move to the start of the next period (exactly at the end of the current one)
            current_start = current_end

        return periods
