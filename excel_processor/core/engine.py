# excel_processor/core/engine.py
from pathlib import Path
from typing import Dict, Any, Optional, Generator, List
import pandas as pd
import logging
from ..core.excel_reader import ExcelReader
from ..processors.formula_processor import FormulaProcessor
from ..processors.data_processor import DataProcessor
from ..validators.excel_validator import ExcelValidator
from ..models.worksheet import WorksheetInfo

class ExcelProcessor:
    """Main engine for processing Excel workbooks."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Excel processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.excel_reader = None
        self.formula_processor = FormulaProcessor(config)
        self.data_processor = DataProcessor(config)
        self.validator = ExcelValidator(config.get('validation', {}))
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def process_file(self, 
                    excel_path: str,
                    output_dir: Path,
                    chunk_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Process Excel file and generate outputs.
        
        Args:
            excel_path: Path to Excel file
            output_dir: Directory for output files
            chunk_size: Optional chunk size for large files
            
        Returns:
            Dictionary containing processing results
        """
        try:
            self.logger.info(f"Processing Excel file: {excel_path}")
            
            # Initialize reader and read workbook
            self.excel_reader = ExcelReader(excel_path)
            worksheet_info = self.excel_reader.read_workbook()
            
            # Determine if chunked processing is needed
            if chunk_size and any(len(info.data) > chunk_size 
                                for info in worksheet_info.values()):
                self.logger.info("Using chunked processing")
                result = self._process_in_chunks(worksheet_info, chunk_size, output_dir)
            else:
                self.logger.info("Processing entire workbook")
                result = self._process_full(worksheet_info, output_dir)
            
            self.logger.info("Processing completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}")
            raise
        finally:
            if self.excel_reader:
                self.excel_reader.close()
    
    def _process_full(self,
                     worksheet_info: Dict[str, WorksheetInfo],
                     output_dir: Optional[Path]) -> Dict[str, Any]:
        """Process entire workbook at once."""
        try:
            # Process formulas
            processed_data = self.formula_processor.process(
                {name: info.data for name, info in worksheet_info.items()}
            )
            
            # Validate results if enabled
            validation_results = None
            if self.config.get('validation', {}).get('enabled', True):
                validation_results = self.validator.validate(
                    original_data=worksheet_info,
                    processed_data=processed_data
                )
            
            # Save outputs if directory provided
            if output_dir:
                self._save_outputs(processed_data, output_dir)
            
            return {
                'status': 'success',
                'processed_sheets': processed_data,
                'validation_results': validation_results
            }
            
        except Exception as e:
            self.logger.error(f"Error in full processing: {str(e)}")
            raise
    
    def _process_in_chunks(self,
                          worksheet_info: Dict[str, WorksheetInfo],
                          chunk_size: int,
                          output_dir: Optional[Path]) -> Dict[str, Any]:
        """Process workbook in chunks for memory efficiency."""
        try:
            # Initialize output containers
            results = {name: [] for name in worksheet_info.keys()}
            validation_results = []
            
            # Process chunks
            for chunk_data in self._chunk_processing(worksheet_info, chunk_size):
                # Process chunk
                chunk_info = {
                    name: WorksheetInfo(
                        name=info.name,
                        data=chunk_data[name],
                        formulas=info.formulas,
                        input_columns=info.input_columns
                    )
                    for name, info in worksheet_info.items()
                    if name in chunk_data
                }
                
                chunk_results = self._process_full(chunk_info, None)
                
                # Collect results
                for sheet_name, chunk_df in chunk_results['processed_sheets'].items():
                    results[sheet_name].append(chunk_df)
                
                if chunk_results.get('validation_results'):
                    validation_results.append(chunk_results['validation_results'])
            
            # Combine chunks
            final_results = {}
            for sheet_name, chunks in results.items():
                if chunks:
                    final_df = pd.concat(chunks, axis=0, ignore_index=True)
                    final_results[sheet_name] = final_df
                    
                    if output_dir:
                        output_path = output_dir / f"{sheet_name}.csv"
                        final_df.to_csv(output_path, index=False)
            
            return {
                'status': 'success',
                'processed_sheets': final_results,
                'validation_results': self._combine_validation_results(validation_results)
            }
            
        except Exception as e:
            self.logger.error(f"Error in chunked processing: {str(e)}")
            raise
    
    def _chunk_processing(self,
                         worksheet_info: Dict[str, WorksheetInfo],
                         chunk_size: int) -> Generator:
        """Generate chunks of data for processing."""
        sheets = list(worksheet_info.keys())
        total_rows = max(len(info.data) for info in worksheet_info.values())
        
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            
            chunk_data = {}
            for sheet in sheets:
                sheet_data = worksheet_info[sheet].data
                if len(sheet_data) > start_idx:
                    chunk_end = min(end_idx, len(sheet_data))
                    chunk_data[sheet] = sheet_data.iloc[start_idx:chunk_end].copy()
            
            yield chunk_data
    
    def _save_outputs(self, 
                     processed_data: Dict[str, pd.DataFrame],
                     output_dir: Path):
        """Save processed data to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_format = self.config.get('output', {}).get('format', 'csv')
        
        for sheet_name, df in processed_data.items():
            output_path = output_dir / f"{sheet_name}.{output_format}"
            if output_format == 'csv':
                df.to_csv(output_path, index=False)
            elif output_format == 'excel':
                df.to_excel(output_path, index=False)
            elif output_format == 'parquet':
                df.to_parquet(output_path, index=False)
    
    def _combine_validation_results(self,
                                  validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine validation results from multiple chunks."""
        if not validation_results:
            return None
            
        combined = {
            'status': 'success',
            'sheets': {},
            'errors': [],
            'warnings': []
        }
        
        for result in validation_results:
            if result['status'] != 'success':
                combined['status'] = 'error'
            
            combined['errors'].extend(result.get('errors', []))
            combined['warnings'].extend(result.get('warnings', []))
            
            for sheet, sheet_result in result.get('sheets', {}).items():
                if sheet not in combined['sheets']:
                    combined['sheets'][sheet] = {
                        'status': sheet_result['status'],
                        'errors': sheet_result.get('errors', []),
                        'warnings': sheet_result.get('warnings', []),
                        'metrics': sheet_result.get('metrics', {})
                    }
                else:
                    if sheet_result['status'] != 'success':
                        combined['sheets'][sheet]['status'] = 'error'
                    combined['sheets'][sheet]['errors'].extend(
                        sheet_result.get('errors', [])
                    )
                    combined['sheets'][sheet]['warnings'].extend(
                        sheet_result.get('warnings', [])
                    )
                    # Update metrics with worst case values
                    for metric, value in sheet_result.get('metrics', {}).items():
                        if metric in combined['sheets'][sheet]['metrics']:
                            if 'error' in metric.lower():
                                combined['sheets'][sheet]['metrics'][metric] = max(
                                    combined['sheets'][sheet]['metrics'][metric],
                                    value
                                )
                            else:
                                combined['sheets'][sheet]['metrics'][metric] = min(
                                    combined['sheets'][sheet]['metrics'][metric],
                                    value
                                )
                        else:
                            combined['sheets'][sheet]['metrics'][metric] = value
        
        return combined
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging_config = self.config.get('logging', {})
        
        logging.basicConfig(
            level=logging_config.get('level', 'INFO'),
            format=logging_config.get(
                'format',
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ),
            filename=logging_config.get('file')
        )