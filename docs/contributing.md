# docs/contributing.md
# Contributing to Excel Processor

Thank you for considering contributing to Excel Processor! This document outlines the process and guidelines for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/yourusername/excel-processor.git
cd excel-processor
```

3. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

4. Install development dependencies:
```bash
pip install -e ".[dev]"
```

5. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes

3. Run tests:
```bash
pytest
```

4. Run code quality checks:
```bash
black excel_processor tests
isort excel_processor tests
flake8 excel_processor tests
mypy excel_processor
```

5. Commit your changes:
```bash
git add .
git commit -m "Description of changes"
```

6. Push to your fork:
```bash
git push origin feature/your-feature-name
```

7. Create a Pull Request

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings in Google format
- Keep functions focused and small
- Add tests for new features

## Testing

- Write unit tests for new features
- Include integration tests for complex functionality
- Maintain test coverage above 80%
- Use pytest fixtures for common test setup

## Documentation

- Update relevant documentation
- Include docstrings for public APIs
- Add examples for new features
- Update CHANGELOG.md
