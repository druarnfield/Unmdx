# DAX Query Language Specification - Table-Focused Parser Implementation

## Overview

This document outlines the DAX query language components needed for converting MDX queries to DAX. Since **EVALUATE always returns a table**, the parser can be simplified to focus on table expressions and their modifiers. This is a key insight that makes DAX queries conceptually simpler than MDX.

## 1. Core Query Structure

### 1.1 Simplified DAX Query Model

```bnf
<dax_query> ::= [<define_section>] <evaluate_list>

<evaluate_list> ::= <evaluate_statement> [<evaluate_list>]

<evaluate_statement> ::= EVALUATE <table_expression> [<order_by>] [<start_at>]
```

**Key Insight**: Every EVALUATE returns a table, so we only need to parse table expressions!

### 1.2 What This Means for Your Parser

- No need to handle complex scalar vs. table expression distinctions at the query level
- Every result is tabular data
- Even single values are returned as single-cell tables

## 2. Table Expressions - The Core of DAX Queries

### 2.1 Types of Table Expressions

```bnf
<table_expression> ::= <table_name>                    -- Direct table reference
                     | <table_function>                 -- Function that returns a table
                     | { <scalar_expression_list> }     -- Table constructor
                     | ( <table_expression> )           -- Parenthesized expression
```

### 2.2 Primary Table Functions for MDX Conversion

#### SUMMARIZECOLUMNS - The Workhorse

```bnf
SUMMARIZECOLUMNS(
    <groupby_column_list>,     -- Columns to group by
    [<filter_list>],           -- Optional filters
    [<measure_list>]           -- Measures to calculate
)
```

This is likely your most important function for MDX → DAX conversion as it handles:

- Grouping (like MDX axes)
- Filtering (like MDX WHERE)
- Measure calculation

#### FILTER - Simple Row Filtering

```bnf
FILTER(<table>, <boolean_expression>)
```

#### VALUES - Distinct Values

```bnf
VALUES(<column>) | VALUES(<table>)
```

#### ADDCOLUMNS - Add Calculated Columns

```bnf
ADDCOLUMNS(<table>, <name>, <expression> [, <name>, <expression>]...)
```

#### SELECTCOLUMNS - Project Specific Columns

```bnf
SELECTCOLUMNS(<table>, <name>, <expression> [, <name>, <expression>]...)
```

#### CALCULATETABLE - Apply Filter Context

```bnf
CALCULATETABLE(<table_expression>, <filter1> [, <filter2>]...)
```

## 3. Table Constructors - Converting Single Values

### 3.1 Converting Scalar to Table

```bnf
<table_constructor> ::= { <expression> [, <expression>]... }
```

**Examples:**

```dax
-- Single measure as table
EVALUATE { [Total Sales] }

-- Multiple measures as single-row table
EVALUATE { [Total Sales], [Total Cost], [Profit] }

-- ROW function alternative
EVALUATE ROW("Sales", [Total Sales], "Cost", [Total Cost])
```

## 4. DEFINE Section - Preparation Logic

### 4.1 Simplified DEFINE for Queries

```bnf
<define_section> ::= DEFINE <definition_list>

<definition> ::= MEASURE <table>[<name>] = <expression>
               | VAR <name> = <expression>
```

**Note**: For query purposes, you mainly need MEASURE and VAR. TABLE and COLUMN definitions are rarely used and can be omitted initially.

## 5. Result Modifiers

### 5.1 ORDER BY - Sorting the Table

```bnf
<order_by> ::= ORDER BY <column_or_expression> [ASC|DESC] 
                        [, <column_or_expression> [ASC|DESC]]...
```

### 5.2 START AT - Pagination

```bnf
<start_at> ::= START AT <value> [, <value>]...
```

## 6. Key Patterns for MDX to DAX Conversion

### 6.1 MDX Axes → DAX Table

```mdx
-- MDX: Multiple axes with members
SELECT 
  {[Measures].[Sales], [Measures].[Cost]} ON COLUMNS,
  {[Product].[Category].Members} ON ROWS
FROM [Cube]
WHERE ([Time].[Year].[2023])
```

