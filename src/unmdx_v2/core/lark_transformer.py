"""
Lark Transformer for UnMDX v2.
Converts Lark parse trees to structured data for DAX generation.
"""

from typing import Dict, List, Optional, Any, Union
from lark import Transformer, Tree, Token
import logging

logger = logging.getLogger(__name__)


class MDXTransformer(Transformer):
    """
    Transforms Lark parse trees into structured data for DAX generation.
    
    Expected output format:
    {
        "measures": ["Sales Amount"],
        "dimensions": [{"table": "Product", "column": "Category", "selection_type": "members"}],
        "cube": "Adventure Works",
        "where_clause": {
            "filters": [
                {"table": "Date", "column": "Calendar Year", "operator": "=", "value": 2023}
            ]
        }
    }
    """
    
    def __init__(self):
        super().__init__()
        self.measures = []
        self.dimensions = []
        self.cube = None
        self.where_filters = []
        self.calculated_members = []
    
    def start(self, items):
        """Main entry point - return the final structured data"""
        return {
            "measures": self.measures,
            "dimensions": self.dimensions,
            "cube": self.cube,
            "where_clause": {"filters": self.where_filters} if self.where_filters else None
        }
    
    def query(self, items):
        """Process main query structure"""
        # Items can be [with_clause, select_statement] or just [select_statement]
        for item in items:
            if hasattr(item, 'data') and item.data == 'with_clause':
                self._process_with_clause(item)
            elif hasattr(item, 'data') and item.data == 'select_statement':
                self._process_select_statement(item)
        
        return items
    
    def select_statement(self, items):
        """Process SELECT statement - extract axis specs, cube, and WHERE clause"""
        # Items: [axis_spec, axis_spec, ..., cube_name, where_clause?]
        for item in items:
            if hasattr(item, 'data'):
                if item.data == 'axis_spec':
                    self._process_axis_spec(item)
                elif item.data == 'cube_name':
                    self._process_cube_name(item)
                elif item.data == 'where_clause':
                    self._process_where_clause(item)
        
        return items
    
    def _process_axis_spec(self, axis_spec):
        """Process axis specification to extract measures and dimensions"""
        # axis_spec: [non_empty?, set_expr, axis_id]
        set_expr = None
        axis_id = None
        
        for child in axis_spec.children:
            if hasattr(child, 'data'):
                if child.data == 'explicit_set':
                    set_expr = child
                elif child.data == 'implicit_set':
                    set_expr = child
                elif child.data == 'function_call':
                    set_expr = child
                elif child.data.startswith('axis_'):
                    axis_id = child
        
        if set_expr:
            self._process_set_expr(set_expr)
    
    def _process_set_expr(self, set_expr):
        """Process set expression to extract measures and dimensions"""
        if set_expr.data == 'explicit_set':
            # Process contents of {  }
            for child in set_expr.children:
                if child and hasattr(child, 'data') and child.data == 'set_items':
                    self._process_set_items(child)
        elif set_expr.data == 'implicit_set':
            # Single member expression
            for child in set_expr.children:
                if hasattr(child, 'data') and child.data == 'member_expr':
                    self._process_member_expr(child)
        elif set_expr.data == 'function_call':
            # Function call like CROSSJOIN
            self._process_function_call(set_expr)
    
    def _process_set_items(self, set_items):
        """Process set items inside { }"""
        for child in set_items.children:
            if hasattr(child, 'data'):
                if child.data == 'member_item':
                    # Single member
                    for grandchild in child.children:
                        if hasattr(grandchild, 'data') and grandchild.data == 'member_expr':
                            self._process_member_expr(grandchild)
                elif child.data == 'nested_set':
                    # Nested set like { { ... } }
                    self._process_set_expr(child)
                elif child.data == 'tuple_item':
                    # Tuple expression (shouldn't happen in SELECT but just in case)
                    self._process_tuple_expr(child)
    
    def _process_member_expr(self, member_expr):
        """Process member expression to determine if it's a measure or dimension"""
        # member_expr: [bracketed_name, member_tail*]
        path_parts = []
        
        for child in member_expr.children:
            if hasattr(child, 'data'):
                if child.data == 'bracketed_name':
                    content = self._get_bracketed_content(child)
                    path_parts.append(content)
                elif child.data == 'name_tail':
                    # .name
                    for grandchild in child.children:
                        if hasattr(grandchild, 'data') and grandchild.data == 'bracketed_name':
                            content = self._get_bracketed_content(grandchild)
                            path_parts.append(content)
                elif child.data == 'members_tail':
                    # .Members
                    path_parts.append('Members')
                elif child.data == 'children_tail':
                    # .Children
                    path_parts.append('Children')
                elif child.data == 'key_tail':
                    # .&[value]
                    for grandchild in child.children:
                        if hasattr(grandchild, 'data') and grandchild.data == 'bracketed_name':
                            content = self._get_bracketed_content(grandchild)
                            path_parts.append(f'&{content}')
        
        # Reconstruct the path
        if path_parts:
            full_path = '.'.join(path_parts)
            
            # Check if it's a measure
            if path_parts[0] == 'Measures' and len(path_parts) >= 2:
                measure_name = path_parts[1]
                if measure_name not in self.measures:
                    self.measures.append(measure_name)
            
            # Check if it's a dimension with .Members
            elif len(path_parts) >= 3 and path_parts[-1] == 'Members':
                table = path_parts[0]
                column = path_parts[1]
                
                # Check if we already have this dimension
                existing = next((d for d in self.dimensions if d['table'] == table and d['column'] == column), None)
                if not existing:
                    self.dimensions.append({
                        "table": table,
                        "column": column,
                        "selection_type": "members"
                    })
    
    def _process_function_call(self, function_call):
        """Process function calls like CROSSJOIN"""
        # For now, just extract members from the arguments
        for child in function_call.children:
            if hasattr(child, 'data') and child.data == 'function_args':
                self._process_function_args(child)
    
    def _process_function_args(self, function_args):
        """Process function arguments"""
        for child in function_args.children:
            if hasattr(child, 'data'):
                if child.data == 'set_arg':
                    # Set argument { ... }
                    self._process_set_expr(child)
                elif child.data == 'member_arg':
                    # Member argument
                    for grandchild in child.children:
                        if hasattr(grandchild, 'data') and grandchild.data == 'member_expr':
                            self._process_member_expr(grandchild)
    
    def _process_cube_name(self, cube_name):
        """Process cube name"""
        for child in cube_name.children:
            if hasattr(child, 'data'):
                if child.data == 'bracketed_name':
                    self.cube = self._get_bracketed_content(child)
                elif isinstance(child, Token) and child.type == 'identifier':
                    self.cube = str(child.value)
    
    def _process_where_clause(self, where_clause):
        """Process WHERE clause"""
        for child in where_clause.children:
            if hasattr(child, 'data') and child.data == 'where_expr':
                self._process_where_expr(child)
    
    def _process_where_expr(self, where_expr):
        """Process WHERE expression"""
        for child in where_expr.children:
            if hasattr(child, 'data'):
                if child.data == 'tuple_expr':
                    self._process_tuple_expr(child)
                elif child.data == 'member_expr':
                    # Single member in WHERE
                    filter_info = self._extract_filter_from_member(child)
                    if filter_info:
                        self.where_filters.append(filter_info)
    
    def _process_tuple_expr(self, tuple_expr):
        """Process tuple expression for multiple filters"""
        for child in tuple_expr.children:
            if hasattr(child, 'data') and child.data == 'member_or_key':
                self._process_member_or_key(child)
    
    def _process_member_or_key(self, member_or_key):
        """Process member or key in WHERE clause"""
        for child in member_or_key.children:
            if hasattr(child, 'data') and child.data == 'member_expr':
                filter_info = self._extract_filter_from_member(child)
                if filter_info:
                    self.where_filters.append(filter_info)
    
    def _extract_filter_from_member(self, member_expr):
        """Extract filter information from member expression"""
        path_parts = []
        key_value = None
        
        for child in member_expr.children:
            if hasattr(child, 'data'):
                if child.data == 'bracketed_name':
                    content = self._get_bracketed_content(child)
                    path_parts.append(content)
                elif child.data == 'name_tail':
                    for grandchild in child.children:
                        if hasattr(grandchild, 'data') and grandchild.data == 'bracketed_name':
                            content = self._get_bracketed_content(grandchild)
                            path_parts.append(content)
                elif child.data == 'key_tail':
                    # .&[value] - this is the filter value
                    for grandchild in child.children:
                        if hasattr(grandchild, 'data') and grandchild.data == 'bracketed_name':
                            key_value = self._get_bracketed_content(grandchild)
        
        if len(path_parts) >= 2 and key_value is not None:
            table = path_parts[0]
            column = path_parts[1]
            
            # Try to convert key_value to appropriate type
            typed_value = self._convert_value_type(key_value)
            
            return {
                "table": table,
                "column": column,
                "operator": "=",
                "value": typed_value
            }
        
        return None
    
    def _process_with_clause(self, with_clause):
        """Process WITH clause for calculated members"""
        # For now, just note that we have calculated members
        # Full implementation would extract the calculated member definitions
        pass
    
    def _get_bracketed_content(self, bracketed_name):
        """Extract content from bracketed name"""
        for child in bracketed_name.children:
            if isinstance(child, Token) and child.type == 'name_content':
                return str(child.value).strip()
        return ""
    
    def _convert_value_type(self, value_str):
        """Convert string value to appropriate type"""
        # Try to convert to int
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Keep as string
        return value_str


