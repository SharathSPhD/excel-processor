# excel_processor/processors/data_processor.py
from typing import Dict, Any
import pandas as pd
from .base import BaseProcessor
from ..models.dependency_graph import DependencyGraph

class DataProcessor(BaseProcessor):
    def __init__(self, config: Dict[str, Any], dependency_graph: DependencyGraph):
        super().__init__(config)
        self.dependency_graph = dependency_graph
        
    def process(self, input_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Process all data according to dependency order"""
        processed = {}
        processing_order = self.dependency_graph.get_processing_order()
        
        # Initialize with input data
        for sheet_name, df in input_data.items():
            processed[sheet_name] = df.copy()
        
        # Process in dependency order
        for node in processing_order:
            sheet_name, col = node.split('.')
            if self.dependency_graph.graph.nodes[node].get('is_formula'):
                self._process_dependent_column(
                    sheet_name, col, processed
                )
                
        return processed
    
    def _process_dependent_column(self,
                                sheet_name: str,
                                column: str,
                                data: Dict[str, pd.DataFrame]):
        """Process a single dependent column"""
        node = f"{sheet_name}.{column}"
        formula = self.dependency_graph.graph.nodes[node].get('formula')
        if formula:
            # Process using formula processor
            # Implementation depends on formula processor integration
            pass