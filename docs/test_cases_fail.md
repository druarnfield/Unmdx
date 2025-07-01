# MDX to DAX Test Cases - Invalid MDX Queries for Error Handling

## Test Case 21: Missing FROM Clause

### Input MDX (Invalid)

```mdx
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       {[Product].[Category].Members} ON ROWS
WHERE ([Date].[Calendar Year].&[2023])
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.MISSING_REQUIRED_CLAUSE,
    message="Missing required FROM clause in MDX query",
    line=3,
    position=0,
    context="Expected: FROM [cube_name] before WHERE clause",
    suggestion="Add FROM clause: FROM [Adventure Works]"
)
```

### Why It’s Invalid

MDX queries require a FROM clause to specify the cube. The query jumps directly from SELECT to WHERE without specifying the data source.

-----

## Test Case 22: Mismatched Brackets in Member Reference

### Input MDX (Invalid)

```mdx
SELECT {[Measures].[Sales Amount} ON COLUMNS,
       {[Product].[Category].Members}} ON ROWS
FROM [Adventure Works]
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.BRACKET_MISMATCH,
    message="Mismatched brackets in member reference",
    line=1,
    position=35,
    context="[Measures].[Sales Amount} - missing closing bracket ']'",
    suggestion="Check all member references have matching '[' and ']' brackets"
)
```

### Why It’s Invalid

Member references must have matching square brackets. `[Sales Amount}` mixes bracket types, and there’s an extra `}` in the second line.

-----

## Test Case 23: Invalid Axis Specification

### Input MDX (Invalid)

```mdx
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       {[Product].[Category].Members} ON ROWS,
       {[Customer].[Country].Members} ON COLUMNS
FROM [Adventure Works]
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.DUPLICATE_AXIS,
    message="Axis 'COLUMNS' is specified multiple times",
    line=3,
    position=40,
    context="COLUMNS axis already defined on line 1",
    suggestion="Use a different axis (PAGES, CHAPTERS, SECTIONS) or combine sets on same axis"
)
```

### Why It’s Invalid

Each axis can only be specified once in an MDX query. COLUMNS (AXIS(0)) is defined twice.

-----

## Test Case 24: Circular Reference in Calculated Member

### Input MDX (Invalid)

```mdx
WITH 
MEMBER [Measures].[Calc1] AS [Measures].[Calc2] * 2
MEMBER [Measures].[Calc2] AS [Measures].[Calc1] / 2
SELECT {[Measures].[Calc1], [Measures].[Calc2]} ON 0
FROM [Adventure Works]
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.CIRCULAR_REFERENCE,
    message="Circular reference detected in calculated members",
    line=2,
    position=0,
    context="[Calc1] references [Calc2] which references [Calc1]",
    suggestion="Resolve circular dependency by using base measures or breaking the reference chain",
    circular_path=["[Measures].[Calc1]", "[Measures].[Calc2]", "[Measures].[Calc1]"]
)
```

### Why It’s Invalid

Calculated members cannot have circular dependencies. Calc1 depends on Calc2, which depends on Calc1.

-----

## Test Case 25: Missing Set Delimiters

### Input MDX (Invalid)

```mdx
SELECT [Measures].[Sales Amount], [Measures].[Order Count] ON COLUMNS,
       [Product].[Category].Members ON ROWS
FROM [Adventure Works]
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.MISSING_SET_DELIMITER,
    message="Set specification missing required braces '{}'",
    line=1,
    position=7,
    context="Expected: {[Measures].[Sales Amount], [Measures].[Order Count]}",
    suggestion="Wrap set members in curly braces: {member1, member2}"
)
```

### Why It’s Invalid

Sets in MDX must be enclosed in curly braces `{}`. The measures are listed without braces.

-----

## Test Case 26: Invalid CrossJoin Syntax

### Input MDX (Invalid)

```mdx
SELECT {[Measures].[Sales Amount]} ON 0,
CROSSJOIN([Product].[Category].Members,
          [Customer].[Country].Members,
          [Date].[Calendar Year].Members) ON 1
FROM [Adventure Works]
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.INVALID_FUNCTION_ARGS,
    message="CROSSJOIN function accepts exactly 2 arguments, but 3 were provided",
    line=2,
    position=0,
    context="CROSSJOIN with 3 sets: Product, Customer, Date",
    suggestion="Nest CROSSJOIN calls: CROSSJOIN(CROSSJOIN(set1, set2), set3)"
)
```

### Why It’s Invalid

CROSSJOIN accepts exactly two set arguments. To cross join three sets, you need nested CROSSJOIN calls.

-----

## Test Case 27: Mixed Hierarchy in Single Set

### Input MDX (Invalid)

```mdx
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       {[Product].[Category].[Bikes],
        [Product].[Subcategory].[Mountain Bikes],
        [Product].[Category].[Accessories]} ON ROWS
FROM [Adventure Works]
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.HIERARCHY_MISMATCH,
    message="Mixed hierarchy levels in single set",
    line=2,
    position=0,
    context="Set contains members from different levels: [Category] and [Subcategory]",
    suggestion="Use separate sets or ensure all members are from the same hierarchy level",
    conflicting_levels=[
        {"member": "[Product].[Category].[Bikes]", "level": "Category"},
        {"member": "[Product].[Subcategory].[Mountain Bikes]", "level": "Subcategory"}
    ]
)
```

