# excel_processor/validators/base_validator.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from ..models.worksheet import WorksheetInfo
from ..models.formula import Formula

class BaseValidator(ABC):
    """Base class for all validators in the Excel processor."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize validator with configuration.
        
        Args:
            config: Validation configuration dictionary
        """
        self.config = config
        self.tolerance = config.get('tolerance', 1e-10)
        self.strict_mode = config.get('strict_mode', False)
        self.validation_cache: Dict[str, Any] = {}
    
    @abstractmethod
    def validate(self, 
                original_data: Dict[str, Any],
                processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate processed data against original data.
        
        Args:
            original_data: Original data for validation
            processed_data: Processed data to validate
            
        Returns:
            Dictionary containing validation results
        """
        pass
    
    def _validate_structure(self,
                          original: pd.DataFrame,
                          processed: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate structural consistency between original and processed data.
        
        Args:
            original: Original DataFrame
            processed: Processed DataFrame
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check shapes
        if original.shape != processed.shape:
            errors.append(
                f"Shape mismatch: original {original.shape} vs processed {processed.shape}"
            )
            return False, errors
            
        # Check column names
        if not original.columns.equals(processed.columns):
            missing_cols = set(original.columns) - set(processed.columns)
            extra_cols = set(processed.columns) - set(original.columns)
            if missing_cols:
                errors.append(f"Missing columns in processed data: {missing_cols}")
            if extra_cols:
                errors.append(f"Extra columns in processed data: {extra_cols}")
            return False, errors
            
        return len(errors) == 0, errors
    
    def _validate_data_types(self,
                           original: pd.DataFrame,
                           processed: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate data type consistency.
        
        Args:
            original: Original DataFrame
            processed: Processed DataFrame
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        for col in original.columns:
            orig_type = original[col].dtype
            proc_type = processed[col].dtype
            
            # Check if types are compatible
            if not self._are_types_compatible(orig_type, proc_type):
                errors.append(
                    f"Type mismatch in column {col}: "
                    f"original {orig_type} vs processed {proc_type}"
                )
                
        return len(errors) == 0, errors
    
    def _are_types_compatible(self, type1: np.dtype, type2: np.dtype) -> bool:
        """
        Check if two data types are compatible.
        
        Args:
            type1: First data type
            type2: Second data type
            
        Returns:
            True if types are compatible, False otherwise
        """
        # Both numeric
        if (pd.api.types.is_numeric_dtype(type1) and 
            pd.api.types.is_numeric_dtype(type2)):
            return True
            
        # Both datetime
        if (pd.api.types.is_datetime64_any_dtype(type1) and 
            pd.api.types.is_datetime64_any_dtype(type2)):
            return True
            
        # Both string/object
        if (pd.api.types.is_string_dtype(type1) and 
            pd.api.types.is_string_dtype(type2)):
            return True
            
        # If one is object, allow it (might contain mixed types)
        if pd.api.types.is_object_dtype(type1) or pd.api.types.is_object_dtype(type2):
            return True
            
        return type1 == type2
    
    def _validate_numeric_values(self,
                               original: pd.Series,
                               processed: pd.Series) -> Tuple[bool, Dict[str, float]]:
        """
        Validate numeric values within tolerance.
        
        Args:
            original: Original Series
            processed: Processed Series
            
        Returns:
            Tuple of (is_valid, metrics)
        """
        if not (pd.api.types.is_numeric_dtype(original) and 
                pd.api.types.is_numeric_dtype(processed)):
            return True, {}
            
        # Calculate differences
        diff = np.abs(original - processed)
        max_diff = diff.max()
        mean_diff = diff.mean()
        
        # Calculate metrics
        metrics = {
            'max_absolute_error': float(max_diff),
            'mean_absolute_error': float(mean_diff),
            'within_tolerance': float(
                (diff <= self.tolerance).mean() * 100  # percentage
            )
        }
        
        is_valid = max_diff <= self.tolerance if self.strict_mode else True
        
        return is_valid, metrics
    
    def _validate_formula_result(self,
                               formula: Formula,
                               original_series: pd.Series,
                               processed_series: pd.Series) -> Tuple[bool, List[str]]:
        """
        Validate formula calculation results.
        
        Args:
            formula: Formula object
            original_series: Original result Series
            processed_series: Processed result Series
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Check for NaN consistency
            orig_nulls = original_series.isna()
            proc_nulls = processed_series.isna()
            if not orig_nulls.equals(proc_nulls):
                errors.append(
                    f"Mismatch in NaN values for formula {formula.raw_formula}"
                )
            
            # Remove NaN values for comparison
            orig_clean = original_series[~orig_nulls]
            proc_clean = processed_series[~proc_nulls]
            
            # Compare non-NaN values
            if len(orig_clean) > 0 and len(proc_clean) > 0:
                is_valid, metrics = self._validate_numeric_values(
                    orig_clean, proc_clean
                )
                if not is_valid:
                    errors.append(
                        f"Formula {formula.raw_formula} results differ: {metrics}"
                    )
                    
        except Exception as e:
            errors.append(f"Error validating formula {formula.raw_formula}: {str(e)}")
            
        return len(errors) == 0, errors
    
    def _generate_validation_report(self,
                                  validation_results: Dict[str, Any]) -> str:
        """
        Generate a readable validation report.
        
        Args:
            validation_results: Validation results dictionary
            
        Returns:
            Formatted validation report string
        """
        report = ["Validation Report", "================\n"]
        
        overall_status = validation_results.get('status', 'unknown')
        report.append(f"Overall Status: {overall_status}\n")
        
        if 'sheets' in validation_results:
            report.append("Sheet Details:")
            for sheet_name, sheet_results in validation_results['sheets'].items():
                report.append(f"\n{sheet_name}:")
                report.append(f"  Status: {sheet_results.get('status', 'unknown')}")
                
                if 'metrics' in sheet_results:
                    report.append("  Metrics:")
                    for metric, value in sheet_results['metrics'].items():
                        report.append(f"    {metric}: {value}")
                        
                if 'errors' in sheet_results and sheet_results['errors']:
                    report.append("  Errors:")
                    for error in sheet_results['errors']:
                        report.append(f"    - {error}")
                        
        if 'errors' in validation_results and validation_results['errors']:
            report.append("\nGlobal Errors:")
            for error in validation_results['errors']:
                report.append(f"  - {error}")
                
        return "\n".join(report)