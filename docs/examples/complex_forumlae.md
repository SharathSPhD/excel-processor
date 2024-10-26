# docs/examples/complex_formulas.md
# Handling Complex Excel Formulas

This guide demonstrates how the Excel Processor handles various complex Excel formulas.

## 1. Nested Functions

### Excel Formula
```excel
=IF(SUM(A1:A10)>100, AVERAGE(B1:B10), MAX(C1:C10))
```

### Configuration
```yaml
excel_processor:
  formula_handling:
    nested_depth: unlimited
    cache_intermediate: true
```

### Python Implementation
```python
from excel_processor import ExcelProcessor

processor = ExcelProcessor('config.yaml')
formula = processor.parse_formula('=IF(SUM(A1:A10)>100, AVERAGE(B1:B10), MAX(C1:C10))')
print(formula.python_equivalent)
```

Output:
```python
np.where(
    df.loc['A1':'A10'].sum() > 100,
    df.loc['B1':'B10'].mean(),
    df.loc['C1':'C10'].max()
)
```

## 2. VLOOKUP and INDEX/MATCH

### Excel Formula
```excel
=VLOOKUP(A2, Sheet2!$A$1:$C$100, 2, FALSE)
```

### Python Equivalent
```python
result_df = pd.merge(
    df1[['A2']],
    df2.iloc[0:100, 0:3],
    left_on='A2',
    right_on='A',
    how='left'
)['B']
```

## 3. Array Formulas

### Excel Formula
```excel
{=SUM(IF(A1:A100>0, B1:B100, 0))}
```

### Python Equivalent
```python
np.sum(np.where(df['A'].iloc[0:100] > 0, df['B'].iloc[0:100], 0))
```