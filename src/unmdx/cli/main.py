"""Main CLI application for the unmdx tool."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ..parser.mdx_parser import MDXParseError, MDXParser

app = typer.Typer(
    name="unmdx", help="Convert MDX queries to DAX with human-readable explanations"
)
console = Console()


@app.command()
def convert(
    input_file: Path | None = typer.Option(
        None, "--input", "-i", help="Input MDX file to convert"
    ),
    output_file: Path | None = typer.Option(
        None, "--output", "-o", help="Output file for DAX query"
    ),
    explain: bool = typer.Option(
        True, "--explain/--no-explain", help="Generate human-readable explanation"
    ),
    query: str | None = typer.Option(
        None, "--query", "-q", help="MDX query string to convert"
    ),
) -> None:
    """Convert MDX query to DAX with optional explanation."""

    # Get MDX input
    mdx_query = ""
    if query:
        mdx_query = query
    elif input_file:
        if not input_file.exists():
            console.print(f"[red]Error: Input file '{input_file}' not found[/red]")
            raise typer.Exit(1)
        mdx_query = input_file.read_text()
    else:
        console.print("[yellow]Enter your MDX query (press Ctrl+D when done):[/yellow]")
        try:
            mdx_query = typer.get_text_stream("stdin").read()
        except KeyboardInterrupt:
            console.print("\n[yellow]Conversion cancelled[/yellow]")
            raise typer.Exit(0)

    if not mdx_query.strip():
        console.print("[red]Error: No MDX query provided[/red]")
        raise typer.Exit(1)

    # Parse and convert
    try:
        parser = MDXParser()
        ir_query = parser.parse(mdx_query)

        # Generate DAX
        dax_query = ir_query.to_dax()

        # Display results
        console.print(
            Panel(
                Syntax(dax_query, "sql", theme="monokai"),
                title="🔄 Generated DAX Query",
                border_style="green",
            )
        )

        if explain:
            explanation = ir_query.to_human_readable()
            console.print(
                Panel(
                    explanation,
                    title="📝 Human-Readable Explanation",
                    border_style="blue",
                )
            )

        # Save to output file if specified
        if output_file:
            output_file.write_text(dax_query)
            console.print(f"[green]✓ DAX query saved to '{output_file}'[/green]")

    except MDXParseError as e:
        console.print(f"[red]Parse Error: {e}[/red]")
        if e.original_error:
            console.print(f"[dim]Details: {e.original_error}[/dim]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    input_file: Path | None = typer.Argument(None, help="MDX file to validate"),
    query: str | None = typer.Option(
        None, "--query", "-q", help="MDX query string to validate"
    ),
) -> None:
    """Validate MDX query syntax without conversion."""

    # Get MDX input
    mdx_query = ""
    if query:
        mdx_query = query
    elif input_file:
        if not input_file.exists():
            console.print(f"[red]Error: Input file '{input_file}' not found[/red]")
            raise typer.Exit(1)
        mdx_query = input_file.read_text()
    else:
        console.print("[red]Error: No MDX query provided[/red]")
        raise typer.Exit(1)

    # Validate
    try:
        parser = MDXParser()
        ir_query = parser.parse(mdx_query)

        console.print("[green]✓ MDX query is valid[/green]")

        # Show basic info
        console.print(f"[dim]Measures: {len(ir_query.measures)}[/dim]")
        console.print(f"[dim]Dimensions: {len(ir_query.dimensions)}[/dim]")
        console.print(f"[dim]Filters: {len(ir_query.filters)}[/dim]")
        console.print(f"[dim]Calculations: {len(ir_query.calculations)}[/dim]")

    except MDXParseError as e:
        console.print(f"[red]✗ Invalid MDX: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive() -> None:
    """Start interactive mode for converting MDX queries."""
    from .interactive import InteractiveApp

    app = InteractiveApp()
    app.run()


@app.command()
def version() -> None:
    """Show version information."""
    console.print("unmdx version 0.1.0")
    console.print("MDX to DAX converter with human-readable explanations")


if __name__ == "__main__":
    app()
