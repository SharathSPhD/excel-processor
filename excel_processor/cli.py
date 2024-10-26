# excel_processor/cli.py
import click
import logging
from pathlib import Path
from typing import Optional
from .config.validator import validate_config
from .core.engine import ExcelProcessor

def setup_logging(config: dict):
    """Setup logging based on configuration"""
    logging_config = config.get('logging', {})
    logging.basicConfig(
        level=logging_config.get('level', 'INFO'),
        format=logging_config.get('format'),
        filename=logging_config.get('file')
    )

@click.group()
def cli():
    """Excel Processor CLI"""
    pass

@cli.command()
@click.argument('excel_file', type=click.Path(exists=True))
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory')
@click.option('--validate/--no-validate', default=True, help='Enable/disable validation')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def process(
    excel_file: str,
    config_file: str,
    output_dir: Optional[str],
    validate: bool,
    verbose: bool
):
    """Process Excel file using specified configuration"""
    try:
        # Load and validate configuration
        config = validate_config(config_file)
        
        # Override config with CLI options
        if output_dir:
            config['output']['directory'] = output_dir
        config['validation']['enabled'] = validate
        
        if verbose:
            config['logging']['level'] = 'DEBUG'
        
        # Setup logging
        if config is not None:
            setup_logging(config)
        logger = logging.getLogger(__name__)
        
        # Initialize processor
        processor = ExcelProcessor(config)
        
        # Process Excel file
        output_path = Path(output_dir) if output_dir else None
        results = processor.process_file(
            excel_file,
            output_path
        )
        
        # Display results summary
        if results['status'] == 'success':
            logger.info("Processing completed successfully")
            for sheet, sheet_results in results['processed_sheets'].items():
                logger.info(f"Processed sheet: {sheet}")
                if 'validation_results' in sheet_results:
                    logger.info(f"Validation metrics for {sheet}:")
                    for metric, value in sheet_results['validation_results'].items():
                        logger.info(f"  {metric}: {value}")
        else:
            logger.error("Processing failed")
            for error in results.get('errors', []):
                logger.error(f"Error: {error}")
            raise click.Abort()
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise click.Abort()

@cli.command()
@click.argument('excel_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output analysis file')
def analyze(excel_file: str, output: Optional[str]):
    """Analyze Excel file structure and dependencies"""
    try:
        from excel_processor.core.excel_reader import ExcelReader
        
        reader = ExcelReader(excel_file)
        worksheet_info = reader.read_workbook()
        
        # Create analysis report
        report = {
            'sheets': {},
            'cross_references': []
        }
        
        for sheet_name, info in worksheet_info.items():
            report['sheets'][sheet_name] = {
                'input_columns': list(info.input_columns),
                'formula_columns': list(info.formulas.keys()),
                'row_count': len(info.data),
                'column_count': len(info.data.columns)
            }
            
            # Analyze cross-references
            for col, formula in info.formulas.items():
                deps = info.dependencies.get(col, set())
                if deps:
                    report['cross_references'].append({
                        'from_sheet': sheet_name,
                        'from_column': col,
                        'references': list(deps)
                    })
        
        # Output report
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(report, f, indent=2)
            click.echo(f"Analysis saved to {output}")
        else:
            click.echo("Excel File Analysis:")
            click.echo("\nSheets:")
            for sheet, sheet_info in report['sheets'].items():
                click.echo(f"\n{sheet}:")
                click.echo(f"  Input columns: {', '.join(sheet_info['input_columns'])}")
                click.echo(f"  Formula columns: {', '.join(sheet_info['formula_columns'])}")
                click.echo(f"  Rows: {sheet_info['row_count']}")
                click.echo(f"  Columns: {sheet_info['column_count']}")
            
            if report['cross_references']:
                click.echo("\nCross-sheet references:")
                for ref in report['cross_references']:
                    click.echo(f"  {ref['from_sheet']}.{ref['from_column']} references:")
                    for dep in ref['references']:
                        click.echo(f"    - {dep}")
                        
    except Exception as e:
        click.echo(f"Error analyzing Excel file: {str(e)}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
