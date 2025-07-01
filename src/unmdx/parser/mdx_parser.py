"""MDX Parser using Lark for parsing MDX queries."""

from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from ..ir.models import (
    AggregationType,
    CubeReference,
    Dimension,
    DimensionFilter,
    Filter,
    FilterOperator,
    FilterType,
    HierarchyReference,
    LevelReference,
    Measure,
    MemberSelection,
    MemberSelectionType,
    Query,
    QueryMetadata,
)


class MDXParseError(Exception):
    """Exception raised when MDX parsing fails."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


class MDXParser:
    """Parser for MDX queries using Lark grammar."""

    def __init__(self):
        """Initialize the parser with the MDX grammar."""
        grammar_path = Path(__file__).parent / "mdx_grammar.lark"
        with open(grammar_path) as f:
            grammar = f.read()

        self.parser = Lark(grammar, parser="lalr", transformer=None, start="start")

    def parse(self, mdx_query: str) -> Query:
        """Parse an MDX query string into an IR Query object.

        Args:
            mdx_query: The MDX query string to parse

        Returns:
            Query: The parsed query as an IR object

        Raises:
            MDXParseError: If parsing fails
        """
        try:
            # Parse the MDX query into an AST
            tree = self.parser.parse(mdx_query)

            # Transform the AST into our IR
            transformer = MDXTransformer()
            query = transformer.transform(tree)

            return query

        except LarkError as e:
            raise MDXParseError(f"Failed to parse MDX query: {e}", e)
        except Exception as e:
            raise MDXParseError(f"Unexpected error during parsing: {e}", e)


class MDXTransformer:
    """Transforms the parsed MDX AST into our IR representation."""

    def transform(self, tree: Tree) -> Query:
        """Transform a parsed MDX tree into a Query IR object."""
        return self._transform_mdx_statement(tree)

    def _transform_mdx_statement(self, tree: Tree) -> Query:
        """Transform the root mdx_statement node."""
        select_statement = tree.children[0]  # Simplified - only select statement
        return self._transform_select_statement(select_statement)

    def _transform_select_statement(self, tree: Tree) -> Query:
        """Transform a SELECT statement into a Query."""
        cube = None
        measures = []
        dimensions = []
        filters = []

        for child in tree.children:
            if isinstance(child, Token) or child is None:
                continue

            if child.data == "axis_specification_list":
                # Parse axis specifications to extract measures and dimensions
                axes_data = self._transform_axis_specifications(child)
                measures.extend(axes_data["measures"])
                dimensions.extend(axes_data["dimensions"])

            elif child.data == "cube_specification":
                cube = self._transform_cube_specification(child)

            elif child.data == "where_clause":
                where_filters = self._transform_where_clause(child)
                filters.extend(where_filters)

        return Query(
            cube=cube or CubeReference(name="Unknown"),
            measures=measures,
            dimensions=dimensions,
            filters=filters,
            order_by=[],
            limit=None,
            calculations=[],
            metadata=QueryMetadata(),
        )

    def _transform_axis_specifications(self, tree: Tree) -> dict[str, list]:
        """Transform axis specifications into measures and dimensions."""
        measures = []
        dimensions = []

        for axis_spec in tree.children:
            if axis_spec.data == "axis_specification":
                axis_data = self._transform_axis_specification(axis_spec)

                # Determine if this axis contains measures or dimensions
                axis_name = axis_data["axis_name"]
                set_expr = axis_data["set_expression"]

                if axis_name.lower() in ["columns", "axis(0)"]:
                    # Typically measures go on columns
                    axis_measures = self._extract_measures_from_set(set_expr)
                    measures.extend(axis_measures)
                else:
                    # Other axes typically contain dimensions
                    axis_dimensions = self._extract_dimensions_from_set(set_expr)
                    dimensions.extend(axis_dimensions)

        return {"measures": measures, "dimensions": dimensions}

    def _transform_axis_specification(self, tree: Tree) -> dict[str, Any]:
        """Transform a single axis specification."""
        axis_name = ""
        set_expression = None

        for child in tree.children:
            if isinstance(child, Token):
                continue

            if child.data == "axis_name":
                axis_name = self._get_axis_name(child)
            elif child.data in ["set_expression", "set_literal"]:
                set_expression = child

        return {"axis_name": axis_name, "set_expression": set_expression}

    def _get_axis_name(self, tree: Tree) -> str:
        """Extract axis name from axis_name node."""
        if tree.children:
            child = tree.children[0]
            if isinstance(child, Token):
                return child.value
            elif hasattr(child, "data") and child.data == "axis_number":
                # Handle AXIS(n) format
                return f"AXIS({self._extract_integer(child)})"
        return "UNKNOWN"

    def _extract_measures_from_set(self, set_expr: Tree) -> list[Measure]:
        """Extract measures from a set expression."""
        measures = []

        if set_expr.data == "set_literal":
            # Parse set literal content
            for child in set_expr.children:
                if child.data == "set_content":
                    measures.extend(self._extract_measures_from_set_content(child))

        return measures

    def _extract_measures_from_set_content(self, tree: Tree) -> list[Measure]:
        """Extract measures from set content."""
        measures = []

        for child in tree.children:
            if child.data == "member_expression":
                member_name = self._extract_member_name(child)
                # Assume it's a measure if it contains "Measures"
                if "Measures" in member_name or "measures" in member_name.lower():
                    clean_name = member_name.replace("[Measures].", "").strip("[]")
                    measures.append(
                        Measure(
                            name=clean_name,
                            aggregation=AggregationType.SUM,
                            alias=clean_name,
                        )
                    )

        return measures

    def _extract_dimensions_from_set(self, set_expr: Tree) -> list[Dimension]:
        """Extract dimensions from a set expression."""
        dimensions = []

        if set_expr.data == "set_literal":
            for child in set_expr.children:
                if child.data == "set_content":
                    dimensions.extend(self._extract_dimensions_from_set_content(child))
        elif set_expr.data == "set_function":
            # Handle set functions like Members()
            dimensions.extend(self._extract_dimensions_from_set_function(set_expr))

        return dimensions

    def _extract_dimensions_from_set_content(self, tree: Tree) -> list[Dimension]:
        """Extract dimensions from set content."""
        dimensions = []

        for child in tree.children:
            if child.data == "member_expression":
                member_name = self._extract_member_name(child)
                if not ("Measures" in member_name or "measures" in member_name.lower()):
                    # Parse dimension and level
                    dim_info = self._parse_dimension_member(member_name)
                    if dim_info:
                        dimensions.append(
                            Dimension(
                                hierarchy=HierarchyReference(
                                    table=dim_info["dimension"],
                                    name=dim_info["dimension"],
                                ),
                                level=LevelReference(name=dim_info["level"]),
                                members=MemberSelection(
                                    selection_type=MemberSelectionType.SPECIFIC,
                                    specific_members=[dim_info["member"]],
                                ),
                            )
                        )

        return dimensions

    def _extract_dimensions_from_set_function(self, tree: Tree) -> list[Dimension]:
        """Extract dimensions from set functions like Members()."""
        dimensions = []

        for child in tree.children:
            if child.data == "members_function":
                # Extract dimension from Members() function - simplified grammar
                member_path = child.children[0]  # member_path before .Members
                member_name = self._extract_member_path(member_path)
                dim_info = self._parse_dimension_member(member_name)
                if dim_info:
                    dimensions.append(
                        Dimension(
                            hierarchy=HierarchyReference(
                                table=dim_info["dimension"], name=dim_info["dimension"]
                            ),
                            level=LevelReference(name=dim_info["level"]),
                            members=MemberSelection(
                                selection_type=MemberSelectionType.ALL
                            ),
                        )
                    )

        return dimensions

    def _extract_member_name(self, tree: Tree) -> str:
        """Extract member name from member_expression."""
        if tree.data == "member_expression":
            return self._extract_member_path(tree.children[0])
        return ""

    def _extract_member_path(self, tree: Tree) -> str:
        """Extract member path from member_path node."""
        if tree.data == "member_path":
            parts = []
            for child in tree.children:
                if child.data == "member_part":
                    part_name = child.children[0].value.strip()  # MEMBER_NAME token
                    parts.append(f"[{part_name}]")
            return ".".join(parts)
        return ""

    def _parse_dimension_member(self, member_name: str) -> dict[str, str] | None:
        """Parse a dimension member reference like [Product].[Category].[Bikes]."""
        if "." in member_name:
            parts = member_name.split(".")
            if len(parts) >= 2:
                dimension = parts[0].strip("[]")
                level = parts[1].strip("[]")
                member = parts[-1].strip("[]") if len(parts) > 2 else level
                return {"dimension": dimension, "level": level, "member": member}
        return None

    def _transform_cube_specification(self, tree: Tree) -> CubeReference:
        """Transform cube specification into CubeReference."""
        # Simplified grammar - just get the MEMBER_NAME token
        cube_name = tree.children[0].value.strip()  # MEMBER_NAME token
        return CubeReference(name=cube_name, database=None)

    def _transform_where_clause(self, tree: Tree) -> list[Filter]:
        """Transform WHERE clause into filters."""
        filters = []

        for child in tree.children:
            if child.data == "slicer_specification":
                slicer_filters = self._transform_slicer_specification(child)
                filters.extend(slicer_filters)

        return filters

    def _transform_slicer_specification(self, tree: Tree) -> list[Filter]:
        """Transform slicer specification into filters."""
        filters = []

        for child in tree.children:
            if child.data == "member_expression":
                member_name = self._extract_member_name(child)
                dim_info = self._parse_dimension_member(member_name)

                if dim_info:
                    dimension = Dimension(
                        hierarchy=HierarchyReference(
                            table=dim_info["dimension"], name=dim_info["dimension"]
                        ),
                        level=LevelReference(name=dim_info["level"]),
                        members=MemberSelection(selection_type=MemberSelectionType.ALL),
                    )

                    filter_obj = Filter(
                        filter_type=FilterType.DIMENSION,
                        target=DimensionFilter(
                            dimension=dimension,
                            operator=FilterOperator.EQUALS,
                            values=[dim_info["member"]],
                        ),
                    )
                    filters.append(filter_obj)

        return filters
