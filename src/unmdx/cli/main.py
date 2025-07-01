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
    # TODO: Implement conversion logic
    console.print("[yellow]Conversion not yet implemented[/yellow]")


@app.command()
def explain(
    input_file: Path = typer.Argument(..., help="Input MDX file"),
    format: str = typer.Option("sql", "--format", "-f", help="Explanation format"),
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
    # TODO: Implement explanation logic
    console.print("[yellow]Explanation not yet implemented[/yellow]")


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
