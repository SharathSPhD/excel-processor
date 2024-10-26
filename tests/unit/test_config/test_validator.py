# tests/unit/test_config/test_validator.py
import pytest
from pathlib import Path
from excel_processor.config.validator import validate_config

def test_validate_config(tmp_path):
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        f.write("""
excel_processor:
  validation:
    enabled: true
    level: strict
  output:
    format: csv
    directory: output
  processing:
    parallel: false
    chunk_size: 1000
  logging:
    level: INFO
""")
    
    config = validate_config(config_path)
    assert config['validation']['enabled']
    assert config['validation']['level'] == 'strict'
    assert config['output']['format'] == 'csv'
    assert config['processing']['parallel'] is False

def test_missing_config_file():
    with pytest.raises(ValueError, match="Config file not found"):
        validate_config("nonexistent.yaml")

def test_invalid_config_format(tmp_path):
    config_path = tmp_path / "invalid.yaml"
    with open(config_path, 'w') as f:
        f.write("invalid: yaml: content")
    
    with pytest.raises(ValueError, match="Invalid configuration"):
        validate_config(config_path)