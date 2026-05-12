"""
Data Source Module

This module defines the abstract base class `DataSource` for fetching and formatting data from various providers.
It uses a registry pattern to map `DataProvider` values to concrete implementations of `DataSource`.
"""

from abc import ABC, abstractmethod
from requests import Session
from datetime import datetime
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
    def create(cls, provider: DataProvider) -> "DataSource":
        """
        Creates an instance of the `DataSource` subclass registered for the given provider.

        Args:
            provider (DataProvider): The provider name to create the `DataSource` for.

        Returns:
            DataSource: An instance of the registered `DataSource` subclass.

        Raises:
            ValueError: If no `DataSource` subclass is registered for the given provider.
        """
        if provider not in cls._registry:
            raise ValueError(f"No DataSource registered for provider: {provider}")
        return cls._registry[provider]()

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
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        sensors: Optional[StationSensors] = None,
        variables: Optional[list[str]] = None,
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
