# tests/unit/test_utils/test_validation_utils.py
import pytest
import pandas as pd
import numpy as np
from excel_processor.utils.validation_utils import (
    validate_numeric_range,
    validate_cell_references,
    validate_formula_syntax,
    generate_validation_report
)

def test_validate_numeric_range():
    # Test valid range
    series = pd.Series([1, 2, 3, 4, 5])
    is_valid, errors = validate_numeric_range(series, min_value=1, max_value=5)
    assert is_valid
    assert not errors
    
    # Test invalid range
    series = pd.Series([0, 1, 2, 6])
    is_valid, errors = validate_numeric_range(series, min_value=1, max_value=5)
    assert not is_valid
    assert len(errors) == 2  # Both min and max violations

def test_validate_cell_references():
    formula = '=A1 + Sheet2!B1'
    available_sheets = {
        'Sheet1': pd.DataFrame({'A': [1]}),
        'Sheet2': pd.DataFrame({'B': [2]})
    }
    
    is_valid, errors = validate_cell_references(formula, available_sheets)
    assert is_valid
    assert not errors
    
    # Test invalid references
    formula = '=InvalidSheet!A1'
    is_valid, errors = validate_cell_references(formula, available_sheets)
    assert not is_valid
    assert errors

def test_validate_formula_syntax():
    # Test valid formulas
    valid_formulas = [
        '=A1 + B1',
        '=SUM(A1:A10)',
        '=IF(A1>0, B1, C1)'
    ]
    for formula in valid_formulas:
        is_valid, errors = validate_formula_syntax(formula)
        assert is_valid
        assert not errors
    
    # Test invalid formulas
    invalid_formulas = [
        'A1 + B1',  # Missing =
        '=SUM(A1:A10',  # Unbalanced parentheses
        '=IF(A1>0,, B1)'  # Double comma
    ]
    for formula in invalid_formulas:
        is_valid, errors = validate_formula_syntax(formula)
        assert not is_valid
        assert errors

def test_generate_validation_report():
    original_data = {
        'Sheet1': pd.DataFrame({
            'A': [1, 2, 3],
            'B': [2, 4, 6]
        })
    }
    
    processed_data = {
        'Sheet1': pd.DataFrame({
            'A': [1, 2, 3],
            'B': [2, 4, 6]
        })
    }
    
    formulas = {
        'Sheet1.B': Formula(
            raw_formula='=A*2',
            python_equivalent='df["A"] * 2',
            formula_type=FormulaType.ARITHMETIC,
            dependencies={'A'},
            sheet_name='Sheet1',
            column_name='B'
        )
    }
    
    report = generate_validation_report(
        original_data,
        processed_data,
        formulas,
        tolerance=1e-10
    )
    
    assert report['status'] == 'success'
    assert 'Sheet1' in report['sheets']
    assert report['sheets']['Sheet1']['status'] == 'success'