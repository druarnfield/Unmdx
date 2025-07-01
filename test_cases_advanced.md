# MDX to DAX Test Cases - Complex Hierarchy Queries

## Test Case 11: Redundant Hierarchy Levels with Comments

### Input MDX (Poorly Formatted)

```mdx
SELECT /* OPTIMIZER: USE_AGGREGATE_AWARE */ {[Measures].[Sales Amount]} ON 0,
{/* Include all levels for context */
[Geography].[Geography].[All Geographies].Members, 
[Geography].[Geography].[Country].Members,
[Geography].[Geography].[State-Province].Members, /* State level */
[Geography].[Geography].[City].Members,
[Geography].[Geography].[Postal Code].Members /* This is what we actually want */
} ON 1
FROM [Adventure Works] /* Main cube */
/* WHERE clause intentionally omitted for performance */
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
            hierarchy=HierarchyReference(table="Geography", name="Geography"),
            level=LevelReference(name="Postal Code"),  # Only the deepest level matters
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[],
    order_by=[],
    limit=None,
    calculations=[],
    metadata=QueryMetadata(optimizer_hints=["USE_AGGREGATE_AWARE"])
)
```

### Clean DAX Output

```dax
EVALUATE
SUMMARIZECOLUMNS(
    Geography[Postal Code],
    "Sales Amount", [Sales Amount]
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: each Postal Code

SQL-like representation:
```sql
SELECT Postal Code, SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
GROUP BY Postal Code
```

-----

## Test Case 12: Nested Descendants with Every Parent Listed

### Input MDX (Poorly Formatted)

```mdx
SELECT {[Measures].[Order Quantity] /* Base measure */, 
        [Measures].[Sales Amount] /* Revenue measure */} ON COLUMNS,
{/* Product hierarchy - need SKU level only */
[Product].[Product Categories].[All Products], /* Level 0 */
[Product].[Product Categories].[Category].Members, /* Level 1 */
[Product].[Product Categories].[Subcategory].Members, /* Level 2 */
/* HINT: Next level is critical for analysis */
[Product].[Product Categories].[Product].Members, /* Level 3 - Product Name */
[Product].[Product Categories].[Product].[Product].Members, /* Level 4 - SKU */
DESCENDANTS([Product].[Product Categories].[All Products], 
            [Product].[Product Categories].[Product], /* Actually want SKU */
            SELF_AND_AFTER) /* Include all below */
} ON ROWS
FROM [Adventure Works]
-- Filter: Current year only
WHERE ([Date].[Calendar Year].&[2023])
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Order Quantity", aggregation=AggregationType.SUM),
        Measure(name="Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product Categories"),
            level=LevelReference(name="Product"),  # SKU level
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
        Product[Product],
        "Order Quantity", [Order Quantity],
        "Sales Amount", [Sales Amount]
    ),
    'Date'[Calendar Year] = 2023
)
```

### Human Readable

```
This query will:

1. Calculate: total Order Quantity, total Sales Amount
2. Grouped by: each Product (SKU level)
3. Where:
   - Calendar Year equals 2023

SQL-like representation:
```sql
SELECT Product, 
       SUM(Order Quantity) AS Order Quantity,
       SUM(Sales Amount) AS Sales Amount
FROM Adventure Works
WHERE Calendar Year = 2023
GROUP BY Product
```

-----

## Test Case 13: Organization Hierarchy with Redundant Paths

### Input MDX (Poorly Formatted)