```dax
-- DAX: Single table result
EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    FILTER(ALL('Date'), 'Date'[Year] = 2023),
    "Sales", [Sales],
    "Cost", [Cost]
)
```

### 6.2 MDX Sets → DAX Tables

```mdx
-- MDX: Set of members
{[Product].[Category].[Bikes], [Product].[Category].[Accessories]}
```

```dax
-- DAX: Table with filtered rows
FILTER(
    VALUES(Product[Category]),
    Product[Category] IN {"Bikes", "Accessories"}
)
```

### 6.3 MDX Calculated Members → DAX Measures in DEFINE

```mdx
WITH MEMBER [Measures].[Margin] AS [Measures].[Sales] - [Measures].[Cost]
```

```dax
DEFINE
MEASURE Sales[Margin] = [Sales] - [Cost]
```

## 7. Simplified Parser Implementation Strategy

### Phase 1 - Core Table Operations

1. **EVALUATE + Direct Tables**: `EVALUATE Customer`
1. **FILTER**: `EVALUATE FILTER(Customer, Customer[Country] = "USA")`
1. **VALUES**: `EVALUATE VALUES(Product[Category])`
1. **ORDER BY**: Basic sorting

### Phase 2 - MDX Conversion Essentials

1. **SUMMARIZECOLUMNS**: For typical MDX SELECT queries
1. **DEFINE MEASURE**: For calculated members
1. **Table constructors**: For single measure queries
1. **CALCULATETABLE**: For context modification

### Phase 3 - Advanced Features

1. **ADDCOLUMNS/SELECTCOLUMNS**: For complex projections
1. **Set operations**: UNION, EXCEPT, INTERSECT
1. **Advanced filtering**: Multiple filter contexts

## 8. Practical Conversion Rules

### 8.1 MDX Query Structure → DAX Query

|MDX Component     |DAX Equivalent                                        |
|------------------|------------------------------------------------------|
|SELECT… ON COLUMNS|Measures in SUMMARIZECOLUMNS                          |
|SELECT… ON ROWS   |Group-by columns in SUMMARIZECOLUMNS                  |
|FROM [Cube]       |Implicit from table relationships                     |
|WHERE (…)         |Filter parameter in SUMMARIZECOLUMNS or CALCULATETABLE|
|WITH MEMBER       |DEFINE MEASURE                                        |

### 8.2 Common Function Mappings

|MDX Function|DAX Function                               |
|------------|-------------------------------------------|
|.Members    |VALUES()                                   |
|.Children   |FILTER with relationship                   |
|CrossJoin() |CROSSJOIN() or implicit in SUMMARIZECOLUMNS|
|Filter()    |FILTER()                                   |
|TopCount()  |TOPN()                                     |

## 9. Parser Simplifications

Since everything returns a table, you can:

1. **Single Return Type**: No need for complex type checking
1. **Uniform AST Nodes**: All expressions evaluate to tables
1. **Simpler Validation**: Just ensure expressions are valid table expressions
1. **Straightforward Execution**: Always expect tabular results

## 10. Example Conversions

### Simple Member List

```mdx
-- MDX
SELECT [Product].[Category].Members ON ROWS
FROM [Sales]
```

```dax
-- DAX
EVALUATE VALUES(Product[Category])
```

### Measure with Dimension

```mdx
-- MDX  
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       [Product].[Category].Members ON ROWS
FROM [Sales]
```

```dax
-- DAX
EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)
```

### Filtered Query

```mdx
-- MDX
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       [Product].[Category].Members ON ROWS  
FROM [Sales]
WHERE ([Date].[Year].[2023])
```

```dax
-- DAX
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    'Date'[Year] = 2023
)
```

## Key Takeaway

The beauty of DAX queries is their consistency: **everything is a table**. This means:

- Your parser output is always a table expression
- No complex type resolution needed
- The conversion from MDX’s multidimensional results to DAX’s tabular results is conceptually straightforward
- You can focus on mapping MDX patterns to appropriate DAX table functions

This table-centric approach makes DAX queries both simpler to parse and more predictable to generate from MDX sources.
