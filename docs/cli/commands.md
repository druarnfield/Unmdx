# UnMDX CLI Command Reference

The UnMDX command-line interface provides powerful tools for converting and analyzing MDX queries. This reference covers all available commands and their options.

## Installation

Once UnMDX is installed, the `unmdx` command will be available in your terminal:

```bash
unmdx --help
```

## Global Options

These options are available for all commands:

- `--help`: Show help message and exit

## Commands Overview

UnMDX provides the following commands:

- **`convert`** - Convert MDX queries to DAX format
- **`explain`** - Generate human-readable explanations of MDX queries
- **`interactive`** - Launch interactive MDX editor (coming soon)
- **`version`** - Display version information

---

## convert

Convert MDX file to DAX format.

### Usage

```bash
unmdx convert INPUT_FILE [OPTIONS]
```

### Arguments

- **`INPUT_FILE`** (required): Path to the input MDX file

### Options

- **`--output, -o`** `PATH`: Output DAX file path
  - If not specified, output is displayed in the console
  - Example: `-o output.dax`

- **`--verbose, -v`**: Enable verbose logging
  - Shows detailed debug information
  - Useful for troubleshooting

### Examples

#### Basic conversion to console output
```bash
unmdx convert query.mdx
```

#### Save conversion to file
```bash
unmdx convert query.mdx -o result.dax
```

#### Conversion with debug information
```bash
unmdx convert query.mdx -o result.dax --verbose
```

### Notes

- The convert command is currently in development
- Input file must exist and contain valid MDX syntax
- Output format follows standard DAX conventions

---

## explain

Generate human-readable explanation of MDX query.

### Usage

```bash
unmdx explain INPUT_FILE [OPTIONS]
```

### Arguments

- **`INPUT_FILE`** (required): Path to the input MDX file

### Options

- **`--format, -f`** `TEXT`: Explanation format (default: `sql`)
  - **`sql`**: SQL-like representation
  - **`natural`**: Natural language description
  - **`json`**: Structured JSON output
  - **`markdown`**: Formatted markdown with sections

- **`--detail, -d`** `TEXT`: Detail level (default: `standard`)
  - **`minimal`**: Basic explanation only
  - **`standard`**: Balanced detail level
  - **`detailed`**: Comprehensive analysis

- **`--output, -o`** `PATH`: Output file path
  - If not specified, output is displayed in the console

- **`--include-dax`**: Include DAX comparison in output
  - Shows both MDX and equivalent DAX
  - Helpful for learning DAX patterns

- **`--include-metadata`**: Include query metadata
  - Adds performance metrics
  - Shows query complexity analysis
  - Includes dimension/measure counts

- **`--use-linter/--no-linter`**: Apply MDX linter optimizations (default: enabled)
  - `--use-linter`: Clean up MDX before explaining (default)
  - `--no-linter`: Explain raw MDX without optimization

- **`--verbose, -v`**: Enable verbose logging

### Examples

#### Basic SQL-like explanation
```bash
unmdx explain sales_query.mdx
```

#### Natural language explanation with DAX comparison
```bash
unmdx explain sales_query.mdx -f natural --include-dax
```

#### Detailed markdown report saved to file
```bash
unmdx explain complex_query.mdx -f markdown -d detailed -o report.md
```

#### JSON output for programmatic processing
```bash
unmdx explain query.mdx -f json -o analysis.json
```

#### Analyze raw MDX without optimization
```bash
unmdx explain messy_query.mdx --no-linter
```

### Output Formats

#### SQL Format
Provides an SQL-like representation of the MDX query:
```sql
SELECT 
    Product.Category,
    SUM(Measures.[Sales Amount]) AS [Sales Amount]
FROM [Sales Cube]
WHERE Date.Year = '2023'
GROUP BY Product.Category
```

#### Natural Language Format
Describes the query in plain English:
```
This query retrieves Sales Amount grouped by Product Category 
for the year 2023 from the Sales Cube.
```

#### JSON Format
Structured data suitable for further processing:
```json
{
  "query_type": "SELECT",
  "measures": ["Sales Amount"],
  "dimensions": ["Product.Category"],
  "filters": ["Date.Year = '2023'"],
  "cube": "Sales Cube"
}
```

#### Markdown Format
Comprehensive report with sections:
```markdown
# MDX Query Analysis

## Summary
Query retrieves sales data by product category...

## Structure
- **Measures**: Sales Amount
- **Dimensions**: Product Category
- **Filters**: Year 2023

## Equivalent DAX
...
```

---

## interactive

Launch interactive MDX editor with real-time conversion preview.

### Usage

```bash
unmdx interactive [OPTIONS]
```

### Options

- **`--verbose, -v`**: Enable verbose logging

### Status

⚠️ **Note**: The interactive command is currently under development and not yet implemented.

### Planned Features

- Real-time MDX to DAX conversion
- Syntax highlighting
- Query validation
- Side-by-side comparison
- Export functionality

---

## version

Display version information about UnMDX.

### Usage

```bash
unmdx version
```

### Example Output

```
unmdx version 0.1.0
Author: Dru Arnfield
```

---

## Common Workflows

### 1. Quick MDX Analysis

To quickly understand what an MDX query does:

```bash
unmdx explain query.mdx -f natural
```

### 2. Batch Conversion

Convert multiple files using shell scripting:

```bash
for file in *.mdx; do
    unmdx convert "$file" -o "${file%.mdx}.dax"
done
```

### 3. Documentation Generation

Create a comprehensive analysis report:

```bash
unmdx explain complex_query.mdx \
    --format markdown \
    --detail detailed \
    --include-dax \
    --include-metadata \
    --output analysis_report.md
```

### 4. Debug Problem Queries

Analyze problematic MDX without optimization:

```bash
unmdx explain problem_query.mdx \
    --no-linter \
    --verbose \
    --format json \
    -o debug_output.json
```

## Error Handling

UnMDX provides clear error messages for common issues:

### File Not Found
```
Error: Input file 'query.mdx' not found
```

### Invalid Format
```
Error: Invalid format 'xml'. Valid options: sql, natural, json, markdown
```

### Parse Errors
```
Error: Failed to parse MDX - unexpected token at line 5
```

## Performance Tips

1. **Large Files**: For MDX files over 1000 lines, use the CLI rather than the Python API for better performance

2. **Batch Processing**: When processing multiple files, consider using GNU Parallel:
   ```bash
   parallel unmdx convert {} -o {.}.dax ::: *.mdx
   ```

3. **Optimization Levels**: Use `--no-linter` for faster processing if you don't need optimization

## Environment Variables

UnMDX respects the following environment variables:

- **`UNMDX_LOG_LEVEL`**: Set default log level (DEBUG, INFO, WARNING, ERROR)
- **`UNMDX_CONFIG_PATH`**: Path to default configuration file

## Exit Codes

UnMDX uses standard exit codes:

- **0**: Success
- **1**: General error (file not found, parse error, etc.)
- **2**: Invalid command line arguments

## Getting Help

For more information:

1. Use `--help` with any command: `unmdx explain --help`
2. Check the [Troubleshooting Guide](../troubleshooting/common-issues.md)
3. Visit the [GitHub repository](https://github.com/druarnfield/unmdx)
4. Report issues at [GitHub Issues](https://github.com/druarnfield/unmdx/issues)