```mdx
WITH /* Calculated members section */
MEMBER [Measures].[Avg Sale] AS 
    /* FORMULA: Average transaction size */
    [Measures].[Sales Amount] / [Measures].[Order Count],
    FORMAT_STRING = "Currency" /* Format hint */
SELECT 
{[Measures].[Sales Amount], 
 [Measures].[Order Count] /* Transaction count */, 
 [Measures].[Avg Sale]} ON 0,
{/* Organization hierarchy - deeply nested */
/* ROOT */ [Employee].[Employees].[All Employees],
/* L1 */   [Employee].[Employees].[CEO].Members,
/* L2 */   [Employee].[Employees].[VP].Members, -- Vice Presidents
/* L3 */   [Employee].[Employees].[Director].Members,
/* L4 */   [Employee].[Employees].[Manager].Members,
/* L5 */   [Employee].[Employees].[Lead].Members,
/* L6 */   [Employee].[Employees].[Senior].Members, -- Senior level
/* L7 */   [Employee].[Employees].[Employee].Members -- Individual contributors (NEEDED)
} ON 1
FROM [Adventure Works]
/* OPTIMIZER: IGNORE_CALCULATED_MEMBERS = FALSE */
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="Order Count", aggregation=AggregationType.COUNT),
        Measure(name="Avg Sale", aggregation=AggregationType.CUSTOM, format_string="Currency")
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Employee", name="Employees"),
            level=LevelReference(name="Employee"),  # Level 7 - Individual contributors
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[],
    order_by=[],
    limit=None,
    calculations=[
        Calculation(
            name="Avg Sale",
            calculation_type=CalculationType.MEASURE,
            expression=BinaryOperation(
                left=MeasureReference("Sales Amount"),
                operator="/",
                right=MeasureReference("Order Count")
            )
        )
    ]
)
```

### Clean DAX Output

```dax
DEFINE
    MEASURE Sales[Avg Sale] = DIVIDE([Sales Amount], [Order Count])
EVALUATE
SUMMARIZECOLUMNS(
    Employee[Employee],
    "Sales Amount", [Sales Amount],
    "Order Count", [Order Count],
    "Avg Sale", [Avg Sale]
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount, count of Order Count, Avg Sale
2. Grouped by: each Employee (individual contributors)
4. With these calculations:
   - Calculate Avg Sale as Sales Amount divided by Order Count

SQL-like representation:
```sql
SELECT Employee, 
       SUM(Sales Amount) AS Sales Amount,
       COUNT(Order Count) AS Order Count,
       SUM(Sales Amount) / COUNT(Order Count) AS Avg Sale
FROM Adventure Works
GROUP BY Employee
```

-----

## Test Case 14: Date Hierarchy with All Levels and CrossJoin

### Input MDX (Poorly Formatted)

```mdx
SELECT /* Measures */ {[Measures].[Internet Sales Amount]} ON COLUMNS,
CROSSJOIN(
    {/* Date hierarchy - all levels listed */
    [Date].[Calendar].[All Periods], /* Root */
    [Date].[Calendar].[Calendar Year].Members, /* Year */
    [Date].[Calendar].[Calendar Semester].Members, /* Semester */
    [Date].[Calendar].[Calendar Quarter].Members, /* Quarter */
    /* IMPORTANT: Month level needed for seasonality */
    [Date].[Calendar].[Month].Members, /* Month */
    [Date].[Calendar].[Date].Members /* Daily - actual requirement */
    },
    {/* Second dimension */
    [Product].[Category].Members /* Product categories */
    }
) /* End CrossJoin */ ON ROWS
-- Cube specification
FROM [Adventure Works]
/* WHERE: Filtered to recent data only */
WHERE ([Customer].[Customer Geography].[Country].&[United States])
-- End of query
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Internet Sales Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Date", name="Calendar"),
            level=LevelReference(name="Date"),  # Daily level
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        ),
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
                    hierarchy=HierarchyReference(table="Customer", name="Customer Geography"),
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
        'Date'[Date],
        Product[Category],
        "Internet Sales Amount", [Internet Sales Amount]
    ),
    Customer[Country] = "United States"
)
```

### Human Readable

```
This query will:

1. Calculate: total Internet Sales Amount
2. Grouped by: each Date, each Category
3. Where:
   - Country equals United States

