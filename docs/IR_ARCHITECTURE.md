# IR Architecture Documentation

## Overview

The Intermediate Representation (IR) serves as the bridge between parsed MDX queries and generated DAX queries. It represents the semantic intent of queries in a normalized, implementation-agnostic way.

## Core Design Principles

1. **Semantic Focus**: IR captures what the query means, not how it's written
2. **Bidirectional Conversion**: Each IR node supports both `to_dax()` and `to_human_readable()`
3. **Validation Built-in**: IR models validate themselves and track dependencies
4. **Metadata Rich**: Captures parsing context, warnings, optimization hints

## Architecture Layers

### 1. Core Query Structure

```
Query (Root)
├── CubeReference - Data source
├── Measures[] - What to calculate
├── Dimensions[] - How to group
├── Filters[] - What to include/exclude
├── Calculations[] - Custom calculations
├── OrderBy[] - Sorting
├── Limit - Result limiting
└── QueryMetadata - Tracking and optimization
```

### 2. Key Components

#### CubeReference
- Maps MDX cube to DAX data model
- Handles database/schema qualifiers
- Simple string representation in DAX

#### Measure
- Name, aggregation type, optional expression
- Supports aliases and format strings
- Can track dependencies through expressions
- Aggregation types: SUM, AVG, COUNT, DISTINCT_COUNT, MIN, MAX, CUSTOM

#### Dimension
- Hierarchy + Level + Member Selection
- Maps to DAX table[column] references
- Member selection types:
  - ALL: All members at level
  - SPECIFIC: Listed members only
  - CHILDREN/DESCENDANTS: Hierarchy navigation
  - RANGE: Member ranges

#### Filter
- Three types: DIMENSION, MEASURE, NON_EMPTY
- DimensionFilter: IN, EQUALS, NOT_EQUALS, CONTAINS
- MeasureFilter: GT, LT, GTE, LTE, EQ, NEQ
- NonEmptyFilter: Exclude blanks

#### Expression System
- Base Expression class with multiple implementations:
  - Constant: Literal values
  - MeasureReference: Reference to measures
  - MemberReference: Reference to dimension members
  - BinaryOperation: +, -, *, /
  - FunctionCall: SUM, AVG, etc.
  - ConditionalExpression: IF/IIF logic
- Each expression type implements:
  - `to_dax()`: Convert to DAX syntax
  - `to_human_readable()`: English description
  - `get_dependencies()`: Track references

## DAX Generation Strategy

### 1. Query Structure

```dax
DEFINE
    MEASURE Table[CustomMeasure] = <expression>
EVALUATE
<table_expression>
ORDER BY <columns>
```

### 2. Table Expression Selection

The DAX generator must choose the appropriate table expression based on query characteristics:

#### For Queries with Dimensions (Most Common)
Use `SUMMARIZECOLUMNS`:
```dax
SUMMARIZECOLUMNS(
    Table1[Column1],
    Table2[Column2],
    FILTER(ALL(Table1), <condition>),
    "Measure Name", [Measure]
)
```

#### For Measure-Only Queries
Use ROW or table constructor:
```dax
{ "Measure1", [Measure1], "Measure2", [Measure2] }
```

#### For Complex Filtering
May need nested CALCULATETABLE:
```dax
CALCULATETABLE(
    SUMMARIZECOLUMNS(...),
    <filter_conditions>
)
```

### 3. Filter Translation

MDX filters in WHERE clause map to DAX filters:

- **Dimension Filters**: 
  - MDX: `WHERE ([Geography].[Country].[USA])`
  - DAX: `FILTER(ALL(Geography), Geography[Country] = "USA")`

- **Measure Filters**:
  - MDX: `FILTER(..., [Measures].[Sales] > 1000)`
  - DAX: `[Sales] > 1000` (in CALCULATE context)

- **Non-Empty**:
  - MDX: `NON EMPTY`
  - DAX: `<> BLANK()` conditions

### 4. Calculation Handling

Calculated members become DAX measures:

- **Simple Calculations**:
  - MDX: `WITH MEMBER [Measures].[Profit Margin] AS [Profit]/[Sales]`
  - DAX: `MEASURE Sales[Profit Margin] = DIVIDE([Profit], [Sales])`

