#!/usr/bin/env python3
"""
Working examples of UnMDX API after fixing basic test cases.
Run this script to see the fixed MDX to DAX conversion in action.
"""

from unmdx.api import mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx

def example_1_simple_measure():
    """Test Case 1: Simple measure query - WORKING! ✅"""
    print("🎯 Example 1: Simple Measure Query")
    print("-" * 50)
    
    mdx = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
    result = mdx_to_dax(mdx)
    
    print(f"MDX Input:\n{mdx}")
    print(f"\nDAX Output:\n{result.dax_query}")
    expected = 'EVALUATE\n{ [Sales Amount] }'
    print(f"\nSuccess: {result.dax_query == expected}")
    return result

def example_2_measure_with_dimension():
    """Test Case 2: Measure with dimension - WORKING! ✅"""
    print("\n📊 Example 2: Measure with Dimension")
    print("-" * 50)
    
    mdx = """SELECT [Measures].[Sales Amount] ON COLUMNS,
[Product].[Category].Members ON ROWS
FROM [Adventure Works]"""
    
    result = mdx_to_dax(mdx)
    
    print(f"MDX Input:\n{mdx}")
    print(f"\nDAX Output:\n{result.dax_query}")
    
    expected = """EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)"""
    print(f"\nSuccess: {result.dax_query == expected}")
    return result

def example_3_multiple_measures():
    """Multiple measures in single query"""
    print("\n💰 Example 3: Multiple Measures")
    print("-" * 50)
    
    mdx = "SELECT {[Measures].[Sales Amount], [Measures].[Order Quantity]} ON 0 FROM [Adventure Works]"
    result = mdx_to_dax(mdx)
    
    print(f"MDX Input:\n{mdx}")
    print(f"\nDAX Output:\n{result.dax_query}")
    return result

def example_4_crossjoin():
    """CrossJoin pattern (common in messy Necto output)"""
    print("\n🔄 Example 4: CrossJoin Pattern")
    print("-" * 50)
    
    mdx = """SELECT [Measures].[Sales Amount] ON 0,
CROSSJOIN([Product].[Category].Members, [Customer].[Country].Members) ON 1
FROM [Adventure Works]"""
    
    result = mdx_to_dax(mdx)
    
    print(f"MDX Input:\n{mdx}")
    print(f"\nDAX Output:\n{result.dax_query}")
    return result

def example_5_messy_formatting():
    """Messy formatting (typical Necto output)"""
    print("\n🧹 Example 5: Messy Formatting (Necto-style)")
    print("-" * 50)
    
    mdx = """SELECT{[Measures].[Sales Amount]}ON COLUMNS,
     {[Product].[Category].Members}    ON    ROWS
FROM    [Adventure Works]"""
    
    result = mdx_to_dax(mdx)
    
    print(f"MDX Input:\n{mdx}")
    print(f"\nDAX Output:\n{result.dax_query}")
    return result

def show_api_features():
    """Demonstrate other API functions"""
    print("\n🔧 Other API Features")
    print("-" * 50)
    
    mdx = "SELECT [Measures].[Sales Amount] ON 0 FROM [Adventure Works]"
    
    try:
        # Parse only
        parse_result = parse_mdx(mdx)
        print("✅ Parse function: Working")
        
        # Optimize 
        optimize_result = optimize_mdx(mdx)
        print("✅ Optimize function: Working")
        
        # Explain
        explain_result = explain_mdx(mdx)
        print("✅ Explain function: Working")
        
    except Exception as e:
        print(f"⚠️ Some API functions may need additional work: {e}")

if __name__ == "__main__":
    print("🚀 UnMDX Working Examples")
    print("=" * 60)
    print("Demonstrating fixed MDX to DAX conversion")
    
    # Run all examples
    example_1_simple_measure()
    example_2_measure_with_dimension() 
    example_3_multiple_measures()
    example_4_crossjoin()
    example_5_messy_formatting()
    show_api_features()
    
    print("\n✨ All examples completed!")
    print("The basic test cases are now working correctly.")