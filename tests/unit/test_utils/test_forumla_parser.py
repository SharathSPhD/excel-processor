# tests/unit/test_utils/test_formula_parser.py
import pytest
from excel_processor.utils.formula_parser import FormulaParser
from excel_processor.models.formula import FormulaType

def test_basic_formulas():
    """Test parsing of basic formulas."""
    parser = FormulaParser()
    
    test_cases = [
        {
            'formula': '=A1 + B1',
            'expected_deps': {'A1', 'B1'},
            'expected_type': FormulaType.ARITHMETIC
        },
        {
            'formula': '=SUM(A1:A10)',
            'expected_deps': {'A1:A10'},
            'expected_type': FormulaType.AGGREGATE
        },
        {
            'formula': '=IF(A1>0, B1, C1)',
            'expected_deps': {'A1', 'B1', 'C1'},
            'expected_type': FormulaType.LOGICAL
        }
    ]
    
    for case in test_cases:
        formula = parser.parse(case['formula'], 'Sheet1', 'Result')
        assert formula.dependencies == case['expected_deps']
        assert formula.formula_type == case['expected_type']

def test_cross_sheet_references():
    """Test parsing of formulas with cross-sheet references."""
    parser = FormulaParser()
    
    formula_str = '=Sheet2!A1 + Sheet3!B2:B10'
    formula = parser.parse(formula_str, 'Sheet1', 'Result')
    
    assert 'Sheet2!A1' in formula.dependencies
    assert 'Sheet3!B2:B10' in formula.dependencies

def test_special_functions():
    """Test parsing of special Excel functions."""
    parser = FormulaParser()
    
    test_cases = [
        {
            'formula': '=VLOOKUP(A1, Sheet2!B:C, 2, FALSE)',
            'expected_type': FormulaType.LOOKUP
        },
        {
            'formula': '=CONCATENATE(A1, " ", B1)',
            'expected_type': FormulaType.TEXT
        }
    ]
    
    for case in test_cases:
        formula = parser.parse(case['formula'], 'Sheet1', 'Result')
        assert formula.formula_type == case['expected_type']
        assert formula.python_equivalent is not None

def test_error_handling():
    """Test error handling in formula parsing."""
    parser = FormulaParser()
    
    # Test formula without '='
    with pytest.raises(ValueError, match="Formula must start with '='"):
        parser.parse('A1 + B1', 'Sheet1', 'Result')
    
    # Test empty formula
    with pytest.raises(ValueError):
        parser.parse('=', 'Sheet1', 'Result')

def test_array_formulas():
    """Test parsing of array formulas."""
    parser = FormulaParser()
    
    formula_str = '={SUM(IF(A1:A10>0, B1:B10, 0))}'
    formula = parser.parse(formula_str, 'Sheet1', 'Result')
    
    assert formula.formula_type == FormulaType.AGGREGATE
    assert 'A1:A10' in formula.dependencies
    assert 'B1:B10' in formula.dependencies

def test_complex_nested_formulas():
    """Test parsing of complex nested formulas."""
    parser = FormulaParser()
    
    formula_str = '=IF(SUM(A1:A5)>100, AVERAGE(B1:B5), MAX(C1:C5))'
    formula = parser.parse(formula_str, 'Sheet1', 'Result')
    
    assert formula.formula_type == FormulaType.LOGICAL
    assert all(dep in formula.dependencies for dep in ['A1:A5', 'B1:B5', 'C1:C5'])
    assert 'np.where' in formula.python_equivalent
    assert 'np.mean' in formula.python_equivalent

def test_cell_reference_conversion():
    """Test conversion of cell references to Python equivalents."""
    parser = FormulaParser()
    
    # Test single cell reference
    formula_str = '=A1'
    formula = parser.parse(formula_str, 'Sheet1', 'Result')
    assert 'df.iloc[0, 0]' in formula.python_equivalent
    
    # Test range reference
    formula_str = '=SUM(A1:B10)'
    formula = parser.parse(formula_str, 'Sheet1', 'Result')
    assert 'df.iloc[0:10' in formula.python_equivalent

def test_excel_column_conversion():
    """Test conversion of Excel column letters to numbers."""
    parser = FormulaParser()
    
    test_cases = [
        ('A', 0),
        ('B', 1),
        ('Z', 25),
        ('AA', 26),
        ('ZZ', 701)
    ]
    
    for col, expected in test_cases:
        result = parser._excel_col_to_num(col)
        assert result == expected, f"Failed for column {col}"

def test_null_safe_functions():
    """Test null-safe function conversions."""
    parser = FormulaParser()
    
    formula_str = '=SUM(A1:A10)'
    formula = parser.parse(formula_str, 'Sheet1', 'Result')
    
    # Check if null-safe wrapper is applied
    assert 'if len' in formula.python_equivalent
    assert 'else 0' in formula.python_equivalent