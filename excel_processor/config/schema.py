# excel_processor/config/schema.py
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

class ValidationLevel(str, Enum):
    STRICT = "strict"
    NORMAL = "normal"
    RELAXED = "relaxed"

class OutputFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    PARQUET = "parquet"

class ValidationConfig(BaseModel):
    enabled: bool = True
    level: ValidationLevel = ValidationLevel.NORMAL
    tolerance: float = 1e-10
    check_formulas: bool = True
    check_dependencies: bool = True
    compare_outputs: bool = True

class OutputConfig(BaseModel):
    format: OutputFormat = OutputFormat.CSV
    directory: str = "output"
    separate_sheets: bool = True
    include_metadata: bool = True

class ProcessingConfig(BaseModel):
    parallel: bool = False
    chunk_size: Optional[int] = None
    max_workers: int = 4

class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: Optional[str] = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class ExcelProcessorConfig(BaseModel):
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    @validator('processing')
    def validate_processing(cls, v):
        if v.parallel and not v.chunk_size:
            v.chunk_size = 1000
        return v