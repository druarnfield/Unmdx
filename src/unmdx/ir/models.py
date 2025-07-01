"""Core IR model classes."""

from typing import List, Optional, Union, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import (
    AggregationType, MemberSelectionType, FilterType, FilterOperator,
    ComparisonOperator, CalculationType, SortDirection
)
from .expressions import Expression


class CubeReference(BaseModel):
    """Reference to the data source."""
    
    name: str
    database: Optional[str] = None
    schema_name: Optional[str] = Field(None, alias="schema")
    
    def to_dax(self) -> str:
        """Convert to DAX table reference."""
        # In DAX, this maps to table relationships
        return f"-- Using model: {self.name}"
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        return f"the {self.name} data model"


class HierarchyReference(BaseModel):
    """Reference to a hierarchy within a dimension."""
    
    table: str  # DAX table name
    name: str   # Hierarchy name
    
    def to_dax(self) -> str:
        """Convert to DAX table reference."""
        return self.table
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        return f"{self.name} hierarchy"


class LevelReference(BaseModel):
    """Reference to a level within a hierarchy."""
    
    name: str
    ordinal: Optional[int] = None  # Level depth in hierarchy
    
    def to_dax(self) -> str:
        """Convert to DAX column reference."""
        return self.name
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        return self.name


class MemberSelection(BaseModel):
    """How members are selected from a dimension."""
    
    selection_type: MemberSelectionType
    specific_members: Optional[List[str]] = None
    parent_member: Optional[str] = None
    range_start: Optional[str] = None
    range_end: Optional[str] = None
    
    def is_all_members(self) -> bool:
        """Check if this selects all members."""
        return self.selection_type == MemberSelectionType.ALL
    
    def is_specific_members(self) -> bool:
        """Check if this selects specific members."""
        return self.selection_type == MemberSelectionType.SPECIFIC
    
    def get_member_list(self) -> List[str]:
        """Get list of specific members if available."""
        if self.selection_type == MemberSelectionType.SPECIFIC and self.specific_members:
            return self.specific_members
        return []
    
    @model_validator(mode='after')
    def validate_specific_members(self):
        """Validate specific members are provided when needed."""
        if self.selection_type == MemberSelectionType.SPECIFIC and not self.specific_members:
            raise ValueError("specific_members required when selection_type is SPECIFIC")
        return self


class Dimension(BaseModel):
    """A dimension for grouping."""
    
    hierarchy: HierarchyReference
    level: LevelReference
    members: MemberSelection
    alias: Optional[str] = None
    
    def to_dax(self) -> str:
        """Convert to DAX column reference."""
        return f"{self.hierarchy.table}[{self.level.name}]"
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        if self.members.is_all_members():
            return f"each {self.level.name}"
        elif self.members.is_specific_members():
            member_list = self.members.get_member_list()
            if len(member_list) <= 3:
                return f"{self.level.name} ({', '.join(member_list)})"
            else:
                return f"{self.level.name} ({len(member_list)} specific values)"
        else:
            return f"specific {self.level.name} values"


class Measure(BaseModel):
    """A measure to be calculated."""
    
    name: str
    aggregation: AggregationType
    expression: Optional[Expression] = None
    alias: Optional[str] = None
    format_string: Optional[str] = None
    
    def to_dax(self) -> str:
        """Convert to DAX measure reference."""
        measure_name = self.alias or self.name
        return f'"{measure_name}", [{self.name}]'
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        agg_text = {
            AggregationType.SUM: "total",
            AggregationType.AVG: "average",
            AggregationType.COUNT: "count of",
            AggregationType.DISTINCT_COUNT: "distinct count of",
            AggregationType.MIN: "minimum",
            AggregationType.MAX: "maximum",
            AggregationType.CUSTOM: ""
        }
        agg_prefix = agg_text.get(self.aggregation, "")
        display_name = self.alias or self.name
        return f"{agg_prefix} {display_name}".strip()
    
    def get_dependencies(self) -> List[str]:
        """Get list of dependencies for this measure."""
        if self.expression:
            return self.expression.get_dependencies()
        return []