SQL-like representation:
```sql
SELECT Date, Category, SUM(Internet Sales Amount) AS Internet Sales Amount
FROM Adventure Works
WHERE Country = 'United States'
GROUP BY Date, Category
```

-----

## Test Case 15: Account Hierarchy with Parent-Child Relationships

### Input MDX (Poorly Formatted)

```mdx
/* QUERY: Financial reporting extract */
/* OPTIMIZER_HINT: PREFER_FORMULA_ENGINE */
SELECT 
    NON EMPTY {
        [Measures].[Amount] /* Base financial measure */
    } ON 0,
    NON EMPTY {
        /* Chart of Accounts hierarchy - need detail accounts */
        [Account].[Accounts].[All Accounts], -- Level 0
        [Account].[Accounts].[Account Type].Members, -- Level 1: Assets, Liabilities, etc
        [Account].[Accounts].[Account Category].Members, -- Level 2: Current Assets, Fixed Assets
        [Account].[Accounts].[Account Group].Members, -- Level 3: Cash, Receivables
        [Account].[Accounts].[Account Subgroup].Members, -- Level 4: Operating Cash, Restricted Cash
        /* HINT: GL_OPTIMIZER prefers leaf level */
        [Account].[Accounts].[Account].Members -- Level 5: Individual GL Accounts (REQUIRED)
    } /* End account specification */ ON 1
FROM [Finance Cube]
WHERE (
    /* Time filter */
    [Date].[Fiscal].[Fiscal Year].&[FY2023],
    /* Scenario */
    [Scenario].[Scenario].&[Actual] /* Not budget */
)
/* END QUERY */
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Finance Cube"),
    measures=[
        Measure(name="Amount", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Account", name="Accounts"),
            level=LevelReference(name="Account"),  # Level 5 - GL Accounts
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Fiscal"),
                    level=LevelReference(name="Fiscal Year"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["FY2023"]
            )
        ),
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Scenario", name="Scenario"),
                    level=LevelReference(name="Scenario"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["Actual"]
            )
        ),
        Filter(
            filter_type=FilterType.NON_EMPTY,
            target=NonEmptyFilter(measure="Amount")
        )
    ],
    order_by=[],
    limit=None,
    calculations=[],
    metadata=QueryMetadata(optimizer_hints=["PREFER_FORMULA_ENGINE", "GL_OPTIMIZER"])
)
```

### Clean DAX Output

```dax
EVALUATE
FILTER(
    CALCULATETABLE(
        SUMMARIZECOLUMNS(
            Account[Account],
            "Amount", [Amount]
        ),
        'Date'[Fiscal Year] = "FY2023",
        Scenario[Scenario] = "Actual"
    ),
    [Amount] <> BLANK()
)
```

### Human Readable

```
This query will:

1. Calculate: total Amount
2. Grouped by: each Account (GL Account level)
3. Where:
   - Fiscal Year equals FY2023
   - Scenario equals Actual
   - Amount is not empty

SQL-like representation:
```sql
SELECT Account, SUM(Amount) AS Amount
FROM Finance Cube
WHERE Fiscal Year = 'FY2023'
  AND Scenario = 'Actual'
GROUP BY Account
HAVING SUM(Amount) IS NOT NULL
```

-----

## Test Case 16: Ragged Hierarchy with Mixed Levels

### Input MDX (Poorly Formatted)

```mdx
WITH 
/* KPI Calculations */
MEMBER [Measures].[YoY Growth] AS
    /* Year over Year calculation */
    /* FORMULA_ENGINE_HINT: USE_CACHE */
    ([Measures].[Sales Amount] - 
     (ParallelPeriod([Date].[Calendar].[Calendar Year], 1), [Measures].[Sales Amount])) /
    (ParallelPeriod([Date].[Calendar].[Calendar Year], 1), [Measures].[Sales Amount]),
    FORMAT_STRING = "Percent" /* Display as percentage */
