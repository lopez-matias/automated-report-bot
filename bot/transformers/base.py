from abc import ABC, abstractmethod
import pandas as pd


class BaseTransformer(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        pass