def transform_parse_tree(parse_tree: Tree) -> Dict[str, Any]:
    """
    Transform a Lark parse tree into structured data for DAX generation.
    
    Args:
        parse_tree: Lark parse tree from MDX parser
        
    Returns:
        Dictionary with structured MDX data
    """
    # Use a custom tree walking approach instead of the Transformer base class
    # This gives us more control over the processing
    
    measures = []
    dimensions = []
    cube = None
    where_filters = []
    
    def walk_tree(node):
        nonlocal measures, dimensions, cube, where_filters
        
        if isinstance(node, Tree):
            # Process different node types
            if node.data == 'cube_name':
                cube = extract_cube_name(node)
            elif node.data == 'member_expr':
                process_member_expr(node)
            elif node.data == 'where_clause':
                process_where_clause(node)
            
            # Recursively walk children
            for child in node.children:
                walk_tree(child)
    
    def extract_cube_name(cube_node):
        """Extract cube name from cube_name node"""
        for child in cube_node.children:
            if isinstance(child, Tree) and child.data == 'bracketed_name':
                return get_bracketed_content(child)
        return None
    
    def process_member_expr(member_node):
        """Process member expression to extract measures and dimensions"""
        path_parts = []
        
        for child in member_node.children:
            if isinstance(child, Tree):
                if child.data == 'bracketed_name':
                    content = get_bracketed_content(child)
                    path_parts.append(content)
                elif child.data == 'name_tail':
                    # .name part
                    for grandchild in child.children:
                        if isinstance(grandchild, Tree) and grandchild.data == 'bracketed_name':
                            content = get_bracketed_content(grandchild)
                            path_parts.append(content)
                elif child.data == 'members_tail':
                    path_parts.append('Members')
                elif child.data == 'children_tail':
                    path_parts.append('Children')
                elif child.data == 'key_tail':
                    # .&[value] part
                    for grandchild in child.children:
                        if isinstance(grandchild, Tree) and grandchild.data == 'bracketed_name':
                            content = get_bracketed_content(grandchild)
                            path_parts.append(f'&{content}')
        
        # Process the path
        if path_parts:
            # Check if it's a measure
            if path_parts[0] == 'Measures' and len(path_parts) >= 2:
                measure_name = path_parts[1]
                if measure_name not in measures:
                    measures.append(measure_name)
            
            # Check if it's a dimension with .Members
            elif len(path_parts) >= 3 and path_parts[-1] == 'Members':
                table = path_parts[0]
                column = path_parts[1]
                
                # Check if we already have this dimension
                existing = next((d for d in dimensions if d['table'] == table and d['column'] == column), None)
                if not existing:
                    dimensions.append({
                        "table": table,
                        "column": column,
                        "selection_type": "members"
                    })
    
    def process_where_clause(where_node):
        """Process WHERE clause to extract filters"""
        def extract_filter_from_member(member_node):
            """Extract filter information from member expression"""
            path_parts = []
            key_value = None
            
            for child in member_node.children:
                if isinstance(child, Tree):
                    if child.data == 'bracketed_name':
                        content = get_bracketed_content(child)
                        path_parts.append(content)
                    elif child.data == 'name_tail':
                        for grandchild in child.children:
                            if isinstance(grandchild, Tree) and grandchild.data == 'bracketed_name':
                                content = get_bracketed_content(grandchild)
                                path_parts.append(content)
                    elif child.data == 'key_tail':
                        # .&[value] - this is the filter value
                        for grandchild in child.children:
                            if isinstance(grandchild, Tree) and grandchild.data == 'bracketed_name':
                                key_value = get_bracketed_content(grandchild)
            
            if len(path_parts) >= 2 and key_value is not None:
                table = path_parts[0]
                column = path_parts[1]
                
                # Try to convert key_value to appropriate type
                typed_value = convert_value_type(key_value)
                
                return {
                    "table": table,
                    "column": column,
                    "operator": "=",
                    "value": typed_value
                }
            
            return None
        
        # Walk the WHERE clause looking for member expressions
        def walk_where(node):
            if isinstance(node, Tree):
                if node.data == 'member_expr':
                    filter_info = extract_filter_from_member(node)
                    if filter_info:
                        where_filters.append(filter_info)
                
                # Recurse
                for child in node.children:
                    walk_where(child)
        
        walk_where(where_node)
    
    def get_bracketed_content(bracketed_node):
        """Extract content from bracketed name"""
        for child in bracketed_node.children:
            if isinstance(child, Tree) and child.data == 'name_content':
                # The content is in the child of name_content
                for grandchild in child.children:
                    if isinstance(grandchild, Token):
                        return str(grandchild.value).strip()
            elif isinstance(child, Token):
                # Direct token - might be the content
                return str(child.value).strip()
        return ""
    
    def convert_value_type(value_str):
        """Convert string value to appropriate type"""
        # Try to convert to int
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Keep as string
        return value_str
    
    # Walk the entire tree
    walk_tree(parse_tree)
    
    # Return the structured data
    return {
        "measures": measures,
        "dimensions": dimensions,
        "cube": cube,
        "where_clause": {"filters": where_filters} if where_filters else None
    }


if __name__ == "__main__":
    # Test with sample parse tree (would need actual parsing)
    from lark_parser import LarkMDXParser
    
    test_queries = [
        "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]",
        
        """SELECT {[Measures].[Sales Amount]} ON COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]""",
        
        """SELECT {[Measures].[Sales Amount]} ON COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].&[2023])""",
        
        """SELECT {[Measures].[Sales Amount]} ON COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].&[2023], [Geography].[Country].&[United States])"""
    ]
    
    parser = LarkMDXParser()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n=== Test Query {i} ===")
        print(f"Query: {query}")
        
        # Parse the query
        result = parser.parse(query)
        
        if result.success:
            print("✅ Parse successful")
            
            # Transform the parse tree
            structured_data = transform_parse_tree(result.tree)
            
            print("Structured data:")
            for key, value in structured_data.items():
                if value:
                    print(f"  {key}: {value}")
        else:
            print(f"❌ Parse failed: {result.error}")