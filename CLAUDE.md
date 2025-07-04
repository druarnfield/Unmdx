# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Note**: This file (CLAUDE.md) is local-only and not committed to git. All project documentation files have been moved to the `docs/` directory for better organization.

## CURRENT ROLE: CODEBASE AUDITOR

I am currently acting as an external auditor brought in to assess this project. The original developer claims the project is production-ready, but integration tests are failing and real-world functionality is broken. My task is to:

1. Conduct a comprehensive review of all planning documentation
2. Analyze the current implementation against the specifications
3. Identify root design and implementation flaws
4. Provide a detailed audit report with findings
5. Create an actionable recovery plan to salvage the project

The audit will focus on:
- Architecture mismatches between planning and implementation
- Missing or incorrectly implemented core functionality
- Technical debt and code quality issues
- Testing gaps and why tests are failing
- Specific reasons for real-world failure

## Documentation Structure

All project documentation has been organized in the `docs/` directory:
- **Architecture**: `docs/ir_spec.md`, `docs/IR_ARCHITECTURE.md`
- **Specifications**: `docs/mdx_spec.md`, `docs/dax_spec.md`, `docs/linter_spec.md`
- **Grammar**: `docs/mdx_grammar_spec_pt1.md`, `docs/mdx_grammar_spec_pt2.md`
- **Project Management**: `docs/project_overview.md`, `docs/ir_transformer.md`
- **Test Cases**: `docs/test_cases_basic.md`, `docs/test_cases_advanced.md`, `docs/test_cases_fail.md`
- **Examples**: `examples/queries/` directory contains sample MDX files

## Package Management

This project uses **uv** for Python package management instead of pip/poetry. Common commands:
- `uv sync` - Install dependencies and sync environment
- `uv add <package>` - Add a new dependency
- `uv run <command>` - Run commands in the uv environment
- `uv run pytest` - Run tests
- `uv run python -m unmdx.cli.main` - Run the CLI

## Project Overview

This is a comprehensive Python CLI tool for converting MDX queries (particularly messy output from Necto SSAS cubes) into clean, optimized DAX queries with human-readable explanations.

## Architecture

The project follows a multi-stage transformation pipeline:

1. **MDX Parser** - Lark-based parser handling poorly formatted MDX from Oracle Essbase/Necto
2. **Intermediate Representation (IR)** - Normalized semantic representation that captures query intent
3. **Linter** - Cleans and optimizes parsed MDX structure, removes redundant patterns
4. **DAX Generator** - Produces clean DAX queries from IR using SUMMARIZECOLUMNS and EVALUATE
5. **SQL Explainer** - Generates human-readable SQL-like explanations from IR

## Key Components

### Parser Implementation (mdx_spec.md)
- Follows BNF grammar for complete MDX language support
- Handles complex nested structures, calculated members, and set operations
- Priority: Core SELECT-FROM-WHERE → Advanced features → Optimization

### Intermediate Representation (ir_spec.md)
- Semantic rather than syntactic representation
- Core classes: Query, Measure, Dimension, Filter, Expression, Calculation
- Supports both DAX generation and human-readable explanations
- Each IR node implements `to_dax()` and `to_human_readable()` methods

### Common MDX Patterns from Necto
The parser is designed to handle "spaghetti mess" output including:
- Redundant parentheses and nesting
- Verbose function call chains
- Duplicate member specifications
- Complex calculated members with unclear dependencies
- Unnecessary CrossJoins that can be simplified

## Technology Stack

- Python 3.10+
- Lark for MDX parsing
- Textual for CLI interface
- Pydantic for IR data models  
- Pytest for testing
- Black/Ruff for code quality

## Development Commands

Based on the project plan, these commands should be available:
- `pytest` - Run test suite (target: 90% coverage overall)
- `black .` - Code formatting
- `ruff check` - Linting
- `mypy .` - Type checking

## Testing Strategy

Follows test pyramid approach:
- 60% Unit tests (individual functions, class methods, edge cases)
- 30% Integration tests (component integration, parser+transformer)
- 10% E2E tests (full workflow, real MDX files)

Test cases are organized in:
- Basic test cases (test_cases_basic.md) - Tests 1-10
- Advanced test cases (test_cases_advanced.md) - Tests 11-20  
- Failure test cases (test_cases_fail.md) - Tests 21-30

## Code Quality Standards

- Test coverage minimum 90% overall, 100% for critical paths
- All utility functions must have 100% test coverage
- Every error path must have a test
- Pre-commit hooks run unit tests
- Use fixtures for MDX test data management

## Performance Targets

- Parse 1000-line MDX query in < 1 second
- Generate DAX in < 100ms after parsing
- Memory usage < 500MB for large queries
- Successfully convert 95% of Necto-generated queries