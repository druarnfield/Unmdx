#!/usr/bin/env python3
"""
Test script to verify the complete UnMDX v2 workflow
"""

from core.parser import parse_mdx
from core.dax_generator import generate_dax

def test_complete_workflow():
    """Test the complete MDX to DAX workflow"""
    
    print("🧪 Testing UnMDX v2 Complete Workflow")
    print("=" * 50)
    
    # Test cases from the integration tests
    test_cases = [
        {
            'name': 'Test Case 1: Simple Measure',
            'mdx': 'SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]',
            'expected': 'EVALUATE\n{ [Sales Amount] }'
        },
        {
            'name': 'Test Case 2: Measure with Dimension',
            'mdx': '''SELECT{[Measures].[Sales Amount]}ON COLUMNS,
     {[Product].[Category].Members}    ON    ROWS
FROM    [Adventure Works]''',
            'expected': '''EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)'''
        },
        {
            'name': 'Test Case 3: Multiple Measures with Dimension',
            'mdx': '''SELECT {{{[Measures].[Sales Amount]}, {[Measures].[Order Quantity]}}} ON 0,
{[Date].[Calendar Year].Members} ON 1
FROM [Adventure Works]''',
            'expected': '''EVALUATE
SUMMARIZECOLUMNS(
    'Date'[Calendar Year],
    "Sales Amount", [Sales Amount],
    "Order Quantity", [Order Quantity]
)'''
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{test_case['name']}:")
        print(f"MDX: {test_case['mdx'][:50]}...")
        
        try:
            # Step 1: Parse MDX
            parsed = parse_mdx(test_case['mdx'])
            print(f"✅ Parsed: {parsed}")
            
            # Step 2: Generate DAX
            dax = generate_dax(parsed)
            print(f"✅ Generated DAX:")
            print(dax)
            
            # Step 3: Verify result
            if dax == test_case['expected']:
                print("✅ PASSED")
                passed += 1
            else:
                print("❌ FAILED - Output doesn't match expected")
                print(f"Expected: {repr(test_case['expected'])}")
                print(f"Actual:   {repr(dax)}")
                failed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print(f"\n📊 FINAL RESULTS: {passed} passed, {failed} failed")
    return passed == len(test_cases)

if __name__ == "__main__":
    success = test_complete_workflow()
    exit(0 if success else 1)