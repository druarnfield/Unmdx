"""
Test WHERE clause functionality for UnMDX v2.

This test file specifically validates the WHERE clause parsing enhancement
that was added to support Test Cases 4 and 9.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unmdx_v2.core.parser import parse_mdx
from unmdx_v2 import mdx_to_dax
import json


def test_where_clause_test_case_4():
    """Test Case 4: Simple WHERE clause"""
    mdx = """SELECT {[Measures].[Sales Amount]} ON COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].&[2023])"""
    
    expected_where = {
        "filters": [
            {
                "table": "Date",
                "column": "Calendar Year",
                "operator": "=",
                "value": 2023
            }
        ]
    }
    
    print("=== Test Case 4: Simple WHERE clause ===")
    print(f"MDX: {mdx}")
    
    try:
        result = parse_mdx(mdx)
        print(f"✅ Parsed successfully")
        print(f"WHERE clause: {result['where_clause']}")
        
        # Verify WHERE clause structure
        assert result['where_clause'] is not None, "WHERE clause should not be None"
        assert result['where_clause']['filters'] == expected_where['filters'], f"Expected {expected_where['filters']}, got {result['where_clause']['filters']}"
        
        # Verify other components still work
        assert result['measures'] == ["Sales Amount"], f"Expected ['Sales Amount'], got {result['measures']}"
        assert len(result['dimensions']) == 1, f"Expected 1 dimension, got {len(result['dimensions'])}"
        assert result['cube'] == "Adventure Works", f"Expected 'Adventure Works', got {result['cube']}"
        
        print("✅ Test Case 4 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test Case 4 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_where_clause_test_case_9():
    """Test Case 9: Multiple filters in WHERE clause"""
    mdx = """SELECT {[Measures].[Sales Amount]} ON COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].&[2023], [Geography].[Country].&[United States])"""
    
    expected_where = {
        "filters": [
            {
                "table": "Date",
                "column": "Calendar Year",
                "operator": "=",
                "value": 2023
            },
            {
                "table": "Geography",
                "column": "Country",
                "operator": "=",
                "value": "United States"
            }
        ]
    }
    
    print("\n=== Test Case 9: Multiple WHERE filters ===")
    print(f"MDX: {mdx}")
    
    try:
        result = parse_mdx(mdx)
        print(f"✅ Parsed successfully")
        print(f"WHERE clause: {result['where_clause']}")
        
        # Verify WHERE clause structure
        assert result['where_clause'] is not None, "WHERE clause should not be None"
        assert len(result['where_clause']['filters']) == 2, f"Expected 2 filters, got {len(result['where_clause']['filters'])}"
        
        # Check each filter
        for i, expected_filter in enumerate(expected_where['filters']):
            actual_filter = result['where_clause']['filters'][i]
            assert actual_filter == expected_filter, f"Filter {i}: Expected {expected_filter}, got {actual_filter}"
        
        # Verify other components still work
        assert result['measures'] == ["Sales Amount"], f"Expected ['Sales Amount'], got {result['measures']}"
        assert len(result['dimensions']) == 1, f"Expected 1 dimension, got {len(result['dimensions'])}"
        assert result['cube'] == "Adventure Works", f"Expected 'Adventure Works', got {result['cube']}"
        
        print("✅ Test Case 9 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test Case 9 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_where_clause_edge_cases():
    """Test edge cases for WHERE clause parsing"""
    print("\n=== WHERE Clause Edge Cases ===")
    
    test_cases = [
        # No WHERE clause
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube]", None, "No WHERE clause"),
        
        # Empty WHERE clause
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE ()", None, "Empty WHERE clause"),
        
        # String values with quotes
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE ([Product].[Name].&[\"Bike\"])", {
            "filters": [{"table": "Product", "column": "Name", "operator": "=", "value": "Bike"}]
        }, "String value with quotes"),
        
        # Numeric values
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE ([Date].[Year].&[2023])", {
            "filters": [{"table": "Date", "column": "Year", "operator": "=", "value": 2023}]
        }, "Numeric value"),
        
        # Float values
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE ([Price].[Amount].&[123.45])", {
            "filters": [{"table": "Price", "column": "Amount", "operator": "=", "value": 123.45}]
        }, "Float value"),
    ]
    
    all_passed = True
    
    for mdx, expected_where, description in test_cases:
        print(f"\n--- {description} ---")
        print(f"MDX: {mdx}")
        
        try:
            result = parse_mdx(mdx)
            actual_where = result['where_clause']
            
            if expected_where is None:
                if actual_where is None:
                    print("✅ Correctly parsed as None")
                else:
                    print(f"❌ Expected None, got {actual_where}")
                    all_passed = False
            else:
                if actual_where == expected_where:
                    print("✅ Correctly parsed")
                else:
                    print(f"❌ Expected {expected_where}, got {actual_where}")
                    all_passed = False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            all_passed = False
    
    return all_passed


def test_backward_compatibility():
    """Test that existing functionality still works"""
    print("\n=== Backward Compatibility Tests ===")
    
    test_cases = [
        ("SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]", "Test Case 1"),
        ("SELECT {[Measures].[Sales Amount]} ON COLUMNS, {[Product].[Category].Members} ON ROWS FROM [Adventure Works]", "Test Case 2"),
        ("SELECT {{{[Measures].[Sales Amount]}, {[Measures].[Order Quantity]}}} ON 0, {[Date].[Calendar Year].Members} ON 1 FROM [Adventure Works]", "Test Case 3"),
    ]
    
    all_passed = True
    
    for mdx, description in test_cases:
        print(f"\n--- {description} ---")
        print(f"MDX: {mdx}")
        
        try:
            result = parse_mdx(mdx)
            
            # Basic checks
            assert result['measures'], "Should have measures"
            assert result['cube'], "Should have cube"
            assert result['where_clause'] is None, "Should have no WHERE clause"
            
            print("✅ Backward compatibility maintained")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            all_passed = False
    
    return all_passed


def run_all_where_clause_tests():
    """Run all WHERE clause tests"""
    print("🧪 RUNNING WHERE CLAUSE TESTS FOR UNMDX V2")
    print("=" * 60)
    
    results = []
    
    # Core WHERE clause tests
    results.append(("Test Case 4 (Simple WHERE)", test_where_clause_test_case_4()))
    results.append(("Test Case 9 (Multiple WHERE)", test_where_clause_test_case_9()))
    results.append(("WHERE Edge Cases", test_where_clause_edge_cases()))
    results.append(("Backward Compatibility", test_backward_compatibility()))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 WHERE CLAUSE TEST RESULTS")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL WHERE CLAUSE TESTS PASSED!")
        return True
    else:
        print("💥 SOME WHERE CLAUSE TESTS FAILED!")
        return False


if __name__ == "__main__":
    success = run_all_where_clause_tests()
    sys.exit(0 if success else 1)