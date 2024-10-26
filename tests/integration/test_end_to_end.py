# tests/integration/test_end_to_end.py
import pytest
import pandas as pd
from pathlib import Path
from excel_processor.core.engine import ExcelProcessor

def test_full_processing_workflow(simple_excel_file, sample_config, tmp_path):
    """Test complete workflow from Excel to processed output."""
    
    # Initialize processor
    processor = ExcelProcessor(sample_config)
    
    # Process file
    result = processor.process_file(simple_excel_file, tmp_path)
    
    assert result['status'] == 'success'
    
    # Verify output files
    sheet1_output = pd.read_csv(tmp_path / 'Sheet1.csv')
    sheet2_output = pd.read_csv(tmp_path / 'Sheet2.csv')
    
    # Verify calculations
    assert all(sheet1_output['Formula1'] == sheet1_output['Input'] * 2)
    assert all(sheet1_output['Formula2'] == sheet1_output['Formula1'] + sheet1_output['Input'])
    assert all(sheet2_output['Reference'] == sheet1_output['Formula1'])

def test_error_handling_workflow(create_test_excel, sample_config, tmp_path):
    """Test error handling in complete workflow."""
    
    # Create Excel with various edge cases
    content = {
        'Sheet1': {
            'headers': ['Input', 'Invalid', 'Circular'],
            'data': [[1, None, None]],
            'formulas': {
                'Invalid': '=InvalidFunction(Input)',
                'Circular': '=Circular + 1'
            }
        }
    }
    excel_file = create_test_excel(content)
    
    processor = ExcelProcessor(sample_config)
    
    with pytest.raises(ValueError) as exc_info:
        processor.process_file(excel_file, tmp_path)
    
    error_msg = str(exc_info.value)
    assert 'InvalidFunction' in error_msg or 'Circular' in error_msg

def test_process_file_with_none_config(simple_excel_file, tmp_path):
    """Test that process_file raises ValueError when config is None."""
    
    with pytest.raises(ValueError, match="Config cannot be None"):
        processor = ExcelProcessor(None)
        processor.process_file(simple_excel_file, tmp_path)
