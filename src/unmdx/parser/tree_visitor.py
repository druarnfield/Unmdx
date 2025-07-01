"""Parse tree visitor for debugging and analysis."""

from dataclasses import dataclass
from typing import Any

from lark import Token, Tree

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class QueryStructure:
    """Structure information extracted from MDX parse tree."""
    measures: list[str]
    dimensions: list[dict[str, str]]
    filters: list[dict[str, Any]]
    calculations: list[dict[str, str]]
    axes: list[dict[str, str]]
    cube_name: str | None
    has_with_clause: bool
    max_nesting_depth: int
    comment_hints: list[str]


class MDXTreeAnalyzer:
    """
    Advanced tree visitor for analyzing MDX parse trees.
    
    Extracts semantic information and provides debugging utilities.
    """

    def __init__(self, tree: Tree):
        self.tree = tree
        self.logger = get_logger(__name__)

    def analyze(self) -> QueryStructure:
        """
        Perform complete analysis of the parse tree.
        
        Returns:
            QueryStructure with extracted information
        """
        return QueryStructure(
            measures=self.extract_measures(),
            dimensions=self.extract_dimensions(),
            filters=self.extract_filters(),
            calculations=self.extract_calculations(),
            axes=self.extract_axes(),
            cube_name=self.extract_cube_name(),
            has_with_clause=self.has_with_clause(),
            max_nesting_depth=self.calculate_max_nesting(),
            comment_hints=self.extract_comment_hints()
        )

    def extract_measures(self) -> list[str]:
        """Extract all measure references from the tree."""
        measures = set()

        def traverse(node):
            if isinstance(node, Tree):
                if node.data == "qualified_member":
                    measure_name = self._extract_measure_name(node)
                    if measure_name:
                        measures.add(measure_name)

                # Also check member expressions that might be measures
                elif node.data == "member_expression":
                    measure_name = self._extract_measure_from_member_expr(node)
                    if measure_name:
                        measures.add(measure_name)

                for child in node.children:
                    traverse(child)

        traverse(self.tree)
        return sorted(list(measures))

    def extract_dimensions(self) -> list[dict[str, str]]:
        """Extract dimension information from axis specifications."""
        dimensions = []

        # Find all axis specifications
        axis_specs = self._find_nodes("axis_specification")

        for axis_spec in axis_specs:
            axis_name = self._extract_axis_name(axis_spec)
            set_expressions = self._find_nodes_in_subtree(axis_spec, "set_expression")

            for set_expr in set_expressions:
                dim_info = self._extract_dimension_from_set(set_expr)
                if dim_info:
                    dim_info["axis"] = axis_name
                    dimensions.append(dim_info)

        return dimensions

    def extract_filters(self) -> list[dict[str, Any]]:
        """Extract filter information from WHERE clause."""
        filters = []

        where_clause = self._find_first_node("where_clause")
        if not where_clause:
            return filters

        slicer_spec = self._find_first_node_in_subtree(where_clause, "slicer_specification")
        if not slicer_spec:
            return filters

        # Handle tuple expressions (multiple filters)
        tuple_expr = self._find_first_node_in_subtree(slicer_spec, "tuple_expression")
        if tuple_expr:
            filters.extend(self._extract_filters_from_tuple(tuple_expr))
        else:
            # Single member expression
            member_expr = self._find_first_node_in_subtree(slicer_spec, "member_expression")
            if member_expr:
                filter_info = self._extract_filter_from_member(member_expr)
                if filter_info:
                    filters.append(filter_info)

        return filters

    def extract_calculations(self) -> list[dict[str, str]]:
        """Extract calculated member definitions from WITH clause."""
        calculations = []

        with_clause = self._find_first_node("with_clause")
        if not with_clause:
            return calculations

        member_defs = self._find_nodes_in_subtree(with_clause, "member_definition")

        for member_def in member_defs:
            calc_info = self._extract_calculation_info(member_def)
            if calc_info:
                calculations.append(calc_info)

        return calculations

    def extract_axes(self) -> list[dict[str, str]]:
        """Extract axis information."""
        axes = []

        axis_specs = self._find_nodes("axis_specification")

        for i, axis_spec in enumerate(axis_specs):
            axis_info = {
                "position": i,
                "name": self._extract_axis_name(axis_spec),
                "has_non_empty": self._has_non_empty(axis_spec),
                "set_type": self._classify_set_expression(axis_spec)
            }
            axes.append(axis_info)

        return axes

    def extract_cube_name(self) -> str | None:
        """Extract cube name from FROM clause."""
        cube_spec = self._find_first_node("cube_specification")
        if not cube_spec:
            return None

        # Check for bracketed identifier
        bracketed_id = self._find_first_node_in_subtree(cube_spec, "bracketed_identifier")
        if bracketed_id and bracketed_id.children:
            return bracketed_id.children[0].value

        # Check for simple identifier
        identifier = self._find_first_node_in_subtree(cube_spec, "identifier")
        if identifier and identifier.children:
            return identifier.children[0].value

        return None

    def has_with_clause(self) -> bool:
        """Check if query has a WITH clause."""
        return self._find_first_node("with_clause") is not None

    def calculate_max_nesting(self) -> int:
        """Calculate maximum nesting depth of sets."""
        max_depth = 0

        def traverse(node, depth=0):
            nonlocal max_depth

            if isinstance(node, Tree):
                current_depth = depth
                if node.data in ("set_expression", "set_expression_nested"):
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)

                for child in node.children:
                    traverse(child, current_depth)

        traverse(self.tree)
        return max_depth

    def extract_comment_hints(self) -> list[str]:
        """Extract optimizer hints and other comments."""
        hints = []

        def traverse(node):
            if isinstance(node, Token):
                if hasattr(node, "type") and "COMMENT" in node.type:
                    comment_text = node.value
                    if "OPTIMIZER" in comment_text.upper():
                        hints.append(comment_text.strip())
            elif isinstance(node, Tree):
                for child in node.children:
                    traverse(child)

        traverse(self.tree)
        return hints

    def _find_nodes(self, node_type: str) -> list[Tree]:
        """Find all nodes of specified type."""
        nodes = []

        def traverse(node):
            if isinstance(node, Tree):
                if node.data == node_type:
                    nodes.append(node)
                for child in node.children:
                    traverse(child)

        traverse(self.tree)
        return nodes

    def _find_first_node(self, node_type: str) -> Tree | None:
        """Find first node of specified type."""
        nodes = self._find_nodes(node_type)
        return nodes[0] if nodes else None

    def _find_nodes_in_subtree(self, subtree: Tree, node_type: str) -> list[Tree]:
        """Find nodes of specified type within a subtree."""
        nodes = []

        def traverse(node):
            if isinstance(node, Tree):
                if node.data == node_type:
                    nodes.append(node)
                for child in node.children:
                    traverse(child)

        traverse(subtree)
        return nodes

    def _find_first_node_in_subtree(self, subtree: Tree, node_type: str) -> Tree | None:
        """Find first node of specified type within a subtree."""
        nodes = self._find_nodes_in_subtree(subtree, node_type)
        return nodes[0] if nodes else None

    def _extract_measure_name(self, qualified_member: Tree) -> str | None:
        """Extract measure name from qualified member expression."""
        # Look for pattern [Measures].[MeasureName]
        bracketed_ids = self._find_nodes_in_subtree(qualified_member, "bracketed_identifier")

        if len(bracketed_ids) >= 2:
            first_part = bracketed_ids[0].children[0].value if bracketed_ids[0].children else ""
            second_part = bracketed_ids[1].children[0].value if bracketed_ids[1].children else ""

            if first_part.lower() == "measures":
                return second_part

        return None

    def _extract_measure_from_member_expr(self, member_expr: Tree) -> str | None:
        """Extract measure name from member expression."""
        # Check if this contains a qualified member that's a measure
        qualified_members = self._find_nodes_in_subtree(member_expr, "qualified_member")
        for qm in qualified_members:
            measure_name = self._extract_measure_name(qm)
            if measure_name:
                return measure_name

        return None

    def _extract_dimension_from_set(self, set_expr: Tree) -> dict[str, str] | None:
        """Extract dimension information from set expression."""
        # Look for qualified members that represent dimensions
        qualified_members = self._find_nodes_in_subtree(set_expr, "qualified_member")

        for qm in qualified_members:
            bracketed_ids = self._find_nodes_in_subtree(qm, "bracketed_identifier")

            if len(bracketed_ids) >= 2:
                parts = []
                for bid in bracketed_ids:
                    if bid.children:
                        parts.append(bid.children[0].value)

                # Skip measures
                if parts[0].lower() != "measures":
                    return {
                        "dimension": parts[0],
                        "hierarchy": parts[1] if len(parts) > 1 else parts[0],
                        "level": parts[2] if len(parts) > 2 else None,
                        "member": parts[3] if len(parts) > 3 else None
                    }

        return None

    def _extract_axis_name(self, axis_spec: Tree) -> str:
        """Extract axis name from axis specification."""
        # Look for axis-related nodes directly
        for child in axis_spec.children:
            if isinstance(child, Tree):
                if child.data == "axis_columns":
                    return "columns"
                elif child.data == "axis_rows":
                    return "rows"
                elif child.data == "axis_pages":
                    return "pages"
                elif child.data == "axis_chapters":
                    return "chapters"
                elif child.data == "axis_sections":
                    return "sections"
                elif child.data in ("axis_number", "axis_number_short"):
                    # Extract the number
                    for grandchild in child.children:
                        if isinstance(grandchild, Token) and grandchild.type == "NUMBER":
                            return f"axis_{grandchild.value}"

        return "unknown"

    def _has_non_empty(self, axis_spec: Tree) -> bool:
        """Check if axis specification has NON EMPTY modifier."""
        return self._find_first_node_in_subtree(axis_spec, "non_empty") is not None

    def _classify_set_expression(self, axis_spec: Tree) -> str:
        """Classify the type of set expression on this axis."""
        set_exprs = self._find_nodes_in_subtree(axis_spec, "set_expression")
        if not set_exprs:
            return "empty"

        # Check for function calls
        func_calls = self._find_nodes_in_subtree(axis_spec, "function_call")
        if func_calls:
            return "function"

        # Check for explicit sets
        if len(set_exprs) == 1:
            return "explicit"

        return "complex"

    def _extract_filters_from_tuple(self, tuple_expr: Tree) -> list[dict[str, Any]]:
        """Extract filter information from tuple expression."""
        filters = []

        member_exprs = self._find_nodes_in_subtree(tuple_expr, "member_expression")

        for member_expr in member_exprs:
            filter_info = self._extract_filter_from_member(member_expr)
            if filter_info:
                filters.append(filter_info)

        return filters

    def _extract_filter_from_member(self, member_expr: Tree) -> dict[str, Any] | None:
        """Extract filter information from member expression."""
        # Check if this is a member function (e.g., .&[2023])
        member_function = self._find_first_node_in_subtree(member_expr, "member_function")
        if member_function:
            # Extract the base member (dimension and hierarchy)
            qualified_member = self._find_first_node_in_subtree(member_function, "qualified_member")
            if qualified_member:
                bracketed_ids = self._find_nodes_in_subtree(qualified_member, "bracketed_identifier")
                
                dimension = None
                level = None
                if len(bracketed_ids) >= 2:
                    dimension = bracketed_ids[0].children[0].value if bracketed_ids[0].children else None
                    level = bracketed_ids[1].children[0].value if bracketed_ids[1].children else None
                
                # Extract the value from member function (after the &)
                value = None
                # Look for bracketed_identifier that's a direct child of member_function (not in qualified_member)
                for child in member_function.children:
                    if isinstance(child, Tree) and child.data == "bracketed_identifier":
                        value = child.children[0].value if child.children else None
                        break
                
                if dimension:
                    return {
                        "dimension": dimension,
                        "level": level,
                        "value": value,
                        "operator": "equals"
                    }
        
        # Fall back to regular member expression handling
        qualified_members = self._find_nodes_in_subtree(member_expr, "qualified_member")

        for qm in qualified_members:
            bracketed_ids = self._find_nodes_in_subtree(qm, "bracketed_identifier")

            if len(bracketed_ids) >= 2:
                parts = []
                for bid in bracketed_ids:
                    if bid.children:
                        parts.append(bid.children[0].value)

                # Extract dimension and value
                if len(parts) >= 2:
                    # Handle patterns like [Date].[Calendar Year].&[2023]
                    dimension = parts[0]
                    level = parts[1] if len(parts) > 1 else None

                    # Look for key reference (&[value])
                    value = None
                    if len(parts) > 2 and parts[2].startswith("&"):
                        value = parts[2][1:]  # Remove &
                    elif len(parts) > 2:
                        value = parts[2]

                    return {
                        "dimension": dimension,
                        "level": level,
                        "value": value,
                        "operator": "equals"
                    }

        return None

    def _extract_calculation_info(self, member_def: Tree) -> dict[str, str] | None:
        """Extract calculation information from member definition."""
        # Find member identifier
        member_id = self._find_first_node_in_subtree(member_def, "member_identifier")
        if not member_id:
            return None

        # Extract name
        bracketed_id = self._find_first_node_in_subtree(member_id, "bracketed_identifier")
        name = None
        if bracketed_id and bracketed_id.children:
            name = bracketed_id.children[0].value

        # Find value expression
        value_expr = self._find_first_node_in_subtree(member_def, "value_expression")

        # Extract expression text (simplified)
        expression = self._extract_expression_text(value_expr) if value_expr else None

        return {
            "name": name,
            "expression": expression,
            "type": "member"
        } if name else None

    def _extract_expression_text(self, expr_node: Tree) -> str:
        """Extract text representation of expression (simplified)."""
        # This is a simplified version - in practice you'd want more sophisticated handling
        def traverse(node):
            if isinstance(node, Token):
                return node.value
            elif isinstance(node, Tree):
                parts = []
                for child in node.children:
                    part = traverse(child)
                    if part:
                        parts.append(part)
                return " ".join(parts)
            return ""

        return traverse(expr_node).strip()


