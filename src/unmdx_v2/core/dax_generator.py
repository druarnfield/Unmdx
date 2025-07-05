"""
Simple DAX Generator for UnMDX v2 - Recovery Implementation

This DAX generator focuses on WORKING functionality for basic test cases.
It converts parsed MDX structures into clean DAX queries.
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DAXGenerationError(Exception):
    """Raised when DAX generation fails"""
    pass


class SimpleDAXGenerator:
    """
    A simple DAX generator that converts parsed MDX structures to DAX queries.
    
    Handles the patterns needed for Test Cases 1-3:
    1. Measures only: EVALUATE\n{ [MeasureName] }
    2. Measures + Dimensions: EVALUATE\nSUMMARIZECOLUMNS(...)
    3. Multiple measures: Include all measures in SUMMARIZECOLUMNS
    """
    
    def __init__(self):
        pass
    
    def generate(self, parsed_mdx: Dict[str, Any]) -> str:
        """
        Generate DAX query from parsed MDX structure.
        
        Args:
            parsed_mdx: Dictionary with parsed MDX components:
                {
                    "measures": ["Sales Amount"],
                    "dimensions": [{"table": "Product", "column": "Category", "selection_type": "members"}],
                    "cube": "Adventure Works",
                    "where_clause": None
                }
                
        Returns:
            DAX query string
            
        Raises:
            DAXGenerationError: If DAX generation fails
        """
        try:
            measures = parsed_mdx.get("measures", [])
            dimensions = parsed_mdx.get("dimensions", [])
            
            if not measures:
                raise DAXGenerationError("No measures found in parsed MDX")
            
            # Case 1: Measures only (no dimensions)
            if not dimensions:
                return self._generate_measures_only(measures)
            
            # Case 2 & 3: Measures with dimensions
            return self._generate_with_dimensions(measures, dimensions)
            
        except Exception as e:
            logger.error(f"Failed to generate DAX: {str(e)}")
            raise DAXGenerationError(f"Failed to generate DAX: {str(e)}")
    
    def _generate_measures_only(self, measures: List[str]) -> str:
        """
        Generate DAX for measures-only queries.
        
        Format: EVALUATE\n{ [MeasureName] }
        Multiple measures: EVALUATE\n{ [Measure1], [Measure2] }
        """
        if len(measures) == 1:
            return f"EVALUATE\n{{ [{measures[0]}] }}"
        else:
            measure_list = ", ".join(f"[{measure}]" for measure in measures)
            return f"EVALUATE\n{{ {measure_list} }}"
    
    def _generate_with_dimensions(self, measures: List[str], dimensions: List[Dict[str, str]]) -> str:
        """
        Generate DAX for queries with dimensions.
        
        Format: 
        EVALUATE
        SUMMARIZECOLUMNS(
            Table[Column],
            "MeasureName", [MeasureName]
        )
        """
        dax_parts = ["EVALUATE", "SUMMARIZECOLUMNS("]
        
        # Add dimensions
        for dimension in dimensions:
            table = dimension["table"]
            column = dimension["column"]
            
            # Handle special cases for table names with spaces or reserved words
            # Quote table names that contain spaces, or are reserved words like 'Date'
            if " " in table or table.lower() in ["date", "time"]:
                table_ref = f"'{table}'[{column}]"
            else:
                table_ref = f"{table}[{column}]"
            
            dax_parts.append(f"    {table_ref},")
        
        # Add measures
        for measure in measures:
            dax_parts.append(f'    "{measure}", [{measure}],')
        
        # Remove the last comma and close the function
        if dax_parts[-1].endswith(","):
            dax_parts[-1] = dax_parts[-1][:-1]
        
        dax_parts.append(")")
        
        return "\n".join(dax_parts)


# Convenience function for simple DAX generation
def generate_dax(parsed_mdx: Dict[str, Any]) -> str:
    """
    Generate DAX query from parsed MDX structure.
    
    Args:
        parsed_mdx: Parsed MDX structure from the parser
        
    Returns:
        DAX query string
        
    Raises:
        DAXGenerationError: If generation fails
    """
    generator = SimpleDAXGenerator()
    return generator.generate(parsed_mdx)


# Test the generator with the required examples
if __name__ == "__main__":
    # Test Case 1: Simple measure
    test_case_1 = {
        "measures": ["Sales Amount"],
        "dimensions": [],
        "cube": "Adventure Works",
        "where_clause": None
    }
    
    # Test Case 2: Measure with dimension
    test_case_2 = {
        "measures": ["Sales Amount"],
        "dimensions": [{"table": "Product", "column": "Category", "selection_type": "members"}],
        "cube": "Adventure Works",
        "where_clause": None
    }
    
    # Test Case 3: Multiple measures with dimension
    test_case_3 = {
        "measures": ["Sales Amount", "Order Quantity"],
        "dimensions": [{"table": "Date", "column": "Calendar Year", "selection_type": "members"}],
        "cube": "Adventure Works",
        "where_clause": None
    }
    
    print("=== DAX Generator Tests ===")
    
    try:
        # Test Case 1
        dax_1 = generate_dax(test_case_1)
        print(f"Test Case 1 DAX:\n{dax_1}")
        expected_1 = "EVALUATE\n{ [Sales Amount] }"
        print(f"Expected: {expected_1}")
        print(f"Match: {dax_1 == expected_1}")
        print()
        
        # Test Case 2
        dax_2 = generate_dax(test_case_2)
        print(f"Test Case 2 DAX:\n{dax_2}")
        expected_2 = """EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)"""
        print(f"Expected:\n{expected_2}")
        print(f"Match: {dax_2 == expected_2}")
        print()
        
        # Test Case 3
        dax_3 = generate_dax(test_case_3)
        print(f"Test Case 3 DAX:\n{dax_3}")
        expected_3 = """EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Calendar Year],
    "Sales Amount", [Sales Amount],
    "Order Quantity", [Order Quantity]
)"""
        print(f"Expected:\n{expected_3}")
        print(f"Match: {dax_3 == expected_3}")
        
    except DAXGenerationError as e:
        print(f"Generation failed: {e}")