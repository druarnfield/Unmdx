# Getting Started with UnMDX

Welcome to UnMDX! This guide will help you get up and running with the MDX to DAX converter in just a few minutes.

## What is UnMDX?

UnMDX is a powerful Python package that converts MDX queries (particularly messy output from Necto SSAS cubes) into clean, optimized DAX queries with human-readable explanations. It's designed to help data analysts and developers work more efficiently with multidimensional data.

## Key Features

- **MDX to DAX Conversion**: Transform complex MDX queries into clean DAX format
- **Query Optimization**: Automatically clean up redundant patterns and verbose syntax
- **Human-Readable Explanations**: Get SQL-like explanations of your queries
- **Flexible Configuration**: Customize optimization levels and output formats
- **CLI and API**: Use via command line or integrate into your Python applications

## Prerequisites

- Python 3.10 or higher
- Basic understanding of MDX queries (helpful but not required)

## Installation

### Using pip (recommended)

```bash
pip install unmdx
```

### Using uv (for development)

```bash
uv add unmdx
```

### From source

```bash
git clone https://github.com/druarnfield/unmdx.git
cd unmdx
uv sync  # or pip install -e .
```

## Quick Start

### Command Line Usage

The simplest way to convert an MDX query is using the command line:

```bash
# Convert MDX file to DAX
unmdx convert input.mdx -o output.dax

# Get a human-readable explanation
unmdx explain input.mdx

# Convert with aggressive optimization
unmdx convert input.mdx -o output.dax --optimization-level aggressive
```

### Python API Usage

For programmatic access, use the Python API:

```python
from unmdx import mdx_to_dax, explain_mdx

# Convert MDX to DAX
mdx_query = """
SELECT 
    {[Measures].[Sales Amount]} ON COLUMNS,
    {[Date].[Calendar].[Month].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Geography].[Country].&[United States])
"""

result = mdx_to_dax(mdx_query)
print(result.dax_query)

# Get human-readable explanation
explanation = explain_mdx(mdx_query)
print(explanation.natural_language)
```

## Basic Examples

### Example 1: Simple Measure Query

**Input MDX:**
```mdx
SELECT 
    {[Measures].[Sales Amount]} ON COLUMNS
FROM [Sales Cube]
```

**Output DAX:**
```dax
EVALUATE
SUMMARIZECOLUMNS(
    "Sales Amount", [Sales Amount]
)
```

### Example 2: Measure with Dimension

**Input MDX:**
```mdx
SELECT 
    {[Measures].[Revenue]} ON COLUMNS,
    {[Product].[Category].Members} ON ROWS
FROM [Sales]
```

**Output DAX:**
```dax
EVALUATE
SUMMARIZECOLUMNS(
    'Product'[Category],
    "Revenue", [Revenue]
)
```

### Example 3: Query with Filters

**Input MDX:**
```mdx
SELECT 
    {[Measures].[Sales Amount]} ON COLUMNS,
    {[Date].[Month].Members} ON ROWS
FROM [Sales Cube]
WHERE ([Geography].[Country].&[USA])
```

**Output DAX:**
```dax
EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Month],
    FILTER(
        'Geography',
        'Geography'[Country] = "USA"
    ),
    "Sales Amount", [Sales Amount]
)
```

## Understanding the Output

UnMDX provides multiple output formats to help you understand your queries:

### 1. DAX Query
The primary output - a clean DAX query ready for Power BI or other DAX-compatible tools.

### 2. Human-Readable Explanation
A natural language description of what the query does:

```
This query retrieves Sales Amount grouped by Month for USA, 
showing data from the Sales Cube with geographic filtering.
```

### 3. SQL-Like Format
An SQL-style representation for those familiar with SQL:

```sql
SELECT 
    Date.Month,
    SUM(Measures.[Sales Amount]) AS [Sales Amount]
FROM [Sales Cube]
WHERE Geography.Country = 'USA'
GROUP BY Date.Month
```

## Configuration Options

UnMDX offers several configuration options to customize the conversion:

### Optimization Levels

- **conservative**: Minimal changes, preserve original structure
- **moderate**: Balance between optimization and preservation (default)
- **aggressive**: Maximum optimization, may restructure significantly

### Output Formats

- **dax**: Standard DAX query format
- **pretty**: Formatted DAX with indentation
- **compact**: Minified DAX for space efficiency

### Example with Configuration

```python
from unmdx import mdx_to_dax, create_default_config

# Create custom configuration
config = create_default_config()
config.linter.optimization_level = "aggressive"
config.dax.format_style = "pretty"

# Convert with custom config
result = mdx_to_dax(mdx_query, config=config)
```

## Common Use Cases

### 1. Migrating from SSAS to Power BI

If you're moving from SQL Server Analysis Services (SSAS) to Power BI, UnMDX helps convert your existing MDX queries to DAX format.

### 2. Cleaning Up Necto Output

Necto often generates verbose MDX with redundant patterns. UnMDX automatically cleans these up:

```mdx
# Before (Necto output)
CrossJoin(CrossJoin({[Dim1].[Member]}, {[Dim2].[Member]}), {[Dim3].[Member]})

# After (UnMDX optimized)
([Dim1].[Member], [Dim2].[Member], [Dim3].[Member])
```

### 3. Learning DAX from MDX

Use the explanation feature to understand how MDX concepts map to DAX:

```bash
unmdx explain complex_query.mdx --format markdown
```

## Next Steps

Now that you've got the basics, explore more advanced features:

1. **[Tutorials](tutorials/)** - Step-by-step guides for specific scenarios
2. **[CLI Reference](../cli/commands.md)** - Complete command-line documentation
3. **[API Reference](../api/)** - Detailed API documentation
4. **[Configuration Guide](../configuration/options.md)** - All configuration options explained
5. **[Examples Gallery](../../../examples/)** - Real-world MDX conversion examples

## Getting Help

If you encounter issues or have questions:

1. Check the **[Troubleshooting Guide](../troubleshooting/common-issues.md)**
2. Review the **[FAQ](../troubleshooting/common-issues.md#faq)**
3. Report issues on [GitHub](https://github.com/druarnfield/unmdx/issues)
4. Consult the **[API Documentation](../api/)**

## Performance Tips

- For large queries (>1000 lines), use the CLI for better performance
- Enable caching for repeated conversions
- Use conservative optimization for complex calculated members
- Consider breaking very large queries into smaller chunks

Happy converting! 🚀