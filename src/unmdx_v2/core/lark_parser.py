"""
Minimal Lark-based MDX parser for UnMDX v2.
Focused on correctness and extensibility for Test Cases 1-9.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from lark import Lark, Tree, Token
from lark.exceptions import ParseError, UnexpectedCharacters, UnexpectedToken


@dataclass
class ParseResult:
    """Result from parsing MDX query."""
    success: bool
    tree: Optional[Tree] = None
    error: Optional[str] = None
    error_line: Optional[int] = None
    error_column: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility."""
        return {
            'success': self.success,
            'tree': self.tree,
            'error': self.error,
            'error_line': self.error_line,
            'error_column': self.error_column
        }


class LarkMDXParser:
    """Lark-based MDX parser with focus on extensibility."""
    
    def __init__(self, grammar_file: Optional[str] = None):
        """Initialize the parser with the grammar file."""
        if grammar_file is None:
            # Default to grammar in same directory
            current_dir = Path(__file__).parent
            grammar_file = current_dir / "mdx_grammar_v2.lark"
        
        if not Path(grammar_file).exists():
            raise FileNotFoundError(f"Grammar file not found: {grammar_file}")
        
        # Read the grammar
        with open(grammar_file, 'r') as f:
            grammar = f.read()
        
        # Initialize Lark parser
        # Using LALR for better performance and error messages
        try:
            self.parser = Lark(
                grammar,
                parser='lalr',
                propagate_positions=True,  # For better error reporting
                maybe_placeholders=True,   # Handle optional elements better
                cache=True                  # Enable cache for production
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Lark parser: {e}")
    
    def parse(self, mdx_query: str) -> ParseResult:
        """
        Parse an MDX query and return a parse tree.
        
        Args:
            mdx_query: The MDX query string to parse
            
        Returns:
            ParseResult with tree or error information
        """
        try:
            # Normalize the query slightly (but preserve structure)
            mdx_query = mdx_query.strip()
            
            # Parse the query
            tree = self.parser.parse(mdx_query)
            
            return ParseResult(
                success=True,
                tree=tree
            )
            
        except UnexpectedCharacters as e:
            # Handle unexpected character errors
            return ParseResult(
                success=False,
                error=f"Unexpected character at position {e.pos_in_stream}: '{e.char}'",
                error_line=e.line,
                error_column=e.column
            )
            
        except UnexpectedToken as e:
            # Handle unexpected token errors
            expected = ', '.join(e.expected) if e.expected else 'valid token'
            return ParseResult(
                success=False,
                error=f"Expected {expected} but got '{e.token}' at line {e.line}, column {e.column}",
                error_line=e.line,
                error_column=e.column
            )
            
        except ParseError as e:
            # General parse error
            return ParseResult(
                success=False,
                error=str(e)
            )
            
        except Exception as e:
            # Catch-all for unexpected errors
            return ParseResult(
                success=False,
                error=f"Unexpected error during parsing: {str(e)}"
            )
    
    def pretty_print_tree(self, tree: Tree, indent: int = 0) -> str:
        """Pretty print the parse tree for debugging."""
        lines = []
        prefix = "  " * indent
        
        if isinstance(tree, Tree):
            lines.append(f"{prefix}{tree.data}")
            for child in tree.children:
                lines.append(self.pretty_print_tree(child, indent + 1))
        elif isinstance(tree, Token):
            lines.append(f"{prefix}{tree.type}: {tree.value!r}")
        else:
            lines.append(f"{prefix}{repr(tree)}")
        
        return "\n".join(lines)
    
    def extract_components(self, tree: Tree) -> Dict[str, Any]:
        """
        Extract key components from the parse tree.
        This is a helper for the transformer.
        """
        components = {
            'measures': [],
            'dimensions': [],
            'cube': None,
            'where_filters': [],
            'calculated_members': []
        }
        
        # Walk the tree to extract components
        self._extract_from_tree(tree, components)
        
        return components
    
    def _extract_from_tree(self, node: Any, components: Dict[str, Any]):
        """Recursively extract components from parse tree."""
        if isinstance(node, Tree):
            # Handle different node types
            if node.data == 'cube_name':
                # Extract cube name
                if node.children:
                    components['cube'] = self._get_text(node.children[0])
            
            elif node.data == 'member_expr':
                # Could be a measure or dimension depending on context
                path = self._extract_member_expr(node)
                if path and '[Measures]' in path:
                    components['measures'].append(path)
                elif path:
                    components['dimensions'].append(path)
            
            elif node.data == 'where_clause':
                # Extract WHERE filters
                filters = self._extract_where_filters(node)
                components['where_filters'].extend(filters)
            
            elif node.data == 'member_def':
                # Extract calculated member
                calc_member = self._extract_calculated_member(node)
                if calc_member:
                    components['calculated_members'].append(calc_member)
            
            # Recurse for all children
            for child in node.children:
                self._extract_from_tree(child, components)
    
    def _extract_member_expr(self, node: Tree) -> Optional[str]:
        """Extract a member expression which may include functions."""
        if not isinstance(node, Tree) or node.data != 'member_expr':
            return None
        
        parts = []
        
        # First child should be the initial bracketed name
        if node.children and node.children[0].data == 'bracketed_name':
            parts.append(self._get_text(node.children[0]))
            
            # Then process the tails
            for child in node.children[1:]:
                if child.data == 'name_tail':
                    # This is a .name part
                    for sub_child in child.children:
                        if sub_child.data == 'bracketed_name':
                            parts.append(self._get_text(sub_child))
                elif child.data == 'members_tail':
                    # This is a .Members part
                    parts.append('Members')
                elif child.data == 'children_tail':
                    # This is a .Children part
                    parts.append('Children')
                elif child.data == 'key_tail':
                    # This is a .&[value] part
                    for sub_child in child.children:
                        if sub_child.data == 'bracketed_name':
                            parts.append(f'&{self._get_text(sub_child)}')
        
        return '.'.join(parts) if parts else None
    
    def _extract_qualified_name(self, node: Tree) -> str:
        """Extract a qualified name like [Product].[Category]."""
        if not isinstance(node, Tree) or node.data != 'qualified_name':
            return ''
        
        parts = []
        for child in node.children:
            if child.data == 'bracketed_name':
                parts.append(self._get_text(child))
        
        return '.'.join(parts)
    
    def _extract_where_filters(self, where_node: Tree) -> List[Dict[str, Any]]:
        """Extract filters from WHERE clause."""
        filters = []
        
        # Find the where_expr
        for child in where_node.children:
            if isinstance(child, Tree) and child.data == 'where_expr':
                # Handle tuple expressions (multiple filters)
                if child.children and child.children[0].data == 'tuple_expr':
                    tuple_node = child.children[0]
                    for member_node in tuple_node.children:
                        if isinstance(member_node, Tree) and member_node.data == 'member_or_key':
                            filter_info = self._extract_filter_info(member_node)
                            if filter_info:
                                filters.append(filter_info)
                # Handle single filter
                elif child.children and child.children[0].data == 'member_or_key':
                    filter_info = self._extract_filter_info(child.children[0])
                    if filter_info:
                        filters.append(filter_info)
        
        return filters
    
    def _extract_filter_info(self, member_or_key_node: Tree) -> Optional[Dict[str, Any]]:
        """Extract filter information from a member_or_key node."""
        if not isinstance(member_or_key_node, Tree):
            return None
        
        # Now the key is embedded in the member_expr
        for child in member_or_key_node.children:
            if child.data == 'member_expr':
                member_path = self._extract_member_expr(child)
                if member_path:
                    # Check if it has a key reference (ends with &[value])
                    if '.&' in member_path:
                        # Split the path and key
                        parts = member_path.rsplit('.&', 1)
                        if len(parts) == 2:
                            path = parts[0]
                            key_value = parts[1]
                            return {
                                'path': path,
                                'value': key_value
                            }
                    else:
                        # No key reference
                        return {
                            'path': member_path,
                            'value': None
                        }
        
        return None
    
    def _extract_calculated_member(self, member_def_node: Tree) -> Optional[Dict[str, Any]]:
        """Extract calculated member definition."""
        if not isinstance(member_def_node, Tree) or member_def_node.data != 'member_def':
            return None
        
        name = None
        expression = None
        
        for i, child in enumerate(member_def_node.children):
            if child.data == 'member_expr' and i == 1:  # After MEMBER keyword
                name = self._extract_member_expr(child)
            elif child.data in ['expression', 'arithmetic_expr'] and i > 2:  # After AS
                expression = self._get_text(child)
        
        if name and expression:
            return {
                'name': name,
                'expression': expression
            }
        
        return None
    
    def _get_text(self, node: Any) -> str:
        """Get the text content of a node."""
        if isinstance(node, Token):
            return str(node.value)
        elif isinstance(node, Tree):
            # Reconstruct text from all tokens
            tokens = []
            for child in node.children:
                tokens.append(self._get_text(child))
            return ''.join(tokens)
        else:
            return str(node)
    
    def _get_bracketed_content(self, node: Tree) -> str:
        """Get content inside brackets, e.g., [2023] -> 2023."""
        if not isinstance(node, Tree) or node.data != 'bracketed_name':
            return ''
        
        for child in node.children:
            if isinstance(child, Token) and child.type == 'name_content':
                return str(child.value).strip()
        
        return ''


# Main API function for compatibility
def parse_mdx(mdx_query: str) -> Dict[str, Any]:
    """
    Parse an MDX query using Lark parser.
    
    Args:
        mdx_query: The MDX query string
        
    Returns:
        Dictionary with parsing results
    """
    parser = LarkMDXParser()
    result = parser.parse(mdx_query)
    
    if result.success:
        # Extract components for the transformer
        components = parser.extract_components(result.tree)
        
        return {
            'success': True,
            'parse_tree': result.tree,
            'components': components,
            'pretty_tree': parser.pretty_print_tree(result.tree)
        }
    else:
        return {
            'success': False,
            'error': result.error,
            'error_line': result.error_line,
            'error_column': result.error_column
        }


if __name__ == "__main__":
    # Test the parser with some examples
    test_queries = [
        # Test Case 1
        "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]",
        
        # Test Case 2 (messy spacing)
        """SELECT{[Measures].[Sales Amount]}ON COLUMNS,
     {[Product].[Category].Members}    ON    ROWS
FROM    [Adventure Works]""",
        
        # Test Case 4 (WHERE clause)
        """SELECT {[Measures].[Sales Amount]} ON COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].&[2023])""",
        
        # Test Case 9 (multiple filters)
        """SELECT{[Measures].[Sales Amount]}ON COLUMNS,
{[Product].[Category].Members}ON ROWS
FROM[Adventure Works]
WHERE([Date].[Calendar Year].&[2023],[Geography].[Country].&[United States])"""
    ]
    
    parser = LarkMDXParser()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test Query {i}:")
        print(f"{'='*60}")
        print(f"Query: {query[:100]}...")
        
        result = parser.parse(query)
        
        if result.success:
            print("✅ Parse successful!")
            print("\nParse tree:")
            print(parser.pretty_print_tree(result.tree))
            
            print("\nExtracted components:")
            components = parser.extract_components(result.tree)
            for key, value in components.items():
                if value:
                    print(f"  {key}: {value}")
        else:
            print(f"❌ Parse failed: {result.error}")
            if result.error_line:
                print(f"   Line: {result.error_line}, Column: {result.error_column}")