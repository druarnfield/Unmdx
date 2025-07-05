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
                    "where_clause": {
                        "filters": [
                            {"table": "Date", "column": "Calendar Year", "operator": "=", "value": 2023},
                            {"table": "Geography", "column": "Country", "operator": "=", "value": "United States"}
                        ]
                    }
                }
                
        Returns:
            DAX query string
            
        Raises:
            DAXGenerationError: If DAX generation fails
        """
        try:
            measures = parsed_mdx.get("measures", [])
            dimensions = parsed_mdx.get("dimensions", [])
            where_clause = parsed_mdx.get("where_clause")
            
            if not measures:
                raise DAXGenerationError("No measures found in parsed MDX")
            
            # Case 1: Measures only (no dimensions)
            if not dimensions:
                base_query = self._generate_measures_only(measures)
                # For measures-only queries, we still need to handle WHERE filters
                if where_clause and where_clause.get("filters"):
                    return self._wrap_with_calculatetable(base_query, where_clause.get("filters"))
                return base_query
            
            # Case 2 & 3: Measures with dimensions
            base_query = self._generate_with_dimensions(measures, dimensions)
            
            # Check if any dimension needs specific member filtering
            specific_filters = self._extract_specific_member_filters(dimensions)
            
            # Combine WHERE clause filters with specific member filters
            all_filters = []
            if where_clause and where_clause.get("filters"):
                all_filters.extend(where_clause.get("filters"))
            if specific_filters:
                all_filters.extend(specific_filters)
            
            # If there are any filters, wrap with CALCULATETABLE
            if all_filters:
                return self._wrap_with_calculatetable(base_query, all_filters)
            
            return base_query
            
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
        
        # Add dimensions (only include those that need to be in SUMMARIZECOLUMNS)
        for dimension in dimensions:
            table = dimension["table"]
            column = dimension["column"]
            
            # Skip specific member dimensions - they will be handled as filters
            if dimension.get("selection_type") == "specific":
                continue
            
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
    
    def _wrap_with_calculatetable(self, base_query: str, filters: List[Dict[str, Any]]) -> str:
        """
        Wrap a base query with CALCULATETABLE to apply WHERE clause filters.
        
        Args:
            base_query: The base DAX query (EVALUATE with SUMMARIZECOLUMNS or measures)
            filters: List of filter dictionaries with table, column, operator, and value
            
        Returns:
            DAX query wrapped with CALCULATETABLE
        """
        # For measures-only queries, we need to handle them differently
        if base_query.startswith("EVALUATE\n{"):
            # Measures-only queries need special handling
            # Extract the measure expression
            measure_expr = base_query.replace("EVALUATE\n", "")
            
            # Generate filter expressions
            filter_expressions = []
            for filter_item in filters:
                filter_expr = self._generate_filter_expression(filter_item)
                filter_expressions.append(filter_expr)
            
            # Build CALCULATETABLE with measures
            dax_parts = ["EVALUATE", "CALCULATETABLE("]
            dax_parts.append(f"    {measure_expr},")
            
            # Add filter expressions
            for filter_expr in filter_expressions:
                dax_parts.append(f"    {filter_expr},")
            
            # Remove the last comma and close
            if dax_parts[-1].endswith(","):
                dax_parts[-1] = dax_parts[-1][:-1]
            
            dax_parts.append(")")
            return "\n".join(dax_parts)
        
        # For SUMMARIZECOLUMNS queries, wrap the entire SUMMARIZECOLUMNS expression
        if "SUMMARIZECOLUMNS(" in base_query:
            # Extract the SUMMARIZECOLUMNS part
            summarize_part = base_query.replace("EVALUATE\n", "")
            
            # Generate filter expressions
            filter_expressions = []
            for filter_item in filters:
                filter_expr = self._generate_filter_expression(filter_item)
                filter_expressions.append(filter_expr)
            
            # Build CALCULATETABLE wrapper
            dax_parts = ["EVALUATE", "CALCULATETABLE("]
            
            # Add the SUMMARIZECOLUMNS with proper indentation
            summarize_lines = summarize_part.split("\n")
            for i, line in enumerate(summarize_lines):
                if i == 0:
                    dax_parts.append(f"    {line}")
                else:
                    dax_parts.append(f"    {line}")
            
            # Add comma after SUMMARIZECOLUMNS
            if not dax_parts[-1].endswith(","):
                dax_parts[-1] = dax_parts[-1] + ","
            
            # Add filter expressions
            for filter_expr in filter_expressions:
                dax_parts.append(f"    {filter_expr},")
            
            # Remove the last comma and close
            if dax_parts[-1].endswith(","):
                dax_parts[-1] = dax_parts[-1][:-1]
            
            dax_parts.append(")")
            return "\n".join(dax_parts)
        
        # Fallback - shouldn't happen with current implementation
        return base_query
    
    def _extract_specific_member_filters(self, dimensions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract specific member filters from dimensions.
        
        Args:
            dimensions: List of dimension dictionaries
            
        Returns:
            List of filter dictionaries for specific members
        """
        filters = []
        
        for dimension in dimensions:
            if dimension.get("selection_type") == "specific":
                table = dimension["table"]
                column = dimension["column"]
                specific_members = dimension.get("specific_members", [])
                
                if specific_members:
                    # Create an IN filter for specific members
                    filters.append({
                        "table": table,
                        "column": column,
                        "operator": "IN",
                        "value": specific_members
                    })
        
        return filters
    
    def _generate_filter_expression(self, filter_item: Dict[str, Any]) -> str:
        """
        Generate a DAX filter expression from a filter dictionary.
        
        Args:
            filter_item: Dictionary with table, column, operator, and value keys
            
        Returns:
            DAX filter expression string
        """
        table = filter_item["table"]
        column = filter_item["column"]
        operator = filter_item.get("operator", "=")
        value = filter_item["value"]
        
        # Handle table name quoting (same logic as dimensions)
        if " " in table or table.lower() in ["date", "time"]:
            table_ref = f"'{table}'[{column}]"
        else:
            table_ref = f"{table}[{column}]"
        
        # Handle different operators
        if operator == "IN":
            # Handle IN operator for specific members
            if isinstance(value, list):
                # Format each value in the list
                formatted_values = []
                for v in value:
                    if isinstance(v, str):
                        formatted_values.append(f'"{v}"')
                    else:
                        formatted_values.append(str(v))
                
                values_str = ", ".join(formatted_values)
                return f"{table_ref} IN {{{values_str}}}"
            else:
                # Single value with IN operator
                if isinstance(value, str):
                    formatted_value = f'"{value}"'
                else:
                    formatted_value = str(value)
                return f"{table_ref} IN {{{formatted_value}}}"
        else:
            # Handle = operator (and default case)
            if isinstance(value, str):
                # String values need quotes
                formatted_value = f'"{value}"'
            else:
                # Numeric values don't need quotes
                formatted_value = str(value)
            
            return f"{table_ref} = {formatted_value}"


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
    
    # Test Case 4: Simple WHERE clause
    test_case_4 = {
        "measures": ["Sales Amount"],
        "dimensions": [{"table": "Product", "column": "Category", "selection_type": "members"}],
        "cube": "Adventure Works",
        "where_clause": {
            "filters": [
                {"table": "Date", "column": "Calendar Year", "operator": "=", "value": 2023}
            ]
        }
    }
    
    # Test Case 6: Specific member selection
    test_case_6 = {
        "measures": ["Sales Amount"],
        "dimensions": [{
            "table": "Product", 
            "column": "Category", 
            "selection_type": "specific",
            "specific_members": ["Bikes", "Accessories"]
        }],
        "cube": "Adventure Works",
        "where_clause": None
    }
    
    # Test Case 9: Multiple filters
    test_case_9 = {
        "measures": ["Sales Amount"],
        "dimensions": [{"table": "Product", "column": "Category", "selection_type": "members"}],
        "cube": "Adventure Works",
        "where_clause": {
            "filters": [
                {"table": "Date", "column": "Calendar Year", "operator": "=", "value": 2023},
                {"table": "Geography", "column": "Country", "operator": "=", "value": "United States"}
            ]
        }
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
        print()
        
        # Test Case 4: WHERE clause
        dax_4 = generate_dax(test_case_4)
        print(f"Test Case 4 DAX:\n{dax_4}")
        expected_4 = """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    'Date'[Calendar Year] = 2023
)"""
        print(f"Expected:\n{expected_4}")
        print(f"Match: {dax_4 == expected_4}")
        print()
        
        # Test Case 6: Specific member selection
        dax_6 = generate_dax(test_case_6)
        print(f"Test Case 6 DAX:\n{dax_6}")
        expected_6 = """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        "Sales Amount", [Sales Amount]
    ),
    Product[Category] IN {"Bikes", "Accessories"}
)"""
        print(f"Expected:\n{expected_6}")
        print(f"Match: {dax_6 == expected_6}")
        print()
        
        # Test Case 9: Multiple filters
        dax_9 = generate_dax(test_case_9)
        print(f"Test Case 9 DAX:\n{dax_9}")
        expected_9 = """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    'Date'[Calendar Year] = 2023,
    Geography[Country] = "United States"
)"""
        print(f"Expected:\n{expected_9}")
        print(f"Match: {dax_9 == expected_9}")
        
    except DAXGenerationError as e:
        print(f"Generation failed: {e}")