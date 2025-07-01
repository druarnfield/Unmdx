"""MDX Parser implementation using Lark."""

from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree
from lark.exceptions import LarkError, ParseError, UnexpectedInput, UnexpectedToken

from ..utils.logging import get_logger

logger = get_logger(__name__)


class MDXParseError(Exception):
    """Custom exception for MDX parsing errors."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
        context: str | None = None,
        original_error: Exception | None = None
    ):
        self.message = message
        self.line = line
        self.column = column
        self.context = context
        self.original_error = original_error

        # Build error message
        error_parts = [message]
        if line is not None and column is not None:
            error_parts.append(f"at line {line}, column {column}")
        if context:
            error_parts.append(f"near '{context}'")

        super().__init__(": ".join(error_parts))


class MDXParser:
    """
    MDX Parser wrapper for Lark parser.
    
    Provides error handling, debugging features, and convenience methods
    for parsing MDX queries from Necto SSAS cubes.
    """

    def __init__(self, grammar_path: Path | None = None, debug: bool = False):
        """
        Initialize the MDX parser.
        
        Args:
            grammar_path: Path to the Lark grammar file. If None, uses default.
            debug: Enable debug mode for more verbose parsing information.
        """
        self.debug = debug
        self._parser = None

        # Load grammar
        if grammar_path is None:
            grammar_path = Path(__file__).parent / "mdx_grammar.lark"

        self.grammar_path = grammar_path
        self._load_grammar()

    def _load_grammar(self) -> None:
        """Load the Lark grammar from file."""
        try:
            with open(self.grammar_path, encoding="utf-8") as f:
                grammar_text = f.read()

            # Create parser with options for handling messy MDX
            self._parser = Lark(
                grammar_text,
                parser="earley",  # More tolerant of ambiguity
                ambiguity="resolve",  # Auto-resolve ambiguities
                propagate_positions=True,  # Track line/column for errors
                maybe_placeholders=True,  # Allow optional elements
                debug=self.debug
            )

            logger.info(f"Loaded MDX grammar from {self.grammar_path}")

        except FileNotFoundError:
            raise MDXParseError(f"Grammar file not found: {self.grammar_path}")
        except Exception as e:
            raise MDXParseError(f"Failed to load grammar: {e}", original_error=e)

    def parse(self, mdx_query: str) -> Tree:
        """
        Parse an MDX query string into a parse tree.
        
        Args:
            mdx_query: The MDX query string to parse
            
        Returns:
            Lark Tree object representing the parsed query
            
        Raises:
            MDXParseError: If parsing fails
        """
        if not mdx_query or not mdx_query.strip():
            raise MDXParseError("Empty or whitespace-only query")

        try:
            logger.debug(f"Parsing MDX query: {mdx_query[:100]}...")

            # Clean query - remove extra whitespace but preserve structure
            cleaned_query = self._clean_query(mdx_query)

            # Parse the query
            tree = self._parser.parse(cleaned_query)

            logger.debug("Successfully parsed MDX query")
            return tree

        except UnexpectedToken as e:
            # Extract context information
            line = getattr(e, "line", None)
            column = getattr(e, "column", None)
            context = self._extract_context(mdx_query, line, column)

            raise MDXParseError(
                f"Unexpected token: {e.token}",
                line=line,
                column=column,
                context=context,
                original_error=e
            )

        except UnexpectedInput as e:
            line = getattr(e, "line", None)
            column = getattr(e, "column", None)
            context = self._extract_context(mdx_query, line, column)

            raise MDXParseError(
                f"Unexpected input: {str(e)}",
                line=line,
                column=column,
                context=context,
                original_error=e
            )

        except ParseError as e:
            raise MDXParseError(
                f"Parse error: {str(e)}",
                original_error=e
            )

        except LarkError as e:
            raise MDXParseError(
                f"Lark parser error: {str(e)}",
                original_error=e
            )

        except Exception as e:
            raise MDXParseError(
                f"Unexpected error during parsing: {str(e)}",
                original_error=e
            )

    def parse_file(self, file_path: Path) -> Tree:
        """
        Parse an MDX query from a file.
        
        Args:
            file_path: Path to the MDX file
            
        Returns:
            Lark Tree object representing the parsed query
            
        Raises:
            MDXParseError: If file reading or parsing fails
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            logger.info(f"Parsing MDX file: {file_path}")
            return self.parse(content)

        except FileNotFoundError:
            raise MDXParseError(f"MDX file not found: {file_path}")
        except Exception as e:
            raise MDXParseError(
                f"Failed to read MDX file {file_path}: {e}",
                original_error=e
            )

    def validate_syntax(self, mdx_query: str) -> dict[str, Any]:
        """
        Validate MDX syntax without full parsing.
        
        Args:
            mdx_query: The MDX query string to validate
            
        Returns:
            Dictionary with validation results:
            - valid: bool - Whether syntax is valid
            - errors: List[str] - List of error messages
            - warnings: List[str] - List of warning messages
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }

        try:
            tree = self.parse(mdx_query)
            result["valid"] = True

            # Check for potential issues
            warnings = self._analyze_query_structure(tree)
            result["warnings"] = warnings

        except MDXParseError as e:
            result["errors"].append(str(e))

        return result

    def _clean_query(self, query: str) -> str:
        """
        Clean MDX query for better parsing.
        
        Removes excessive whitespace while preserving structure.
        """
        # Remove leading/trailing whitespace
        query = query.strip()

        # Normalize line endings
        query = query.replace("\r\n", "\n").replace("\r", "\n")

        # Remove empty lines
        lines = [line.rstrip() for line in query.split("\n") if line.strip()]

        return "\n".join(lines)

    def _extract_context(self, query: str, line: int | None, column: int | None) -> str | None:
        """Extract context around the error location."""
        if line is None:
            return None

        lines = query.split("\n")
        if line > len(lines):
            return None

        # Get the line with the error (1-indexed)
        error_line = lines[line - 1] if line > 0 else ""

        # Extract a reasonable context window
        if column is not None and column > 0:
            start = max(0, column - 20)
            end = min(len(error_line), column + 20)
            context = error_line[start:end]

            # Add pointer to exact location
            if column <= len(error_line):
                pointer_pos = column - start - 1
                if 0 <= pointer_pos < len(context):
                    context += "\n" + " " * pointer_pos + "^"

            return context

        return error_line[:50] + "..." if len(error_line) > 50 else error_line

    def _analyze_query_structure(self, tree: Tree) -> list[str]:
        """Analyze parsed tree for potential issues and return warnings."""
        warnings = []

        # Check for deeply nested sets
        max_nesting = self._find_max_nesting(tree)
        if max_nesting > 5:
            warnings.append(f"Deeply nested sets detected (depth: {max_nesting}). Consider simplifying.")

        # Check for redundant constructs
        if self._has_redundant_crossjoins(tree):
            warnings.append("Redundant CrossJoin operations detected. These can be simplified.")

        # Check for empty sets
        if self._has_empty_sets(tree):
            warnings.append("Empty sets detected. These may be removed during optimization.")

        return warnings

    def _find_max_nesting(self, tree: Tree) -> int:
        """Find the maximum nesting depth of sets in the tree."""
        max_depth = 0

        def traverse(node, depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            if isinstance(node, Tree):
                if node.data in ("set_expression", "set_expression_nested"):
                    depth += 1

                for child in node.children:
                    traverse(child, depth)

        traverse(tree)
        return max_depth

    def _has_redundant_crossjoins(self, tree: Tree) -> bool:
        """Check if the tree contains redundant CrossJoin operations."""
        # Simple heuristic: look for nested CrossJoin calls
        def traverse(node):
            if isinstance(node, Tree):
                if node.data == "function_call":
                    # Check if this is a CrossJoin
                    if (node.children and
                        isinstance(node.children[0], Token) and
                        node.children[0].value.upper() == "CROSSJOIN"):

                        # Check if any of the arguments are also CrossJoins
                        for child in node.children[1:]:
                            if self._contains_crossjoin(child):
                                return True

                for child in node.children:
                    if traverse(child):
                        return True
            return False

        return traverse(tree)

    def _contains_crossjoin(self, node) -> bool:
        """Check if a node contains a CrossJoin function."""
        if isinstance(node, Tree):
            if node.data == "function_call":
                if (node.children and
                    isinstance(node.children[0], Token) and
                    node.children[0].value.upper() == "CROSSJOIN"):
                    return True

            for child in node.children:
                if self._contains_crossjoin(child):
                    return True
        return False

    def _has_empty_sets(self, tree: Tree) -> bool:
        """Check if the tree contains empty sets."""
        def traverse(node):
            if isinstance(node, Tree):
                if node.data == "set_expression":
                    # Check if this is an empty set {}
                    if len(node.children) == 0:
                        return True

                for child in node.children:
                    if traverse(child):
                        return True
            return False

        return traverse(tree)


class MDXTreeVisitor:
    """
    Visitor for traversing and debugging MDX parse trees.
    
    Provides utilities for examining the structure of parsed MDX queries.
    """

    def __init__(self, tree: Tree):
        self.tree = tree
        self.logger = get_logger(__name__)

    def print_tree(self, indent: int = 2) -> str:
        """Return a pretty-printed representation of the tree."""
        return self.tree.pretty(indent_str=" " * indent)

    def find_nodes(self, node_type: str) -> list[Tree]:
        """Find all nodes of a specific type in the tree."""
        nodes = []

        def traverse(node):
            if isinstance(node, Tree):
                if node.data == node_type:
                    nodes.append(node)

                for child in node.children:
                    traverse(child)

        traverse(self.tree)
        return nodes

    def extract_measures(self) -> list[str]:
        """Extract all measure names from the tree."""
        measures = []

        # Look for patterns like [Measures].[MeasureName]
        def traverse(node):
            if isinstance(node, Tree):
                if node.data == "qualified_member":
                    # Check if this is a measure reference
                    parts = []
                    for child in node.children:
                        if isinstance(child, Tree) and child.data == "bracketed_identifier":
                            if child.children:
                                parts.append(child.children[0].value)

                    # If we have at least 2 parts and first is "Measures"
                    if len(parts) >= 2 and parts[0].lower() == "measures":
                        measures.append(parts[1])

                for child in node.children:
                    traverse(child)

        traverse(self.tree)
        return list(set(measures))  # Remove duplicates

    def extract_dimensions(self) -> list[dict[str, str]]:
        """Extract dimension information from the tree."""
        dimensions = []

        # Look for dimension references in axis specifications
        axis_nodes = self.find_nodes("axis_specification")

        for axis_node in axis_nodes:
            # Extract set expressions from this axis
            set_nodes = self.find_nodes_in_subtree(axis_node, "set_expression")

            for set_node in set_nodes:
                dim_info = self._extract_dimension_from_set(set_node)
                if dim_info:
                    dimensions.append(dim_info)

        return dimensions

    def find_nodes_in_subtree(self, subtree: Tree, node_type: str) -> list[Tree]:
        """Find nodes of a specific type within a subtree."""
        nodes = []

        def traverse(node):
            if isinstance(node, Tree):
                if node.data == node_type:
                    nodes.append(node)

                for child in node.children:
                    traverse(child)

        traverse(subtree)
        return nodes

    def _extract_dimension_from_set(self, set_node: Tree) -> dict[str, str] | None:
        """Extract dimension information from a set expression."""
        # Look for member expressions that reference dimensions
        member_nodes = self.find_nodes_in_subtree(set_node, "qualified_member")

        for member_node in member_nodes:
            parts = []
            for child in member_node.children:
                if isinstance(child, Tree) and child.data == "bracketed_identifier":
                    if child.children:
                        parts.append(child.children[0].value)

            # If we have dimension.hierarchy or dimension.level patterns
            if len(parts) >= 2:
                return {
                    "dimension": parts[0],
                    "hierarchy": parts[1] if len(parts) > 1 else parts[0],
                    "level": parts[2] if len(parts) > 2 else None
                }

        return None