- **Complex Expressions**:
  - Use DIVIDE() for safe division
  - Use appropriate DAX functions (CALCULATE, FILTER, etc.)

## Implementation Patterns

### 1. Dimension to Column Mapping

```python
# IR Dimension
dimension = Dimension(
    hierarchy=HierarchyReference(table="Product", name="ProductHierarchy"),
    level=LevelReference(name="Category"),
    members=MemberSelection(selection_type=MemberSelectionType.ALL)
)

# DAX Output
"Product[Category]"
```

### 2. Measure with Aggregation

```python
# IR Measure
measure = Measure(
    name="Sales Amount",
    aggregation=AggregationType.SUM,
    alias="Total Sales"
)

# DAX Output (in SUMMARIZECOLUMNS)
'"Total Sales", [Sales Amount]'
```

### 3. Filter Conditions

```python
# IR DimensionFilter
filter = DimensionFilter(
    dimension=dimension,
    operator=FilterOperator.IN,
    values=["Bikes", "Accessories"]
)

# DAX Output
'Product[Category] IN {"Bikes", "Accessories"}'
```

### 4. Expression Trees

```python
# IR Expression for Profit Margin
expression = BinaryOperation(
    left=BinaryOperation(
        left=MeasureReference("Profit"),
        operator="/",
        right=MeasureReference("Sales")
    ),
    operator="*",
    right=Constant(100)
)

# DAX Output
'DIVIDE([Profit], [Sales]) * 100'
```

## Special Considerations

### 1. Division Safety
Always use DIVIDE() instead of "/" operator to handle division by zero:
```dax
DIVIDE([Numerator], [Denominator], 0)  -- Returns 0 if denominator is 0
```

### 2. Multiple Hierarchy Levels
When query has multiple levels from same hierarchy, only use the deepest:
```
Country -> State -> City -> PostalCode
Use only: PostalCode (if all are present)
```

### 3. CrossJoin Handling
MDX CrossJoin becomes multiple columns in SUMMARIZECOLUMNS:
```
MDX: CROSSJOIN([Product].[Category].Members, [Geography].[Country].Members)
DAX: SUMMARIZECOLUMNS(Product[Category], Geography[Country], ...)
```

### 4. Empty Handling
- MDX empty cells are NULL
- DAX uses BLANK()
- Use ISBLANK() for testing

### 5. Set Operations
MDX set operations need special handling:
- Union: Combine filter conditions with OR
- Intersect: Combine filter conditions with AND
- Except: Use NOT IN or <>

## Error Handling

The IR tracks errors and warnings in QueryMetadata:

1. **Validation Errors**:
   - Circular dependencies in calculations
   - Missing required fields
   - Invalid filter references

2. **Transformation Warnings**:
   - Redundant hierarchy levels
   - Excessive nesting
   - Unsupported MDX features

3. **Optimization Hints**:
   - From MDX comments
   - Detected patterns
   - Performance suggestions

## Testing Requirements

For DAX Generator with ~100% coverage:

1. **Core Functionality**:
   - Simple queries (measures only)
   - Dimensional queries
   - Filtered queries
   - Calculated measures
   - Complex expressions

2. **Edge Cases**:
   - Empty queries
   - Division by zero
   - Null/blank handling
   - Very long identifiers
   - Special characters in names

3. **Error Paths**:
   - Invalid IR structures
   - Unsupported features
   - Circular dependencies

4. **All IR Model Methods**:
   - Every to_dax() method
   - Every to_human_readable() method
   - Validation methods
   - Dependency tracking

## Performance Considerations

1. **String Building**: Use list joining instead of concatenation
2. **Validation**: Validate once during IR construction
3. **Caching**: Cache frequently used mappings
4. **Memory**: Stream large results instead of building in memory

## Future Extensions

1. **Additional DAX Patterns**:
   - Time intelligence
   - Ranking functions
   - Statistical calculations

2. **Optimization**:
   - Query simplification
   - Filter pushdown
   - Measure consolidation

3. **Advanced Features**:
   - Parameterized queries
   - Dynamic measures
   - Row-level security
