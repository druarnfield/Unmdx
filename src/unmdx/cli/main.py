"""Main CLI entry point."""

from pathlib import Path

from rich.console import Console
import typer

from ..utils.logging import get_logger, setup_logging

app = typer.Typer(
    name="unmdx",
    help="MDX to DAX converter with human-readable explanations",
    no_args_is_help=True,
)
console = Console()
logger = get_logger(__name__)


@app.command()
def convert(
    input_file: Path = typer.Argument(..., help="Input MDX file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output DAX file"),
    optimization_level: str = typer.Option("moderate", "--optimization-level", help="Optimization level (none, conservative, moderate, aggressive)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Convert MDX file to DAX."""
    if verbose:
        setup_logging("DEBUG")
    else:
        setup_logging("INFO")

    logger.info(f"Converting {input_file} to DAX...")

    if not input_file.exists():
        console.print(f"[red]Error: Input file '{input_file}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Found input file: {input_file}")

    try:
        # Import here to avoid circular dependencies
        from ..api import mdx_to_dax
        from ..config import create_default_config, OptimizationLevel
        
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            mdx_content = f.read()
        
        # Create configuration
        config = create_default_config()
        try:
            config.linter.optimization_level = OptimizationLevel(optimization_level.lower())
        except ValueError:
            console.print(f"[red]Error: Invalid optimization level '{optimization_level}'. Valid options: none, conservative, moderate, aggressive[/red]")
            raise typer.Exit(1)
        
        # Convert MDX to DAX
        result = mdx_to_dax(mdx_content, config=config)
        
        # Output results
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(result.dax_query)
            console.print(f"[green]✓[/green] DAX query written to: {output}")
        else:
            console.print("\n" + "="*50)
            console.print(result.dax_query)
            console.print("="*50)
        
        # Show summary
        console.print(f"[green]✓[/green] Successfully converted {input_file}")
        console.print(f"Processing time: {result.performance.total_time:.2f}s")
        if result.optimization_applied:
            console.print(f"Optimization level: {result.optimization_level}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(1)


@app.command()
def explain(
    input_file: Path = typer.Argument(..., help="Input MDX file"),
    format: str = typer.Option("sql", "--format", "-f", help="Explanation format (sql, natural, json, markdown)"),
    detail: str = typer.Option("standard", "--detail", "-d", help="Detail level (minimal, standard, detailed)"),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
    include_dax: bool = typer.Option(False, "--include-dax", help="Include DAX comparison"),
    include_metadata: bool = typer.Option(False, "--include-metadata", help="Include query metadata"),
    use_linter: bool = typer.Option(True, "--use-linter/--no-linter", help="Apply MDX linter optimizations"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Generate human-readable explanation of MDX query."""
    if verbose:
        setup_logging("DEBUG")
    else:
        setup_logging("INFO")

    logger.info(f"Explaining {input_file}...")

    if not input_file.exists():
        console.print(f"[red]Error: Input file '{input_file}' not found[/red]")
        raise typer.Exit(1)

    console.print(f"[green]✓[/green] Found input file: {input_file}")

    try:
        # Import here to avoid circular dependencies
        from ..explainer import ExplainerGenerator, ExplanationConfig, ExplanationFormat, ExplanationDetail
        
        # Validate format
        try:
            explanation_format = ExplanationFormat(format.lower())
        except ValueError:
            console.print(f"[red]Error: Invalid format '{format}'. Valid options: sql, natural, json, markdown[/red]")
            raise typer.Exit(1)
        
        # Validate detail level
        try:
            explanation_detail = ExplanationDetail(detail.lower())
        except ValueError:
            console.print(f"[red]Error: Invalid detail level '{detail}'. Valid options: minimal, standard, detailed[/red]")
            raise typer.Exit(1)
        
        # Create configuration
        config = ExplanationConfig(
            format=explanation_format,
            detail=explanation_detail,
            include_dax_comparison=include_dax,
            include_metadata=include_metadata,
            use_linter=use_linter
        )
        
        # Generate explanation
        generator = ExplainerGenerator(debug=verbose)
        explanation = generator.explain_file(input_file, config, output)
        
        # Display results
        if output:
            console.print(f"[green]✓[/green] Explanation written to: {output}")
        else:
            console.print("\n" + "="*50)
            console.print(explanation)
            console.print("="*50)
        
        console.print(f"[green]✓[/green] Successfully explained {input_file}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Launch interactive MDX editor."""
    if verbose:
        setup_logging("DEBUG")
    else:
        setup_logging("INFO")

    logger.info("Launching interactive mode...")
    console.print("[blue]Interactive mode[/blue]")
    # TODO: Implement interactive TUI
    console.print("[yellow]Interactive mode not yet implemented[/yellow]")


@app.command()
def version():
    """Show version information."""
    from .. import __author__, __version__
    console.print(f"unmdx version {__version__}")
    console.print(f"Author: {__author__}")


if __name__ == "__main__":
    app()
