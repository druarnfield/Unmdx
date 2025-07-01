# Intermediate Representation (IR) Specification for MDX to DAX Converter

## Overview

This IR serves as a normalized, simplified representation of multidimensional queries that can be:

1. Generated from parsed MDX (after linting/normalization)
1. Converted to DAX queries
1. Explained in human-readable SQL-like terms

The IR is designed to be **semantic** rather than syntactic - it captures the intent of the query, not the specific syntax.

## 1. Core IR Structure

### 1.1 Query Node (Root)

```python
@dataclass
class Query:
    """Root node representing a complete query"""
    # Data source
    cube: CubeReference
    
    # What to calculate/retrieve
    measures: List[Measure]
    
    # Grouping dimensions
    dimensions: List[Dimension]
    
    # Filtering conditions
    filters: List[Filter]
    
    # Sorting
    order_by: List[OrderBy]
    
    # Limiting results
    limit: Optional[Limit]
    
    # Calculated members/measures
    calculations: List[Calculation]
    
    # Metadata for optimization
    metadata: QueryMetadata
```

### 1.2 Human-Readable Generation

Each IR node can generate a SQL-like explanation:

```python
def to_human_readable(self) -> str:
    """Generate SQL-like explanation"""
    return f"""
    SELECT {', '.join(m.to_human_readable() for m in self.measures)}
    FROM {self.cube.name}
    GROUP BY {', '.join(d.to_human_readable() for d in self.dimensions)}
    WHERE {' AND '.join(f.to_human_readable() for f in self.filters)}
    ORDER BY {', '.join(o.to_human_readable() for o in self.order_by)}
    """
```

## 2. Core Components

### 2.1 Cube Reference

```python
@dataclass
class CubeReference:
    """Reference to the data source"""
    name: str
    database: Optional[str]
    
    def to_dax(self) -> str:
        # In DAX, this maps to table relationships
        return f"-- Using model: {self.name}"
    
    def to_human_readable(self) -> str:
        return f"the {self.name} data model"
```

### 2.2 Measures

```python
@dataclass
class Measure:
    """A measure to be calculated"""
    name: str
    aggregation: AggregationType
    expression: Optional[Expression]
    alias: Optional[str]
    format_string: Optional[str]
    
    def to_dax(self) -> str:
        if self.alias:
            return f'"{self.alias}", [{self.name}]'
        return f'"{self.name}", [{self.name}]'
    
    def to_human_readable(self) -> str:
        agg_text = {
            AggregationType.SUM: "total",
            AggregationType.AVG: "average",
            AggregationType.COUNT: "count of",
            AggregationType.MIN: "minimum",
            AggregationType.MAX: "maximum"
        }
        return f"{agg_text.get(self.aggregation, '')} {self.name}"

class AggregationType(Enum):
    SUM = "SUM"
    AVG = "AVERAGE"
    COUNT = "COUNT"
    DISTINCT_COUNT = "DISTINCTCOUNT"
    MIN = "MIN"
    MAX = "MAX"
    CUSTOM = "CUSTOM"
```

### 2.3 Dimensions

```python
@dataclass
class Dimension:
    """A dimension for grouping"""
    hierarchy: HierarchyReference
    level: LevelReference
    members: MemberSelection
    
    def to_dax(self) -> str:
        if self.members.is_all_members():
            return f"{self.hierarchy.table}[{self.level.name}]"
        else:
            # Will need filtering
            return f"{self.hierarchy.table}[{self.level.name}]"
    
    def to_human_readable(self) -> str:
        if self.members.is_all_members():
            return f"each {self.level.name}"
        else:
            return f"specific {self.level.name} values"

@dataclass
class MemberSelection:
    """How members are selected from a dimension"""
    selection_type: MemberSelectionType
    specific_members: Optional[List[str]] = None
    
    def is_all_members(self) -> bool:
        return self.selection_type == MemberSelectionType.ALL

class MemberSelectionType(Enum):
    ALL = "ALL"              # All members at this level
    SPECIFIC = "SPECIFIC"    # Listed members
    CHILDREN = "CHILDREN"    # Children of a member
    DESCENDANTS = "DESCENDANTS"
    RANGE = "RANGE"         # Member range
```

