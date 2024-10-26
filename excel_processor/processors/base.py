# excel_processor/processors/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

class BaseProcessor(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process the input data"""
        pass
    
    def validate_input(self, data: Any) -> bool:
        """Validate input data"""
        return True