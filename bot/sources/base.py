from abc import ABC, abstractmethod
import pandas as pd


class BaseSource(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def extract(self) -> pd.DataFrame:
        pass
