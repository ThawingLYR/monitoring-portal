from src.datasource.datasource_model import DataSource

from requests import Session
from datetime import datetime

from typing import Any, Dict
from pandas import DataFrame


@DataSource.register("frost")
class FrostDataSource(DataSource):
    def __init__(self):
        super().__init__()
        self.provider = "frost"

    def _get_session(self) -> Session:
        # Implementation for Frost
        pass

    def _format_data(self, data: Dict[str, Any]) -> DataFrame:
        # Implementation for Frost
        pass

    def get_data(self, start_time: datetime = None, end_time: datetime = None):
        # Implementation for Frost
        pass
