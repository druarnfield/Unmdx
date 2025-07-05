#!/usr/bin/env python3
"""
Integration tests for all basic test cases from test_cases_basic.md
This will reveal what's actually working vs failing.
"""

from unmdx.api import mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx
from unmdx.config import create_default_config


class TestBasicCases:
    """Test all 10 basic test cases from test_cases_basic.md"""
    
    def setup_method(self):
        """Setup with formatting disabled for exact matching"""
        self.config = create_default_config()
        self.config.dax.format_output = False
    
    def test_case_1_simple_measure(self):
        """Test Case 1: Simple Measure Query"""
        mdx = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
        expected_dax = "EVALUATE\n{ [Sales Amount] }"
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 1 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            print(f"Test Case 1 failed with exception: {e}")
            raise e
    
    def test_case_2_measure_with_dimension(self):
        """Test Case 2: Measure with Dimension (Messy Spacing)"""
        mdx = """SELECT{[Measures].[Sales Amount]}ON COLUMNS,
     {[Product].[Category].Members}    ON    ROWS
FROM    [Adventure Works]"""
        
        expected_dax = """EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 2 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            raise Exception(f"Test Case 2 failed with exception: {e}")
    
    def test_case_3_multiple_measures(self):
        """Test Case 3: Multiple Measures (Redundant Braces)"""
        mdx = """SELECT {{{[Measures].[Sales Amount]}, {[Measures].[Order Quantity]}}} ON 0,
{[Date].[Calendar Year].Members} ON 1
FROM [Adventure Works]"""
        
        expected_dax = """EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Calendar Year],
    "Sales Amount", [Sales Amount],
    "Order Quantity", [Order Quantity]
)"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 3 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            # This will likely fail - let's see what we get
            if actual_dax != expected_dax:
                print(f"❌ MISMATCH - Expected: {expected_dax}, Got: {actual_dax}")
                raise AssertionError(f"Expected: {expected_dax}, Got: {actual_dax}")
            
        except Exception as e:
            print(f"Test Case 3 failed with exception: {e}")
            raise e
    
    def test_case_4_simple_where_clause(self):
        """Test Case 4: Simple WHERE Clause"""
        mdx = """SELECT   {[Measures].[Sales Amount]}   ON   COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE    ([Date].[Calendar Year].&[2023])"""
        
        expected_dax = """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    'Date'[Calendar Year] = 2023
)"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 4 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            # This will likely fail - filters are complex
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            print(f"Test Case 4 failed with exception: {e}")
            raise Exception(f"Test Case 4 failed with exception: {e}")
    
    def test_case_5_crossjoin(self):
        """Test Case 5: CrossJoin with Redundant Parentheses"""
        mdx = """SELECT {[Measures].[Sales Amount]} ON 0,
CROSSJOIN(({[Product].[Category].Members}),
          ({[Customer].[Country].Members})) ON 1
FROM [Adventure Works]"""
        
        expected_dax = """EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    Customer[Country],
    "Sales Amount", [Sales Amount]
)"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 5 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            # CrossJoin parsing is complex
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            print(f"Test Case 5 failed with exception: {e}")
            raise Exception(f"Test Case 5 failed with exception: {e}")
    
    def test_case_6_specific_member_selection(self):
        """Test Case 6: Specific Member Selection (Verbose)"""
        mdx = """SELECT{[Measures].[Sales Amount]}ON AXIS(0),
{{[Product].[Category].[Bikes]},{[Product].[Category].[Accessories]}}ON AXIS(1)
FROM[Adventure Works]"""
        
        expected_dax = """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    Product[Category] IN {"Bikes", "Accessories"}
)"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 6 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            # Specific member selection is very complex
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            print(f"Test Case 6 failed with exception: {e}")
            raise Exception(f"Test Case 6 failed with exception: {e}")
    
    def test_case_7_calculated_member(self):
        """Test Case 7: Simple Calculated Member"""
        mdx = """WITH MEMBER[Measures].[Average Price]AS[Measures].[Sales Amount]/[Measures].[Order Quantity]
SELECT{[Measures].[Sales Amount],[Measures].[Order Quantity],[Measures].[Average Price]}ON 0
FROM[Adventure Works]"""
        
        expected_dax = """DEFINE
    MEASURE Sales[Average Price] = DIVIDE([Sales Amount], [Order Quantity])
