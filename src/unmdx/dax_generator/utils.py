"""
Utility functions for DAX generation.
"""

from typing import List, Dict, Set, Tuple
import re

from ..ir.models import Query, Measure, Dimension, Filter
from ..ir.expressions import Expression, BinaryOperation, FunctionCall
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DAXOptimizer:
    """
    Optimizes DAX queries for performance and readability.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def optimize_query(self, query: Query) -> Query:
        """
        Optimize IR query before DAX generation.
        
        Args:
            query: Original IR query
            
        Returns:
            Optimized IR query
        """
        self.logger.debug("Optimizing query for DAX generation")
        
        # Create a copy to avoid modifying original
        optimized = Query(
            measures=self._optimize_measures(query.measures),
            dimensions=self._optimize_dimensions(query.dimensions),
            filters=self._optimize_filters(query.filters),
            calculated_members=query.calculated_members.copy(),
            cube_name=query.cube_name
        )
        
        return optimized
    
    def _optimize_measures(self, measures: List[Measure]) -> List[Measure]:
        """Optimize measure expressions for DAX."""
        optimized = []
        
        for measure in measures:
            if measure.expression:
                # Optimize the expression
                optimized_expr = self._optimize_expression(measure.expression)
                optimized_measure = Measure(
                    name=measure.name,
                    alias=measure.alias,
                    expression=optimized_expr,
                    format_string=measure.format_string,
                    is_calculated=measure.is_calculated
                )
                optimized.append(optimized_measure)
            else:
                optimized.append(measure)
        
        return optimized
    
    def _optimize_dimensions(self, dimensions: List[Dimension]) -> List[Dimension]:
        """Remove duplicate dimensions and optimize references."""
        # Remove duplicates while preserving order
        seen = set()
        optimized = []
        
        for dim in dimensions:
            dim_key = (dim.dimension, dim.hierarchy)
            if dim_key not in seen:
                seen.add(dim_key)
                optimized.append(dim)
        
        return optimized
    
    def _optimize_filters(self, filters: List[Filter]) -> List[Filter]:
        """Combine and optimize filter expressions."""
        # Group filters by dimension
        filter_groups = {}
        
        for filter_obj in filters:
            key = (filter_obj.dimension, filter_obj.level)
            if key not in filter_groups:
                filter_groups[key] = []
            filter_groups[key].append(filter_obj)
        
        # Optimize each group
        optimized = []
        for group in filter_groups.values():
            if len(group) == 1:
                optimized.append(group[0])
            else:
                # Combine multiple filters on same dimension/level
                combined = self._combine_filters(group)
                optimized.append(combined)
        
        return optimized
    
    def _combine_filters(self, filters: List[Filter]) -> Filter:
        """Combine multiple filters on the same dimension."""
        if not filters:
            return None
        
        if len(filters) == 1:
            return filters[0]
        
        # For now, just return the first filter
        # TODO: Implement proper filter combination logic
        return filters[0]
    
    def _optimize_expression(self, expr: Expression) -> Expression:
        """Optimize individual expressions."""
        if isinstance(expr, BinaryOperation):
            return self._optimize_binary_operation(expr)
        elif isinstance(expr, FunctionCall):
            return self._optimize_function_call(expr)
        else:
            return expr
    
    def _optimize_binary_operation(self, expr: BinaryOperation) -> Expression:
        """Optimize binary operations."""
        # Optimize operands first
        left = self._optimize_expression(expr.left)
        right = self._optimize_expression(expr.right)
        
        # Create optimized binary operation
        return BinaryOperation(
            left=left,
            operator=expr.operator,
            right=right
        )
    
    def _optimize_function_call(self, expr: FunctionCall) -> Expression:
        """Optimize function calls."""
        # Optimize arguments
        optimized_args = [self._optimize_expression(arg) for arg in expr.arguments]
        
        return FunctionCall(
            function_type=expr.function_type,
            arguments=optimized_args
        )


class DAXFormatter:
    """
    Formats DAX code for readability.
    """
    
    def __init__(self, max_line_length: int = 120, indent_size: int = 4):
        self.max_line_length = max_line_length
        self.indent_size = indent_size
        self.logger = get_logger(__name__)
    
    def format(self, dax_code: str) -> str:
        """
        Format DAX code for better readability.
        
        Args:
            dax_code: Raw DAX code
            
        Returns:
            Formatted DAX code
        """
        self.logger.debug("Formatting DAX code")
        
        lines = dax_code.split('\n')
        formatted_lines = []
        current_indent = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append("")
                continue
            
            # Adjust indentation for closing brackets/parentheses
            if line.startswith(')') or line.startswith('}'):
                current_indent = max(0, current_indent - self.indent_size)
            
            # Apply indentation
            indented_line = ' ' * current_indent + line
            
            # Break long lines if needed
            if len(indented_line) > self.max_line_length:
                broken_lines = self._break_long_line(indented_line, current_indent)
                formatted_lines.extend(broken_lines)
            else:
                formatted_lines.append(indented_line)
            
            # Adjust indentation for opening brackets/parentheses
            if line.endswith('(') or line.endswith('{') or line.endswith(','):
                current_indent += self.indent_size
        
        return '\n'.join(formatted_lines)
    
    def _break_long_line(self, line: str, base_indent: int) -> List[str]:
        """Break a long line into multiple lines."""
        # Simple line breaking at commas
        if ',' in line:
            parts = line.split(',')
            broken_lines = []
            
            for i, part in enumerate(parts):
                part = part.strip()
                if i == 0:
                    # First part keeps original indentation
                    broken_lines.append(' ' * base_indent + part + ',')
                elif i == len(parts) - 1:
                    # Last part without comma
                    broken_lines.append(' ' * (base_indent + self.indent_size) + part)
                else:
                    # Middle parts with comma
                    broken_lines.append(' ' * (base_indent + self.indent_size) + part + ',')
            
            return broken_lines
        else:
            # Can't break, return as is
            return [line]


def validate_dax_syntax(dax_code: str) -> Dict[str, any]:
    """
    Validate DAX syntax for common issues.
    
    Args:
        dax_code: DAX code to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check for balanced parentheses
    paren_count = dax_code.count('(') - dax_code.count(')')
    if paren_count != 0:
        result["valid"] = False
        result["errors"].append(f"Unbalanced parentheses: {abs(paren_count)} {'extra opening' if paren_count > 0 else 'extra closing'}")
    
    # Check for balanced brackets
    bracket_count = dax_code.count('[') - dax_code.count(']')
    if bracket_count != 0:
        result["valid"] = False
        result["errors"].append(f"Unbalanced brackets: {abs(bracket_count)} {'extra opening' if bracket_count > 0 else 'extra closing'}")
    
    # Check for common DAX keywords
    required_keywords = ["EVALUATE"]
    for keyword in required_keywords:
        if keyword not in dax_code.upper():
            result["warnings"].append(f"Missing required keyword: {keyword}")
    
    return result