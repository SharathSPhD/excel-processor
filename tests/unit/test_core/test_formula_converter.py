# tests/unit/test_core/test_formula_converter.py
import pytest
from excel_processor.core.formula_converter import FormulaConverter
from excel_processor.models.formula import FormulaType

def test_basic_arithmetic():
    converter = FormulaConverter()
    formula = converter.convert_formula(
        '=A1 + B1',
        'Sheet1',
        'C1'
    )
    
    assert formula.python_equivalent == 'df.iloc[0, 0] + df.iloc[0, 1]'
    assert formula.formula_type == FormulaType.ARITHMETIC

def test_sum_function():
    converter = FormulaConverter()
    formula = converter.convert_formula(
        '=SUM(A1:A10)',
        'Sheet1',
        'B1'
    )
    
    assert 'np.sum' in formula.python_equivalent
    assert formula.formula_type == FormulaType.AGGREGATE

def test_if_function():
    converter = FormulaConverter()
    formula = converter.convert_formula(
        '=IF(A1>10, B1, C1)',
        'Sheet1',
        'D1'
    )
    
    assert 'np.where' in formula.python_equivalent
    assert formula.formula_type == FormulaType.LOGICAL

def test_vlookup():
    converter = FormulaConverter()
    formula = converter.convert_formula(
        '=VLOOKUP(A1, Sheet2!A:B, 2, FALSE)',
        'Sheet1',
        'E1'
    )
    
    assert 'pd.merge' in formula.python_equivalent
    assert formula.formula_type == FormulaType.LOOKUP

def test_nested_functions():
    converter = FormulaConverter()
    formula = converter.convert_formula(
        '=IF(SUM(A1:A5)>100, AVERAGE(B1:B5), MAX(C1:C5))',
        'Sheet1',
        'D1'
    )
    
    assert 'np.where' in formula.python_equivalent
    assert 'np.sum' in formula.python_equivalent
    assert 'np.mean' in formula.python_equivalent
    assert formula.formula_type == FormulaType.LOGICAL

def test_cross_sheet_reference():
    converter = FormulaConverter()
    formula = converter.convert_formula(
        '=Sheet2!A1 + Sheet3!B1',
        'Sheet1',
        'C1'
    )
    
    assert 'data["Sheet2"]' in formula.python_equivalent
    assert 'data["Sheet3"]' in formula.python_equivalent

def test_invalid_formula():
    converter = FormulaConverter()
    with pytest.raises(ValueError):
        converter.convert_formula(
            'Invalid Formula',  # Missing '='
            'Sheet1',
            'A1'
        )

def test_array_formula():
    converter = FormulaConverter()
    formula = converter.convert_formula(
        '{=SUM(IF(A1:A10>0, B1:B10, 0))}',
        'Sheet1',
        'C1'
    )
    
    assert 'np.sum' in formula.python_equivalent
    assert 'np.where' in formula.python_equivalent
    assert formula.formula_type == FormulaType.AGGREGATE
