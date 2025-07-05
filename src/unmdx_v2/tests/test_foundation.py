"""
Foundation tests for UnMDX v2 - Testing the basic functionality that MUST work.

These tests verify that our rewrite actually solves the problems identified in the audit.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unmdx_v2 import mdx_to_dax
from unmdx_v2.core import parse_mdx, generate_dax, ConversionError


def test_case_1_simple_measure():
    """Test Case 1: Simple Measure Query - MUST WORK"""
    mdx = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
    expected_dax = "EVALUATE\n{ [Sales Amount] }"
    
    print(f"\n=== TEST CASE 1: Simple Measure ===")
    print(f"MDX: {mdx}")
    print(f"Expected: {repr(expected_dax)}")
    
    try:
        actual_dax = mdx_to_dax(mdx)
        print(f"Actual: {repr(actual_dax)}")
        print(f"Match: {actual_dax == expected_dax}")
        
        assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
        print("✅ PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_case_2_measure_with_dimension():
    """Test Case 2: Measure with Dimension - MUST WORK"""
    mdx = """SELECT{[Measures].[Sales Amount]}ON COLUMNS,
     {[Product].[Category].Members}    ON    ROWS
FROM    [Adventure Works]"""
    
    expected_dax = """EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)"""
    
    print(f"\n=== TEST CASE 2: Measure with Dimension ===")
    print(f"MDX: {mdx}")
    print(f"Expected: {repr(expected_dax)}")
    
    try:
        actual_dax = mdx_to_dax(mdx)
        print(f"Actual: {repr(actual_dax)}")
        print(f"Match: {actual_dax == expected_dax}")
        
        assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
        print("✅ PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_case_3_multiple_measures():
    """Test Case 3: Multiple Measures - MUST WORK"""
    mdx = """SELECT {{{[Measures].[Sales Amount]}, {[Measures].[Order Quantity]}}} ON 0,
{[Date].[Calendar Year].Members} ON 1
FROM [Adventure Works]"""
    
    expected_dax = """EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Calendar Year],
    "Sales Amount", [Sales Amount],
    "Order Quantity", [Order Quantity]
)"""
    
    print(f"\n=== TEST CASE 3: Multiple Measures ===")
    print(f"MDX: {mdx}")
    print(f"Expected: {repr(expected_dax)}")
    
    try:
        actual_dax = mdx_to_dax(mdx)
        print(f"Actual: {repr(actual_dax)}")
        print(f"Match: {actual_dax == expected_dax}")
        
        assert actual_dax == expected_dax, f"Expected: {expected_dax}, Got: {actual_dax}"
        print("✅ PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_parser_directly():
    """Test parser component directly"""
    print(f"\n=== PARSER UNIT TEST ===")
    
    test_cases = [
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube]", {
            "measures": ["Sales"],
            "dimensions": [],
            "cube": "Cube"
        }),
        ("SELECT {[Measures].[Sales]} ON COLUMNS, {[Product].[Category].Members} ON ROWS FROM [Cube]", {
            "measures": ["Sales"],
            "dimensions": [{"table": "Product", "column": "Category", "selection_type": "members"}],
            "cube": "Cube"
        })
    ]
    
    all_passed = True
    
    for mdx, expected in test_cases:
        try:
            result = parse_mdx(mdx)
            print(f"MDX: {mdx}")
            print(f"Expected: {expected}")
            print(f"Actual: {result}")
            
            # Check key fields
            if (result["measures"] == expected["measures"] and 
                result["dimensions"] == expected["dimensions"] and
                result["cube"] == expected["cube"]):
                print("✅ Parser test PASSED")
            else:
                print("❌ Parser test FAILED")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Parser test FAILED with exception: {e}")
            all_passed = False
    
    return all_passed


def test_dax_generator_directly():
    """Test DAX generator component directly"""
    print(f"\n=== DAX GENERATOR UNIT TEST ===")
    
    test_cases = [
        ({
            "measures": ["Sales Amount"],
            "dimensions": [],
            "cube": "Adventure Works",
            "where_clause": None
        }, "EVALUATE\n{ [Sales Amount] }"),
        
        ({
            "measures": ["Sales Amount"],
            "dimensions": [{"table": "Product", "column": "Category", "selection_type": "members"}],
            "cube": "Adventure Works",
            "where_clause": None
        }, "EVALUATE\nSUMMARIZECOLUMNS(\n    Product[Category],\n    \"Sales Amount\", [Sales Amount]\n)")
    ]
    
    all_passed = True
    
    for parsed_structure, expected_dax in test_cases:
        try:
            result = generate_dax(parsed_structure)
            print(f"Input: {parsed_structure}")
            print(f"Expected: {repr(expected_dax)}")
            print(f"Actual: {repr(result)}")
            
            if result == expected_dax:
                print("✅ DAX generator test PASSED")
            else:
                print("❌ DAX generator test FAILED")
                all_passed = False
                
        except Exception as e:
            print(f"❌ DAX generator test FAILED with exception: {e}")
            all_passed = False
    
    return all_passed


def test_error_handling():
    """Test error handling"""
    print(f"\n=== ERROR HANDLING TEST ===")
    
    test_cases = [
        "",  # Empty string
        "INVALID MDX QUERY",  # Invalid syntax
        "SELECT FROM",  # Incomplete query
    ]
    
    all_passed = True
    
    for invalid_mdx in test_cases:
        try:
            result = mdx_to_dax(invalid_mdx)
            print(f"❌ ERROR HANDLING FAILED: {invalid_mdx} should have failed but returned: {result}")
            all_passed = False
        except ConversionError:
            print(f"✅ Correctly rejected invalid MDX: {repr(invalid_mdx)}")
        except Exception as e:
            print(f"❌ Wrong exception type for {repr(invalid_mdx)}: {e}")
            all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all foundation tests"""
    print("🧪 RUNNING UNMDX V2 FOUNDATION TESTS")
    print("=" * 60)
    
    results = []
    
    # Core functionality tests
    results.append(("Test Case 1", test_case_1_simple_measure()))
    results.append(("Test Case 2", test_case_2_measure_with_dimension()))
    results.append(("Test Case 3", test_case_3_multiple_measures()))
    
    # Component tests
    results.append(("Parser Unit Test", test_parser_directly()))
    results.append(("DAX Generator Unit Test", test_dax_generator_directly()))
    
    # Error handling
    results.append(("Error Handling", test_error_handling()))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! UnMDX v2 foundation is working correctly.")
        return True
    else:
        print("💥 SOME TESTS FAILED! Foundation needs more work.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)