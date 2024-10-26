# excel_processor/processors/formula_processor.py
from typing import Dict, Any, Set, List, Optional
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from ..models.formula import Formula, FormulaType
from ..models.dependency_graph import DependencyGraph
from ..utils.formula_parser import FormulaParser  # Changed this import
from .base import BaseProcessor

class FormulaProcessor(BaseProcessor):
    """Processes Excel formulas with support for parallel execution and array formulas."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.formula_cache: Dict[str, Formula] = {}
        self.dependency_graph = DependencyGraph()
        self.parallel = config.get('processing', {}).get('parallel', False)
        self.chunk_size = config.get('processing', {}).get('chunk_size', 1000)
        self.max_workers = config.get('processing', {}).get('max_workers', 4)
        self._context_cache: Dict[str, Dict[str, Any]] = {}
        self.formula_parser = FormulaParser()  # Added this line
    
    def parse_formula(self, formula: str, sheet_name: str, column: str) -> Formula:
        """Parse Excel formula and create Formula object."""
        return self.formula_parser.parse(formula, sheet_name, column)
    
    def process(self, sheet_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Process all formulas across sheets."""
        try:
            # Validate input data
            self._validate_input_data(sheet_data)
            
            # Get processing order from dependency graph
            processing_order = self.dependency_graph.get_processing_order()
            
            # Initialize result with input data
            result_data = {name: df.copy() for name, df in sheet_data.items()}
            
            # Process formulas in order
            for node_id in processing_order:
                if self.dependency_graph.graph.nodes[node_id].get('is_formula'):
                    sheet_name, column = node_id.split('.')
                    formula = self.formula_cache.get(node_id)
                    if formula:
                        result_data[sheet_name][column] = self._process_formula(
                            formula, result_data
                        )
            
            return result_data
            
        except Exception as e:
            raise ValueError(f"Error processing formulas: {str(e)}")

    # ... rest of the code remains the same ...
    
    def _process_formula(self, 
                        formula: Formula,
                        data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Process a single formula."""
        try:
            # Check if parallel processing should be used
            if (self.parallel and 
                len(data[formula.sheet_name]) > self.chunk_size):
                return self._process_formula_parallel(formula, data)
            else:
                return self._process_formula_single(formula, data)
                
        except Exception as e:
            raise ValueError(
                f"Error processing formula {formula.raw_formula}: {str(e)}"
            )
    
    def _process_formula_single(self,
                              formula: Formula,
                              data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Process formula in single-threaded mode."""
        try:
            # Get or create context
            context = self._get_evaluation_context(formula, data)
            
            # Handle different formula types
            if formula.formula_type == FormulaType.LOOKUP:
                return self._handle_lookup_formula(formula, context)
            elif formula.formula_type == FormulaType.AGGREGATE:
                return self._handle_aggregate_formula(formula, context)
            elif formula.formula_type == FormulaType.ARRAY:
                return self._handle_array_formula(formula, context)
            else:
                # Standard formula evaluation
                result = eval(formula.python_equivalent, context)
                return self._convert_to_series(result, len(data[formula.sheet_name]))
                
        except Exception as e:
            raise ValueError(f"Error in formula evaluation: {str(e)}")
    
    def _process_formula_parallel(self,
                                formula: Formula,
                                data: Dict[str, pd.DataFrame]) -> pd.Series:
        """Process formula using parallel execution."""
        try:
            df = data[formula.sheet_name]
            
            # Ensure all dependent data is available
            for dep in formula.dependencies:
                sheet_name = dep.split('!')[0] if '!' in dep else formula.sheet_name
                if sheet_name not in data:
                    raise ValueError(f"Missing dependent sheet: {sheet_name}")
            
            # Split data into chunks
            chunk_size = min(self.chunk_size, len(df))
            chunks = np.array_split(df, max(1, len(df) // chunk_size))
            
            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                for chunk in chunks:
                    chunk_data = {
                        sheet: (chunk if sheet == formula.sheet_name 
                               else df_copy.copy())
                        for sheet, df_copy in data.items()
                    }
                    futures.append(
                        executor.submit(
                            self._process_formula_single,
                            formula,
                            chunk_data
                        )
                    )
                
                # Collect results
                results = []
                for future in futures:
                    try:
                        results.append(future.result())
                    except Exception as e:
                        raise ValueError(
                            f"Error in parallel processing: {str(e)}"
                        )
            
            return pd.concat(results, axis=0)
            
        except Exception as e:
            raise ValueError(f"Error in parallel processing: {str(e)}")
    
    def _get_evaluation_context(self,
                              formula: Formula,
                              data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Create context for formula evaluation."""
        context = {
            'np': np,
            'pd': pd,
            'data': data,
            'df': data[formula.sheet_name]
        }
        
        # Add helper functions
        context.update({
            'to_numeric': lambda x: pd.to_numeric(x, errors='coerce'),
            'to_datetime': lambda x: pd.to_datetime(x, errors='coerce'),
            'coalesce': lambda *args: next((arg for arg in args if pd.notna(arg)), None),
            'is_error': lambda x: pd.isna(x) | (x == '#ERROR!'),
            'if_error': lambda x, default: default if context['is_error'](x) else x
        })
        
        # Add array operation helpers
        context.update({
            'broadcast': lambda x: np.broadcast_to(x, (len(context['df']),)),
            'array_if': lambda c, t, f: np.where(c, t, f),
            'array_sum': lambda x: np.sum(x, axis=1) if len(x.shape) > 1 else x
        })
        
        return context
    
    def _convert_to_series(self, result: Any, length: int) -> pd.Series:
        """Convert formula result to pandas Series."""
        if isinstance(result, pd.Series):
            return result
        elif isinstance(result, pd.DataFrame):
            if result.shape[1] == 1:
                return result.iloc[:, 0]
            else:
                raise ValueError("Formula resulted in multiple columns")
        elif isinstance(result, np.ndarray):
            if len(result.shape) == 1:
                return pd.Series(result)
            else:
                return pd.Series(result.flatten())
        else:
            # Scalar result - broadcast to all rows
            return pd.Series([result] * length)
    
    def _handle_lookup_formula(self,
                             formula: Formula,
                             context: Dict[str, Any]) -> pd.Series:
        """Handle VLOOKUP, HLOOKUP type formulas."""
        try:
            result = eval(formula.python_equivalent, context)
            return self._convert_to_series(result, len(context['df']))
        except Exception as e:
            raise ValueError(f"Error in lookup formula: {str(e)}")
    
    def _handle_aggregate_formula(self,
                                formula: Formula,
                                context: Dict[str, Any]) -> pd.Series:
        """Handle SUM, AVERAGE type formulas."""
        try:
            result = eval(formula.python_equivalent, context)
            if np.isscalar(result):
                return pd.Series([result] * len(context['df']))
            return self._convert_to_series(result, len(context['df']))
        except Exception as e:
            raise ValueError(f"Error in aggregate formula: {str(e)}")
    
    def _handle_array_formula(self,
                            formula: Formula,
                            context: Dict[str, Any]) -> pd.Series:
        """Handle array formulas with broadcasting."""
        try:
            result = eval(formula.python_equivalent, context)
            if isinstance(result, np.ndarray):
                if len(result.shape) > 1:
                    result = np.sum(result, axis=1)
                return pd.Series(result)
            else:
                return pd.Series([result] * len(context['df']))
        except Exception as e:
            raise ValueError(f"Error in array formula: {str(e)}")
    
    def _validate_input_data(self, data: Dict[str, pd.DataFrame]):
        """Validate input data before processing."""
        if not data:
            raise ValueError("No input data provided")
            
        for sheet_name, df in data.items():
            if not isinstance(df, pd.DataFrame):
                raise ValueError(
                    f"Invalid data type for sheet {sheet_name}: "
                    f"expected DataFrame, got {type(df)}"
                )
            
            if df.empty:
                raise ValueError(f"Empty DataFrame for sheet {sheet_name}")
    
    def clear_cache(self):
        """Clear formula and context caches."""
        self.formula_cache.clear()
        self._context_cache.clear()