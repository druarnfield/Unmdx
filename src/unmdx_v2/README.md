# UnMDX v2 - Simple MDX Parser

A pragmatic, working MDX parser for the UnMDX v2 rewrite. This parser focuses on **working functionality** over perfect parsing and handles the most common MDX patterns.

## Features

- **Simple and Robust**: Uses regex-based parsing for reliability
- **Fast**: Optimized for common MDX patterns
- **Practical**: Handles real-world MDX queries from tools like Necto
- **Extensible**: Easy to add new patterns as needed

## Supported Patterns

1. **Basic Measure Selection**:
   ```mdx
   SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]
   ```

2. **Measures with Dimensions**:
   ```mdx
   SELECT {[Measures].[Revenue]} ON COLUMNS, {[Product].[Category].Members} ON ROWS FROM [Sales Cube]
   ```

3. **Multiple Measures**:
   ```mdx
   SELECT {[Measures].[Sales Amount], [Measures].[Profit]} ON 0 FROM [Adventure Works]
   ```

## Usage

```python
from unmdx_v2.core.parser import parse_mdx

# Parse a simple MDX query
query = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
result = parse_mdx(query)

print(result)
# Output:
# {
#     "measures": ["Sales Amount"],
#     "dimensions": [],
#     "cube": "Adventure Works",
#     "where_clause": None
# }
```

## Output Structure

The parser returns a consistent dictionary structure:

```python
{
    "measures": ["MeasureName1", "MeasureName2"],  # List of measure names
    "dimensions": [                                # List of dimension specifications
        {
            "table": "DimensionName",
            "column": "HierarchyName", 
            "selection_type": "members"
        }
    ],
    "cube": "CubeName",                           # Source cube name
    "where_clause": None                          # WHERE clause (not implemented yet)
}
```

## Error Handling

The parser includes robust error handling:

```python
from unmdx_v2.core.parser import parse_mdx, MDXParseError

try:
    result = parse_mdx("INVALID MDX QUERY")
except MDXParseError as e:
    print(f"Parse failed: {e}")
```

## Design Philosophy

This parser is designed for the UnMDX v2 recovery project with these principles:

1. **Working over Perfect**: Focus on parsing the queries that actually need to work
2. **Simple over Complex**: Use straightforward regex patterns instead of complex grammar
3. **Robust over Comprehensive**: Handle variations in whitespace, case, and formatting
4. **Extensible**: Easy to add new patterns as requirements grow

## Testing

Run the included test script to verify functionality:

```bash
python3 test_parser_v2.py
```

## Limitations

- WHERE clauses are not yet implemented
- Complex calculated members are not supported
- Advanced MDX functions are not parsed
- Focus is on SELECT-FROM patterns only

These limitations are intentional to keep the parser simple and working for the most common use cases.