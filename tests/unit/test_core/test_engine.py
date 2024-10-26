# tests/unit/test_core/test_engine.py
import pytest
from pathlib import Path
from excel_processor.core.engine import ExcelProcessor

def test_processor_initialization(sample_config):
    processor = ExcelProcessor(sample_config)
    assert processor.config == sample_config
    assert processor.excel_reader is None
    assert processor.validator is not None

def test_process_file(simple_excel_file, sample_config, tmp_path):
    processor = ExcelProcessor(sample_config)
    result = processor.process_file(simple_excel_file, tmp_path)
    
    assert result['status'] == 'success'
    assert 'Sheet1' in result['processed_sheets']
    assert 'Sheet2' in result['processed_sheets']
    
    # Check output files
    assert (tmp_path / 'Sheet1.csv').exists()
    assert (tmp_path / 'Sheet2.csv').exists()

def test_process_file_with_validation(simple_excel_file, sample_config, tmp_path):
    config = sample_config.copy()
    config['validation']['enabled'] = True
    
    processor = ExcelProcessor(config)
    result = processor.process_file(simple_excel_file, tmp_path)
    
    assert result['status'] == 'success'
    assert 'validation_results' in result
    assert result['validation_results']['overall_status'] == 'success'

def test_process_file_with_errors(create_test_excel, sample_config, tmp_path):
    # Create Excel with invalid formula
    content = {
        'Sheet1': {
            'headers': ['Input', 'Invalid'],
            'data': [[1, None]],
            'formulas': {
                'Invalid': '=InvalidFunction(Input)'
            }
        }
    }
    excel_file = create_test_excel(content)
    
    processor = ExcelProcessor(sample_config)
    with pytest.raises(ValueError):
        processor.process_file(excel_file, tmp_path)

def test_excel_processor_constructor_with_none_config():
    with pytest.raises(ValueError, match="Config cannot be None"):
        ExcelProcessor(None)

def test_process_file_with_none_config(simple_excel_file, tmp_path):
    with pytest.raises(ValueError, match="Config cannot be None"):
        processor = ExcelProcessor(None)
        processor.process_file(simple_excel_file, tmp_path)
