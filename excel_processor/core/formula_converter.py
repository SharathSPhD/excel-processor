# excel_processor/core/formula_converter.py
from typing import Dict, Any, Optional, Set
import re
from ..models.formula import Formula, FormulaType
from ..utils.excel_utils import extract_cell_references, parse_cell_reference

class FormulaConverter:
    """Converts Excel formulas to Python code."""
    
    def __init__(self):
        self.excel_to_python_funcs = {
            # Basic operations
            'SUM': 'np.sum',
            'AVERAGE': 'np.mean',
            'COUNT': 'np.count_nonzero',
            'MAX': 'np.max',
            'MIN': 'np.min',
            
            # Logical functions
            'IF': self._convert_if,
            'AND': 'np.logical_and',
            'OR': 'np.logical_or',
            'NOT': 'np.logical_not',
            
            # Lookup functions
            'VLOOKUP': self._convert_vlookup,
            'HLOOKUP': self._convert_hlookup,
            'INDEX': self._convert_index,
            'MATCH': self._convert_match,
            
            # Text functions
            'CONCATENATE': self._convert_concatenate,
            'LEFT': self._convert_left,
            'RIGHT': self._convert_right,
            'MID': self._convert_mid,
            
            # Date functions
            'DATE': self._convert_date,
            'EDATE': self._convert_edate,
            'TODAY': 'pd.Timestamp.today()'
        }
    
    def convert_formula(self, 
                       formula: str,
                       sheet_name: str,
                       column_name: str) -> Formula:
        """
        Convert Excel formula to Python code.
        
        Args:
            formula: Excel formula string
            sheet_name: Name of the worksheet
            column_name: Target column name
            
        Returns:
            Formula object with Python equivalent
        """
        if not formula.startswith('='):
            raise ValueError("Formula must start with '='")
        
        # Remove '=' and handle array formulas
        formula = formula.lstrip('={').rstrip('}')
        
        # Extract dependencies
        dependencies = extract_cell_references(formula)
        
        # Convert the formula
        python_code = self._convert_formula_string(formula)
        
        # Determine formula type
        formula_type = self._determine_formula_type(formula)
        
        return Formula(
            raw_formula=formula,
            python_equivalent=python_code,
            formula_type=formula_type,
            dependencies=dependencies,
            sheet_name=sheet_name,
            column_name=column_name
        )
    
    def _convert_formula_string(self, formula: str) -> str:
        """Convert Excel formula string to Python code."""
        python_formula = formula
        
        # Replace Excel operators
        python_formula = python_formula.replace('<>', '!=')
        
        # Convert cell references
        cell_refs = re.findall(r'[A-Z]+[0-9]+(?::[A-Z]+[0-9]+)?', python_formula)
        for ref in sorted(cell_refs, key=len, reverse=True):
            if ':' in ref:
                python_ref = self._convert_range_reference(ref)
            else:
                python_ref = self._convert_cell_reference(ref)
            python_formula = python_formula.replace(ref, python_ref)
        
        # Convert Excel functions
        for excel_func, python_func in self.excel_to_python_funcs.items():
            if callable(python_func):
                if excel_func in python_formula:
                    python_formula = python_func(python_formula)
            else:
                python_formula = python_formula.replace(excel_func, python_func)
        
        return python_formula
    
    def _convert_if(self, formula: str) -> str:
        """Convert Excel IF function to numpy.where."""
        pattern = r'IF\((.*?),(.*?),(.*?)\)'
        match = re.search(pattern, formula)
        if match:
            condition, true_value, false_value = match.groups()
            return f'np.where({condition}, {true_value}, {false_value})'
        return formula
    
    def _convert_vlookup(self, formula: str) -> str:
        """Convert VLOOKUP to pandas merge/lookup."""
        pattern = r'VLOOKUP\((.*?),(.*?),(.*?),(.*?)\)'
        match = re.search(pattern, formula)
        if match:
            lookup_value, table_array, col_index, exact_match = match.groups()
            return (f'pd.merge(pd.DataFrame({lookup_value}), {table_array}, '
                   f'how="left").iloc[:, {int(col_index)-1}]')
        return formula
    
    def _convert_index(self, formula: str) -> str:
        """Convert INDEX to pandas iloc."""
        pattern = r'INDEX\((.*?),(.*?),(.*?)\)'
        match = re.search(pattern, formula)
        if match:
            array, row_num, col_num = match.groups()
            return f'{array}.iloc[{row_num}-1, {col_num}-1]'
        return formula
    
    def _convert_concatenate(self, formula: str) -> str:
        """Convert CONCATENATE to string concatenation."""
        pattern = r'CONCATENATE\((.*?)\)'
        match = re.search(pattern, formula)
        if match:
            args = match.group(1).split(',')
            return ' + '.join(arg.strip() for arg in args)
        return formula
    
    def _convert_cell_reference(self, ref: str) -> str:
        """Convert single cell reference to pandas accessor."""
        sheet, col, row = parse_cell_reference(ref)
        if sheet:
            return f'data["{sheet}"].iloc[{row-1}, {col}]'
        return f'df.iloc[{row-1}, {col}]'
    
    def _convert_range_reference(self, ref: str) -> str:
        """Convert range reference to pandas accessor."""
        start, end = ref.split(':')
        start_sheet, start_col, start_row = parse_cell_reference(start)
        end_sheet, end_col, end_row = parse_cell_reference(end)
        
        if start_sheet:
            return (f'data["{start_sheet}"].iloc[{start_row-1}:{end_row}, '
                   f'{start_col}:{end_col}]')
        return f'df.iloc[{start_row-1}:{end_row}, {start_col}:{end_col}]'
    
    def _determine_formula_type(self, formula: str) -> FormulaType:
        """Determine the type of Excel formula."""
        formula_upper = formula.upper()
        
        if any(f in formula_upper for f in ['SUM', 'AVERAGE', 'COUNT', 'MAX', 'MIN']):
            return FormulaType.AGGREGATE
        elif any(f in formula_upper for f in ['IF', 'AND', 'OR', 'NOT']):
            return FormulaType.LOGICAL
        elif any(f in formula_upper for f in ['VLOOKUP', 'HLOOKUP', 'INDEX', 'MATCH']):
            return FormulaType.LOOKUP
        elif any(f in formula_upper for f in ['CONCATENATE', 'LEFT', 'RIGHT', 'MID']):
            return FormulaType.TEXT
        elif any(f in formula_upper for f in ['DATE', 'EDATE', 'TODAY']):
            return FormulaType.DATE
        else:
            return FormulaType.ARITHMETIC