SELECT 
{[Measures].[Sales Amount] /* Current period sales */, 
 [Measures].[YoY Growth] /* Calculated growth */} ON 0,
{/* Ragged geography hierarchy - some countries have states, others don't */
/* Level 0 */ [Geography].[Geography].[All],
/* Level 1 */ [Geography].[Geography].[Country].Members,
/* Level 2 */ [Geography].[Geography].[State-Province].Members, -- Not all countries have this
/* Level 3 */ [Geography].[Geography].[County].Members, -- US specific
/* Level 4 */ [Geography].[Geography].[City].Members, -- Universal
/* Level 5 */ [Geography].[Geography].[Postal Code].Members -- Most granular (NEEDED)
} ON 1
FROM [Adventure Works]
/* Time context for comparison */
WHERE ([Date].[Calendar Year].&[2023])
/* QUERY_TIMEOUT: 300 */
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="YoY Growth", aggregation=AggregationType.CUSTOM, format_string="Percent")
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Geography", name="Geography"),
            level=LevelReference(name="Postal Code"),  # Most granular level
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
    calculations=[
        Calculation(
            name="YoY Growth",
            calculation_type=CalculationType.MEASURE,
            expression=BinaryOperation(
                left=BinaryOperation(
                    left=MeasureReference("Sales Amount"),
                    operator="-",
                    right=TimeIntelligenceExpression(
                        function="PARALLELPERIOD",
                        measure="Sales Amount",
                        period_type="Year",
                        offset=-1
                    )
                ),
                operator="/",
                right=TimeIntelligenceExpression(
                    function="PARALLELPERIOD",
                    measure="Sales Amount",
                    period_type="Year",
                    offset=-1
                )
            )
        )
    ],
    metadata=QueryMetadata(timeout=300)
)
```

### Clean DAX Output

```dax
DEFINE
    MEASURE Sales[YoY Growth] = 
        VAR CurrentYearSales = [Sales Amount]
        VAR PriorYearSales = CALCULATE([Sales Amount], DATEADD('Date'[Date], -1, YEAR))
        RETURN DIVIDE(CurrentYearSales - PriorYearSales, PriorYearSales)
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Geography[Postal Code],
        "Sales Amount", [Sales Amount],
        "YoY Growth", [YoY Growth]
    ),
    'Date'[Calendar Year] = 2023
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount, YoY Growth
2. Grouped by: each Postal Code
3. Where:
   - Calendar Year equals 2023
4. With these calculations:
   - Calculate YoY Growth as (Sales Amount minus Sales Amount from parallel period Year -1) divided by Sales Amount from parallel period Year -1

SQL-like representation:
```sql
SELECT Postal Code, 
       SUM(Sales Amount) AS Sales Amount,
       (SUM(Sales Amount) - LAG(SUM(Sales Amount), 1) OVER (PARTITION BY Postal Code ORDER BY Year)) 
       / LAG(SUM(Sales Amount), 1) OVER (PARTITION BY Postal Code ORDER BY Year) AS YoY Growth
FROM Adventure Works
WHERE Calendar Year = 2023
GROUP BY Postal Code
```

-----

## Test Case 17: Multiple Hierarchies with Redundant Ancestors

### Input MDX (Poorly Formatted)

