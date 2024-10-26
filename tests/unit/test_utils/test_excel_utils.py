# tests/unit/test_utils/test_excel_utils.py
import pytest
from excel_processor.utils.excel_utils import (
    extract_cell_references,
    parse_cell_reference,
    get_column_range
)

def test_extract_cell_references():
    # Test single cell reference
    refs = extract_cell_references('=A1 + B1')
    assert refs == {'A1', 'B1'}
    
    # Test range reference
    refs = extract_cell_references('=SUM(A1:A10)')
    assert refs == {'A1:A10'}
    
    # Test cross-sheet reference
    refs = extract_cell_references('=Sheet2!A1 + Sheet3!B1')
    assert refs == {'Sheet2!A1', 'Sheet3!B1'}
    
    # Test complex formula
    refs = extract_cell_references('=IF(SUM(A1:A5)>0, MAX(B1:B5), Sheet2!C1)')
    assert refs == {'A1:A5', 'B1:B5', 'Sheet2!C1'}

def test_parse_cell_reference():
    # Test single cell
    sheet, col, row = parse_cell_reference('A1')
    assert (sheet, col, row) == ('', 'A', 1)
    
    # Test sheet reference
    sheet, col, row = parse_cell_reference('Sheet1!B2')
    assert (sheet, col, row) == ('Sheet1', 'B', 2)
    
    # Test invalid reference
    with pytest.raises(ValueError):
        parse_cell_reference('Invalid')

def test_get_column_range(simple_excel_file):
    from openpyxl import load_workbook
    wb = load_workbook(simple_excel_file)
    ws = wb['Sheet1']
    
    min_col, max_col = get_column_range(ws)
    assert min_col == 1
    assert max_col > 0
