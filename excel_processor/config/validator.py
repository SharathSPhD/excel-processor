# excel_processor/config/validator.py
from typing import Union, Dict, Any
from pathlib import Path
import yaml
from .schema import ExcelProcessorConfig

class ConfigValidator:
    """Validates and processes configuration files."""
    
    def __init__(self):
        self.required_sections = {
            'validation',
            'output',
            'processing',
            'logging'
        }
        
        self.valid_output_formats = {'csv', 'excel', 'parquet'}
        self.valid_validation_levels = {'strict', 'normal', 'relaxed'}
    
    def validate_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate configuration file against schema.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Validated configuration dictionary
        """
        try:
            config_path = Path(config_path)
            
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            # Load configuration
            with open(config_path) as f:
                config_dict = yaml.safe_load(f)
            
            # Validate basic structure
            if not isinstance(config_dict, dict):
                raise ValueError("Invalid configuration format")
            
            processor_config = config_dict.get('excel_processor', {})
            
            # Check required sections
            missing_sections = self.required_sections - set(processor_config.keys())
            if missing_sections:
                raise ValueError(f"Missing required config sections: {missing_sections}")
            
            # Validate individual sections
            self._validate_validation_config(processor_config.get('validation', {}))
            self._validate_output_config(processor_config.get('output', {}))
            self._validate_processing_config(processor_config.get('processing', {}))
            self._validate_logging_config(processor_config.get('logging', {}))
            
            # Create config with defaults
            config = ExcelProcessorConfig(
                **processor_config
            )
            
            return config.dict()
            
        except Exception as e:
            raise ValueError(f"Error validating configuration: {str(e)}")
    
    def _validate_validation_config(self, config: Dict[str, Any]):
        """Validate validation section configuration."""
        if 'level' in config and config['level'] not in self.valid_validation_levels:
            raise ValueError(
                f"Invalid validation level. Must be one of: "
                f"{self.valid_validation_levels}"
            )
        
        if 'tolerance' in config:
            tolerance = config['tolerance']
            if not isinstance(tolerance, (int, float)) or tolerance <= 0:
                raise ValueError("Validation tolerance must be a positive number")
    
    def _validate_output_config(self, config: Dict[str, Any]):
        """Validate output section configuration."""
        if 'format' in config and config['format'] not in self.valid_output_formats:
            raise ValueError(
                f"Invalid output format. Must be one of: {self.valid_output_formats}"
            )
        
        if 'directory' in config:
            directory = config['directory']
            if not isinstance(directory, str):
                raise ValueError("Output directory must be a string")
    
    def _validate_processing_config(self, config: Dict[str, Any]):
        """Validate processing section configuration."""
        if 'parallel' in config and not isinstance(config['parallel'], bool):
            raise ValueError("parallel must be a boolean value")
        
        if 'chunk_size' in config:
            chunk_size = config['chunk_size']
            if not isinstance(chunk_size, int) or chunk_size <= 0:
                raise ValueError("chunk_size must be a positive integer")
        
        if 'max_workers' in config:
            max_workers = config['max_workers']
            if not isinstance(max_workers, int) or max_workers <= 0:
                raise ValueError("max_workers must be a positive integer")
    
    def _validate_logging_config(self, config: Dict[str, Any]):
        """Validate logging section configuration."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if 'level' in config and config['level'] not in valid_levels:
            raise ValueError(f"Invalid logging level. Must be one of: {valid_levels}")

def validate_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate configuration file and return validated config.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Validated configuration dictionary
    """
    validator = ConfigValidator()
    return validator.validate_config(config_path)