```mdx
/* MULTI-DIMENSIONAL ANALYSIS QUERY */
/* CACHE_MODE: WRITEBACK_ENABLED */
SELECT NON EMPTY {
    [Measures].[Sales Amount] /* Revenue */,
    [Measures].[Total Cost] /* COGS */,
    [Measures].[Margin] /* Profit */
} /* Measures set */ ON COLUMNS,
NON EMPTY CROSSJOIN(
    CROSSJOIN(
        {/* Customer hierarchy - need customer level */
        [Customer].[Customer Geography].[All Customers], -- Root
        [Customer].[Customer Geography].[Country].Members, -- L1
        [Customer].[Customer Geography].[State-Province].Members, -- L2
        [Customer].[Customer Geography].[City].Members, -- L3
        [Customer].[Customer Geography].[Customer].Members -- L4 (REQUIRED)
        },
        {/* Product hierarchy - need SKU */
        [Product].[Product Categories].[All Products], -- Root
        [Product].[Product Categories].[Category].Members, -- L1
        [Product].[Product Categories].[Subcategory].Members, -- L2
        [Product].[Product Categories].[Product].Members -- L3 SKU (REQUIRED)
        }
    ),
    {/* Time hierarchy - need month level */
    [Date].[Calendar].[All Periods], -- Root
    [Date].[Calendar].[Calendar Year].Members, -- Year
    [Date].[Calendar].[Calendar Quarter].Members, -- Quarter
    [Date].[Calendar].[Month].Members -- Month (REQUIRED)
    /* OPTIMIZER: AVOID_DAILY_GRANULARITY */
    }
) ON ROWS
FROM [Adventure Works]
/* EXECUTION_MODE: CELL_BY_CELL */
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="Total Cost", aggregation=AggregationType.SUM),
        Measure(name="Margin", aggregation=AggregationType.SUM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Customer", name="Customer Geography"),
            level=LevelReference(name="Customer"),  # L4
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        ),
        Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product Categories"),
            level=LevelReference(name="Product"),  # L3 SKU
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        ),
        Dimension(
            hierarchy=HierarchyReference(table="Date", name="Calendar"),
            level=LevelReference(name="Month"),  # Month level
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
    calculations=[],
    metadata=QueryMetadata(
        cache_mode="WRITEBACK_ENABLED",
        execution_mode="CELL_BY_CELL",
        optimizer_hints=["AVOID_DAILY_GRANULARITY"]
    )
)
```

### Clean DAX Output

```dax
EVALUATE
FILTER(
    SUMMARIZECOLUMNS(
        Customer[Customer],
        Product[Product],
        'Date'[Month],
        "Sales Amount", [Sales Amount],
        "Total Cost", [Total Cost],
        "Margin", [Margin]
    ),
    [Sales Amount] <> BLANK()
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount, total Total Cost, total Margin
2. Grouped by: each Customer, each Product, each Month
3. Where:
   - Sales Amount is not empty

SQL-like representation:
```sql
SELECT Customer, Product, Month, 
       SUM(Sales Amount) AS Sales Amount,
       SUM(Total Cost) AS Total Cost,
       SUM(Margin) AS Margin
FROM Adventure Works
GROUP BY Customer, Product, Month
HAVING SUM(Sales Amount) IS NOT NULL
```

-----

## Test Case 18: Recursive Hierarchy with All Levels Expanded

### Input MDX (Poorly Formatted)

```mdx
WITH 
/* Recursive calculations for organizational metrics */
MEMBER [Measures].[Team Total] AS
    /* RECURSION_LIMIT: 10 */
    AGGREGATE(
        DESCENDANTS([Employee].[Employees].CurrentMember, 
                    [Employee].[Employees].[Employee], /* Leaf level */
                    SELF_AND_BEFORE),
        [Measures].[Sales Amount]
    ) /* Sum including all reports */
SELECT 
    {[Measures].[Sales Amount] /* Individual sales */,
     [Measures].[Team Total] /* Rollup */} ON 0,
    {/* Organizational hierarchy - all management levels */
    /* HINT: ORG_TREE_OPTIMIZATION = TRUE */
    [Employee].[Employees].[All], -- CEO level
    [Employee].[Employees].[Level 01].Members, -- EVP
    [Employee].[Employees].[Level 02].Members, -- SVP
    [Employee].[Employees].[Level 03].Members, -- VP
    [Employee].[Employees].[Level 04].Members, -- Director
    [Employee].[Employees].[Level 05].Members, -- Sr Manager
    [Employee].[Employees].[Level 06].Members, -- Manager
    [Employee].[Employees].[Level 07].Members, -- Team Lead
    [Employee].[Employees].[Level 08].Members, -- Sr IC
    [Employee].[Employees].[Level 09].Members -- IC (NEEDED)
    /* MAX_DEPTH_REACHED */
    } ON 1
