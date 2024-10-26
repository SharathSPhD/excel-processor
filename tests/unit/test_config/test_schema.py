# tests/unit/test_config/test_schema.py
import pytest
from excel_processor.config.schema import (
    ExcelProcessorConfig,
    ValidationConfig,
    OutputConfig,
    ValidationLevel
)

def test_validation_config():
    config = ValidationConfig(
        enabled=True,
        level=ValidationLevel.STRICT,
        tolerance=1e-10
    )
    assert config.enabled
    assert config.level == ValidationLevel.STRICT
    assert config.tolerance == 1e-10

def test_output_config():
    config = OutputConfig(
        format='csv',
        directory='output',
        separate_sheets=True
    )
    assert config.format == 'csv'
    assert config.directory == 'output'
    assert config.separate_sheets

def test_full_config():
    config_dict = {
        'validation': {
            'enabled': True,
            'level': 'strict',
            'tolerance': 1e-10
        },
        'output': {
            'format': 'csv',
            'directory': 'output'
        },
        'processing': {
            'parallel': True,
            'chunk_size': 1000
        }
    }
    
    config = ExcelProcessorConfig(**config_dict)
    assert config.validation.enabled
    assert config.output.format == 'csv'
    assert config.processing.parallel

def test_invalid_config():
    with pytest.raises(ValueError):
        ValidationConfig(level='invalid_level')
    
    with pytest.raises(ValueError):
        OutputConfig(format='invalid_format')