EVALUATE
{
    [Sales Amount],
    [Order Quantity],
    [Average Price]
}"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 7 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            # Calculated members are very complex
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            print(f"Test Case 7 failed with exception: {e}")
            raise Exception(f"Test Case 7 failed with exception: {e}")
    
    def test_case_8_non_empty(self):
        """Test Case 8: NON EMPTY with Nested Sets"""
        mdx = """SELECT NON EMPTY{{[Measures].[Sales Amount]}}ON 0,
NON EMPTY{{{[Product].[Category].Members}}}ON 1
FROM[Adventure Works]"""
        
        expected_dax = """EVALUATE
FILTER(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    [Sales Amount] <> BLANK()
)"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 8 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            # NON EMPTY is complex
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            print(f"Test Case 8 failed with exception: {e}")
            raise Exception(f"Test Case 8 failed with exception: {e}")
    
    def test_case_9_multiple_filters(self):
        """Test Case 9: Multiple Filters in WHERE (Complex Tuple)"""
        mdx = """SELECT{[Measures].[Sales Amount]}ON COLUMNS,
{[Product].[Category].Members}ON ROWS
FROM[Adventure Works]
WHERE([Date].[Calendar Year].&[2023],[Geography].[Country].&[United States])"""
        
        expected_dax = """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        Product[Category],
        "Sales Amount", [Sales Amount]
    ),
    'Date'[Calendar Year] = 2023,
    Geography[Country] = "United States"
)"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 9 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            # Multiple filters are very complex
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            print(f"Test Case 9 failed with exception: {e}")
            raise Exception(f"Test Case 9 failed with exception: {e}")
    
    def test_case_10_empty_sets(self):
        """Test Case 10: Empty Sets and Redundant Constructs"""
        mdx = """SELECT{{{{}}},{[Measures].[Sales Amount]},{{}}}ON 0,
{[Date].[Calendar].[Calendar Year].Members}ON 1
FROM[Adventure Works]WHERE()"""
        
        expected_dax = """EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Calendar Year],
    "Sales Amount", [Sales Amount]
)"""
        
        try:
            result = mdx_to_dax(mdx, config=self.config)
            actual_dax = result.dax_query
            
            print(f"\n=== TEST CASE 10 ===")
            print(f"MDX: {mdx}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(actual_dax)}")
            print(f"Match: {actual_dax == expected_dax}")
            
            # Empty set handling is complex
            assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
            
        except Exception as e:
            print(f"Test Case 10 failed with exception: {e}")
            raise Exception(f"Test Case 10 failed with exception: {e}")


class TestAPIFunctions:
    """Test all main API functions with basic cases"""
    
    def test_parse_mdx_function(self):
        """Test parse_mdx function"""
        mdx = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
        
        try:
            result = parse_mdx(mdx)
            print(f"\n=== PARSE_MDX TEST ===")
            print(f"Result type: {type(result)}")
            print(f"Has parse_tree: {hasattr(result, 'parse_tree')}")
            print(f"Parse successful: {result.parse_tree is not None}")
            
            assert result.parse_tree is not None, "Parse tree should not be None"
            
        except Exception as e:
            raise Exception(f"parse_mdx failed: {e}")
    
    def test_optimize_mdx_function(self):
        """Test optimize_mdx function"""
        mdx = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
        
        try:
            result = optimize_mdx(mdx)
            print(f"\n=== OPTIMIZE_MDX TEST ===")
            print(f"Result type: {type(result)}")
            print(f"Has optimized_mdx: {hasattr(result, 'optimized_mdx')}")
            
            assert hasattr(result, 'optimized_mdx'), "Should have optimized_mdx attribute"
            
        except Exception as e:
            raise Exception(f"optimize_mdx failed: {e}")
    
    def test_explain_mdx_function(self):
        """Test explain_mdx function"""
        mdx = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
        
        try:
            result = explain_mdx(mdx)
            print(f"\n=== EXPLAIN_MDX TEST ===")
            print(f"Result type: {type(result)}")
            print(f"Has explanation: {hasattr(result, 'explanation')}")
            
            assert hasattr(result, 'explanation'), "Should have explanation attribute"
            
        except Exception as e:
            raise Exception(f"explain_mdx failed: {e}")


if __name__ == "__main__":
    # Run the tests directly to see what's failing
    test_basic = TestBasicCases()
    test_basic.setup_method()
    
    print("🧪 Running Integration Tests for Basic Test Cases")
    print("=" * 70)
    
    test_methods = [
        (test_basic.test_case_1_simple_measure, "Test Case 1: Simple Measure"),
        (test_basic.test_case_2_measure_with_dimension, "Test Case 2: Measure with Dimension"),
        (test_basic.test_case_3_multiple_measures, "Test Case 3: Multiple Measures"),
        (test_basic.test_case_4_simple_where_clause, "Test Case 4: WHERE Clause"),
        (test_basic.test_case_5_crossjoin, "Test Case 5: CrossJoin"),
        (test_basic.test_case_6_specific_member_selection, "Test Case 6: Specific Members"),
        (test_basic.test_case_7_calculated_member, "Test Case 7: Calculated Member"),
        (test_basic.test_case_8_non_empty, "Test Case 8: NON EMPTY"),
        (test_basic.test_case_9_multiple_filters, "Test Case 9: Multiple Filters"),
        (test_basic.test_case_10_empty_sets, "Test Case 10: Empty Sets"),
    ]
    
    passed = 0
    failed = 0
    
    for test_method, test_name in test_methods:
        try:
            test_method()
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)[:200]}...")
            failed += 1
    
    print(f"\n📊 RESULTS: {passed} passed, {failed} failed out of {len(test_methods)} tests")
    
    # Test API functions
    print(f"\n🔧 Testing API Functions")
    test_api = TestAPIFunctions()
    
    api_tests = [
        (test_api.test_parse_mdx_function, "parse_mdx"),
        (test_api.test_optimize_mdx_function, "optimize_mdx"),
        (test_api.test_explain_mdx_function, "explain_mdx"),
    ]
    
    for test_method, test_name in api_tests:
        try:
            test_method()
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)[:100]}...")