FROM [HR Analytics]
WHERE (
    [Date].[Fiscal Quarter].&[FY2023-Q4] /* Latest quarter */
    /* FILTER_EARLY: TRUE */
)
```

### IR Representation

```python
Query(
    cube=CubeReference(name="HR Analytics"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="Team Total", aggregation=AggregationType.CUSTOM)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Employee", name="Employees"),
            level=LevelReference(name="Level 09"),  # Individual Contributors
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Fiscal"),
                    level=LevelReference(name="Fiscal Quarter"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["FY2023-Q4"]
            )
        )
    ],
    order_by=[],
    limit=None,
    calculations=[
        Calculation(
            name="Team Total",
            calculation_type=CalculationType.MEASURE,
            expression=AggregateExpression(
                function="AGGREGATE",
                scope="DESCENDANTS_SELF_AND_BEFORE",
                measure="Sales Amount"
            )
        )
    ],
    metadata=QueryMetadata(
        optimizer_hints=["ORG_TREE_OPTIMIZATION", "FILTER_EARLY"],
        recursion_limit=10
    )
)
```

### Clean DAX Output

```dax
DEFINE
    MEASURE Employee[Team Total] = 
        CALCULATE(
            [Sales Amount],
            FILTER(
                ALL(Employee),
                PATHCONTAINS(Employee[Path], EARLIER(Employee[EmployeeKey]))
            )
        )
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Employee[Employee],
        "Sales Amount", [Sales Amount],
        "Team Total", [Team Total]
    ),
    'Date'[Fiscal Quarter] = "FY2023-Q4"
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount, Team Total
2. Grouped by: each Employee (individual contributor level)
3. Where:
   - Fiscal Quarter equals FY2023-Q4
4. With these calculations:
   - Calculate Team Total as aggregate of Sales Amount for all descendants including self

SQL-like representation:
```sql
WITH RECURSIVE TeamHierarchy AS (
    -- Recursive CTE to calculate team totals
    SELECT EmployeeID, ManagerID, Sales Amount
    FROM HR Analytics
    WHERE Fiscal Quarter = 'FY2023-Q4'
)
SELECT Employee, 
       SUM(Sales Amount) AS Sales Amount,
       SUM(Sales Amount) OVER (PARTITION BY Team) AS Team Total
FROM TeamHierarchy
GROUP BY Employee
```

-----

## Test Case 19: Time Hierarchy with Every Period Type

### Input MDX (Poorly Formatted)

```mdx
/* TIME INTELLIGENCE QUERY */
/* STORAGE_ENGINE_HINT: USE_AGGREGATIONS */
SELECT 
    /* Measures with time intelligence */
    {[Measures].[Internet Sales Amount] /* Current period */,
     [Measures].[Internet Order Count] /* Transactions */
    } ON COLUMNS,
    /* Every possible time period - only need weeks */
    {[Date].[Calendar Time].[All Periods], -- Root
     [Date].[Calendar Time].[Calendar Year].Members, -- Years
     /* COMMENT: Semester level rarely used */
     [Date].[Calendar Time].[Calendar Semester].Members, -- Semesters
     [Date].[Calendar Time].[Calendar Quarter].Members, -- Quarters
     /* Monthly data aggregation point */
     [Date].[Calendar Time].[Month].Members, -- Months
     /* TARGET_LEVEL: Week */
     [Date].[Calendar Time].[Calendar Week].Members, -- Weeks (REQUIRED)
     /* NOTE: Daily would be too granular */
     -- [Date].[Calendar Time].[Date].Members -- Days (commented out)
    } ON ROWS
FROM [Adventure Works]
/* Complex WHERE clause */
WHERE (
    /* Multiple filters */
    [Product].[Color].&[Black], /* Color filter */
    [Customer].[Country].&[United States], /* Geographic filter */
    [Promotion].[Promotion Type].&[No Discount] /* Promo filter */
    /* PARALLEL_EXECUTION: ENABLED */
)
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Internet Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="Internet Order Count", aggregation=AggregationType.COUNT)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Date", name="Calendar Time"),
            level=LevelReference(name="Calendar Week"),  # Week level only
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
    ],
    filters=[
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Color"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["Black"]
            )
        ),
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Customer", name="Customer"),
                    level=LevelReference(name="Country"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["United States"]
            )
        ),
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Promotion", name="Promotion"),
                    level=LevelReference(name="Promotion Type"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["No Discount"]
            )
        )
    ],
    order_by=[],
    limit=None,
    calculations=[],
    metadata=QueryMetadata(
        storage_hint="USE_AGGREGATIONS",
        parallel_execution=True
    )
)
```

