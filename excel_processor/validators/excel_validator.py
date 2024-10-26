# excel_processor/validators/excel_validator.py
from typing import Dict, Any
import pandas as pd
import numpy as np
from .base_validator import BaseValidator

class ExcelValidator(BaseValidator):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tolerance = config.get('tolerance', 1e-10)
        
    def validate(self, 
                original_data: Dict[str, pd.DataFrame],
                processed_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate processed results against original Excel data"""
        validation_results = {
            'overall_status': 'success',
            'sheets': {},
            'errors': []
        }
        
        for sheet_name in original_data.keys():
            sheet_validation = self._validate_sheet(
                original_data[sheet_name],
                processed_data.get(sheet_name),
                sheet_name
            )
            validation_results['sheets'][sheet_name] = sheet_validation
            
            if sheet_validation['status'] != 'success':
                validation_results['overall_status'] = 'failed'
                validation_results['errors'].extend(sheet_validation['errors'])
                
        return validation_results
    
    def _validate_sheet(self,
                       original: pd.DataFrame,
                       processed: pd.DataFrame,
                       sheet_name: str) -> Dict[str, Any]:
        """Validate a single sheet"""
        result = {
            'status': 'success',
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        if processed is None:
            result['status'] = 'failed'
            result['errors'].append(f"Missing processed data for sheet {sheet_name}")
            return result
            
        # Validate structure
        if not self._validate_structure(original, processed, result):
            return result
            
        # Validate values
        self._validate_values(original, processed, result)
        
        # Calculate validation metrics
        result['metrics'] = self._calculate_metrics(original, processed)
        
        return result
    
    def _validate_structure(self,
                          original: pd.DataFrame,
                          processed: pd.DataFrame,
                          result: Dict[str, Any]) -> bool:
        """Validate structural consistency"""
        if original.shape != processed.shape:
            result['status'] = 'failed'
            result['errors'].append(
                f"Shape mismatch: original {original.shape} vs processed {processed.shape}"
            )
            return False
            
        if not original.columns.equals(processed.columns):
            result['status'] = 'failed'
            result['errors'].append("Column mismatch between original and processed data")
            return False
            
        return True
    
    def _validate_values(self,
                        original: pd.DataFrame,
                        processed: pd.DataFrame,
                        result: Dict[str, Any]):
        """Validate numerical values within tolerance"""
        for col in original.columns:
            if pd.api.types.is_numeric_dtype(original[col]):
                diff = np.abs(original[col] - processed[col])
                if (diff > self.tolerance).any():
                    result['status'] = 'failed'
                    result['errors'].append(
                        f"Value mismatch in column {col}: max diff {diff.max()}"
                    )
    
    def _calculate_metrics(self,
                         original: pd.DataFrame,
                         processed: pd.DataFrame) -> Dict[str, float]:
        """Calculate validation metrics"""
        metrics = {
            'max_absolute_error': 0.0,
            'mean_absolute_error': 0.0,
            'matching_cells_percentage': 0.0
        }
        
        numeric_cols = [col for col in original.columns 
                       if pd.api.types.is_numeric_dtype(original[col])]
        
        if numeric_cols:
            all_diffs = []
            for col in numeric_cols:
                diff = np.abs(original[col] - processed[col])
                all_diffs.extend(diff.dropna())
            
            if all_diffs:
                metrics['max_absolute_error'] = max(all_diffs)
                metrics['mean_absolute_error'] = sum(all_diffs) / len(all_diffs)
                matching_cells = sum(1 for d in all_diffs if d <= self.tolerance)
                metrics['matching_cells_percentage'] = (
                    matching_cells / len(all_diffs) * 100
                )
                
        return metrics