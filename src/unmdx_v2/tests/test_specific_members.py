"""
Test specific member selection functionality for UnMDX v2.

This test validates Test Case 6: Specific member selection like 
{{[Product].[Category].[Bikes]},{[Product].[Category].[Accessories]}}
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unmdx_v2.core.parser import parse_mdx
from unmdx_v2.core.dax_generator import generate_dax
from unmdx_v2 import mdx_to_dax
import json


def test_specific_member_selection_test_case_6():
    """Test Case 6: Specific member selection"""
    mdx = "SELECT{[Measures].[Sales Amount]}ON AXIS(0), {{[Product].[Category].[Bikes]},{[Product].[Category].[Accessories]}}ON AXIS(1) FROM[Adventure Works]"
    
    expected_parsed = {
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
    
    expected_dax = """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        "Sales Amount", [Sales Amount]
    ),
    Product[Category] IN {"Bikes", "Accessories"}
)"""
    
    print("=== Test Case 6: Specific Member Selection ===")
    print(f"MDX: {mdx}")
    print(f"Expected parsed: {expected_parsed}")
    print(f"Expected DAX: {expected_dax}")
    
    try:
        # Test parsing
        result = parse_mdx(mdx)
        print(f"✅ Parsed successfully")
        print(f"Parsed result: {result}")
        
        # Verify parsing results
        assert result['measures'] == expected_parsed['measures'], f"Expected measures {expected_parsed['measures']}, got {result['measures']}"
        assert result['cube'] == expected_parsed['cube'], f"Expected cube {expected_parsed['cube']}, got {result['cube']}"
        assert result['where_clause'] == expected_parsed['where_clause'], f"Expected where_clause {expected_parsed['where_clause']}, got {result['where_clause']}"
        
        # Check dimension structure
        assert len(result['dimensions']) == 1, f"Expected 1 dimension, got {len(result['dimensions'])}"
        
        dimension = result['dimensions'][0]
        expected_dimension = expected_parsed['dimensions'][0]
        assert dimension['table'] == expected_dimension['table'], f"Expected table {expected_dimension['table']}, got {dimension['table']}"
        assert dimension['column'] == expected_dimension['column'], f"Expected column {expected_dimension['column']}, got {dimension['column']}"
        assert dimension['selection_type'] == expected_dimension['selection_type'], f"Expected selection_type {expected_dimension['selection_type']}, got {dimension['selection_type']}"
        assert set(dimension['specific_members']) == set(expected_dimension['specific_members']), f"Expected specific_members {expected_dimension['specific_members']}, got {dimension['specific_members']}"
        
        print("✅ Parsing verification PASSED")
        
        # Test DAX generation
        dax_result = generate_dax(result)
        print(f"Generated DAX: {dax_result}")
        
        # Verify DAX structure (normalize whitespace for comparison)
        def normalize_dax(dax_str):
            return '\n'.join(line.strip() for line in dax_str.strip().split('\n'))
        
        normalized_expected = normalize_dax(expected_dax)
        normalized_actual = normalize_dax(dax_result)
        
        if normalized_actual == normalized_expected:
            print("✅ DAX generation PASSED")
        else:
            print(f"❌ DAX generation FAILED")
            print(f"Expected normalized: {repr(normalized_expected)}")
            print(f"Actual normalized: {repr(normalized_actual)}")
            return False
        
        # Test end-to-end
        end_to_end_result = mdx_to_dax(mdx)
        print(f"End-to-end result: {end_to_end_result}")
        
        normalized_end_to_end = normalize_dax(end_to_end_result)
        
        if normalized_end_to_end == normalized_expected:
            print("✅ End-to-end test PASSED")
        else:
            print(f"❌ End-to-end test FAILED")
            print(f"Expected normalized: {repr(normalized_expected)}")
            print(f"End-to-end normalized: {repr(normalized_end_to_end)}")
            return False
        
        print("✅ Test Case 6 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Test Case 6 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_member_single_value():
    """Test specific member selection with single value"""
    mdx = "SELECT{[Measures].[Sales Amount]}ON AXIS(0), {[Product].[Category].[Bikes]}ON AXIS(1) FROM[Adventure Works]"
    
    expected_parsed = {
        "measures": ["Sales Amount"],
        "dimensions": [{
            "table": "Product", 
            "column": "Category", 
            "selection_type": "specific",
            "specific_members": ["Bikes"]
        }],
        "cube": "Adventure Works",
        "where_clause": None
    }
    
    expected_dax = """EVALUATE