class DimensionFilter(BaseModel):
    """Filter on dimension members."""
    
    dimension: Dimension
    operator: FilterOperator
    values: List[str]
    
    def to_dax(self) -> str:
        """Convert to DAX filter expression."""
        table_column = f"{self.dimension.hierarchy.table}[{self.dimension.level.name}]"
        
        if self.operator == FilterOperator.EQUALS and len(self.values) == 1:
            return f"{table_column} = \"{self.values[0]}\""
        elif self.operator == FilterOperator.IN or (self.operator == FilterOperator.EQUALS and len(self.values) > 1):
            values_list = ', '.join(f'"{v}"' for v in self.values)
            return f"{table_column} IN {{{values_list}}}"
        elif self.operator == FilterOperator.NOT_EQUALS:
            if len(self.values) == 1:
                return f"{table_column} <> \"{self.values[0]}\""
            else:
                values_list = ', '.join(f'"{v}"' for v in self.values)
                return f"NOT({table_column} IN {{{values_list}}})"
        elif self.operator == FilterOperator.CONTAINS:
            # Use SEARCH function for contains
            return f"NOT(ISERROR(SEARCH(\"{self.values[0]}\", {table_column})))"
        else:
            # Default case
            return f"{table_column} {self.operator.value} \"{self.values[0]}\""
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        level_name = self.dimension.level.name
        
        if self.operator == FilterOperator.EQUALS:
            if len(self.values) == 1:
                return f"{level_name} equals {self.values[0]}"
            else:
                return f"{level_name} is one of ({', '.join(self.values)})"
        elif self.operator == FilterOperator.IN:
            return f"{level_name} is one of ({', '.join(self.values)})"
        elif self.operator == FilterOperator.NOT_EQUALS:
            if len(self.values) == 1:
                return f"{level_name} not equal to {self.values[0]}"
            else:
                return f"{level_name} not in ({', '.join(self.values)})"
        elif self.operator == FilterOperator.CONTAINS:
            return f"{level_name} contains {self.values[0]}"
        else:
            return f"{level_name} {self.operator.value} {self.values[0]}"


class MeasureFilter(BaseModel):
    """Filter on measure values."""
    
    measure: Measure
    operator: ComparisonOperator
    value: Union[float, int]
    
    def to_dax(self) -> str:
        """Convert to DAX filter expression."""
        return f"[{self.measure.name}] {self.operator.value} {self.value}"
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        op_text = {
            ComparisonOperator.GT: "greater than",
            ComparisonOperator.LT: "less than",
            ComparisonOperator.GTE: "at least",
            ComparisonOperator.LTE: "at most",
            ComparisonOperator.EQ: "equals",
            ComparisonOperator.NEQ: "not equal to"
        }
        measure_name = self.measure.alias or self.measure.name
        return f"{measure_name} is {op_text[self.operator]} {self.value}"


class NonEmptyFilter(BaseModel):
    """Filter for non-empty cells."""
    
    measure: Optional[str] = None  # Specific measure to check, or None for any measure
    
    def to_dax(self) -> str:
        """Convert to DAX filter expression."""
        if self.measure:
            return f"[{self.measure}] <> BLANK()"
        else:
            return "-- Non-empty filter (requires context)"
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        if self.measure:
            return f"{self.measure} is not empty"
        else:
            return "exclude empty cells"


class Filter(BaseModel):
    """A filter condition."""
    
    filter_type: FilterType
    target: Union[DimensionFilter, MeasureFilter, NonEmptyFilter]
    
    def to_dax(self) -> str:
        """Convert to DAX filter expression."""
        return self.target.to_dax()
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        return self.target.to_human_readable()


class OrderBy(BaseModel):
    """Ordering specification."""
    
    expression: Union[str, Expression]  # Column name or expression
    direction: SortDirection = SortDirection.ASC
    
    def to_dax(self) -> str:
        """Convert to DAX ORDER BY clause."""
        if isinstance(self.expression, str):
            expr_dax = f"[{self.expression}]"
        else:
            expr_dax = self.expression.to_dax()
        
        if self.direction == SortDirection.DESC:
            expr_dax += " DESC"
        
        return expr_dax
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        if isinstance(self.expression, str):
            expr_text = self.expression
        else:
            expr_text = self.expression.to_human_readable()
        
        direction_text = "descending" if self.direction == SortDirection.DESC else "ascending"
        return f"{expr_text} ({direction_text})"


class Limit(BaseModel):
    """Limit specification."""
    
    count: int
    offset: int = 0
    
    def to_dax(self) -> str:
        """Convert to DAX TOP clause."""
        if self.offset > 0:
            # DAX doesn't have OFFSET, would need to use TOPN with ranking
            return f"-- TOP {self.count} OFFSET {self.offset} (requires ranking)"
        else:
            return f"TOP({self.count})"
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        if self.offset > 0:
            return f"limit to {self.count} rows starting from row {self.offset + 1}"
        else:
            return f"limit to first {self.count} rows"


