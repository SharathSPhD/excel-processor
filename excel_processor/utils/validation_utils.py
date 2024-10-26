# excel_processor/utils/validation_utils.py
from typing import Dict, Any, List, Tuple, Optional, Set
import pandas as pd
import numpy as np
import re
from ..models.formula import Formula

def validate_numeric_range(series: pd.Series,
                         min_value: Optional[float] = None,
                         max_value: Optional[float] = None) -> Tuple[bool, List[str]]:
    """Validate numeric values within specified range."""
    errors = []
    
    try:
        # Handle non-numeric data
        if not pd.api.types.is_numeric_dtype(series):
            return False, ["Values must be numeric"]
        
        # Handle NaN values
        if series.isna().any():
            nan_count = series.isna().sum()
            errors.append(f"Contains {nan_count} missing values")
        
        # Convert to numeric, coercing errors to NaN
        numeric_series = pd.to_numeric(series, errors='coerce')
        
        # Check minimum value
        if min_value is not None:
            mask = numeric_series < min_value
            if mask.any():
                invalid_values = series[mask].tolist()
                errors.append(
                    f"Values below minimum {min_value}: {invalid_values[:5]}"
                    f"{' and more' if len(invalid_values) > 5 else ''}"
                )
        
        # Check maximum value
        if max_value is not None:
            mask = numeric_series > max_value
            if mask.any():
                invalid_values = series[mask].tolist()
                errors.append(
                    f"Values above maximum {max_value}: {invalid_values[:5]}"
                    f"{' and more' if len(invalid_values) > 5 else ''}"
                )
        
        return len(errors) == 0, errors
        
    except Exception as e:
        return False, [f"Error validating numeric range: {str(e)}"]

