# docs/configuration.md
# Configuration Guide

## Basic Configuration
```yaml
excel_processor:
  validation:
    enabled: true
    level: normal
    tolerance: 1e-10
  
  output:
    format: csv
    directory: output
    separate_sheets: true
    
  processing:
    parallel: false
    chunk_size: 1000
    
  logging:
    level: INFO
    file: processor.log
```

## Advanced Configuration
```yaml
excel_processor:
  validation:
    enabled: true
    level: strict
    tolerance: 1e-10
    check_formulas: true
    check_dependencies: true
    compare_outputs: true
    
  output:
    format: csv
    directory: output
    separate_sheets: true
    include_metadata: true
    compression: none
    
  processing:
    parallel: true
    chunk_size: 5000
    max_workers: 4
    memory_limit: 1GB
    
  logging:
    level: DEBUG
    file: processor.log
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    rotate: true
    max_size: 10MB
```