### Clean DAX Output

```dax
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        'Date'[Calendar Week],
        "Internet Sales Amount", [Internet Sales Amount],
        "Internet Order Count", [Internet Order Count]
    ),
    Product[Color] = "Black",
    Customer[Country] = "United States",
    Promotion[Promotion Type] = "No Discount"
)
```

### Human Readable

```
This query will:

1. Calculate: total Internet Sales Amount, count of Internet Order Count
2. Grouped by: each Calendar Week
3. Where:
   - Color equals Black
   - Country equals United States
   - Promotion Type equals No Discount

SQL-like representation:
```sql
SELECT Calendar Week, 
       SUM(Internet Sales Amount) AS Internet Sales Amount,
       COUNT(Internet Order Count) AS Internet Order Count
FROM Adventure Works
WHERE Color = 'Black'
  AND Country = 'United States'
  AND Promotion Type = 'No Discount'
GROUP BY Calendar Week
```

-----

## Test Case 20: Matrix Organization with Every Reporting Line

### Input MDX (Poorly Formatted)

```mdx
/* MATRIX ORG STRUCTURE QUERY */
WITH 
/* Calculate dotted-line relationships */
MEMBER [Measures].[Matrix Reports] AS
    /* CUSTOM_ROLLUP_ENABLED */
    COUNT(
        FILTER(
            /* Check both solid and dotted lines */
            EXISTING [Employee].[Reports To].Members,
            [Measures].[Collaboration Score] > 0
        )
    ) /* Count of matrix relationships */
SELECT 
    {[Measures].[Sales Amount] /* Direct sales */,
     [Measures].[Matrix Reports] /* Dotted line count */,
     [Measures].[Collaboration Score] /* Cross-team metric */
    } ON 0,
    /* All possible reporting relationships */
    {/* Primary hierarchy - solid line reporting */
    [Employee].[Reports To].[All], -- CEO
    [Employee].[Reports To].[Level 01].Members, -- C-Suite
    [Employee].[Reports To].[Level 02].Members, -- EVP
    /* MATRIX_START */
    [Employee].[Reports To].[Level 03].Members, -- SVP
    [Employee].[Reports To].[Level 04].Members, -- VP
    [Employee].[Reports To].[Level 05].Members, -- Director
    [Employee].[Reports To].[Level 06].Members, -- Sr Manager
    [Employee].[Reports To].[Level 07].Members, -- Manager
    [Employee].[Reports To].[Level 08].Members, -- Lead
    [Employee].[Reports To].[Level 09].Members, -- Sr IC
    [Employee].[Reports To].[Level 10].Members, -- IC (REQUIRED)
    /* MATRIX_END */
    /* Include dotted-line relationships */
    DESCENDANTS([Employee].[Reports To].[All], 10, SELF_AND_AFTER)
    } ON 1
