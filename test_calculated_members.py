#!/usr/bin/env python3
"""
Test calculated members functionality comprehensively
"""

from unmdx.api import mdx_to_dax
from unmdx.config import create_default_config


def test_calculated_members():
    """Test various calculated member scenarios"""
    config = create_default_config()
    config.dax.format_output = False
    
    print("🧪 Testing Calculated Members Functionality")
    print("=" * 60)
    
    # Test Case 1: Simple Division
    print("\n1. Simple Division (Test Case 7)")
    mdx = """WITH MEMBER[Measures].[Average Price]AS[Measures].[Sales Amount]/[Measures].[Order Quantity]
SELECT{[Measures].[Sales Amount],[Measures].[Order Quantity],[Measures].[Average Price]}ON 0
FROM[Adventure Works]"""
    
    try:
        result = mdx_to_dax(mdx, config=config)
        print(f"✅ Result:\n{result.dax_query}")
        assert "DEFINE" in result.dax_query
        assert "MEASURE Sales[Average Price] = DIVIDE([Sales Amount], [Order Quantity])" in result.dax_query
        assert "EVALUATE" in result.dax_query
        print("✅ Simple Division PASSED")
    except Exception as e:
        print(f"❌ Simple Division FAILED: {e}")
    
    # Test Case 2: Multiple Calculated Members
    print("\n2. Multiple Calculated Members")
    mdx = """WITH 
MEMBER [Measures].[Profit] AS [Measures].[Revenue] - [Measures].[Cost]
MEMBER [Measures].[Margin] AS [Measures].[Profit] / [Measures].[Revenue]
SELECT {[Measures].[Revenue], [Measures].[Cost], [Measures].[Profit], [Measures].[Margin]} ON 0
FROM [Adventure Works]"""
    
    try:
        result = mdx_to_dax(mdx, config=config)
        print(f"✅ Result:\n{result.dax_query}")
        assert "DEFINE" in result.dax_query
        assert "MEASURE Sales[Profit]" in result.dax_query
        assert "MEASURE Sales[Margin]" in result.dax_query
        assert "EVALUATE" in result.dax_query
        print("✅ Multiple Calculated Members PASSED")
    except Exception as e:
        print(f"❌ Multiple Calculated Members FAILED: {e}")
    
    # Test Case 3: Complex Expression with Parentheses
    print("\n3. Complex Expression with Parentheses")
    mdx = """WITH MEMBER [Measures].[Complex] AS ([Measures].[A] + [Measures].[B]) * [Measures].[C]
SELECT {[Measures].[A], [Measures].[B], [Measures].[C], [Measures].[Complex]} ON 0
FROM [Adventure Works]"""
    
    try:
        result = mdx_to_dax(mdx, config=config)
        print(f"✅ Result:\n{result.dax_query}")
        assert "DEFINE" in result.dax_query
        assert "MEASURE Sales[Complex]" in result.dax_query
        assert "EVALUATE" in result.dax_query
        print("✅ Complex Expression PASSED")
    except Exception as e:
        print(f"❌ Complex Expression FAILED: {e}")
    
    # Test Case 4: Calculated Member with Dimension
    print("\n4. Calculated Member with Dimension")
    mdx = """WITH MEMBER [Measures].[Price] AS [Measures].[Sales] / [Measures].[Quantity]
SELECT {[Measures].[Sales], [Measures].[Quantity], [Measures].[Price]} ON 0,
{[Product].[Category].Members} ON 1
FROM [Adventure Works]"""
    
    try:
        result = mdx_to_dax(mdx, config=config)
        print(f"✅ Result:\n{result.dax_query}")
        assert "DEFINE" in result.dax_query
        assert "MEASURE Sales[Price]" in result.dax_query
        assert "SUMMARIZECOLUMNS" in result.dax_query
        assert "Product[Category]" in result.dax_query
        print("✅ Calculated Member with Dimension PASSED")
    except Exception as e:
        print(f"❌ Calculated Member with Dimension FAILED: {e}")
    
    # Test Case 5: Function Calls in Calculated Member
    print("\n5. Function Calls in Calculated Member")
    mdx = """WITH MEMBER [Measures].[Safe Division] AS DIVIDE([Measures].[A], [Measures].[B])
SELECT {[Measures].[A], [Measures].[B], [Measures].[Safe Division]} ON 0
FROM [Adventure Works]"""
    
    try:
        result = mdx_to_dax(mdx, config=config)
        print(f"✅ Result:\n{result.dax_query}")
        assert "DEFINE" in result.dax_query
        assert "MEASURE Sales[Safe Division]" in result.dax_query
        assert "EVALUATE" in result.dax_query
        print("✅ Function Calls PASSED")
    except Exception as e:
        print(f"❌ Function Calls FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Calculated Members Test Suite Complete")


if __name__ == "__main__":
    test_calculated_members()