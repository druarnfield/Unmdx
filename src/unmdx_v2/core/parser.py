"""
MDX Parser for UnMDX v2 - Lark-based Implementation

This parser uses Lark to provide robust parsing of MDX queries.
It converts parse trees to structured data for DAX generation.
"""

from typing import Dict, List, Optional, Any
import logging

from .lark_parser import LarkMDXParser
from .lark_transformer import transform_parse_tree

logger = logging.getLogger(__name__)


class MDXParseError(Exception):
    """Raised when MDX parsing fails"""
    pass


class LarkBasedMDXParser:
    """
    A Lark-based MDX parser that provides robust parsing.
    
    Supported patterns:
    1. SELECT {[Measures].[MeasureName]} ON 0 FROM [CubeName]
    2. SELECT {[Measures].[MeasureName]} ON COLUMNS, {[Dimension].[Hierarchy].Members} ON ROWS FROM [CubeName]
    3. WHERE clauses with single and multiple filters
    4. Complex nested structures and function calls
    
    Returns a consistent dict structure for downstream processing.
    """
    
    def __init__(self):
        # Initialize the Lark parser
        self.lark_parser = LarkMDXParser()
    
    def parse(self, mdx_query: str) -> Dict[str, Any]:
        """
        Parse an MDX query and return a structured representation.
        
        Args:
            mdx_query: The MDX query string to parse
            
        Returns:
            Dictionary with parsed components:
            {
                "measures": ["MeasureName"],
                "dimensions": [{"table": "Dimension", "column": "Hierarchy", "selection_type": "members"}],
                "cube": "CubeName",
                "where_clause": None
            }
            
        Raises:
            MDXParseError: If the query cannot be parsed
        """
        try:
            # Use Lark to parse the query
            parse_result = self.lark_parser.parse(mdx_query)
            
            if not parse_result.success:
                error_msg = f"Parse failed: {parse_result.error}"
                if parse_result.error_line:
                    error_msg += f" at line {parse_result.error_line}, column {parse_result.error_column}"
                raise MDXParseError(error_msg)
            
            # Transform the parse tree to structured data
            structured_data = transform_parse_tree(parse_result.tree)
            
            logger.debug(f"Parsed MDX query: {structured_data}")
            return structured_data
            
        except MDXParseError:
            # Re-raise parse errors
            raise
        except Exception as e:
            logger.error(f"Failed to parse MDX query: {str(e)}")
            raise MDXParseError(f"Failed to parse MDX query: {str(e)}")
    
    def validate_query(self, mdx_query: str) -> bool:
        """
        Validate if the query can be parsed by this parser.
        
        Args:
            mdx_query: The MDX query to validate
            
        Returns:
            True if the query can be parsed, False otherwise
        """
        try:
            self.parse(mdx_query)
            return True
        except MDXParseError:
            return False
    
    def get_supported_patterns(self) -> List[str]:
        """
        Return a list of supported MDX patterns.
        
        Returns:
            List of pattern descriptions
        """
        return [
            "SELECT {[Measures].[MeasureName]} ON 0 FROM [CubeName]",
            "SELECT {[Measures].[MeasureName]} ON COLUMNS, {[Dimension].[Hierarchy].Members} ON ROWS FROM [CubeName]",
            "Multiple measures in single axis",
            "Mixed measures and dimensions on different axes",
            "WHERE clause with single filter: WHERE ([Dimension].[Hierarchy].&[Key])",
            "WHERE clause with multiple filters: WHERE ([Dim1].[Hier1].&[Key1], [Dim2].[Hier2].&[Key2])",
            "Complex nested structures and function calls",
            "Calculated members with WITH clause",
            "NON EMPTY clauses"
        ]


# Convenience function for Lark-based parsing
def parse_mdx(mdx_query: str) -> Dict[str, Any]:
    """
    Parse an MDX query using the Lark-based parser.
    
    Args:
        mdx_query: The MDX query string to parse
        
    Returns:
        Parsed query structure
        
    Raises:
        MDXParseError: If parsing fails
    """
    parser = LarkBasedMDXParser()
    return parser.parse(mdx_query)


# Test the parser with the required examples
if __name__ == "__main__":
    # Test with the required examples
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
    
    for i, test_query in enumerate(test_queries, 1):
        print(f"\n=== Test Query {i} ===")
        print(f"Query: {test_query[:50]}...")
        
        try:
            result = parse_mdx(test_query)
            print(f"✅ Parsed successfully")
            print(f"  Measures: {result['measures']}")
            print(f"  Dimensions: {result['dimensions']}")
            print(f"  Cube: {result['cube']}")
            if result['where_clause']:
                print(f"  WHERE filters: {result['where_clause']['filters']}")
        except MDXParseError as e:
            print(f"❌ Parse failed: {e}")