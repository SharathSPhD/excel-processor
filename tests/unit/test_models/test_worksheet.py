# tests/unit/test_models/test_worksheet.py
import pytest
import pandas as pd
from excel_processor.models.worksheet import WorksheetInfo

def test_worksheet_info_creation():
    """Test basic WorksheetInfo creation."""
    data = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    
    worksheet = WorksheetInfo(
        name="Test",
        data=data,
        formulas={'B': '=A*2'},
        input_columns={'A'}
    )
    
    assert worksheet.name == "Test"
    assert worksheet.data.equals(data)
    assert worksheet.formulas == {'B': '=A*2'}
    assert worksheet.input_columns == {'A'}

def test_worksheet_info_defaults():
    """Test WorksheetInfo with default values."""
    data = pd.DataFrame({'A': [1, 2, 3]})
    worksheet = WorksheetInfo(
        name="Test",
        data=data
    )
    
    assert worksheet.formulas == {}
    assert worksheet.input_columns == set()
    assert worksheet.dependencies == {}