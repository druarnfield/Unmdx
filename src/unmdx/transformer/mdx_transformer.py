"""Main MDX to IR transformer implementation."""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from lark import Token, Tree
from lark.exceptions import LarkError

from ..ir import (
    Query, CubeReference, Measure, Dimension, Filter, Calculation,
    HierarchyReference, LevelReference, MemberSelection, DimensionFilter,
    AggregationType, MemberSelectionType, FilterType, FilterOperator,
    CalculationType, QueryMetadata, Expression, Constant, MeasureReference,
    BinaryOperation, FunctionCall, MemberReference, FunctionType, ComparisonOperator
)
from ..parser.mdx_parser import MDXParser, MDXParseError
from ..utils.logging import get_logger

from .hierarchy_normalizer import HierarchyNormalizer
from .set_flattener import SetFlattener
from .comment_extractor import CommentExtractor

logger = get_logger(__name__)


class TransformationError(Exception):
    """Error during MDX to IR transformation."""
    
    def __init__(self, message: str, node: Optional[Tree] = None, context: Optional[str] = None):
        self.message = message
        self.node = node
        self.context = context
        super().__init__(f"{message}" + (f" in {context}" if context else ""))


class TransformationWarning:
    """Warning during transformation."""
    
    def __init__(self, message: str, node: Optional[Tree] = None, context: Optional[str] = None):
        self.message = message
        self.node = node
        self.context = context
    
    def __str__(self) -> str:
        return f"Warning: {self.message}" + (f" in {self.context}" if self.context else "")


