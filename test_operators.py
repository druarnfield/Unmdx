#!/usr/bin/env python3
"""
Test different arithmetic operators in calculated members
"""

from unmdx.api import mdx_to_dax
from unmdx.config import create_default_config


def test_operators():
    """Test different arithmetic operators"""
    config = create_default_config()
    config.dax.format_output = False
    
    print("🧪 Testing Arithmetic Operators in Calculated Members")
    print("=" * 60)
    
    # Test each operator
    operators = [
        ("+", "addition", "([A] + [B])"),
        ("-", "subtraction", "([A] - [B])"),
        ("*", "multiplication", "([A] * [B])"),
        ("/", "division", "DIVIDE([A], [B])"),
    ]
    
    for op, name, expected_dax in operators:
        print(f"\n{name.upper()} ({op})")
        print("-" * 30)
        
        mdx = f"""WITH MEMBER[Measures].[Test]AS[Measures].[A]{op}[Measures].[B]
SELECT{{[Measures].[A],[Measures].[B],[Measures].[Test]}}ON 0
FROM[Adventure Works]"""
        
        try:
            result = mdx_to_dax(mdx, config=config)
            
            # Check that DEFINE clause exists
            assert "DEFINE" in result.dax_query, "DEFINE clause missing"
            
            # Check that the expected DAX expression is generated
            if expected_dax in result.dax_query:
                print(f"✅ {expected_dax}")
                print(f"✅ {name.capitalize()} operator working correctly")
            else:
                print(f"❌ Expected: {expected_dax}")
                print(f"❌ Got: {result.dax_query}")
                
        except Exception as e:
            print(f"❌ {name.capitalize()} test failed: {e}")
    
    print(f"\n" + "=" * 60)
    print("✅ Operator Test Suite Complete")


if __name__ == "__main__":
    test_operators()