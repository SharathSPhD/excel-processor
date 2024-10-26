# docs/examples/cross_sheet_references.md
# Cross-Sheet Reference Handling

This guide explains how the Excel Processor manages dependencies between different worksheets.

## 1. Direct References

### Excel Structure
```
Sheet1:
A1: 100
B1: =Sheet2!A1

Sheet2:
A1: =Sheet1!A1 * 2
```

### Dependency Resolution
```python
from excel_processor.models import DependencyGraph

# Create dependency graph
graph = DependencyGraph()
graph.add_node("Sheet1.A1", is_input=True)
graph.add_node("Sheet2.A1", formula="Sheet1!A1 * 2")
graph.add_node("Sheet1.B1", formula="Sheet2!A1")

# Get processing order
order = graph.get_processing_order()
print(order)  # ['Sheet1.A1', 'Sheet2.A1', 'Sheet1.B1']
```

## 2. Complex Dependencies

### Excel Structure
```
Sheet1:
A1: =SUM(Sheet2!A1:A10)
B1: =Sheet3!B1

Sheet2:
A1:A10: [values]
B1: =Sheet3!A1

Sheet3:
A1: =Sheet1!A1
B1: =Sheet2!B1
```

### Configuration
```yaml
excel_processor:
  dependency_handling:
    detect_cycles: true
    max_depth: 10
    resolve_order: topological
```

### Error Handling
```python
try:
    graph.validate()
except ValueError as e:
    print(f"Circular dependency detected: {e}")
```

# docs/sample_configs/complex_workbook.yaml
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
    directory: processed_data
    separate_sheets: true
    include_metadata: true
    
  processing:
    parallel: true
    chunk_size: 5000
    max_workers: 4
    memory_limit: 2GB
    
  formula_handling:
    nested_depth: unlimited
    cache_intermediate: true
    array_formula_support: true
    
  dependency_handling:
    detect_cycles: true
    max_depth: 20
    resolve_order: topological
    
  logging:
    level: DEBUG
    file: processor.log
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    rotate: true
    max_size: 10MB
    
  error_handling:
    strict_mode: false
    ignore_missing_refs: false
    default_value: 0
    error_log: errors.log

sheets:
  sheet1:
    name: "Financial Data"
    input_columns:
      - "Revenue"
      - "Costs"
    formula_columns:
      - "Margin"
      - "Percentage"
    dependencies:
      - "Sheet2.Rates"
      
  sheet2:
    name: "Reference Data"
    input_columns:
      - "Rates"
      - "Categories"
    formula_columns:
      - "Adjusted_Rates"
    dependencies: []

validations:
  margin:
    type: range
    min: 0
    max: 1000000
  percentage:
    type: range
    min: 0
    max: 100
  rates:
    type: positive