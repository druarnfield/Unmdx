"""
Simple MDX Parser for UnMDX v2 - Recovery Implementation

This parser focuses on WORKING functionality over perfect parsing.
It handles the most common MDX patterns using regex-based matching.
"""

import re
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class MDXParseError(Exception):
    """Raised when MDX parsing fails"""
    pass


class SimpleMDXParser:
    """
    A simple, regex-based MDX parser that handles common patterns.
    
    Supported patterns:
    1. SELECT {[Measures].[MeasureName]} ON 0 FROM [CubeName]
    2. SELECT {[Measures].[MeasureName]} ON COLUMNS, {[Dimension].[Hierarchy].Members} ON ROWS FROM [CubeName]
    
    Returns a consistent dict structure for downstream processing.
    """
    
    def __init__(self):
        # Precompile regex patterns for better performance
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Set up regex patterns for MDX parsing"""
        
        # Pattern to match measures: [Measures].[MeasureName]
        self.measure_pattern = re.compile(
            r'\[Measures\]\.\[([^\]]+)\]', 
            re.IGNORECASE
        )
        
        # Pattern to match dimensions: [Dimension].[Hierarchy].Members
        self.dimension_pattern = re.compile(
            r'\[([^\]]+)\]\.\[([^\]]+)\]\.Members', 
            re.IGNORECASE
        )
        
        # Pattern to match cube name: FROM [CubeName]
        self.cube_pattern = re.compile(
            r'FROM\s*\[([^\]]+)\]', 
            re.IGNORECASE
        )
        
        # Pattern to match the main SELECT structure
        self.select_pattern = re.compile(
            r'SELECT\s*(.+?)\s*FROM\s*', 
            re.IGNORECASE | re.DOTALL
        )
        
        # Pattern to split axes (ON 0, ON COLUMNS, ON ROWS)
        # This pattern captures content up to ON, handling nested braces properly
        self.axis_pattern = re.compile(
            r'(\{(?:[^{}]|{[^{}]*})*\})\s+ON\s+(0|COLUMNS|ROWS|1)', 
            re.IGNORECASE
        )
        
        # Alternative pattern for when we need to find multiple axes separated by commas
        self.multi_axis_pattern = re.compile(
            r'(\{(?:[^{}]|{[^{}]*})*\})\s+ON\s+(0|COLUMNS|ROWS|1)(?:\s*,\s*(\{(?:[^{}]|{[^{}]*})*\})\s+ON\s+(0|COLUMNS|ROWS|1))?',
            re.IGNORECASE
        )
    
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
            # Clean up the query
            cleaned_query = self._clean_query(mdx_query)
            
            # Extract cube name
            cube_name = self._extract_cube_name(cleaned_query)
            
            # Extract SELECT portion
            select_portion = self._extract_select_portion(cleaned_query)
            
            # Parse axes
            measures, dimensions = self._parse_axes(select_portion)
            
            # Build result structure
            result = {
                "measures": measures,
                "dimensions": dimensions,
                "cube": cube_name,
                "where_clause": None  # Not implemented yet
            }
            
            logger.debug(f"Parsed MDX query: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse MDX query: {str(e)}")
            raise MDXParseError(f"Failed to parse MDX query: {str(e)}")
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize the MDX query"""
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', query.strip())
        
        # Remove common redundant patterns
        cleaned = re.sub(r'\{\s*\{([^}]+)\}\s*\}', r'{\1}', cleaned)  # Remove nested braces
        cleaned = re.sub(r'\s*,\s*', ', ', cleaned)  # Normalize commas
        
        return cleaned
    
    def _extract_cube_name(self, query: str) -> str:
        """Extract cube name from the query"""
        match = self.cube_pattern.search(query)
        if not match:
            raise MDXParseError("Could not find cube name in query")
        
        return match.group(1)
    
    def _extract_select_portion(self, query: str) -> str:
        """Extract the SELECT portion of the query"""
        match = self.select_pattern.search(query)
        if not match:
            raise MDXParseError("Could not find SELECT portion in query")
        
        return match.group(1)
    
    def _parse_axes(self, select_portion: str) -> tuple[List[str], List[Dict[str, str]]]:
        """Parse axes to extract measures and dimensions"""
        measures = []
        dimensions = []
        
        # Use a more robust approach to find all axes
        # Split by comma first, then process each part
        parts = self._split_axes(select_portion)
        
        for part in parts:
            part = part.strip()
            
            # Check if this part contains an axis specification
            axis_match = re.search(r'(\{.*\})\s+ON\s+(0|COLUMNS|ROWS|1)', part, re.IGNORECASE)
            if axis_match:
                axis_content = axis_match.group(1).strip()
                
                # Check if this axis contains measures
                measure_matches = self.measure_pattern.findall(axis_content)
                if measure_matches:
                    measures.extend(measure_matches)
                
                # Check if this axis contains dimensions
                dimension_matches = self.dimension_pattern.findall(axis_content)
                for table, column in dimension_matches:
                    dimensions.append({
                        "table": table,
                        "column": column,
                        "selection_type": "members"
                    })
        
        # If no measures found yet, search the entire select portion
        if not measures:
            # Look for all measures in the entire select portion
            all_measures = self.measure_pattern.findall(select_portion)
            if all_measures:
                measures.extend(all_measures)
        
        return measures, dimensions
    
    def _split_axes(self, select_portion: str) -> List[str]:
        """Split the select portion into individual axes, handling nested braces"""
        parts = []
        current_part = ""
        brace_count = 0
        
        i = 0
        while i < len(select_portion):
            char = select_portion[i]
            
            if char == '{':
                brace_count += 1
                current_part += char
            elif char == '}':
                brace_count -= 1
                current_part += char
            elif char == ',' and brace_count == 0:
                # We're at a top-level comma, split here
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
            
            i += 1
        
        # Add the last part
        if current_part.strip():
            parts.append(current_part.strip())
        
        return parts
    
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
            "Mixed measures and dimensions on different axes"
        ]


# Convenience function for simple parsing
def parse_mdx(mdx_query: str) -> Dict[str, Any]:
    """
    Parse an MDX query using the simple parser.
    
    Args:
        mdx_query: The MDX query string to parse
        
    Returns:
        Parsed query structure
        
    Raises:
        MDXParseError: If parsing fails
    """
    parser = SimpleMDXParser()
    return parser.parse(mdx_query)


# Test the parser with the required example
if __name__ == "__main__":
    # Test with the required example
    test_query = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
    
    try:
        result = parse_mdx(test_query)
        print(f"Parsed successfully: {result}")
    except MDXParseError as e:
        print(f"Parse failed: {e}")