class MDXTransformer:
    """
    Transforms MDX parse trees into IR (Intermediate Representation).
    
    This class is the main entry point for converting parsed MDX queries
    into a clean, semantic IR that can be used for DAX generation and
    human-readable explanations.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the transformer.
        
        Args:
            debug: Enable debug logging and additional validation
        """
        self.debug = debug
        self.logger = get_logger(__name__)
        
        # Initialize helper components
        self.hierarchy_normalizer = HierarchyNormalizer()
        self.set_flattener = SetFlattener()
        self.comment_extractor = CommentExtractor()
        
        # Transformation state
        self.errors: List[TransformationError] = []
        self.warnings: List[TransformationWarning] = []
        self.current_context: Optional[str] = None
        
        # Cache for member lookups and hierarchy mappings
        self._hierarchy_cache: Dict[str, HierarchyReference] = {}
        self._member_cache: Dict[str, str] = {}  # member_name -> hierarchy_table
    
    def transform(self, tree: Tree, source_mdx: Optional[str] = None) -> Query:
        """
        Transform an MDX parse tree into IR.
        
        Args:
            tree: The parsed MDX tree from Lark
            source_mdx: Original MDX query text for metadata
            
        Returns:
            Query IR object
            
        Raises:
            TransformationError: If transformation fails
        """
        try:
            # Reset state
            self.errors.clear()
            self.warnings.clear()
            self._hierarchy_cache.clear()
            self._member_cache.clear()
            
            start_time = datetime.now()
            
            # Extract comments and hints first
            comment_hints = self.comment_extractor.extract_hints(tree, source_mdx)
            
            # Transform main query components
            self.current_context = "query_root"
            query = self._transform_query(tree)
            
            # Add metadata
            end_time = datetime.now()
            transform_duration = (end_time - start_time).total_seconds() * 1000
            
            query.metadata.created_at = start_time
            query.metadata.transform_duration_ms = transform_duration
            
            if source_mdx:
                query.metadata.source_mdx_hash = hashlib.md5(source_mdx.encode()).hexdigest()
            
            # Add warnings to metadata
            for warning in self.warnings:
                query.metadata.add_warning(str(warning))
            
            # Add errors if any (shouldn't happen if we got here)
            for error in self.errors:
                query.metadata.add_error(str(error))
            
            # Add comment hints to metadata
            for hint in comment_hints:
                query.metadata.optimization_hints.append(str(hint))
            
            # Validate the result
            issues = query.validate_query()
            if issues:
                for issue in issues:
                    query.metadata.add_warning(f"Validation issue: {issue}")
            
            self.logger.info(f"Transformed MDX to IR in {transform_duration:.2f}ms")
            
            return query
            
        except Exception as e:
            if isinstance(e, TransformationError):
                raise
            else:
                raise TransformationError(f"Unexpected error during transformation: {str(e)}")
    
    def _transform_query(self, tree: Tree) -> Query:
        """Transform the root query node."""
        self.current_context = "query"
        
        # Find main query components
        cube = self._extract_cube_reference(tree)
        measures = self._extract_measures(tree)
        dimensions = self._extract_dimensions(tree)
        filters = self._extract_filters(tree)
        calculations = self._extract_calculations(tree)
        order_by = self._extract_order_by(tree)
        limit = self._extract_limit(tree)
        
        # Create query metadata
        metadata = QueryMetadata()
        
        return Query(
            cube=cube,
            measures=measures,
            dimensions=dimensions,
            filters=filters,
            calculations=calculations,
            order_by=order_by,
            limit=limit,
            metadata=metadata
        )
    
    def _extract_cube_reference(self, tree: Tree) -> CubeReference:
        """Extract cube reference from cube specification."""
        self.current_context = "cube_reference"
        
        # Look for cube_specification (actual parser output)
        cube_nodes = self._find_nodes(tree, "cube_specification")
        if not cube_nodes:
            # Fallback: try old from_clause format for compatibility
            from_nodes = self._find_nodes(tree, "from_clause")
            if not from_nodes:
                raise TransformationError("No cube specification found in query")
            cube_node = from_nodes[0]
        else:
            cube_node = cube_nodes[0]
        
        # Extract cube name from bracketed_identifier
        bracketed_ids = self._find_nodes(cube_node, "bracketed_identifier")
        if bracketed_ids:
            cube_name = self._extract_identifier_value(bracketed_ids[0])
        else:
            # Try to find any identifier in cube specification
            identifiers = self._find_nodes(cube_node, "identifier")
            if not identifiers:
                raise TransformationError("No cube identifier found in cube specification")
            cube_name = self._extract_identifier_value(identifiers[0])
        
        # Check for database/schema qualifiers
        database = None
        schema_name = None
        
        # Handle qualified names like [Database].[Schema].[Cube]
        if "." in cube_name or "[" in cube_name:
            parts = self._parse_qualified_name(cube_name)
            if len(parts) == 3:
                database, schema_name, cube_name = parts
            elif len(parts) == 2:
                schema_name, cube_name = parts
        
        return CubeReference(name=cube_name, database=database, schema=schema_name)
    
    def _extract_measures(self, tree: Tree) -> List[Measure]:
        """Extract measures from SELECT clause."""
        self.current_context = "measures"
        measures = []
        
        # Look for SELECT statement
        select_nodes = self._find_nodes(tree, "select_statement")
        if not select_nodes:
            return measures
        
        select_node = select_nodes[0]
        
        # Find measure expressions on columns axis (axis 0)
        axis_nodes = self._find_nodes(select_node, "axis_specification")
        for axis_node in axis_nodes:
            axis_id = self._get_axis_id(axis_node)
            if axis_id == 0:  # Columns axis
                measure_exprs = self._extract_measures_from_axis(axis_node)
                measures.extend(measure_exprs)
        
        return measures
    
    def _extract_dimensions(self, tree: Tree) -> List[Dimension]:
        """Extract dimensions from SELECT clause."""
        self.current_context = "dimensions"
        dimensions = []
        
        # Look for SELECT statement
        select_nodes = self._find_nodes(tree, "select_statement")
        if not select_nodes:
            return dimensions
        
        select_node = select_nodes[0]
        
        # Find dimension expressions on rows axis (axis 1) and higher
        axis_nodes = self._find_nodes(select_node, "axis_specification")
        for axis_node in axis_nodes:
            axis_id = self._get_axis_id(axis_node)
            if axis_id >= 1:  # Rows axis and higher
                dim_exprs = self._extract_dimensions_from_axis(axis_node)
                dimensions.extend(dim_exprs)
        
        return dimensions
    
    def _extract_filters(self, tree: Tree) -> List[Filter]:
        """Extract filters from WHERE clause."""
        self.current_context = "filters"
        filters = []
        
        # Look for WHERE clause
        where_nodes = self._find_nodes(tree, "where_clause")
        if not where_nodes:
            return filters
        
        where_node = where_nodes[0]
        
        # Extract filter expressions
        filter_exprs = self._extract_filter_expressions(where_node)
        filters.extend(filter_exprs)
        
        return filters
    
    def _extract_calculations(self, tree: Tree) -> List[Calculation]:
        """Extract calculated members from WITH clause."""
        self.current_context = "calculations"
        calculations = []
        
        # Look for WITH clause
        with_nodes = self._find_nodes(tree, "with_clause")
        if not with_nodes:
            return calculations
        
        with_node = with_nodes[0]
        
        # Extract member definitions (calculated members)
        member_def_nodes = self._find_nodes(with_node, "member_definition")
        for calc_node in member_def_nodes:
            calculation = self._transform_calculated_member(calc_node)
            if calculation:
                calculations.append(calculation)
        
        return calculations
    
    def _extract_order_by(self, tree: Tree) -> List:
        """Extract ORDER BY clause (not commonly used in MDX)."""
        # MDX doesn't typically have ORDER BY, but we might find ordering hints
        return []
    
    def _extract_limit(self, tree: Tree) -> Optional:
        """Extract limit/top clause."""
        # Look for TOP functions or similar limiting constructs
        return None
    
    def _transform_calculated_member(self, calc_node: Tree) -> Optional[Calculation]:
        """Transform a calculated member definition."""
        try:
            # Extract member name from qualified_member
            member_name = self._extract_calculated_member_name(calc_node)
            
            # Extract expression - first try calculation_expression (directly in member_definition)
            expr_nodes = self._find_nodes(calc_node, "calculation_expression")
            if not expr_nodes:
                # Fallback to value_expression
                expr_nodes = self._find_nodes(calc_node, "value_expression")
                if not expr_nodes:
                    expr_nodes = self._find_nodes(calc_node, "numeric_expression")
                    if not expr_nodes:
                        self._add_warning(f"No expression found for calculated member {member_name}")
                        return None
            
            # Transform the expression properly
            expression = self._transform_calculation_expression(expr_nodes[0])
            
            # Determine if this is a measure or member calculation
            calc_type = CalculationType.MEASURE  # Default to measure
            if self._is_member_calculation(calc_node):
                calc_type = CalculationType.MEMBER
            
            # Extract format string if present
            format_string = None
            format_nodes = self._find_nodes(calc_node, "format_clause")
            if format_nodes:
                format_string = self._extract_format_string(format_nodes[0])
            
            return Calculation(
                name=member_name,
                calculation_type=calc_type,
                expression=expression,
                format_string=format_string
            )
            
        except Exception as e:
            self._add_error(f"Failed to transform calculated member: {str(e)}", calc_node)
            return None
    
    def _transform_expression(self, expr_node: Tree) -> Expression:
        """Transform an expression node into IR expression."""
        if expr_node.data == "binary_operation":
            return self._transform_binary_operation(expr_node)
        elif expr_node.data == "function_call":
            return self._transform_function_call(expr_node)
        elif expr_node.data == "member_reference":
            return self._transform_member_reference(expr_node)
        elif expr_node.data == "measure_reference":
            return self._transform_measure_reference(expr_node)
        elif expr_node.data == "numeric_literal":
            return self._transform_numeric_literal(expr_node)
        elif expr_node.data == "string_literal":
            return self._transform_string_literal(expr_node)
        else:
            # Default handling for unknown expression types
            return Constant(value=str(expr_node))
    
    def _transform_binary_operation(self, op_node: Tree) -> BinaryOperation:
        """Transform binary operation."""
        children = list(op_node.children)
        if len(children) < 3:
            raise TransformationError("Invalid binary operation", op_node)
        
        left = self._transform_expression(children[0])
        operator = str(children[1])
        right = self._transform_expression(children[2])
        
        return BinaryOperation(left=left, operator=operator, right=right)
    
    def _transform_function_call(self, func_node: Tree) -> FunctionCall:
        """Transform function call."""
        # Extract function name
        func_name = self._extract_function_name(func_node)
        
        # Extract arguments
        arg_nodes = self._find_nodes(func_node, "argument")
        arguments = []
        for arg_node in arg_nodes:
            arg_expr = self._transform_expression(arg_node)
            arguments.append(arg_expr)
        
        # Determine function type
        func_type = self._determine_function_type(func_name)
        
        return FunctionCall(
            function_type=func_type,
            function_name=func_name,
            arguments=arguments
        )
    
    def _transform_member_reference(self, member_node: Tree) -> MemberReference:
        """Transform member reference."""
        member_name = self._extract_member_name(member_node)
        hierarchy_name = self._extract_hierarchy_name(member_node) or "DefaultHierarchy"
        
        return MemberReference(
            dimension=hierarchy_name,
            hierarchy=hierarchy_name, 
            member=member_name
        )
    
    def _transform_measure_reference(self, measure_node: Tree) -> MeasureReference:
        """Transform measure reference."""
        measure_name = self._extract_measure_name(measure_node)
        return MeasureReference(measure_name=measure_name)
    
    def _transform_numeric_literal(self, num_node: Tree) -> Constant:
        """Transform numeric literal."""
        value_str = str(num_node.children[0])
        
        # Try to parse as int first, then float
        try:
            if "." in value_str:
                value = float(value_str)
            else:
                value = int(value_str)
        except ValueError:
            value = value_str  # Keep as string if parsing fails
        
        return Constant(value=value)
    
    def _transform_string_literal(self, str_node: Tree) -> Constant:
        """Transform string literal."""
        value = str(str_node.children[0])
        # Remove quotes if present
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        
        return Constant(value=value)
    
    # Helper methods
    
    def _find_nodes(self, tree: Tree, node_type: str) -> List[Tree]:
        """Find all nodes of a specific type in the tree."""
        nodes = []
        
        if isinstance(tree, Tree):
            if tree.data == node_type:
                nodes.append(tree)
            
            for child in tree.children:
                if isinstance(child, Tree):
                    nodes.extend(self._find_nodes(child, node_type))
        
        return nodes
    
    def _extract_identifier_value(self, node: Tree) -> str:
        """Extract identifier value from node."""
        if isinstance(node, Token):
            return str(node)
        elif isinstance(node, Tree):
            if node.children:
                return str(node.children[0])
        return str(node)
    
    def _parse_qualified_name(self, name: str) -> List[str]:
        """Parse qualified name like [Database].[Schema].[Object]."""
        # Remove brackets and split by dots
        parts = []
        current = ""
        in_brackets = False
        
        for char in name:
            if char == "[":
                in_brackets = True
                current = ""  # Reset current when entering brackets
            elif char == "]":
                in_brackets = False
                if current.strip():
                    parts.append(current.strip())
                    current = ""
            elif char == "." and not in_brackets:
                if current.strip():
                    parts.append(current.strip())
                    current = ""
            else:
                if char != "[" and char != "]":  # Don't include bracket chars
                    current += char
        
        if current.strip():
            parts.append(current.strip())
        
        return parts
    
    def _get_axis_id(self, axis_node: Tree) -> int:
        """Get axis ID (0=columns, 1=rows, etc.)."""
        # Look for axis identifier nodes
        axis_columns = self._find_nodes(axis_node, "axis_columns")
        if axis_columns:
            return 0
        
        axis_rows = self._find_nodes(axis_node, "axis_rows")
        if axis_rows:
            return 1
        
        # Look for numeric axis nodes (ON 0, ON 1, etc.)
        axis_number_short = self._find_nodes(axis_node, "axis_number_short")
        if axis_number_short:
            # Extract the number from within the axis_number_short node
            for axis_num_node in axis_number_short:
                for child in axis_num_node.children:
                    if isinstance(child, Token) and child.type == "NUMBER":
                        return int(str(child))
        
        axis_number = self._find_nodes(axis_node, "axis_number")
        if axis_number:
            # Extract the number from AXIS(n) syntax
            for axis_num_node in axis_number:
                for child in axis_num_node.children:
                    if isinstance(child, Token) and child.type == "NUMBER":
                        return int(str(child))
        
        # Fallback: look for direct tokens
        axis_tokens = [child for child in axis_node.children if isinstance(child, Token)]
        for token in axis_tokens:
            token_str = str(token).upper()
            if "COLUMNS" in token_str or token_str == "0":
                return 0
            elif "ROWS" in token_str or token_str == "1":
                return 1
            elif token_str.isdigit():
                return int(token_str)
        
        return 0  # Default to columns
    
    def _extract_measures_from_axis(self, axis_node: Tree) -> List[Measure]:
        """Extract measures from an axis specification."""
        measures = []
        
        # Look for member expressions that reference the Measures hierarchy
        member_exprs = self._find_nodes(axis_node, "member_expression")
        for member_expr in member_exprs:
            # Check if this is a measure (hierarchy is "Measures")
            if self._is_measure_expression(member_expr):
                measure_name = self._extract_measure_name(member_expr)
                if measure_name:
                    measure = Measure(
                        name=measure_name,
                        aggregation=AggregationType.SUM  # Default aggregation
                    )
                    measures.append(measure)
        
        return measures
    
    def _extract_dimensions_from_axis(self, axis_node: Tree) -> List[Dimension]:
        """Extract dimensions from an axis specification."""
        dimensions = []
        
        # Look for member expressions that reference non-Measures hierarchies
        member_exprs = self._find_nodes(axis_node, "member_expression")
        for member_expr in member_exprs:
            # Check if this is a dimension (not a measure)
            if not self._is_measure_expression(member_expr):
                dimension = self._transform_dimension_from_member_expr(member_expr)
                if dimension:
                    dimensions.append(dimension)
        
        return dimensions
    
    def _transform_dimension_node(self, dim_node: Tree) -> Optional[Dimension]:
        """Transform a dimension node."""
        try:
            # Extract hierarchy and level information
            hierarchy_name = self._extract_hierarchy_from_dimension(dim_node)
            level_name = self._extract_level_from_dimension(dim_node)
            
            # Create hierarchy and level references
            hierarchy = HierarchyReference(table=hierarchy_name, name=hierarchy_name)
            level = LevelReference(name=level_name)
            
            # For now, assume all members (would need more sophisticated analysis)
            members = MemberSelection(selection_type=MemberSelectionType.ALL)
            
            return Dimension(
                hierarchy=hierarchy,
                level=level,
                members=members
            )
            
        except Exception as e:
            self._add_warning(f"Failed to transform dimension: {str(e)}")
            return None
    
    def _extract_filter_expressions(self, where_node: Tree) -> List[Filter]:
        """Extract filter expressions from WHERE clause."""
        filters = []
        
        # Look for member expressions in the WHERE clause (slicer specifications)
        member_exprs = self._find_nodes(where_node, "member_expression")
        for member_expr in member_exprs:
            # Create a filter from the member expression
            filter_obj = self._create_filter_from_member_expr(member_expr)
            if filter_obj:
                filters.append(filter_obj)
        
        return filters
    
    def _extract_calculated_member_name(self, calc_node: Tree) -> str:
        """Extract name from calculated member definition."""
        # Look for qualified_member (the member name in member_definition)
        qualified_member_nodes = self._find_nodes(calc_node, "qualified_member")
        if qualified_member_nodes:
            # Extract the member name from the qualified member
            qualified_member = qualified_member_nodes[0]
            # Look for the last bracketed_identifier or identifier (the member name part)
            bracketed_ids = self._find_nodes(qualified_member, "bracketed_identifier")
            if bracketed_ids:
                # Get the last one (should be the member name)
                return self._extract_identifier_value(bracketed_ids[-1])
            
            identifiers = self._find_nodes(qualified_member, "identifier")
            if identifiers:
                return self._extract_identifier_value(identifiers[-1])
        
        # Fallback to any identifier in the calc_node
        identifiers = self._find_nodes(calc_node, "identifier")
        if identifiers:
            return self._extract_identifier_value(identifiers[0])
        
        return "Unknown Member"
    
    def _transform_calculation_expression(self, expr_node: Tree) -> Expression:
        """Transform a calculation expression from a WITH clause."""
        # Handle calculation_expression which typically has: value_expression arithmetic_op value_expression
        if expr_node.data == "calculation_expression":
            # Look for the pattern: left_expr operator right_expr  
            children = list(expr_node.children)
            if len(children) >= 3:
                # Extract left operand, operator, and right operand
                left_expr = self._transform_member_to_measure_reference(children[0])
                operator = self._extract_arithmetic_operator(children[1])
                right_expr = self._transform_member_to_measure_reference(children[2])
                
                return BinaryOperation(left=left_expr, operator=operator, right=right_expr)
        
        # For value_expression that might contain a calculation_expression
        calculation_exprs = self._find_nodes(expr_node, "calculation_expression")
        if calculation_exprs:
            return self._transform_calculation_expression(calculation_exprs[0])
        
        # Handle direct member expressions
        member_exprs = self._find_nodes(expr_node, "member_expression")
        if member_exprs:
            # For measure references, extract the measure name
            if len(member_exprs) == 1:
                return self._transform_member_to_measure_reference(member_exprs[0])
            else:
                # Multiple member expressions - look for arithmetic operators
                # This is a fallback for complex expressions
                return self._transform_complex_calculation(expr_node)
        
        # Fallback: treat as constant
        return Constant(value=str(expr_node))
    
    def _transform_member_to_measure_reference(self, member_expr: Tree) -> Expression:
        """Transform a member expression to a measure reference for calculations."""
        # Extract measure name from [Measures].[MeasureName] format
        measure_name = self._extract_measure_name_from_member_expr(member_expr)
        if measure_name:
            return MeasureReference(measure_name=measure_name)
        
        # Fallback
        return Constant(value=str(member_expr))
    
    def _extract_measure_name_from_member_expr(self, member_expr: Tree) -> Optional[str]:
        """Extract measure name from a member expression like [Measures].[Sales Amount]."""
        # Look for qualified_member structure
        qualified_members = self._find_nodes(member_expr, "qualified_member") 
        if qualified_members:
            # Get all bracketed identifiers
            bracketed_ids = self._find_nodes(qualified_members[0], "bracketed_identifier")
            if len(bracketed_ids) >= 2:
                # First should be [Measures], second should be the measure name
                hierarchy_name = self._extract_identifier_value(bracketed_ids[0])
                measure_name = self._extract_identifier_value(bracketed_ids[1])
                if hierarchy_name and hierarchy_name.lower() == "measures":
                    return measure_name
        
        # Fallback: look for any member_identifier
        member_ids = self._find_nodes(member_expr, "member_identifier")
        if member_ids:
            bracketed_ids = self._find_nodes(member_ids[0], "bracketed_identifier")
            if bracketed_ids:
                return self._extract_identifier_value(bracketed_ids[0])
        
        return None
    
    def _extract_arithmetic_operator(self, op_node: Tree) -> str:
        """Extract arithmetic operator from arithmetic_op node."""
        if op_node.data == "arithmetic_op":
            # Get the token representing the operator
            for child in op_node.children:
                if isinstance(child, Token):
                    # Map token types to operator symbols
                    token_to_op = {
                        'PLUS': '+',
                        'MINUS': '-',
                        'MULTIPLY': '*',
                        'DIVIDE': '/'
                    }
                    if child.type in token_to_op:
                        return token_to_op[child.type]
                    else:
                        # Fallback to token value if type mapping fails
                        return str(child.value)
            
            # If no children found, this indicates a parsing issue
            self._add_warning("Empty arithmetic operator node - grammar parsing issue detected")
            return "/"  # For calculated members, division is most common
        return "+"  # Default fallback
    
    def _transform_complex_calculation(self, expr_node: Tree) -> Expression:
        """Handle complex calculation expressions with multiple operands."""
        # This is a simplified implementation for complex expressions
        # For now, just create a constant with the expression text
        return Constant(value=str(expr_node))
    
    def _extract_format_string(self, format_node: Tree) -> Optional[str]:
        """Extract format string from format_clause."""
        # Look for string_literal in the format clause
        string_literals = self._find_nodes(format_node, "string_literal")
        if string_literals:
            return self._extract_identifier_value(string_literals[0])
        return None
    
    def _is_member_calculation(self, calc_node: Tree) -> bool:
        """Determine if this is a member calculation vs measure calculation."""
        # Simple heuristic: if it contains dimension references, it's likely a member
        member_refs = self._find_nodes(calc_node, "member_reference")
        return len(member_refs) > 0
    
    def _extract_function_name(self, func_node: Tree) -> str:
        """Extract function name from function call."""
        # Look for function identifier
        func_tokens = [child for child in func_node.children if isinstance(child, Token)]
        if func_tokens:
            return str(func_tokens[0])
        
        return "Unknown"
    
    def _determine_function_type(self, func_name: str) -> FunctionType:
        """Determine function type based on function name."""
        func_name_upper = func_name.upper()
        
        # Map common function names to types
        function_type_map = {
            "SUM": FunctionType.SUM,
            "COUNT": FunctionType.COUNT,
            "AVG": FunctionType.AVG,
            "MIN": FunctionType.MIN,
            "MAX": FunctionType.MAX,
            "CROSSJOIN": FunctionType.CROSSJOIN,
            "FILTER": FunctionType.FILTER,
            "MEMBERS": FunctionType.MEMBERS,
            "CHILDREN": FunctionType.CHILDREN,
        }
        
        return function_type_map.get(func_name_upper, FunctionType.MATH)
    
    def _extract_member_name(self, member_node: Tree) -> str:
        """Extract member name from member reference."""
        return self._extract_identifier_value(member_node)
    
    def _extract_hierarchy_name(self, member_node: Tree) -> Optional[str]:
        """Extract hierarchy name from member reference."""
        # This would need more sophisticated parsing
        return None
    
    def _extract_measure_name(self, measure_node: Tree) -> str:
        """Extract measure name from measure reference."""
        return self._extract_identifier_value(measure_node)
    
    def _extract_hierarchy_from_dimension(self, dim_node: Tree) -> str:
        """Extract hierarchy name from dimension node."""
        return "DefaultHierarchy"  # Placeholder
    
    def _extract_level_from_dimension(self, dim_node: Tree) -> str:
        """Extract level name from dimension node."""
        return "DefaultLevel"  # Placeholder
    
    def _add_error(self, message: str, node: Optional[Tree] = None):
        """Add an error to the collection."""
        error = TransformationError(message, node, self.current_context)
        self.errors.append(error)
        self.logger.error(str(error))
    
    def _add_warning(self, message: str, node: Optional[Tree] = None):
        """Add a warning to the collection."""
        warning = TransformationWarning(message, node, self.current_context)
        self.warnings.append(warning)
        self.logger.warning(str(warning))
    
    def _is_measure_expression(self, member_expr: Tree) -> bool:
        """Check if a member expression references the Measures hierarchy."""
        # Look for hierarchy_expression nodes
        hierarchy_nodes = self._find_nodes(member_expr, "hierarchy_expression")
        for hierarchy_node in hierarchy_nodes:
            # Check if the hierarchy name is "Measures"
            bracketed_ids = self._find_nodes(hierarchy_node, "bracketed_identifier")
            if bracketed_ids:
                hierarchy_name = self._extract_identifier_value(bracketed_ids[0])
                if hierarchy_name and hierarchy_name.lower() == "measures":
                    return True
        return False
    
    def _extract_measure_name(self, member_expr: Tree) -> Optional[str]:
        """Extract measure name from a member expression."""
        # Look for member_identifier nodes (the measure name part)
        member_id_nodes = self._find_nodes(member_expr, "member_identifier")
        for member_id_node in member_id_nodes:
            # Try bracketed identifier first
            bracketed_ids = self._find_nodes(member_id_node, "bracketed_identifier")
            if bracketed_ids:
                return self._extract_identifier_value(bracketed_ids[0])
            # Fallback to regular identifier
            identifiers = self._find_nodes(member_id_node, "identifier")
            if identifiers:
                return self._extract_identifier_value(identifiers[0])
        return None
    
    def _transform_dimension_from_member_expr(self, member_expr: Tree) -> Optional[Dimension]:
        """Transform a dimension from a member expression."""
        try:
            # Extract hierarchy name
            hierarchy_name = self._extract_hierarchy_name(member_expr)
            if not hierarchy_name:
                return None
                
            # Extract level name (if specified)
            level_name = self._extract_level_name(member_expr)
            
            # Extract member selection type
            member_selection = self._extract_member_selection(member_expr)
            
            # Create hierarchy and level references
            hierarchy = HierarchyReference(table=hierarchy_name, name=hierarchy_name)
            level = LevelReference(name=level_name) if level_name else None
            
            return Dimension(
                hierarchy=hierarchy,
                level=level,
                members=member_selection
            )
            
        except Exception as e:
            self._add_warning(f"Failed to transform dimension from member expression: {str(e)}")
            return None
    
    def _extract_hierarchy_name(self, member_expr: Tree) -> Optional[str]:
        """Extract hierarchy name from a member expression."""
        # Look for hierarchy_expression nodes directly
        hierarchy_nodes = self._find_nodes(member_expr, "hierarchy_expression")
        for hierarchy_node in hierarchy_nodes:
            bracketed_ids = self._find_nodes(hierarchy_node, "bracketed_identifier")
            if bracketed_ids:
                return self._extract_identifier_value(bracketed_ids[0])
        
        # For member_function nodes containing key references, extract from nested member_expression
        member_funcs = self._find_nodes(member_expr, "member_function")
        for func_node in member_funcs:
            nested_member_exprs = self._find_nodes(func_node, "member_expression")
            for nested_expr in nested_member_exprs:
                hierarchy_nodes = self._find_nodes(nested_expr, "hierarchy_expression")
                for hierarchy_node in hierarchy_nodes:
                    bracketed_ids = self._find_nodes(hierarchy_node, "bracketed_identifier")
                    if bracketed_ids:
                        return self._extract_identifier_value(bracketed_ids[0])
        
        return None
    
    def _extract_level_name(self, member_expr: Tree) -> Optional[str]:
        """Extract level name from a member expression."""
        # Look for level_expression nodes directly
        level_nodes = self._find_nodes(member_expr, "level_expression")
        for level_node in level_nodes:
            bracketed_ids = self._find_nodes(level_node, "bracketed_identifier")
            if bracketed_ids:
                return self._extract_identifier_value(bracketed_ids[0])
        
        # For member_function nodes containing key references, extract from nested member_expression
        # In this case, the member_identifier in the nested expression is actually the level name
        member_funcs = self._find_nodes(member_expr, "member_function")
        for func_node in member_funcs:
            nested_member_exprs = self._find_nodes(func_node, "member_expression")
            for nested_expr in nested_member_exprs:
                member_id_nodes = self._find_nodes(nested_expr, "member_identifier")
                for member_id_node in member_id_nodes:
                    bracketed_ids = self._find_nodes(member_id_node, "bracketed_identifier")
                    if bracketed_ids:
                        return self._extract_identifier_value(bracketed_ids[0])
        
        return None
    
    def _extract_member_selection(self, member_expr: Tree) -> MemberSelection:
        """Extract member selection type from a member expression."""
        # Check for .Members which indicates all members
        member_id_nodes = self._find_nodes(member_expr, "member_identifier")
        for member_id_node in member_id_nodes:
            identifiers = self._find_nodes(member_id_node, "identifier")
            for identifier in identifiers:
                value = self._extract_identifier_value(identifier)
                if value and value.lower() == "members":
                    return MemberSelection(selection_type=MemberSelectionType.ALL)
        
        # Default to specific member selection
        return MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
    
    def _create_filter_from_member_expr(self, member_expr: Tree) -> Optional[Filter]:
        """Create a filter from a member expression in WHERE clause."""
        try:
            # Extract hierarchy and member information
            hierarchy_name = self._extract_hierarchy_name(member_expr)
            if not hierarchy_name:
                return None
                
            # Extract level and member information
            level_name = self._extract_level_name(member_expr)
            member_name = self._extract_specific_member_value(member_expr)
            if not member_name:
                return None
            
            # Create a dimension object for the filter
            hierarchy = HierarchyReference(table=hierarchy_name, name=hierarchy_name)
            level = LevelReference(name=level_name) if level_name else LevelReference(name=hierarchy_name)
            
            # Create a specific member selection for the filter
            members = MemberSelection(
                selection_type=MemberSelectionType.SPECIFIC,
                specific_members=[member_name]
            )
            
            dimension = Dimension(
                hierarchy=hierarchy,
                level=level,
                members=members
            )
            
            # Create a dimension filter for equality
            dimension_filter = DimensionFilter(
                dimension=dimension,
                operator=FilterOperator.EQUALS,
                values=[member_name]
            )
            
            # Wrap in Filter object
            return Filter(
                filter_type=FilterType.DIMENSION,
                target=dimension_filter
            )
            
        except Exception as e:
            self._add_warning(f"Failed to create filter from member expression: {str(e)}")
            return None
    
    def _extract_specific_member_name(self, member_expr: Tree) -> Optional[str]:
        """Extract specific member name from a member expression (for filters)."""
        # For filters, we want the full qualified member name
        parts = []
        
        # Get hierarchy name
        hierarchy_name = self._extract_hierarchy_name(member_expr)
        if hierarchy_name:
            parts.append(hierarchy_name)
        
        # Get level name if present
        level_name = self._extract_level_name(member_expr)
        if level_name:
            parts.append(level_name)
        
        # Get member name
        member_id_nodes = self._find_nodes(member_expr, "member_identifier")
        for member_id_node in member_id_nodes:
            # Try bracketed identifier first
            bracketed_ids = self._find_nodes(member_id_node, "bracketed_identifier")
            if bracketed_ids:
                member_name = self._extract_identifier_value(bracketed_ids[0])
                if member_name:
                    parts.append(member_name)
                    break
        
        # Return the qualified member name
        return ".".join(parts) if parts else None
    
    def _extract_specific_member_value(self, member_expr: Tree) -> Optional[str]:
        """Extract the specific member value (just the member name, not qualified)."""
        # First check for key references like .&[2023]
        if self._has_key_reference(member_expr):
            key_value = self._extract_key_reference_value(member_expr)
            if key_value:
                return key_value
        
        # Get just the member name part for the filter value
        member_id_nodes = self._find_nodes(member_expr, "member_identifier")
        for member_id_node in member_id_nodes:
            # Try bracketed identifier first
            bracketed_ids = self._find_nodes(member_id_node, "bracketed_identifier")
            if bracketed_ids:
                return self._extract_identifier_value(bracketed_ids[0])
        return None
    
    def _has_key_reference(self, member_expr: Tree) -> bool:
        """Check if member expression has a key reference (.&[...])."""
        # Look for member_function nodes that have a bracketed_identifier as direct child
        # This indicates a key reference like .&[2023]
        member_funcs = self._find_nodes(member_expr, "member_function")
        for func_node in member_funcs:
            # Check if this function node has a bracketed_identifier as a direct child
            # (not nested within a member_expression)
            for child in func_node.children:
                if isinstance(child, Tree) and child.data == "bracketed_identifier":
                    # Make sure it's not part of a nested member_expression
                    nested_member_exprs = [c for c in func_node.children 
                                         if isinstance(c, Tree) and c.data == "member_expression"]
                    if nested_member_exprs:
                        # If this bracketed_identifier is not contained in the nested member_expression,
                        # it's a key reference
                        if not self._is_ancestor_of(nested_member_exprs[0], child):
                            return True
        return False
    
    def _extract_key_reference_value(self, member_expr: Tree) -> Optional[str]:
        """Extract the value from a key reference (.&[value])."""
        member_funcs = self._find_nodes(member_expr, "member_function")
        for func_node in member_funcs:
            # The key reference value is in a bracketed_identifier that's a direct child
            # after the nested member_expression
            bracketed_ids = self._find_nodes(func_node, "bracketed_identifier")
            # Skip the first bracketed_identifier (which is part of the nested member_expression)
            # and get the one that contains the key value
            nested_member_exprs = self._find_nodes(func_node, "member_expression")
            if nested_member_exprs and bracketed_ids:
                # The key value is typically the last bracketed_identifier in the member_function
                for bracketed_id in reversed(bracketed_ids):
                    # Check if this bracketed_identifier is not part of the nested member expression
                    if not self._is_ancestor_of(nested_member_exprs[0], bracketed_id):
                        return self._extract_identifier_value(bracketed_id)
        return None
    
    def _is_ancestor_of(self, ancestor: Tree, descendant: Tree) -> bool:
        """Check if ancestor tree contains descendant tree."""
        if ancestor == descendant:
            return True
        if hasattr(ancestor, 'children'):
            for child in ancestor.children:
                if isinstance(child, Tree) and self._is_ancestor_of(child, descendant):
                    return True
        return False