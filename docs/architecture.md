# docs/architecture.md
# Excel Processor Architecture

## Overview
The Excel Processor is designed to handle complex Excel workbooks with multiple sheets and interdependent formulas. The system follows a modular architecture with clear separation of concerns.

## Core Components

### 1. Excel Parser
- Reads Excel workbooks
- Extracts data, formulas, and dependencies
- Handles cell references and formula parsing

### 2. Formula Processor
- Converts Excel formulas to Python code
- Handles dependencies between sheets
- Manages formula execution order

### 3. Data Processor
- Processes input data
- Applies converted formulas
- Manages data flow between sheets

### 4. Validation System
- Validates processed results against original Excel
- Ensures formula integrity
- Provides detailed validation reports

## Data Flow
1. Excel File → Parser → Raw Data + Formula Information
2. Formula Analysis → Dependency Graph → Processing Order
3. Data Processing → Formula Application → Output Generation
4. Validation → Results Comparison → Validation Report

## Error Handling
- Comprehensive error catching and reporting
- Detailed logging at all stages
- Validation feedback for data integrity
