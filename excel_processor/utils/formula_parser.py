# excel_processor/utils/formula_parser.py
import re
from typing import Set, Dict, Any
from ..models.formula import Formula, FormulaType

class FormulaParser:
    def __init__(self):
        self.excel_to_python_funcs = {
            'SUM': 'np.sum',
            'AVERAGE': 'np.mean',
            'COUNT': 'np.count_nonzero',
            'MAX': 'np.max',
            'MIN': 'np.min',
            'IF': self._convert_if,
            'VLOOKUP': self._convert_vlookup,
            'HLOOKUP': self._convert_hlookup,
            'INDEX': self._convert_index,
            'MATCH': self._convert_match,
            'CONCATENATE': self._convert_concatenate,
            'LEFT': self._convert_left,
            'RIGHT': self._convert_right,
            'MID': self._convert_mid
        }
        
        self.null_safe_funcs = {
            'np.sum': 'lambda x: np.sum(x) if len(x) > 0 else 0',
            'np.mean': 'lambda x: np.mean(x) if len(x) > 0 else 0',
            'np.max': 'lambda x: np.max(x) if len(x) > 0 else 0',
            'np.min': 'lambda x: np.min(x) if len(x) > 0 else 0'
        }
    
    def _convert_if(self, formula: str) -> str:
        """Convert Excel IF function to numpy.where."""
        pattern = r'IF\((.*?),(.*?),(.*?)\)'
        match = re.search(pattern, formula)
        if match:
            condition, true_value, false_value = match.groups()
            return f'np.where({condition}, {true_value}, {false_value})'
        return formula

    def _convert_hlookup(self, formula: str) -> str:
        """Convert HLOOKUP to pandas merge/lookup."""
        pattern = r'HLOOKUP\((.*?),(.*?),(.*?),(.*?)\)'
        match = re.search(pattern, formula)
        if match:
            lookup_value, table_array, row_index, exact_match = match.groups()
            return (
                f'pd.merge('
                f'pd.DataFrame({lookup_value}).T, {table_array}.T, '
                f'how="left").iloc[{int(row_index)-1}, 0]'
                f'.fillna(0)'
            )
        return formula

    def _convert_index(self, formula: str) -> str:
        """Convert INDEX to pandas iloc."""
        pattern = r'INDEX\((.*?),(.*?),(.*?)\)'
        match = re.search(pattern, formula)
        if match:
            array, row_num, col_num = match.groups()
            return f'{array}.iloc[{row_num}-1, {col_num}-1]'
        return formula

    def _convert_match(self, formula: str) -> str:
        """Convert MATCH to pandas index/search."""
        pattern = r'MATCH\((.*?),(.*?),(.*?)\)'
        match = re.search(pattern, formula)
        if match:
            lookup_value, lookup_array, match_type = match.groups()
            return f'(pd.Series({lookup_array}) == {lookup_value}).idxmax() + 1'
        return formula

    def _convert_concatenate(self, formula: str) -> str:
        """Convert CONCATENATE to string concatenation."""
        pattern = r'CONCATENATE\((.*?)\)'
        match = re.search(pattern, formula)
        if match:
            args = match.group(1).split(',')
            return ' + '.join(f'str({arg.strip()})' for arg in args)
        return formula

    def _convert_left(self, formula: str) -> str:
        """Convert LEFT to string slicing."""
        pattern = r'LEFT\((.*?),(\d+)\)'
        match = re.search(pattern, formula)
        if match:
            text, num_chars = match.groups()
            return f'str({text})[:int({num_chars})]'
        return formula

    def _convert_right(self, formula: str) -> str:
        """Convert RIGHT to string slicing."""
        pattern = r'RIGHT\((.*?),(\d+)\)'
        match = re.search(pattern, formula)
        if match:
            text, num_chars = match.groups()
            return f'str({text})[-int({num_chars}):]'
        return formula

    def _convert_mid(self, formula: str) -> str:
        """Convert MID to string slicing."""
        pattern = r'MID\((.*?),(\d+),(\d+)\)'
        match = re.search(pattern, formula)
        if match:
            text, start_num, num_chars = match.groups()
            start = int(start_num) - 1
            return f'str({text})[{start}:{start}+int({num_chars})]'
        return formula