class TreeDebugger:
    """Utility for debugging parse trees with detailed output."""

    def __init__(self, tree: Tree):
        self.tree = tree

    def print_detailed(self, max_depth: int | None = None) -> str:
        """Print detailed tree structure with node types and values."""
        lines = []

        def traverse(node, depth=0, prefix=""):
            if max_depth is not None and depth > max_depth:
                return

            indent = "  " * depth

            if isinstance(node, Tree):
                lines.append(f"{indent}{prefix}Tree({node.data})")
                for i, child in enumerate(node.children):
                    child_prefix = f"[{i}] "
                    traverse(child, depth + 1, child_prefix)

            elif isinstance(node, Token):
                lines.append(f"{indent}{prefix}Token({node.type}: '{node.value}')")

            else:
                lines.append(f"{indent}{prefix}Other: {repr(node)}")

        traverse(self.tree)
        return "\n".join(lines)

    def find_issues(self) -> list[str]:
        """Find potential issues in the parse tree."""
        issues = []
        analyzer = MDXTreeAnalyzer(self.tree)

        # Check for empty nodes
        if self._has_empty_nodes():
            issues.append("Empty nodes found in parse tree")

        # Check nesting depth
        max_depth = analyzer.calculate_max_nesting()
        if max_depth > 10:
            issues.append(f"Very deep nesting detected: {max_depth} levels")

        # Check for malformed constructs
        if self._has_malformed_constructs():
            issues.append("Malformed constructs detected")

        return issues

    def _has_empty_nodes(self) -> bool:
        """Check for empty nodes in the tree."""
        def traverse(node):
            if isinstance(node, Tree):
                if not node.children:
                    return True
                for child in node.children:
                    if traverse(child):
                        return True
            return False

        return traverse(self.tree)

    def _has_malformed_constructs(self) -> bool:
        """Check for malformed constructs."""
        # This is a placeholder - in practice you'd check for specific malformed patterns
        return False
