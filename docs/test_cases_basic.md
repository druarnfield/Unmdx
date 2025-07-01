# MDX to DAX Test Cases - Basic Queries

## Test Case 1: Simple Measure Query

### Input MDX (Poorly Formatted)

```mdx
SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[],
    filters=[],
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
{ [Sales Amount] }
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount

SQL-like representation:
```sql
SELECT SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
```

-----

## Test Case 2: Measure with Dimension (Messy Spacing)

### Input MDX (Poorly Formatted)

```mdx
SELECT{[Measures].[Sales Amount]}ON COLUMNS,
     {[Product].[Category].Members}    ON    ROWS
FROM    [Adventure Works]
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[],
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: each Category

SQL-like representation:
```sql
SELECT Category, SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
GROUP BY Category
```

-----

## Test Case 3: Multiple Measures (Redundant Braces)

### Input MDX (Poorly Formatted)

```mdx
SELECT {{{[Measures].[Sales Amount]}, {[Measures].[Order Quantity]}}} ON 0,
{[Date].[Calendar Year].Members} ON 1
FROM [Adventure Works]
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="Order Quantity", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Date", name="Calendar"),
            level=LevelReference(name="Calendar Year"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[],
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Calendar Year],
    "Sales Amount", [Sales Amount],
    "Order Quantity", [Order Quantity]
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount, total Order Quantity
2. Grouped by: each Calendar Year

SQL-like representation:
```sql
SELECT Calendar Year, 
       SUM(Sales Amount) AS Sales Amount,
       SUM(Order Quantity) AS Order Quantity
FROM Adventure Works
GROUP BY Calendar Year
```

-----

## Test Case 4: Simple WHERE Clause

### Input MDX (Poorly Formatted)

```mdx
SELECT   {[Measures].[Sales Amount]}   ON   COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE    ([Date].[Calendar Year].&[2023])
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Calendar"),
                    level=LevelReference(name="Calendar Year"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["2023"]
            )
        )
    ],
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    'Date'[Calendar Year] = 2023
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: each Category
3. Where:
   - Calendar Year equals 2023

SQL-like representation:
```sql
SELECT Category, SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
WHERE Calendar Year = 2023
GROUP BY Category
```

-----

## Test Case 5: CrossJoin with Redundant Parentheses

### Input MDX (Poorly Formatted)

```mdx
SELECT {[Measures].[Sales Amount]} ON 0,
CROSSJOIN(({[Product].[Category].Members}),
          ({[Customer].[Country].Members})) ON 1
FROM [Adventure Works]
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        ),
        Dimension(
            hierarchy=HierarchyReference(table="Customer", name="Customer"),
            level=LevelReference(name="Country"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[],
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    Customer[Country],
    "Sales Amount", [Sales Amount]
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: each Category, each Country

SQL-like representation:
```sql
SELECT Category, Country, SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
GROUP BY Category, Country
```

-----

## Test Case 6: Specific Member Selection (Verbose)

### Input MDX (Poorly Formatted)

```mdx
SELECT{[Measures].[Sales Amount]}ON AXIS(0),
{{[Product].[Category].[Bikes]},{[Product].[Category].[Accessories]}}ON AXIS(1)
FROM[Adventure Works]
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(
                selection_type=MemberSelectionType.SPECIFIC,
                specific_members=["Bikes", "Accessories"]
            )
        )
    ],
    filters=[],
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    Product[Category] IN {"Bikes", "Accessories"}
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: specific Category values (Bikes, Accessories)

SQL-like representation:
```sql
SELECT Category, SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
WHERE Category IN ('Bikes', 'Accessories')
GROUP BY Category
```

-----

## Test Case 7: Simple Calculated Member

### Input MDX (Poorly Formatted)