def validate_cell_references(formula: str,
                           available_sheets: Dict[str, pd.DataFrame]) -> Tuple[bool, List[str]]:
    """Validate cell references in formula."""
    errors = []
    
    try:
        # Extract all references
        sheet_refs = re.finditer(
            r"('?[^!]+?'?)!([A-Z]+[0-9]+(?::[A-Z]+[0-9]+)?)",
            formula
        )
        
        for match in sheet_refs:
            sheet_name = match.group(1).strip("'")
            cell_ref = match.group(2)
            
            # Validate sheet existence
            if sheet_name not in available_sheets:
                errors.append(f"Referenced sheet not found: {sheet_name}")
                continue
            
            # Validate cell reference
            try:
                if ':' in cell_ref:  # Range reference
                    start_ref, end_ref = cell_ref.split(':')
                    validate_single_cell_ref(start_ref, available_sheets[sheet_name])
                    validate_single_cell_ref(end_ref, available_sheets[sheet_name])
                else:  # Single cell reference
                    validate_single_cell_ref(cell_ref, available_sheets[sheet_name])
            except ValueError as e:
                errors.append(f"Invalid cell reference in {sheet_name}: {str(e)}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        return False, [f"Error validating cell references: {str(e)}"]

def validate_single_cell_ref(cell_ref: str, df: pd.DataFrame) -> bool:
    """Validate a single cell reference."""
    try:
        col_pattern = r'([A-Z]+)([0-9]+)'
        match = re.match(col_pattern, cell_ref)
        if not match:
            raise ValueError(f"Invalid cell reference format: {cell_ref}")
        
        col, row = match.groups()
        col_idx = excel_col_to_num(col)
        row_idx = int(row) - 1
        
        if row_idx >= len(df) or col_idx >= len(df.columns):
            raise ValueError(f"Cell reference {cell_ref} out of bounds")
        
        return True
        
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error validating cell reference: {str(e)}")

def validate_formula_syntax(formula: str) -> Tuple[bool, List[str]]:
    """Validate Excel formula syntax."""
    errors = []
    
    try:
        if not formula.startswith('='):
            errors.append("Formula must start with '='")
        
        # Remove '=' and handle array formulas
        formula = formula.lstrip('={').rstrip('}')
        
        # Check balanced parentheses
        if formula.count('(') != formula.count(')'):
            errors.append("Unbalanced parentheses in formula")
        
        # Check for common syntax errors
        if ',,' in formula:
            errors.append("Double commas in formula")
        
        if '()' in formula:
            errors.append("Empty function arguments")
        
        # Validate function names
        function_pattern = r'([A-Z][A-Z0-9.]*)\('
        for match in re.finditer(function_pattern, formula):
            func_name = match.group(1)
            if func_name not in SUPPORTED_FUNCTIONS:
                errors.append(f"Unsupported function: {func_name}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        return False, [f"Error validating formula syntax: {str(e)}"]

def generate_validation_report(original_data: Dict[str, pd.DataFrame],
                             processed_data: Dict[str, pd.DataFrame],
                             formulas: Dict[str, Formula],
                             tolerance: float = 1e-10) -> Dict[str, Any]:
    """Generate comprehensive validation report."""
    report = {
        'status': 'success',
        'sheets': {},
        'errors': [],
        'warnings': []
    }
    
    try:
        for sheet_name, original_df in original_data.items():
            if sheet_name not in processed_data:
                report['errors'].append(f"Missing processed data for sheet {sheet_name}")
                continue
            
            processed_df = processed_data[sheet_name]
            sheet_report = validate_sheet(
                sheet_name,
                original_df,
                processed_df,
                formulas,
                tolerance
            )
            
            report['sheets'][sheet_name] = sheet_report
            if sheet_report['status'] == 'error':
                report['status'] = 'error'
                report['errors'].extend(
                    f"{sheet_name}: {error}" 
                    for error in sheet_report['errors']
                )
        
        return report
        
    except Exception as e:
        report['status'] = 'error'
        report['errors'].append(f"Error generating validation report: {str(e)}")
        return report

def validate_sheet(sheet_name: str,
                  original_df: pd.DataFrame,
                  processed_df: pd.DataFrame,
                  formulas: Dict[str, Formula],
                  tolerance: float) -> Dict[str, Any]:
    """Validate a single sheet's data."""
    report = {
        'status': 'success',
        'errors': [],
        'warnings': [],
        'metrics': {}
    }
    
    try:
        # Validate structure
        if original_df.shape != processed_df.shape:
            report['errors'].append(
                f"Shape mismatch: {original_df.shape} vs {processed_df.shape}"
            )
            report['status'] = 'error'
            return report
        
        # Validate columns
        if not original_df.columns.equals(processed_df.columns):
            report['errors'].append("Column mismatch between original and processed data")
            report['status'] = 'error'
            return report
        
        # Validate numeric columns
        numeric_metrics = {}
        for col in original_df.columns:
            if pd.api.types.is_numeric_dtype(original_df[col]):
                if col in formulas:
                    metrics = validate_numeric_column(
                        original_df[col],
                        processed_df[col],
                        tolerance
                    )
                    numeric_metrics[col] = metrics
                    
                    if metrics['max_absolute_error'] > tolerance:
                        report['errors'].append(
                            f"Value mismatch in column {col}: "
                            f"max difference {metrics['max_absolute_error']}"
                        )
                        report['status'] = 'error'
        
        # Calculate overall metrics
        if numeric_metrics:
            report['metrics'] = calculate_overall_metrics(numeric_metrics)
        
        return report
        
    except Exception as e:
        report['status'] = 'error'
        report['errors'].append(f"Error validating sheet: {str(e)}")
        return report

def validate_numeric_column(original: pd.Series,
                          processed: pd.Series,
                          tolerance: float) -> Dict[str, float]:
    """Validate numeric column and calculate metrics."""
    diff = np.abs(original - processed)
    
    return {
        'max_absolute_error': float(diff.max()),
        'mean_absolute_error': float(diff.mean()),
        'within_tolerance': float(
            (diff <= tolerance).mean() * 100  # percentage
        )
    }

def calculate_overall_metrics(column_metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """Calculate overall metrics from column metrics."""
    max_error = max(m['max_absolute_error'] for m in column_metrics.values())
    mean_error = np.mean([m['mean_absolute_error'] for m in column_metrics.values()])
    within_tol = np.mean([m['within_tolerance'] for m in column_metrics.values()])
    
    return {
        'overall_max_error': float(max_error),
        'overall_mean_error': float(mean_error),
        'overall_within_tolerance': float(within_tol)
    }

# Constants
SUPPORTED_FUNCTIONS = {
    'SUM', 'AVERAGE', 'COUNT', 'MAX', 'MIN', 'IF', 'AND', 'OR',
    'VLOOKUP', 'HLOOKUP', 'INDEX', 'MATCH', 'CONCATENATE',
    'LEFT', 'RIGHT', 'MID', 'LEN', 'ROUND', 'ROUNDUP', 'ROUNDDOWN'
}

def excel_col_to_num(col: str) -> int:
    """Convert Excel column letter to number."""
    num = 0
    for c in col:
        num = num * 26 + (ord(c.upper()) - ord('A') + 1)
    return num - 1