### Why It’s Invalid

While technically valid in some MDX implementations, mixing different hierarchy levels in a single set often leads to unexpected results and is considered bad practice.

-----

## Test Case 28: Invalid WHERE Clause Syntax

### Input MDX (Invalid)

```mdx
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       {[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE [Date].[Calendar Year].&[2023] AND [Customer].[Country].&[USA]
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.INVALID_WHERE_SYNTAX,
    message="Invalid WHERE clause syntax - cannot use AND operator",
    line=4,
    position=38,
    context="WHERE clause uses 'AND' between members",
    suggestion="Use tuple syntax: WHERE ([Date].[Calendar Year].&[2023], [Customer].[Country].&[USA])"
)
```

### Why It’s Invalid

WHERE clause in MDX requires a tuple (comma-separated members in parentheses), not boolean operators like AND.

-----

## Test Case 29: Undefined Measure in WITH Clause

### Input MDX (Invalid)

```mdx
WITH 
MEMBER [Measures].[Profit Margin] AS 
    [Measures].[Profit] / [Measures].[Revenue]
SELECT {[Measures].[Sales Amount], 
        [Measures].[Profit Margin]} ON 0,
       {[Product].[Category].Members} ON 1
FROM [Adventure Works]
/* Note: [Measures].[Revenue] doesn't exist, should be [Sales Amount] */
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.UNDEFINED_MEMBER,
    message="Reference to undefined measure in calculated member",
    line=3,
    position=26,
    context="[Measures].[Revenue] is not defined in the cube or query",
    suggestion="Available measures: [Sales Amount], [Order Quantity], [Total Cost]",
    undefined_references=["[Measures].[Revenue]"]
)
```

### Why It’s Invalid

The calculated member references [Measures].[Revenue] which doesn’t exist in the cube schema.

-----

## Test Case 30: Invalid Nested Set Construction

### Input MDX (Invalid)

```mdx
SELECT {{{{[Measures].[Sales Amount]}, {[Measures].[Order Count]}}} ON 0,
       {{{[Product].[Category].Members}},} ON 1
FROM [Adventure Works]
```

### Expected Error from IR

```python
ParseError(
    error_type=ErrorType.INVALID_SET_NESTING,
    message="Invalid set nesting and trailing comma",
    line=2,
    position=39,
    context="Excessive nesting of braces and trailing comma in set definition",
    suggestion="Simplify to: {[Product].[Category].Members}",
    issues=[
        "Unnecessary nested braces in measures set",
        "Trailing comma after set on line 2",
        "Maximum reasonable nesting depth exceeded"
    ]
)
```

### Why It’s Invalid

While MDX allows some nested sets, excessive nesting serves no purpose and the trailing comma after `.Members}},` is a syntax error.

-----

## Error IR Structure

### Error Representation in IR

```python
@dataclass
class ParseError:
    """Represents a parsing error in MDX query"""
    error_type: ErrorType
    message: str
    line: int
    position: int
    context: str
    suggestion: Optional[str] = None
    circular_path: Optional[List[str]] = None
    conflicting_levels: Optional[List[Dict]] = None
    undefined_references: Optional[List[str]] = None
    issues: Optional[List[str]] = None

class ErrorType(Enum):
    MISSING_REQUIRED_CLAUSE = "MISSING_REQUIRED_CLAUSE"
    BRACKET_MISMATCH = "BRACKET_MISMATCH"
    DUPLICATE_AXIS = "DUPLICATE_AXIS"
    CIRCULAR_REFERENCE = "CIRCULAR_REFERENCE"
    MISSING_SET_DELIMITER = "MISSING_SET_DELIMITER"
    INVALID_FUNCTION_ARGS = "INVALID_FUNCTION_ARGS"
    HIERARCHY_MISMATCH = "HIERARCHY_MISMATCH"
    INVALID_WHERE_SYNTAX = "INVALID_WHERE_SYNTAX"
    UNDEFINED_MEMBER = "UNDEFINED_MEMBER"
    INVALID_SET_NESTING = "INVALID_SET_NESTING"
```

### Human-Readable Error Output Example

```
ERROR: Missing required FROM clause in MDX query

Location: Line 3, Position 0
Context: Expected: FROM [cube_name] before WHERE clause

The MDX query is missing the required FROM clause that specifies which cube to query.

Suggestion: Add FROM clause: FROM [Adventure Works]

Example of correct syntax:
SELECT ... ON COLUMNS,
       ... ON ROWS  
FROM [Adventure Works]
WHERE ...
```

-----

## Notes on Error Handling

These test cases demonstrate various types of MDX syntax errors that the parser should catch:

1. **Structural Errors**: Missing required clauses (FROM), duplicate axes
1. **Syntax Errors**: Mismatched brackets, missing delimiters, trailing commas
1. **Semantic Errors**: Circular references, undefined members, hierarchy mismatches
1. **Function Errors**: Invalid argument counts, incorrect syntax
1. **Best Practice Violations**: Mixed hierarchies, excessive nesting

The IR layer should:

- Provide clear, actionable error messages
- Show the exact location of the error
- Suggest fixes where possible
- Include context to help users understand why it’s an error
- Support multiple error reporting (finding all errors, not just the first one)
