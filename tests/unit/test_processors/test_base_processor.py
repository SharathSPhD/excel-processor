# tests/unit/test_processors/test_base_processor.py
import pytest
import pandas as pd
from excel_processor.processors.base import BaseProcessor

@pytest.fixture
def test_processor():
    """Fixture to create a concrete processor for testing."""
    class TestProcessor(BaseProcessor):
        def process(self, data):
            return data
    
    return TestProcessor({'test': 'config'})

def test_base_processor_initialization(test_processor):
    """Test basic initialization of BaseProcessor."""
    assert test_processor.config == {'test': 'config'}

def test_validate_input(test_processor):
    """Test default input validation."""
    assert test_processor.validate_input({'test': 'data'}) is True

def test_abstract_process_method():
    """Test that BaseProcessor cannot be instantiated without process method."""
    with pytest.raises(TypeError):
        BaseProcessor({'test': 'config'})

def test_concrete_implementation(test_processor):
    """Test concrete implementation of BaseProcessor."""
    test_data = {'test': 'data'}
    result = test_processor.process(test_data)
    assert result == test_data