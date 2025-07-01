# Examples

This directory contains example files demonstrating the unmdx library functionality.

## Structure

- `queries/` - Sample MDX query files for testing and demonstration
- `linter_example.py` - Example of using the MDX linter programmatically

## Usage

### Query Examples

Test the explainer with sample queries:

```bash
# Explain a query in different formats
uv run python -m unmdx.cli.main explain examples/queries/example_query.mdx
uv run python -m unmdx.cli.main explain examples/queries/example_query.mdx --format json
uv run python -m unmdx.cli.main explain examples/queries/example_query.mdx --format markdown --detail detailed
```

### Programmatic Usage

```python
from unmdx import explain_mdx, ExplainerGenerator

# Simple explanation
result = explain_mdx("SELECT {[Measures].[Sales]} ON 0 FROM [Cube]")
print(result)

# More control
generator = ExplainerGenerator()
explanation = generator.explain_file("examples/queries/example_query.mdx")
```