FROM [Matrix Organization]
/* Time and scenario filters */
WHERE (
    [Date].[Calendar].[Calendar Year].&[2023], /* Current year */
    [Scenario].[Scenario].&[Actual], /* Actuals only */
    /* ORG_MODEL: MATRIX_WITH_DOTTED_LINES */
    [Organization].[Org Type].&[Matrix] /* Matrix orgs only */
)
/* QUERY_PRIORITY: HIGH */
```

### IR Representation

```python
Query(
    cube=CubeReference(name="Matrix Organization"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="Matrix Reports", aggregation=AggregationType.CUSTOM),
        Measure(name="Collaboration Score", aggregation=AggregationType.AVG)
    ],
    dimensions=[
        Dimension(
            hierarchy=HierarchyReference(table="Employee", name="Reports To"),
            level=LevelReference(name="Level 10"),  # Individual Contributors
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
                    hierarchy=HierarchyReference(table="Scenario", name="Scenario"),
                    level=LevelReference(name="Scenario"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["Actual"]
            )
        ),
        Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=Dimension(
                    hierarchy=HierarchyReference(table="Organization", name="Organization"),
                    level=LevelReference(name="Org Type"),
                    members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                ),
                operator=FilterOperator.EQUALS,
                values=["Matrix"]
            )
        )
    ],
    order_by=[],
    limit=None,
    calculations=[
        Calculation(
            name="Matrix Reports",
            calculation_type=CalculationType.MEASURE,
            expression=CountExpression(
                filter_condition=ComparisonExpression(
                    left=MeasureReference("Collaboration Score"),
                    operator=ComparisonOperator.GT,
                    right=Constant(0)
                )
            )
        )
    ],
    metadata=QueryMetadata(
        org_model="MATRIX_WITH_DOTTED_LINES",
        query_priority="HIGH"
    )
)
```

### Clean DAX Output

```dax
DEFINE
    MEASURE Employee[Matrix Reports] = 
        COUNTROWS(
            FILTER(
                ALL(Employee[Reports To]),
                [Collaboration Score] > 0
            )
        )
EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Employee[Employee],
        "Sales Amount", [Sales Amount],
        "Matrix Reports", [Matrix Reports],
        "Collaboration Score", [Collaboration Score]
    ),
    'Date'[Calendar Year] = 2023,
    Scenario[Scenario] = "Actual",
    Organization[Org Type] = "Matrix"
)
```

### Human Readable

```
This query will:

1. Calculate: total Sales Amount, Matrix Reports, average Collaboration Score
2. Grouped by: each Employee (individual contributor level)
3. Where:
   - Calendar Year equals 2023
   - Scenario equals Actual
   - Org Type equals Matrix
4. With these calculations:
   - Calculate Matrix Reports as count of employees where Collaboration Score > 0

SQL-like representation:
```sql
SELECT Employee, 
       SUM(Sales Amount) AS Sales Amount,
       COUNT(CASE WHEN Collaboration Score > 0 THEN 1 END) AS Matrix Reports,
       AVG(Collaboration Score) AS Collaboration Score
FROM Matrix Organization
WHERE Calendar Year = 2023
  AND Scenario = 'Actual'
  AND Org Type = 'Matrix'
GROUP BY Employee
```

-----

## Notes on Complex Test Cases

These test cases demonstrate:

1. **Excessive Hierarchy Listing**: Every level from root to leaf is explicitly listed when only the leaf level is needed
1. **Query Optimizer Comments**: Comments with hints like `OPTIMIZER:`, `HINT:`, `EXECUTION_MODE:`, etc.
1. **Inline Documentation**: Comments explaining what each level represents
1. **Metadata Comments**: Comments about query performance, timeouts, cache modes
1. **Commented-Out Code**: Some queries include commented-out alternatives
1. **Complex Nesting**: Multiple CrossJoins with redundant hierarchy specifications
1. **Ragged Hierarchies**: Where not all branches go to the same depth
1. **Time Intelligence**: With every possible time period listed
1. **Matrix Organizations**: Complex reporting relationships with dotted lines
1. **Recursive Calculations**: Team rollups and organizational aggregations

The IR successfully normalizes all this complexity down to just the essential components needed for the query.
