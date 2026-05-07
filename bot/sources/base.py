from abc import ABC, abstractmethod
import pandas as pd


class BaseSource(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """Fetch data and return as a DataFrame."""

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        return df
