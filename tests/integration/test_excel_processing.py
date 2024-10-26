# tests/integration/test_excel_processing.py
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from excel_processor import ExcelProcessor

def test_complex_workbook_processing(create_test_excel, sample_config, tmp_path):
    """Test processing of a complex workbook with multiple interdependencies."""
    
    # Create test workbook with complex formulas and dependencies
    content = {
        'Data': {
            'headers': ['ID', 'Value', 'Category'],
            'data': [
                [1, 100, 'A'],
                [2, 200, 'B'],
                [3, 300, 'A']
            ]
        },
        'Lookup': {
            'headers': ['Category', 'Multiplier'],
            'data': [
                ['A', 1.1],
                ['B', 1.2]
            ]
        },
        'Calculations': {
            'headers': ['ID', 'BaseCalc', 'AdjustedCalc', 'Total'],
            'data': [
                [1, None, None, None],
                [2, None, None, None],
                [3, None, None, None]
            ],
            'formulas': {
                'BaseCalc': '=VLOOKUP(ID, Data!A:B, 2, FALSE)',
                'AdjustedCalc': ('=BaseCalc * '
                                'VLOOKUP(VLOOKUP(ID, Data!A:C, 3, FALSE), '
                                'Lookup!A:B, 2, FALSE)'),
                'Total': '=SUM(AdjustedCalc)'
            }
        }
    }
    
    excel_file = create_test_excel(content)
    
    # Process the workbook
    processor = ExcelProcessor(sample_config)
    result = processor.process_file(excel_file, tmp_path)
    
    assert result['status'] == 'success'
    
    # Verify results
    calc_df = pd.read_csv(tmp_path / 'Calculations.csv')
    
    # Verify BaseCalc matches original values
    assert all(calc_df['BaseCalc'] == [100, 200, 300])
    
    # Verify AdjustedCalc includes multipliers
    expected_adjusted = [110, 240, 330]  # A=1.1, B=1.2, A=1.1
    np.testing.assert_array_almost_equal(
        calc_df['AdjustedCalc'],
        expected_adjusted
    )
    
    # Verify Total is sum of AdjustedCalc
    assert calc_df['Total'].iloc[0] == sum(expected_adjusted)

def test_error_recovery_and_logging(create_test_excel, sample_config, tmp_path):
    """Test error handling and recovery in a complex scenario."""
    
    # Create test workbook with some invalid formulas
    content = {
        'Sheet1': {
            'headers': ['Input', 'Valid', 'Invalid1', 'Invalid2'],
            'data': [
                [1, None, None, None],
                [2, None, None, None]
            ],
            'formulas': {
                'Valid': '=Input * 2',
                'Invalid1': '=InvalidFunction(Input)',
                'Invalid2': '=Circular + 1'
            }
        }
    }
    
    excel_file = create_test_excel(content)
    
    # Configure error handling
    config = sample_config.copy()
    config['error_handling'] = {
        'strict_mode': False,
        'ignore_missing_refs': True,
        'default_value': 0
    }
    
    processor = ExcelProcessor(config)
    result = processor.process_file(excel_file, tmp_path)
    
    assert result['status'] == 'completed_with_errors'
    assert 'Sheet1' in result['processed_sheets']
    
    # Verify valid formula worked
    output_df = pd.read_csv(tmp_path / 'Sheet1.csv')
    assert all(output_df['Valid'] == output_df['Input'] * 2)
    
    # Verify invalid formulas were handled
    assert 'Invalid1' in result['errors']
    assert 'Invalid2' in result['errors']

def test_large_dataset_performance(create_test_excel, sample_config, tmp_path):
    """Test performance with large datasets."""
    
    # Create large test dataset
    num_rows = 10000
    content = {
        'Data': {
            'headers': ['ID', 'Value', 'Group'],
            'data': [
                [i, i * 10, f'Group{i % 5}']
                for i in range(num_rows)
            ]
        },
        'Summary': {
            'headers': ['Group', 'Count', 'Sum', 'Average'],
            'data': [
                [f'Group{i}', None, None, None]
                for i in range(5)
            ],
            'formulas': {
                'Count': ('=COUNTIF(Data!C:C, A1)'),
                'Sum': ('=SUMIF(Data!C:C, A1, Data!B:B)'),
                'Average': ('=AVERAGEIF(Data!C:C, A1, Data!B:B)')
            }
        }
    }
    
    excel_file = create_test_excel(content)
    
    # Enable parallel processing
    config = sample_config.copy()
    config['processing']['parallel'] = True
    config['processing']['chunk_size'] = 1000
    
    import time
    start_time = time.time()
    
    processor = ExcelProcessor(config)
    result = processor.process_file(excel_file, tmp_path)
    
    processing_time = time.time() - start_time
    
    assert result['status'] == 'success'
    assert processing_time < 30  # Should process within reasonable time
    
    # Verify results
    summary_df = pd.read_csv(tmp_path / 'Summary.csv')
    
    # Each group should have num_rows/5 entries
    assert all(summary_df['Count'] == num_rows/5)
    
    # Verify averages
    expected_averages = summary_df['Sum'] / summary_df['Count']
    pd.testing.assert_series_equal(
        summary_df['Average'],
        expected_averages,
        check_names=False
    )