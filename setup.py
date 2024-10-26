# setup.py
from setuptools import setup, find_packages

setup(
    name="excel-processor",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas>=1.3.0",
        "openpyxl>=3.0.0",
        "pyyaml>=5.4.0",
        "click>=8.0.0",
        "networkx>=2.6.0",
        "pydantic>=1.8.0",
        "numpy>=1.20.0"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b2",
            "isort>=5.9.0",
            "mypy>=0.910",
            "flake8>=3.9.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "excel-processor=excel_processor.cli:cli"
        ]
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A robust Excel processor for complex workbooks",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/excel-processor",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10"
    ]
)