### 2.4 Filters

```python
@dataclass
class Filter:
    """A filter condition"""
    filter_type: FilterType
    target: Union[DimensionFilter, MeasureFilter]
    
    def to_dax(self) -> str:
        return self.target.to_dax()
    
    def to_human_readable(self) -> str:
        return self.target.to_human_readable()

@dataclass
class DimensionFilter:
    """Filter on dimension members"""
    dimension: Dimension
    operator: FilterOperator
    values: List[str]
    
    def to_dax(self) -> str:
        table = self.dimension.hierarchy.table
        column = self.dimension.level.name
        if self.operator == FilterOperator.IN:
            values_list = ', '.join(f'"{v}"' for v in self.values)
            return f"{table}[{column}] IN {{{values_list}}}"
        elif self.operator == FilterOperator.EQUALS:
            return f"{table}[{column}] = \"{self.values[0]}\""
        # Add more operators as needed
    
    def to_human_readable(self) -> str:
        if self.operator == FilterOperator.IN:
            return f"{self.dimension.level.name} is one of ({', '.join(self.values)})"
        elif self.operator == FilterOperator.EQUALS:
            return f"{self.dimension.level.name} equals {self.values[0]}"

@dataclass
class MeasureFilter:
    """Filter on measure values"""
    measure: Measure
    operator: ComparisonOperator
    value: Union[float, int]
    
    def to_dax(self) -> str:
        return f"[{self.measure.name}] {self.operator.value} {self.value}"
    
    def to_human_readable(self) -> str:
        op_text = {
            ComparisonOperator.GT: "greater than",
            ComparisonOperator.LT: "less than",
            ComparisonOperator.GTE: "at least",
            ComparisonOperator.LTE: "at most",
            ComparisonOperator.EQ: "equals",
            ComparisonOperator.NEQ: "not equal to"
        }
        return f"{self.measure.name} is {op_text[self.operator]} {self.value}"
```

### 2.5 Calculations

```python
@dataclass
class Calculation:
    """A calculated measure or member"""
    name: str
    calculation_type: CalculationType
    expression: Expression
    solve_order: Optional[int] = None
    
    def to_dax_definition(self) -> str:
        return f"MEASURE {self.name} = {self.expression.to_dax()}"
    
    def to_human_readable(self) -> str:
        return f"Calculate {self.name} as {self.expression.to_human_readable()}"

class CalculationType(Enum):
    MEASURE = "MEASURE"
    MEMBER = "MEMBER"
```

### 2.6 Expressions

```python
@dataclass
class Expression:
    """Base class for expressions"""
    pass

@dataclass
class BinaryOperation(Expression):
    """Binary operations like +, -, *, /"""
    left: Expression
    operator: str
    right: Expression
    
    def to_dax(self) -> str:
        # Handle division specially for safety
        if self.operator == "/":
            return f"DIVIDE({self.left.to_dax()}, {self.right.to_dax()})"
        return f"({self.left.to_dax()} {self.operator} {self.right.to_dax()})"
    
    def to_human_readable(self) -> str:
        op_text = {
            "+": "plus",
            "-": "minus",
            "*": "times",
            "/": "divided by"
        }
        return f"{self.left.to_human_readable()} {op_text.get(self.operator, self.operator)} {self.right.to_human_readable()}"

@dataclass
class MeasureReference(Expression):
    """Reference to a measure"""
    measure_name: str
    
    def to_dax(self) -> str:
        return f"[{self.measure_name}]"
    
    def to_human_readable(self) -> str:
        return self.measure_name

@dataclass
class Constant(Expression):
    """Constant value"""
    value: Union[float, int, str]
    
    def to_dax(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)
    
    def to_human_readable(self) -> str:
        return str(self.value)
```