```mdx
WITH MEMBER[Measures].[Average Price]AS[Measures].[Sales Amount]/[Measures].[Order Quantity]
SELECT{[Measures].[Sales Amount],[Measures].[Order Quantity],[Measures].[Average Price]}ON 0
FROM[Adventure Works]
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="Order Quantity", aggregation=AggregationType.SUM),
        Measure(name="Average Price", aggregation=AggregationType.CUSTOM)
    ],
    dimensions=[],
    filters=[],
    order_by=[],
    limit=None,
    calculations=[
        Calculation(
            name="Average Price",
            calculation_type=CalculationType.MEASURE,
            expression=BinaryOperation(
                left=MeasureReference("Sales Amount"),
                operator="/",
                right=MeasureReference("Order Quantity")
            )
        )
    ]
)
```

### Clean DAX Output

```dax
DEFINE
    MEASURE Sales[Average Price] = DIVIDE([Sales Amount], [Order Quantity])
EVALUATE
{
    [Sales Amount],
    [Order Quantity],
    [Average Price]
}
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount, total Order Quantity, Average Price
4. With these calculations:
   - Calculate Average Price as Sales Amount divided by Order Quantity

SQL-like representation:
```sql
SELECT SUM(Sales Amount) AS Sales Amount,
       SUM(Order Quantity) AS Order Quantity,
       SUM(Sales Amount) / SUM(Order Quantity) AS Average Price
FROM Adventure Works
```

-----

## Test Case 8: NON EMPTY with Nested Sets

### Input MDX (Poorly Formatted)

```mdx
SELECT NON EMPTY{{[Measures].[Sales Amount]}}ON 0,
NON EMPTY{{{[Product].[Category].Members}}}ON 1
FROM[Adventure Works]
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[
        Filter(
            filter_type=FilterType.NON_EMPTY,
            target=NonEmptyFilter(measure="Sales Amount")
        )
    ],
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
FILTER(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    [Sales Amount] <> BLANK()
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: each Category
3. Where:
   - Sales Amount is not empty

SQL-like representation:
```sql
SELECT Category, SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
GROUP BY Category
HAVING SUM(Sales Amount) IS NOT NULL
```

-----

## Test Case 9: Multiple Filters in WHERE (Complex Tuple)

### Input MDX (Poorly Formatted)

```mdx
SELECT{[Measures].[Sales Amount]}ON COLUMNS,
{[Product].[Category].Members}ON ROWS
FROM[Adventure Works]
WHERE([Date].[Calendar Year].&[2023],[Geography].[Country].&[United States])
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Calendar"),
                    level=LevelReference(name="Calendar Year"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["2023"]
            )
        ),
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Geography", name="Geography"),
                    level=LevelReference(name="Country"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["United States"]
            )
        )
    ],
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    'Date'[Calendar Year] = 2023,
    Geography[Country] = "United States"
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: each Category
3. Where:
   - Calendar Year equals 2023
   - Country equals United States

SQL-like representation:
```sql
SELECT Category, SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
WHERE Calendar Year = 2023
  AND Country = 'United States'
GROUP BY Category
```

-----

## Test Case 10: Empty Sets and Redundant Constructs

### Input MDX (Poorly Formatted)

```mdx
SELECT{{{{}}},{[Measures].[Sales Amount]},{{}}}ON 0,
{[Date].[Calendar].[Calendar Year].Members}ON 1
FROM[Adventure Works]WHERE()
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Date", name="Calendar"),
            level=LevelReference(name="Calendar Year"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[],  # Empty WHERE clause is ignored
    order_by=[],
    limit=None,
    calculations=[]
)
```

### Clean DAX Output

```dax
EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Calendar Year],
    "Sales Amount", [Sales Amount]
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: each Calendar Year

SQL-like representation:
```sql
SELECT Calendar Year, SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
GROUP BY Calendar Year
```

-----

## Notes on Test Cases

These test cases demonstrate:

1. **Poor Formatting**: Missing spaces, extra spaces, inconsistent spacing
1. **Redundant Constructs**: Multiple nested braces, empty sets
1. **Verbose Syntax**: Using AXIS(0) instead of COLUMNS
1. **Complex Structures**: CrossJoins that can be simplified
1. **Empty Elements**: Empty WHERE clauses, empty sets in SELECT

The IR normalizes all these issues into a clean, semantic representation that can then generate clean DAX and human-readable explanations.