class Calculation(BaseModel):
    """A calculated measure or member."""
    
    name: str
    calculation_type: CalculationType
    expression: Expression
    solve_order: Optional[int] = None
    format_string: Optional[str] = None
    
    def to_dax_definition(self) -> str:
        """Convert to DAX measure definition."""
        if self.calculation_type == CalculationType.MEASURE:
            return f"MEASURE Sales[{self.name}] = {self.expression.to_dax()}"
        else:
            # For members, we might need different handling
            return f"-- CALCULATED MEMBER {self.name} = {self.expression.to_dax()}"
    
    def to_human_readable(self) -> str:
        """Convert to human-readable text."""
        calc_type = "measure" if self.calculation_type == CalculationType.MEASURE else "member"
        return f"Calculate {calc_type} {self.name} as {self.expression.to_human_readable()}"
    
    def get_dependencies(self) -> List[str]:
        """Get list of dependencies for this calculation."""
        return self.expression.get_dependencies()


class QueryMetadata(BaseModel):
    """Metadata for query optimization and tracking."""
    
    created_at: Optional[datetime] = None
    source_mdx_hash: Optional[str] = None
    optimization_hints: List[str] = Field(default_factory=list)
    complexity_score: Optional[int] = None
    estimated_result_size: Optional[int] = None
    
    # Performance tracking
    parse_duration_ms: Optional[float] = None
    transform_duration_ms: Optional[float] = None
    
    # Error tracking
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


