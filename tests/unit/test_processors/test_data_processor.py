# tests/unit/test_processors/test_data_processor.py
import pytest
import pandas as pd
from excel_processor.processors.data_processor import DataProcessor
from excel_processor.models.dependency_graph import DependencyGraph
from excel_processor.utils.formula_parser import FormulaParser

def test_basic_data_processing(sample_config):
    dependency_graph = DependencyGraph()
    processor = DataProcessor(sample_config, dependency_graph)
    
    input_data = {
        'Sheet1': pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
    }
    
    result = processor.process(input_data)
    assert 'Sheet1' in result
    assert result['Sheet1'].equals(input_data['Sheet1'])

def test_data_processing_with_dependencies(sample_config):
    dependency_graph = DependencyGraph()
    
    # Add nodes and dependencies
    dependency_graph.add_node("Sheet1.A", is_formula=False)
    dependency_graph.add_node("Sheet1.B", is_formula=True, formula="=A*2")
    dependency_graph.add_dependency("Sheet1.B", "Sheet1.A")
    
    processor = DataProcessor(sample_config, dependency_graph)
    
    input_data = {
        'Sheet1': pd.DataFrame({
            'A': [1, 2, 3],
            'B': [0, 0, 0]
        })
    }
    
    result = processor.process(input_data)
    assert 'Sheet1' in result
    assert len(result['Sheet1']) == len(input_data['Sheet1'])

def test_data_processor_validation(sample_config):
    dependency_graph = DependencyGraph()
    processor = DataProcessor(sample_config, dependency_graph)
    
    # Test with missing required columns
    with pytest.raises(ValueError):
        processor.process({})
    
    # Test with mismatched data types
    with pytest.raises(ValueError):
        processor.process({
            'Sheet1': 'not a dataframe'
        })