## 3. Query Generation

### 3.1 DAX Generation

```python
class DaxGenerator:
    def generate(self, query: Query) -> str:
        """Generate DAX from IR"""
        parts = []
        
        # Add DEFINE section if there are calculations
        if query.calculations:
            parts.append("DEFINE")
            for calc in query.calculations:
                parts.append(f"  {calc.to_dax_definition()}")
        
        # Main query
        parts.append("EVALUATE")
        
        # Determine the main table function
        if query.dimensions:
            # Use SUMMARIZECOLUMNS for dimensional queries
            parts.append(self._generate_summarizecolumns(query))
        else:
            # Simple measure query
            parts.append(self._generate_measure_table(query))
        
        # Add ORDER BY if needed
        if query.order_by:
            order_parts = [o.to_dax() for o in query.order_by]
            parts.append(f"ORDER BY {', '.join(order_parts)}")
        
        return '\n'.join(parts)
    
    def _generate_summarizecolumns(self, query: Query) -> str:
        """Generate SUMMARIZECOLUMNS function"""
        args = []
        
        # Group by columns
        for dim in query.dimensions:
            args.append(f"    {dim.to_dax()}")
        
        # Filters
        for filter in query.filters:
            args.append(f"    FILTER(ALL({filter.target.dimension.hierarchy.table}), {filter.to_dax()})")
        
        # Measures
        for measure in query.measures:
            args.append(f"    {measure.to_dax()}")
        
        return f"SUMMARIZECOLUMNS(\n{',\\n'.join(args)}\n)"
```

### 3.2 Human-Readable SQL-like Explanation

```python
class HumanReadableGenerator:
    def generate(self, query: Query) -> str:
        """Generate human-readable explanation"""
        parts = []
        
        # Main query explanation
        parts.append("This query will:")
        parts.append("")
        
        # What we're calculating
        if query.measures:
            measure_text = ", ".join(m.to_human_readable() for m in query.measures)
            parts.append(f"1. Calculate: {measure_text}")
        
        # How we're grouping
        if query.dimensions:
            dim_text = ", ".join(d.to_human_readable() for d in query.dimensions)
            parts.append(f"2. Grouped by: {dim_text}")
        
        # Filters
        if query.filters:
            parts.append("3. Where:")
            for filter in query.filters:
                parts.append(f"   - {filter.to_human_readable()}")
        
        # Calculations
        if query.calculations:
            parts.append("4. With these calculations:")
            for calc in query.calculations:
                parts.append(f"   - {calc.to_human_readable()}")
        
        # Sorting
        if query.order_by:
            order_text = ", ".join(o.to_human_readable() for o in query.order_by)
            parts.append(f"5. Sorted by: {order_text}")
        
        # SQL-like representation
        parts.append("")
        parts.append("SQL-like representation:")
        parts.append("```sql")
        parts.append(self._generate_sql_like(query))
        parts.append("```")
        
        return '\n'.join(parts)
    
    def _generate_sql_like(self, query: Query) -> str:
        """Generate SQL-like syntax"""
        sql_parts = []
        
        # SELECT clause
        select_items = []
        for dim in query.dimensions:
            select_items.append(dim.level.name)
        for measure in query.measures:
            alias = measure.alias or measure.name
            select_items.append(f"{measure.aggregation.value}({measure.name}) AS {alias}")
        
        sql_parts.append(f"SELECT {', '.join(select_items)}")
        
        # FROM clause
        sql_parts.append(f"FROM {query.cube.name}")
        
        # WHERE clause
        if query.filters:
            where_conditions = [f.to_human_readable() for f in query.filters]
            sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        # GROUP BY clause
        if query.dimensions:
            group_by_items = [d.level.name for d in query.dimensions]
            sql_parts.append(f"GROUP BY {', '.join(group_by_items)}")
        
        # ORDER BY clause
        if query.order_by:
            order_items = [o.to_human_readable() for o in query.order_by]
            sql_parts.append(f"ORDER BY {', '.join(order_items)}")
        
        return '\n'.join(sql_parts)
