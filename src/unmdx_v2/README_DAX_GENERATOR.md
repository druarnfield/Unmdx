# UnMDX v2 DAX Generator

## Overview

The DAX generator converts parsed MDX structures into clean DAX queries. It handles the basic patterns needed for Test Cases 1-3 and follows the principle of "make it work first, then extend it."

## Implementation

### Location
- `/home/dru/dev/unmdx/src/unmdx_v2/core/dax_generator.py`

### Key Components

1. **SimpleDAXGenerator** - Main class that handles DAX generation
2. **generate_dax()** - Convenience function for simple generation
3. **DAXGenerationError** - Exception class for generation errors

### Supported Patterns

#### Pattern 1: Measures Only
**Input**: `{"measures": ["Sales Amount"], "dimensions": []}`
**Output**: 
```dax
EVALUATE
{ [Sales Amount] }
```

#### Pattern 2: Measures with Dimensions
**Input**: `{"measures": ["Sales Amount"], "dimensions": [{"table": "Product", "column": "Category"}]}`
**Output**: 
```dax
EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)
```

#### Pattern 3: Multiple Measures with Dimensions
**Input**: `{"measures": ["Sales Amount", "Order Quantity"], "dimensions": [{"table": "Date", "column": "Calendar Year"}]}`
**Output**: 
```dax
EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Calendar Year],
    "Sales Amount", [Sales Amount],
    "Order Quantity", [Order Quantity]
)
```

## Key Features

### Table Name Quoting
- Automatically quotes table names that contain spaces
- Quotes reserved words like "Date" and "Time"
- Uses single quotes for table names: `'Date'[Calendar Year]`

### Formatting
- Consistent indentation (4 spaces)
- Proper line breaks between components
- Follows DAX best practices

### Error Handling
- Validates input structure
- Raises descriptive errors for invalid input
- Logs errors for debugging

## Usage

```python
from unmdx_v2.core import parse_mdx, generate_dax

# Parse MDX
mdx = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
parsed = parse_mdx(mdx)

# Generate DAX
dax = generate_dax(parsed)
print(dax)
```

## Testing

The implementation passes all required test cases:
- ✅ Test Case 1: Simple Measure
- ✅ Test Case 2: Measure with Dimension  
- ✅ Test Case 3: Multiple Measures with Dimension

Run tests with:
```bash
cd src/unmdx_v2
python3 test_workflow.py
```

## Future Extensions

The current implementation handles the basic patterns. Future extensions could include:
- WHERE clause support (filters)
- Calculated members (DEFINE section)
- NON EMPTY handling (FILTER)
- CrossJoin support (multiple dimensions)
- Set operations

## Integration

The DAX generator integrates with the existing parser and can be extended to work with the main UnMDX API by creating appropriate wrapper functions.