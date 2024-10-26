# excel_processor/utils/excel_utils.py
import re
from typing import Set, Tuple
import openpyxl
from openpyxl.utils import get_column_letter, column_index_from_string

def extract_cell_references(formula: str) -> Set[str]:
    """Extract cell references from Excel formula"""
    # Match patterns like Sheet1!A1, Sheet1!$A$1, A1:B2
    pattern = r'([A-Za-z0-9_]+!)?\$?[A-Z]+\$?\d+(?::\$?[A-Z]+\$?\d+)?'
    references = set(re.findall(pattern, formula))
    return references

def parse_cell_reference(ref: str) -> Tuple[str, str, int]:
    """Parse Excel cell reference into components"""
    match = re.match(r'(?:(\w+)!)?([A-Z]+)(\d+)', ref)
    if match:
        sheet, col, row = match.groups()
        return (sheet or '', col, int(row))
    raise ValueError(f"Invalid cell reference: {ref}")

def get_column_range(sheet: openpyxl.worksheet.worksheet.Worksheet) -> Tuple[int, int]:
    """Get the valid column range for a worksheet"""
    min_col = 1
    max_col = 1
    
    for row in sheet.iter_rows():
        for cell in row:
            if cell.value is not None:
                max_col = max(max_col, cell.column)
                
    return min_col, max_col