CALCULATETABLE(
    SUMMARIZECOLUMNS(
        "Sales Amount", [Sales Amount]
    ),
    Product[Category] IN {"Bikes"}
)"""
    
    print("\n=== Test Single Specific Member ===")
    print(f"MDX: {mdx}")
    
    try:
        # Test parsing
        result = parse_mdx(mdx)
        print(f"✅ Parsed successfully")
        print(f"Parsed result: {result}")
        
        # Verify parsing results
        assert result['measures'] == expected_parsed['measures'], f"Expected measures {expected_parsed['measures']}, got {result['measures']}"
        assert len(result['dimensions']) == 1, f"Expected 1 dimension, got {len(result['dimensions'])}"
        
        dimension = result['dimensions'][0]
        expected_dimension = expected_parsed['dimensions'][0]
        assert dimension['table'] == expected_dimension['table'], f"Expected table {expected_dimension['table']}, got {dimension['table']}"
        assert dimension['column'] == expected_dimension['column'], f"Expected column {expected_dimension['column']}, got {dimension['column']}"
        assert dimension['selection_type'] == expected_dimension['selection_type'], f"Expected selection_type {expected_dimension['selection_type']}, got {dimension['selection_type']}"
        assert dimension['specific_members'] == expected_dimension['specific_members'], f"Expected specific_members {expected_dimension['specific_members']}, got {dimension['specific_members']}"
        
        print("✅ Single specific member test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Single specific member test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mixed_specific_and_members():
    """Test mixed specific members and .Members in same query"""
    mdx = "SELECT{[Measures].[Sales Amount]}ON AXIS(0), {[Product].[Category].[Bikes], [Date].[Calendar Year].Members}ON AXIS(1) FROM[Adventure Works]"
    
    print("\n=== Test Mixed Specific and Members ===")
    print(f"MDX: {mdx}")
    
    try:
        # Test parsing
        result = parse_mdx(mdx)
        print(f"✅ Parsed successfully")
        print(f"Parsed result: {result}")
        
        # Should have 2 dimensions: one specific Product Category, one members Date Calendar Year
        assert len(result['dimensions']) == 2, f"Expected 2 dimensions, got {len(result['dimensions'])}"
        
        # Find the dimensions
        product_dim = next((d for d in result['dimensions'] if d['table'] == 'Product'), None)
        date_dim = next((d for d in result['dimensions'] if d['table'] == 'Date'), None)
        
        assert product_dim is not None, "Should have Product dimension"
        assert date_dim is not None, "Should have Date dimension"
        
        # Check Product dimension (specific)
        assert product_dim['selection_type'] == 'specific', f"Expected specific selection for Product, got {product_dim['selection_type']}"
        assert product_dim['specific_members'] == ['Bikes'], f"Expected ['Bikes'], got {product_dim['specific_members']}"
        
        # Check Date dimension (members)
        assert date_dim['selection_type'] == 'members', f"Expected members selection for Date, got {date_dim['selection_type']}"
        
        print("✅ Mixed specific and members test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Mixed specific and members test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


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
            
            # Check that dimensions that use .Members still work
            for dim in result.get('dimensions', []):
                if dim.get('selection_type') == 'members':
                    assert 'specific_members' not in dim, "Members dimensions should not have specific_members"
            
            print("✅ Backward compatibility maintained")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            all_passed = False
    
    return all_passed


def run_all_specific_member_tests():
    """Run all specific member tests"""
    print("🧪 RUNNING SPECIFIC MEMBER TESTS FOR UNMDX V2")
    print("=" * 60)
    
    results = []
    
    # Core specific member tests
    results.append(("Test Case 6 (Specific Members)", test_specific_member_selection_test_case_6()))
    results.append(("Single Specific Member", test_specific_member_single_value()))
    results.append(("Mixed Specific and Members", test_mixed_specific_and_members()))
    results.append(("Backward Compatibility", test_backward_compatibility()))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SPECIFIC MEMBER TEST RESULTS")
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
        print("🎉 ALL SPECIFIC MEMBER TESTS PASSED!")
        return True
    else:
        print("💥 SOME SPECIFIC MEMBER TESTS FAILED!")
        return False


if __name__ == "__main__":
    success = run_all_specific_member_tests()
    sys.exit(0 if success else 1)