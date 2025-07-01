"""
Core DAX generator module.

Converts IR (Intermediate Representation) queries into optimized DAX queries.
"""

from typing import List, Dict, Any
from dataclasses import dataclass

from ..ir.models import Query, Measure, Dimension, Filter, DimensionFilter
from ..ir.expressions import Expression
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DAXGenerationOptions:
    """Configuration options for DAX generation."""
    
    use_summarizecolumns: bool = True
    optimize_filters: bool = True
    include_comments: bool = True
    format_output: bool = True
    max_line_length: int = 120


class DAXGenerator:
    """
    Generates optimized DAX queries from IR representation.
    
    Follows modern DAX patterns:
    - Uses SUMMARIZECOLUMNS for multi-dimensional queries
    - Uses EVALUATE statements for table output
    - Optimizes filter expressions
    - Generates clean, readable DAX code
    """
    
    def __init__(self, options: DAXGenerationOptions | None = None):
        """
        Initialize DAX generator.
        
        Args:
            options: Configuration options for DAX generation
        """
        self.options = options or DAXGenerationOptions()
        self.logger = get_logger(__name__)
    
    def generate(self, query: Query) -> str:
        """
        Generate DAX query from IR representation.
        
        Args:
            query: IR Query object
            
        Returns:
            Generated DAX query string
        """
        self.logger.info(f"Generating DAX for query with {len(query.measures)} measures and {len(query.dimensions)} dimensions")
        
        # Start with any DEFINE statements for calculated measures
        define_section = self._generate_define_section(query)
        
        # Generate the main EVALUATE statement
        evaluate_section = self._generate_evaluate_section(query)
        
        # Combine sections
        dax_parts = []
        if define_section.strip():
            dax_parts.append(define_section)
        dax_parts.append(evaluate_section)
        
        dax_query = "\n\n".join(dax_parts)
        
        if self.options.format_output:
            dax_query = self._format_dax(dax_query)
        
        self.logger.debug(f"Generated DAX query: {len(dax_query)} characters")
        return dax_query
    
    def _generate_define_section(self, query: Query) -> str:
        """
        Generate DEFINE section for calculated measures.
        
        Args:
            query: IR Query object
            
        Returns:
            DEFINE section string (empty if no calculated measures)
        """
        if not query.calculations:
            return ""
        
        define_lines = ["DEFINE"]
        
        for calculation in query.calculations:
            calc_def = calculation.to_dax_definition()
            define_lines.append(f"    {calc_def}")
        
        return "\n".join(define_lines)
    
    def _generate_evaluate_section(self, query: Query) -> str:
        """
        Generate EVALUATE section with table expression.
        
        Args:
            query: IR Query object
            
        Returns:
            EVALUATE section string
        """
        if query.dimensions and self.options.use_summarizecolumns:
            table_expr = self._generate_summarizecolumns(query)
        else:
            table_expr = self._generate_simple_table(query)
        
        # Add ORDER BY if needed
        order_clause = self._generate_order_clause(query)
        
        evaluate_parts = ["EVALUATE"]
        evaluate_parts.append(f"    {table_expr}")
        
        if order_clause:
            evaluate_parts.append(f"ORDER BY {order_clause}")
        
        return "\n".join(evaluate_parts)
    
    def _generate_summarizecolumns(self, query: Query) -> str:
        """
        Generate SUMMARIZECOLUMNS expression for multi-dimensional queries.
        
        Args:
            query: IR Query object
            
        Returns:
            SUMMARIZECOLUMNS DAX expression
        """
        # Collect groupby columns from dimensions
        groupby_columns = []
        for dim in query.dimensions:
            column_ref = self._generate_dimension_column(dim)
            groupby_columns.append(column_ref)
        
        # Collect filters
        filter_expressions = []
        for filter_obj in query.filters:
            filter_expr = self._generate_filter_expression(filter_obj)
            if filter_expr:
                filter_expressions.append(filter_expr)
        
        # Collect measures
        measure_expressions = []
        for measure in query.measures:
            measure_expr = self._generate_measure_expression(measure)
            measure_expressions.append(measure_expr)
        
        # Build SUMMARIZECOLUMNS call
        parts = []
        
        # Add groupby columns
        if groupby_columns:
            parts.extend(groupby_columns)
        
        # Add filters if any
        if filter_expressions:
            parts.append(f"FILTER(ALL(), {' && '.join(filter_expressions)})")
        
        # Add measures
        parts.extend(measure_expressions)
        
        separator = ',\n        '
        return f"SUMMARIZECOLUMNS(\n        {separator.join(parts)}\n    )"
    
    def _generate_simple_table(self, query: Query) -> str:
        """
        Generate simple table expression for measure-only queries.
        
        Args:
            query: IR Query object
            
        Returns:
            Table expression string
        """
        if len(query.measures) == 1:
            # Single measure - return as single-cell table
            measure = query.measures[0]
            measure_expr = self._generate_measure_expression(measure)
            return f"{{ {measure_expr} }}"
        else:
            # Multiple measures - use ROW function
            measure_pairs = []
            for measure in query.measures:
                measure_expr = self._generate_measure_expression(measure)
                measure_pairs.append(f'"{measure.alias or measure.name}", {measure_expr}')
            
            separator = ',\n        '
            return f"ROW(\n        {separator.join(measure_pairs)}\n    )"
    
    def _generate_dimension_column(self, dimension: Dimension) -> str:
        """
        Generate column reference for dimension.
        
        Args:
            dimension: IR Dimension object
            
        Returns:
            DAX column reference
        """
        table_name = dimension.hierarchy.table
        column_name = dimension.level.name
        return f"'{table_name}'[{column_name}]"
    
    def _generate_filter_expression(self, filter_obj: Filter) -> str:
        """
        Generate DAX filter expression.
        
        Args:
            filter_obj: IR Filter object
            
        Returns:
            DAX filter expression
        """
        if hasattr(filter_obj, 'expression') and filter_obj.expression:
            return filter_obj.expression.to_dax()
        
        # Fallback for simple filters
        column_ref = f"'{filter_obj.dimension}'[{filter_obj.level or filter_obj.dimension}]"
        
        if filter_obj.operator == "equals":
            return f"{column_ref} = \"{filter_obj.value}\""
        elif filter_obj.operator == "in":
            values = [f'"{v}"' for v in filter_obj.value]
            return f"{column_ref} IN {{ {', '.join(values)} }}"
        else:
            return f"{column_ref} {filter_obj.operator} \"{filter_obj.value}\""
    
    def _generate_measure_expression(self, measure: Measure) -> str:
        """
        Generate DAX measure expression.
        
        Args:
            measure: IR Measure object
            
        Returns:
            DAX measure expression
        """
        if measure.expression:
            return measure.expression.to_dax()
        else:
            # Simple measure reference
            return f"[{measure.name}]"
    
    
    def _generate_order_clause(self, query: Query) -> str:
        """
        Generate ORDER BY clause if needed.
        
        Args:
            query: IR Query object
            
        Returns:
            ORDER BY clause or empty string
        """
        # For now, return empty - can be enhanced later with sort information
        return ""
    
    def _format_dax(self, dax_query: str) -> str:
        """
        Format DAX query for readability.
        
        Args:
            dax_query: Raw DAX query string
            
        Returns:
            Formatted DAX query
        """
        # Basic formatting - can be enhanced with more sophisticated formatting
        lines = dax_query.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Remove excessive whitespace
            line = ' '.join(line.split())
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)