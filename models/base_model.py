# models/base_model.py
from abc import ABC, abstractmethod

class SAXSModel(ABC):
    @abstractmethod
    def calculate(self, *args, **kwargs):
        pass
