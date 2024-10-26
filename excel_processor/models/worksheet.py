# excel_processor/models/worksheet.py
from dataclasses import dataclass, field
from typing import Dict, Set
import pandas as pd

@dataclass
class WorksheetInfo:
    name: str
    data: pd.DataFrame
    formulas: Dict[str, str] = field(default_factory=dict)
    input_columns: Set[str] = field(default_factory=set)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)