```

## 4. Example IR Usage

### 4.1 Simple Sales by Category Query

**MDX Input:**

```mdx
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       {[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].[CY 2023])
```

**IR Representation:**

```python
query = Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(
            name="Sales Amount",
            aggregation=AggregationType.SUM,
            alias="Total Sales"
        )
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
                values=["CY 2023"]
            )
        )
    ],
    order_by=[],
    limit=None,
    calculations=[],
    metadata=QueryMetadata()
)
```

**DAX Output:**

```dax
EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    FILTER(ALL('Date'), 'Date'[Calendar Year] = "CY 2023"),
    "Total Sales", [Sales Amount]
)
```

**Human-Readable Output:**

```
This query will:

1. Calculate: total Sales Amount
2. Grouped by: each Category
3. Where:
   - Calendar Year equals CY 2023

SQL-like representation:
```sql
SELECT Category, SUM(Sales Amount) AS Total Sales
FROM Adventure Works
WHERE Calendar Year = 'CY 2023'
GROUP BY Category
```

```
### 4.2 Complex Query with Calculations

**MDX Input:**
```mdx
WITH MEMBER [Measures].[Profit Margin] AS 
    ([Measures].[Profit] / [Measures].[Sales Amount]) * 100
SELECT {[Measures].[Sales Amount], [Measures].[Profit], [Measures].[Profit Margin]} ON COLUMNS,
       {[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].[CY 2023])
```

**IR Representation:**

```python
query = Query(
    cube=CubeReference(name="Adventure Works"),
    measures=[
        Measure(name="Sales Amount", aggregation=AggregationType.SUM),
        Measure(name="Profit", aggregation=AggregationType.SUM),
        Measure(name="Profit Margin", aggregation=AggregationType.CUSTOM)
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
                values=["CY 2023"]
            )
        )
    ],
    calculations=[
        Calculation(
            name="Profit Margin",
            calculation_type=CalculationType.MEASURE,
            expression=BinaryOperation(
                left=BinaryOperation(
                    left=MeasureReference("Profit"),
                    operator="/",
                    right=MeasureReference("Sales Amount")
                ),
                operator="*",
                right=Constant(100)
            )
        )
    ],
    order_by=[],
    limit=None,
    metadata=QueryMetadata()
)
```

**Human-Readable Output:**

```
This query will:

1. Calculate: total Sales Amount, total Profit, Profit Margin
2. Grouped by: each Category
3. Where:
   - Calendar Year equals CY 2023
4. With these calculations:
   - Calculate Profit Margin as Profit divided by Sales Amount times 100

SQL-like representation:
```sql
SELECT Category, 
       SUM(Sales Amount) AS Sales Amount,
       SUM(Profit) AS Profit,
       (SUM(Profit) / SUM(Sales Amount)) * 100 AS Profit Margin
FROM Adventure Works
WHERE Calendar Year = 'CY 2023'
GROUP BY Category
```

```
## 5. Benefits of This IR Design

1. **Semantic Clarity**: The IR captures what the query does, not how it's written
2. **Easy MDX → IR**: Maps naturally from MDX concepts
3. **Easy IR → DAX**: Direct mapping to DAX table functions
4. **Human Friendly**: Can generate clear explanations
5. **Optimization Ready**: The IR can be analyzed and optimized before generating target code
6. **Extensible**: Easy to add new features or target languages

## 6. Implementation Notes

1. **Linting Integration**: The MDX parser can produce messy IR, which the linter normalizes
2. **Pattern Recognition**: Common MDX patterns can be recognized and simplified in IR
3. **Validation**: IR can be validated for logical consistency
4. **Multiple Targets**: Same IR can generate DAX, SQL, or other query languages
5. **Debugging**: IR provides a clear intermediate state for debugging conversions
```
