# UnMDX - MDX to DAX Converter

A comprehensive Python CLI tool that converts MDX queries (particularly messy output from Necto SSAS cubes) into clean, optimized DAX queries with human-readable explanations.

## Overview

UnMDX transforms complex, poorly formatted MDX queries into:
- Clean, optimized DAX queries using modern DAX patterns
- Human-readable SQL-like explanations 
- Detailed query analysis and optimization suggestions

## Features

- **MDX Parser**: Handles complex, nested MDX from Oracle Essbase/Necto
- **Query Optimization**: Removes redundant patterns and simplifies structures
- **DAX Generation**: Produces clean DAX using SUMMARIZECOLUMNS and EVALUATE
- **Human Explanations**: Generates SQL-like explanations for business users
- **CLI Interface**: Interactive terminal UI with syntax highlighting

## Installation

```bash
pip install unmdx
```

## Development Setup

```bash
# Clone the repository
git clone https://github.com/druarnfield/Unmdx.git
cd Unmdx

# Install development dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
black .
ruff check .
mypy .
```

## Usage

```bash
# Convert MDX file to DAX
unmdx convert input.mdx --output output.dax

# Interactive mode
unmdx interactive

# Generate explanation
unmdx explain input.mdx --format sql
```

## Architecture

The conversion follows a multi-stage pipeline:

1. **Parser** - Lark-based MDX parser
2. **IR** - Intermediate representation for semantic analysis
3. **Linter** - Query optimization and cleanup
4. **Generator** - DAX and explanation generation

## Testing

- **Coverage Target**: 90% overall, 100% for critical paths
- **Test Categories**: Unit (60%), Integration (30%), E2E (10%)
- **Performance**: Parse 1000-line MDX in <1 second

## License

MIT License - see LICENSE file for details.