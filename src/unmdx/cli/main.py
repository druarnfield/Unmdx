"""Main CLI entry point."""

import typer
from rich.console import Console

app = typer.Typer(
    name="unmdx",
    help="MDX to DAX converter with human-readable explanations",
    no_args_is_help=True,
)
console = Console()


@app.command()
def convert(
    input_file: str = typer.Argument(..., help="Input MDX file"),
    output: str = typer.Option(None, "--output", "-o", help="Output DAX file"),
):
    """Convert MDX file to DAX."""
    console.print(f"Converting {input_file} to DAX...")
    # TODO: Implement conversion logic


@app.command()
def explain(
    input_file: str = typer.Argument(..., help="Input MDX file"),
    format: str = typer.Option("sql", "--format", "-f", help="Explanation format"),
):
    """Generate human-readable explanation of MDX query."""
    console.print(f"Explaining {input_file}...")
    # TODO: Implement explanation logic


@app.command()
def interactive():
    """Launch interactive MDX editor."""
    console.print("Launching interactive mode...")
    # TODO: Implement interactive TUI


if __name__ == "__main__":
    app()