# excel_processor/models/formula.py
from dataclasses import dataclass
from typing import Set, Optional, Any
from enum import Enum

class FormulaType(Enum):
    ARITHMETIC = "arithmetic"
    LOGICAL = "logical"
    LOOKUP = "lookup"
    AGGREGATE = "aggregate"
    TEXT = "text"
    DATE = "date"
    CUSTOM = "custom"

@dataclass
class Formula:
    raw_formula: str
    python_equivalent: str
    formula_type: FormulaType
    dependencies: Set[str]
    sheet_name: str
    column_name: str
    error_handling: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate formula structure and dependencies"""
        try:
            # Basic syntax validation
            compile(self.python_equivalent, '<string>', 'eval')
            return True
        except SyntaxError:
            return False