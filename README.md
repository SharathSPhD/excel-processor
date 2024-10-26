# README.md
# Excel Processor

A robust Python package for processing complex Excel workbooks with multiple sheets and interdependent formulas.

## Features

- Handle arbitrary number of worksheets
- Process complex Excel formulas
- Track cross-sheet dependencies
- Validate results against original Excel
- Configurable output formats
- Comprehensive error handling
- Detailed logging and reporting

## Installation

```bash
pip install excel-processor
```

## Quick Start

1. Create a configuration file:

```yaml
# config.yaml
excel_processor:
  validation:
    enabled: true
    level: normal
  output:
    format: csv
    directory: output
```

2. Process an Excel file:

```bash
excel-processor process workbook.xlsx config.yaml
```

3. Analyze an Excel file:

```bash
excel-processor analyze workbook.xlsx --output analysis.json
```

## Documentation

Full documentation available at `docs/`:
- [Architecture](docs/architecture.md)
- [Configuration Guide](docs/configuration.md)
- [Contributing Guide](docs/contributing.md)

## Development

1. Clone the repository:
```bash
git clone https://github.com/yourusername/excel-processor.git
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Run tests:
```bash
pytest
```

## License

MIT License - see LICENSE file for details.