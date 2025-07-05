"""Main DAX generator implementation."""

from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from ..ir import (
    Query, CubeReference, Measure, Dimension, Filter, Calculation,
    OrderBy, Limit, FilterType, AggregationType, MemberSelectionType,
    DimensionFilter, MeasureFilter, NonEmptyFilter, Expression,
    SortDirection, QueryMetadata
)
from ..utils.logging import get_logger
from .expression_converter import ExpressionConverter
from .dax_formatter import DAXFormatter

logger = get_logger(__name__)


class DAXGenerationError(Exception):
    """Error during DAX generation."""
    
    def __init__(self, message: str, context: Optional[str] = None):
        self.message = message
        self.context = context
        super().__init__(f"{message}" + (f" in {context}" if context else ""))


class DAXGenerator:
    """
    Generates DAX queries from IR (Intermediate Representation).
    
    This is the main class responsible for converting semantic IR queries
    into executable DAX queries that can run against Power BI/SSAS models.
    """
    
    def __init__(self, format_output: bool = False, debug: bool = False):
        """
        Initialize the DAX generator.
        
        Args:
            format_output: Whether to format the output DAX for readability
            debug: Enable debug logging
        """
        self.format_output = format_output
        self.debug = debug
        self.logger = get_logger(__name__)
        
        # Initialize helpers
        self.expression_converter = ExpressionConverter()
        self.formatter = DAXFormatter()
        
        # Track generation state
        self.current_context: Optional[str] = None
        self.warnings: List[str] = []
        
        # Cache for table references
        self._table_cache: Dict[str, str] = {}
    
    def generate(self, query: Query) -> str:
        """
        Generate a DAX query from an IR Query object.
        
        Args:
            query: The IR Query to convert
            
        Returns:
            DAX query string
            
        Raises:
            DAXGenerationError: If generation fails
        """
        try:
            # Reset state
            self.warnings.clear()
            self._table_cache.clear()
            
            start_time = datetime.now()
            
            # Validate query
            validation_issues = query.validate_query()
            if validation_issues:
                for issue in validation_issues:
                    self.warnings.append(f"Validation warning: {issue}")
            
            # Build DAX query parts
            parts = []
            
            # Add DEFINE section if there are calculations
            if query.calculations:
                self.current_context = "DEFINE"
                define_section = self._generate_define_section(query.calculations)
                if define_section:
                    parts.append(define_section)
            
            # Add EVALUATE section (main query)
            self.current_context = "EVALUATE"
            evaluate_section = self._generate_evaluate_section(query)
            parts.append(evaluate_section)
            
            # Add ORDER BY if present
            if query.order_by:
                self.current_context = "ORDER BY"
                order_by_section = self._generate_order_by_section(query.order_by)
                if order_by_section:
                    parts.append(order_by_section)
            
            # Combine parts
            dax_query = '\n'.join(parts)
            
            # Format if requested
            if self.format_output:
                dax_query = self.formatter.format(dax_query)
            
            # Log generation time
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.info(f"Generated DAX in {duration:.2f}ms")
            
            return dax_query
            
        except Exception as e:
            if isinstance(e, DAXGenerationError):
                raise
            else:
                raise DAXGenerationError(f"Unexpected error during DAX generation: {str(e)}")
    
    def _generate_define_section(self, calculations: List[Calculation]) -> Optional[str]:
        """Generate DEFINE section with calculated measures."""
        if not calculations:
            return None
        
        lines = ["DEFINE"]
        
        for calc in calculations:
            try:
                # Generate measure definition
                measure_def = self._generate_measure_definition(calc)
                lines.append(f"    {measure_def}")
            except Exception as e:
                self.warnings.append(f"Failed to generate calculation '{calc.name}': {str(e)}")
                self.logger.warning(f"Skipping calculation '{calc.name}': {str(e)}")
        
        return '\n'.join(lines) if len(lines) > 1 else None
    
    def _generate_measure_definition(self, calculation: Calculation) -> str:
        """Generate a MEASURE definition from a Calculation."""
        # Convert expression to DAX
        expr_dax = self.expression_converter.convert(calculation.expression)
        
        # For now, assume all measures belong to a default table
        # In practice, this might need to be configurable
        table_name = "Sales"  # Default table - should be configurable
        
        # Build measure definition
        measure_def = f"MEASURE {table_name}[{calculation.name}] = {expr_dax}"
        
        # Add format string if present
        if calculation.format_string:
            measure_def += f' FORMAT_STRING = "{calculation.format_string}"'
        
        return measure_def
    
    def _generate_evaluate_section(self, query: Query) -> str:
        """Generate EVALUATE section (main query)."""
        # Determine the appropriate table expression
        if query.dimensions:
            # Use SUMMARIZECOLUMNS for dimensional queries
            table_expr = self._generate_summarizecolumns(query)
        else:
            # Simple measure-only query
            table_expr = self._generate_measure_table(query)
            # Handle LIMIT/TOP if present
            if query.limit and query.limit.offset == 0:
                # Simple TOP N
                table_expr = f"TOPN({query.limit.count}, {table_expr})"
            elif query.limit:
                # OFFSET not directly supported - add warning
                self.warnings.append("OFFSET is not directly supported in DAX - consider using ranking functions")
        
        # Check if we need to wrap with FILTER for NON EMPTY
        table_expr = self._apply_non_empty_filter(table_expr, query)
        
        return f"EVALUATE\n{table_expr}"
    
    def _generate_summarizecolumns(self, query: Query) -> str:
        """Generate SUMMARIZECOLUMNS function for dimensional queries."""
        args = []
        
        # 1. Group by columns (dimensions)
        for dimension in query.dimensions:
            column_ref = self._generate_dimension_column(dimension)
            args.append(f"    {column_ref}")
        
        # 2. Filter expressions
        filter_args = self._generate_filter_arguments(query.filters, query.dimensions)
        args.extend(filter_args)
        
        # 3. Measure expressions
        for measure in query.measures:
            measure_arg = self._generate_measure_argument(measure)
            args.append(f"    {measure_arg}")
        
        # Build SUMMARIZECOLUMNS
        if args:
            args_str = ',\n'.join(args)
            return f"SUMMARIZECOLUMNS(\n{args_str}\n)"
        else:
            # Empty query
            return 'ROW("Empty", BLANK())'
    
    def _generate_measure_table(self, query: Query) -> str:
        """Generate table expression for measure-only queries."""
        if not query.measures:
            return 'ROW("Value", BLANK())'
        
        # For measure-only queries, use brace syntax for table literal
        # This is preferred for simple measure queries
        if not query.filters:
            measure_refs = []
            for measure in query.measures:
                measure_refs.append(f"[{measure.name}]")
            
            if len(measure_refs) == 1:
                return f"{{ {measure_refs[0]} }}"
            else:
                # Multi-line format for multiple measures
                measure_list = ',\n    '.join(measure_refs)
                return f"{{\n    {measure_list}\n}}"
        
        # Use ROW function for filtered queries
        measure_pairs = []
        for measure in query.measures:
            name = measure.alias or measure.name
            # Escape the name
            escaped_name = self.formatter.escape_string(name)
            measure_pairs.append(f"{escaped_name}, [{measure.name}]")
        
        return f"ROW({', '.join(measure_pairs)})"
    
    def _generate_dimension_column(self, dimension: Dimension) -> str:
        """Generate column reference for a dimension."""
        table = dimension.hierarchy.table
        column = dimension.level.name if dimension.level else dimension.hierarchy.name
        
        # Format table name properly (with single quotes if needed)
        formatted_table = self._format_table_name(table)
        # Format column name with brackets - always use brackets for column names
        formatted_column = f"[{column}]"
        
        return f"{formatted_table}{formatted_column}"
    
    def _format_table_name(self, table_name: str) -> str:
        """Format table name with proper quoting for DAX."""
        # Quote table names that could conflict with DAX keywords or have special meaning
        # Based on the test expectations, certain table names like 'Date' need quotes
        dax_keywords = {
            'DATE', 'TIME', 'YEAR', 'MONTH', 'DAY', 'HOUR', 'MINUTE', 'SECOND',
            'TRUE', 'FALSE', 'ALL', 'FILTER', 'VALUES', 'DISTINCT'
        }
        
        # Check if table name needs quoting
        needs_quotes = (
            table_name.upper() in dax_keywords or
            ' ' in table_name or
            '-' in table_name or
            not table_name.replace('_', '').isalnum() or
            table_name[0].isdigit()
        )
        
        if needs_quotes:
            escaped = table_name.replace("'", "''")  # Escape single quotes by doubling
            return f"'{escaped}'"
        else:
            return table_name
    
    def _generate_filter_arguments(self, filters: List[Filter], dimensions: List[Dimension]) -> List[str]:
        """Generate filter arguments for SUMMARIZECOLUMNS."""
        filter_args = []
        
        # Group filters by type
        dimension_filters = []
        measure_filters = []
        non_empty_filters = []
        
        for filter_obj in filters:
            if filter_obj.filter_type == FilterType.DIMENSION:
                dimension_filters.append(filter_obj.target)
            elif filter_obj.filter_type == FilterType.MEASURE:
                measure_filters.append(filter_obj.target)
            elif filter_obj.filter_type == FilterType.NON_EMPTY:
                non_empty_filters.append(filter_obj.target)
        
        # Process dimension filters
        for dim_filter in dimension_filters:
            filter_arg = self._generate_dimension_filter(dim_filter)
            if filter_arg:
                filter_args.append(f"    {filter_arg}")
        
        # Process measure filters (these go in CALCULATETABLE if needed)
        if measure_filters:
            # For now, add warning - these need special handling
            self.warnings.append("Measure filters may need CALCULATETABLE wrapper")
            for measure_filter in measure_filters:
                filter_expr = measure_filter.to_dax()
                filter_args.append(f"    FILTER(ALL({measure_filter.measure.name}), {filter_expr})")
        
        # Handle non-empty filters
        if non_empty_filters:
            # This is typically handled by the query structure itself
            self.warnings.append("NON EMPTY behavior is implicit in SUMMARIZECOLUMNS")
        
        # Check for member-specific filters on dimensions
        for dimension in dimensions:
            if dimension.members.is_specific_members():
                # Add filter for specific members
                member_filter = self._generate_member_filter(dimension)
                if member_filter:
                    filter_args.append(f"    {member_filter}")
        
        return filter_args
    
    def _generate_dimension_filter(self, dim_filter: DimensionFilter) -> Optional[str]:
        """Generate filter expression for dimension filter."""
        table = dim_filter.dimension.hierarchy.table
        column = dim_filter.dimension.level.name
        
        # Format identifiers
        table_formatted = self.formatter.format_identifier(table)
        column_formatted = self.formatter.format_identifier(column)
        table_column = f"{table_formatted}{column_formatted}"
        
        # Build filter expression
        filter_expr = dim_filter.to_dax()
        
        # Wrap in FILTER(ALL(table), condition)
        return f"FILTER(ALL({table_formatted}), {filter_expr})"
    
    def _generate_member_filter(self, dimension: Dimension) -> Optional[str]:
        """Generate filter for specific dimension members."""
        if not dimension.members.is_specific_members():
            return None
        
        members = dimension.members.get_member_list()
        if not members:
            return None
        
        table = dimension.hierarchy.table
        column = dimension.level.name
        
        # Format identifiers
        table_formatted = self.formatter.format_identifier(table)
        column_formatted = self.formatter.format_identifier(column)
        table_column = f"{table_formatted}{column_formatted}"
        
        # Build IN expression
        if len(members) == 1:
            value = self.formatter.escape_string(members[0])
            filter_expr = f"{table_column} = {value}"
        else:
            values = [self.formatter.escape_string(m) for m in members]
            values_list = ', '.join(values)
            filter_expr = f"{table_column} IN {{{values_list}}}"
        
        # Wrap in FILTER
        return f"FILTER(ALL({table_formatted}), {filter_expr})"
    
    def _generate_measure_argument(self, measure: Measure) -> str:
        """Generate measure argument for SUMMARIZECOLUMNS."""
        name = measure.alias or measure.name
        
        # Handle custom expressions
        if measure.expression:
            # Convert expression to DAX
            expr_dax = self.expression_converter.convert(measure.expression)
            return f"{self.formatter.escape_string(name)}, {expr_dax}"
        
        # For standard measures, just reference them directly
        # The aggregation is handled by the measure definition itself
        return f"{self.formatter.escape_string(name)}, [{measure.name}]"
    
    def _get_aggregation_function(self, agg_type: AggregationType) -> Optional[str]:
        """Get DAX aggregation function for aggregation type."""
        agg_map = {
            AggregationType.SUM: "SUM",
            AggregationType.AVG: "AVERAGE",
            AggregationType.COUNT: "COUNT",
            AggregationType.DISTINCT_COUNT: "DISTINCTCOUNT",
            AggregationType.MIN: "MIN",
            AggregationType.MAX: "MAX",
        }
        return agg_map.get(agg_type)
    
    def _generate_order_by_section(self, order_by_list: List[OrderBy]) -> Optional[str]:
        """Generate ORDER BY section."""
        if not order_by_list:
            return None
        
        order_parts = []
        for order_item in order_by_list:
            order_expr = order_item.to_dax()
            order_parts.append(order_expr)
        
        return f"ORDER BY {', '.join(order_parts)}"
    
    def get_warnings(self) -> List[str]:
        """Get list of warnings generated during conversion."""
        return self.warnings.copy()
    
    def _apply_non_empty_filter(self, table_expr: str, query: Query) -> str:
        """Apply NON EMPTY filter wrapping if needed."""
        # Check if query has NON EMPTY filters
        non_empty_filters = [f for f in query.filters if f.filter_type == FilterType.NON_EMPTY]
        
        if non_empty_filters:
            # Get the measure to use for the NON EMPTY filter
            non_empty_filter = non_empty_filters[0].target
            measure_name = non_empty_filter.measure
            
            # If no specific measure specified, use the first measure from the query
            if not measure_name and query.measures:
                measure_name = query.measures[0].name
            
            if measure_name:
                # Indent the table expression by 4 more spaces when wrapping in FILTER
                indented_table_expr = '\n'.join('    ' + line if line.strip() else line 
                                              for line in table_expr.split('\n'))
                # Wrap the table expression with FILTER
                return f"FILTER(\n{indented_table_expr},\n    [{measure_name}] <> BLANK()\n)"
        
        return table_expr
    
    def validate_for_dax(self, query: Query) -> List[str]:
        """
        Validate a query for DAX compatibility.
        
        Args:
            query: The query to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for unsupported features
        if query.limit and query.limit.offset > 0:
            issues.append("OFFSET is not directly supported in DAX")
        
        # Check measure references in filters
        for filter_obj in query.filters:
            if filter_obj.filter_type == FilterType.MEASURE:
                issues.append("Measure filters may require special handling in DAX")
        
        # Check for circular dependencies in calculations
        calc_deps = {}
        for calc in query.calculations:
            calc_deps[calc.name] = calc.get_dependencies()
        
        # Simple circular dependency check
        for calc_name, deps in calc_deps.items():
            if calc_name in deps:
                issues.append(f"Circular dependency detected in calculation '{calc_name}'")
        
        # Validate expressions
        for calc in query.calculations:
            expr_issues = self.expression_converter.validate_expression(calc.expression)
            issues.extend(expr_issues)
        
        return issues