# tests/unit/test_core/test_excel_reader.py
import pytest
import pandas as pd
from excel_processor.core.excel_reader import ExcelReader

def test_read_workbook(simple_excel_file):
    reader = ExcelReader(simple_excel_file)
    worksheet_info = reader.read_workbook()
    
    assert 'Sheet1' in worksheet_info
    assert 'Sheet2' in worksheet_info
    
    sheet1 = worksheet_info['Sheet1']
    assert isinstance(sheet1.data, pd.DataFrame)
    assert 'Input' in sheet1.input_columns
    assert 'Formula1' in sheet1.formulas
    assert sheet1.formulas['Formula1'] == '=Input*2'

def test_process_worksheet(simple_excel_file):
    reader = ExcelReader(simple_excel_file)
    reader.workbook = reader._load_workbook(data_only=True)
    reader.formula_workbook = reader._load_workbook(data_only=False)
    
    worksheet_info = reader._process_worksheet('Sheet1')
    assert worksheet_info.name == 'Sheet1'
    assert len(worksheet_info.formulas) == 2
    assert 'Input' in worksheet_info.input_columns

def test_extract_formulas(simple_excel_file):
    reader = ExcelReader(simple_excel_file)
    worksheet_info = reader.read_workbook()
    
    sheet1 = worksheet_info['Sheet1']
    assert sheet1.formulas['Formula1'] == '=Input*2'
    assert sheet1.formulas['Formula2'] == '=Formula1+Input'
    
    sheet2 = worksheet_info['Sheet2']
    assert sheet2.formulas['Reference'] == '=Sheet1!Formula1'

def test_invalid_excel_file():
    with pytest.raises(FileNotFoundError):
        reader = ExcelReader('nonexistent.xlsx')
        reader.read_workbook()