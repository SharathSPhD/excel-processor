# tests/unit/test_models/test_formula.py
import pytest
from excel_processor.models.formula import Formula, FormulaType

def test_formula_creation():
    formula = Formula(
        raw_formula='=A1 + B1',
        python_equivalent='df["A"] + df["B"]',
        formula_type=FormulaType.ARITHMETIC,
        dependencies={'A1', 'B1'},
        sheet_name='Sheet1',
        column_name='C1'
    )
    
    assert formula.raw_formula == '=A1 + B1'
    assert formula.python_equivalent == 'df["A"] + df["B"]'
    assert formula.formula_type == FormulaType.ARITHMETIC
    assert formula.dependencies == {'A1', 'B1'}

def test_formula_validation():
    valid_formula = Formula(
        raw_formula='=SUM(A1:A10)',
        python_equivalent='df["A"].sum()',
        formula_type=FormulaType.AGGREGATE,
        dependencies={'A1:A10'},
        sheet_name='Sheet1',
        column_name='B1'
    )
    assert valid_formula.validate()
    
    invalid_formula = Formula(
        raw_formula='=SUM(A1:A10)',
        python_equivalent='invalid python code /',
        formula_type=FormulaType.AGGREGATE,
        dependencies={'A1:A10'},
        sheet_name='Sheet1',
        column_name='B1'
    )
    assert not invalid_formula.validate()