class Query(BaseModel):
    """Root node representing a complete query."""
    
    # Data source
    cube: CubeReference
    
    # What to calculate/retrieve
    measures: List[Measure] = Field(default_factory=list)
    
    # Grouping dimensions
    dimensions: List[Dimension] = Field(default_factory=list)
    
    # Filtering conditions
    filters: List[Filter] = Field(default_factory=list)
    
    # Sorting
    order_by: List[OrderBy] = Field(default_factory=list)
    
    # Limiting results
    limit: Optional[Limit] = None
    
    # Calculated members/measures
    calculations: List[Calculation] = Field(default_factory=list)
    
    # Metadata for optimization
    metadata: QueryMetadata = Field(default_factory=QueryMetadata)
    
    def to_dax(self) -> str:
        """Generate DAX query from IR."""
        parts = []
        
        # Add DEFINE section if there are calculations
        if self.calculations:
            parts.append("DEFINE")
            for calc in self.calculations:
                parts.append(f"    {calc.to_dax_definition()}")
        
        # Main query
        parts.append("EVALUATE")
        
        # Determine the main table function
        if self.dimensions:
            # Use SUMMARIZECOLUMNS for dimensional queries
            parts.append(self._generate_summarizecolumns())
        else:
            # Simple measure query
            parts.append(self._generate_measure_table())
        
        # Add ORDER BY if needed
        if self.order_by:
            order_parts = [o.to_dax() for o in self.order_by]
            parts.append(f"ORDER BY {', '.join(order_parts)}")
        
        return '\n'.join(parts)
    
    def _generate_summarizecolumns(self) -> str:
        """Generate SUMMARIZECOLUMNS function."""
        args = []
        
        # Group by columns
        for dim in self.dimensions:
            args.append(f"    {dim.to_dax()}")
        
        # Filters (only dimension filters for now)
        for filter_obj in self.filters:
            if filter_obj.filter_type == FilterType.DIMENSION:
                dim_filter = filter_obj.target
                table = dim_filter.dimension.hierarchy.table
                filter_expr = filter_obj.to_dax()
                args.append(f"    FILTER(ALL({table}), {filter_expr})")
        
        # Measures
        for measure in self.measures:
            args.append(f"    {measure.to_dax()}")
        
        newline = '\n'
        return f"SUMMARIZECOLUMNS({newline}{f',{newline}'.join(args)}{newline})"
    
    def _generate_measure_table(self) -> str:
        """Generate simple measure table for queries without dimensions."""
        if not self.measures:
            return "ROW(\"Value\", BLANK())"
        
        measure_pairs = []
        for measure in self.measures:
            measure_name = measure.alias or measure.name
            measure_pairs.append(f'"{measure_name}", [{measure.name}]')
        
        return f"{{ {', '.join(measure_pairs)} }}"
    
    def to_human_readable(self) -> str:
        """Generate human-readable explanation."""
        parts = []
        
        # Main query explanation
        parts.append("This query will:")
        parts.append("")
        
        # What we're calculating
        if self.measures:
            measure_text = ", ".join(m.to_human_readable() for m in self.measures)
            parts.append(f"1. Calculate: {measure_text}")
        
        # How we're grouping
        if self.dimensions:
            dim_text = ", ".join(d.to_human_readable() for d in self.dimensions)
            parts.append(f"2. Grouped by: {dim_text}")
        
        # Filters
        if self.filters:
            parts.append("3. Where:")
            for filter_obj in self.filters:
                parts.append(f"   - {filter_obj.to_human_readable()}")
        
        # Calculations
        if self.calculations:
            parts.append("4. With these calculations:")
            for calc in self.calculations:
                parts.append(f"   - {calc.to_human_readable()}")
        
        # Sorting
        if self.order_by:
            order_text = ", ".join(o.to_human_readable() for o in self.order_by)
            parts.append(f"5. Sorted by: {order_text}")
        
        # Limit
        if self.limit:
            parts.append(f"6. {self.limit.to_human_readable()}")
        
        # SQL-like representation
        parts.append("")
        parts.append("SQL-like representation:")
        parts.append("```sql")
        parts.append(self._generate_sql_like())
        parts.append("```")
        
        return '\n'.join(parts)
    
    def _generate_sql_like(self) -> str:
        """Generate SQL-like syntax."""
        sql_parts = []
        
        # SELECT clause
        select_items = []
        for dim in self.dimensions:
            select_items.append(dim.level.name)
        for measure in self.measures:
            alias = measure.alias or measure.name
            if measure.aggregation != AggregationType.CUSTOM:
                select_items.append(f"{measure.aggregation.value}({measure.name}) AS {alias}")
            else:
                select_items.append(f"{alias}")
        
        sql_parts.append(f"SELECT {', '.join(select_items)}")
        
        # FROM clause
        sql_parts.append(f"FROM {self.cube.name}")
        
        # WHERE clause
        if self.filters:
            where_conditions = []
            for filter_obj in self.filters:
                if filter_obj.filter_type != FilterType.NON_EMPTY:
                    where_conditions.append(filter_obj.to_human_readable())
            if where_conditions:
                sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        # GROUP BY clause
        if self.dimensions:
            group_by_items = [d.level.name for d in self.dimensions]
            sql_parts.append(f"GROUP BY {', '.join(group_by_items)}")
        
        # HAVING clause for measure filters
        having_conditions = []
        for filter_obj in self.filters:
            if filter_obj.filter_type == FilterType.MEASURE:
                having_conditions.append(filter_obj.to_human_readable())
        if having_conditions:
            sql_parts.append(f"HAVING {' AND '.join(having_conditions)}")
        
        # ORDER BY clause
        if self.order_by:
            order_items = [o.to_human_readable() for o in self.order_by]
            sql_parts.append(f"ORDER BY {', '.join(order_items)}")
        
        # LIMIT clause
        if self.limit:
            if self.limit.offset > 0:
                sql_parts.append(f"LIMIT {self.limit.count} OFFSET {self.limit.offset}")
            else:
                sql_parts.append(f"LIMIT {self.limit.count}")
        
        return '\n'.join(sql_parts)
    
    def get_all_dependencies(self) -> Dict[str, List[str]]:
        """Get all dependencies in the query."""
        dependencies = {
            "measures": [],
            "dimensions": [],
            "calculations": []
        }
        
        # Measure dependencies
        for measure in self.measures:
            dependencies["measures"].extend(measure.get_dependencies())
        
        # Dimension dependencies
        for dimension in self.dimensions:
            dependencies["dimensions"].append(f"{dimension.hierarchy.table}.{dimension.level.name}")
        
        # Calculation dependencies
        for calc in self.calculations:
            dependencies["calculations"].extend(calc.get_dependencies())
        
        return dependencies
    
    def validate_query(self) -> List[str]:
        """Validate the query and return list of issues."""
        issues = []
        
        # Check if we have either measures or dimensions
        if not self.measures and not self.dimensions:
            issues.append("Query must have at least one measure or dimension")
        
        # Check for circular dependencies in calculations
        calc_deps = {}
        for calc in self.calculations:
            calc_deps[calc.name] = calc.get_dependencies()
        
        # Simple circular dependency check
        for calc_name, deps in calc_deps.items():
            if calc_name in deps:
                issues.append(f"Calculation '{calc_name}' has circular dependency")
        
        # Check filter compatibility
        for filter_obj in self.filters:
            if filter_obj.filter_type == FilterType.MEASURE:
                measure_filter = filter_obj.target
                measure_names = [m.name for m in self.measures]
                if measure_filter.measure.name not in measure_names:
                    issues.append(f"Filter references measure '{measure_filter.measure.name}' which is not in the query")
        
        return issues