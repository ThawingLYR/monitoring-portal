from abc import ABC, abstractmethod

from requests import Session
from datetime import datetime

from typing import Any, Dict, Type
from pandas import DataFrame

from src.config.config_class import StationConfig, DataProvider, StationSensors


class DataSource(ABC):
    session: Session | None = None
    config: StationConfig | None = None
    provider: DataProvider

    def __init__(self):
        self.session = self._get_session()

        pass

    # Registry to map provider names to child classes
    _registry: Dict[DataProvider, Type["DataSource"]] = {}

    @classmethod
    def register(cls, provider: DataProvider):
        def decorator(child_class: Type["DataSource"]):
            cls._registry[provider] = child_class
            return child_class

        return decorator

    @classmethod
    def create(cls, provider: DataProvider) -> "DataSource":
        if provider not in cls._registry:
            raise ValueError(f"No DataSource registered for provider: {provider}")
        return cls._registry[provider]()

    @abstractmethod
    def _get_session(self) -> Session:
        pass

    @abstractmethod
    def _format_data(self, data: Dict[str, Any]) -> DataFrame:
        pass

    @abstractmethod
    def get_data(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        sensors: StationSensors = None,
        variables: list[str] = [],
    ):
        pass
