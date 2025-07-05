#!/usr/bin/env python3
"""
Validate Agent #1's critical edge case findings with real tests
"""

from unmdx.api import parse_mdx
from unmdx.config import create_default_config

def test_quoted_brackets():
    """Test quoted brackets - Agent #1's HIGH priority issue"""
    test_cases = [
        # Agent #1's examples
        ('SELECT "{}" ON ROWS FROM [Cube]', 'Quoted empty brackets'),
        ("SELECT '{}' ON ROWS FROM [Cube]", 'Single quoted brackets'),
        ('SELECT {"[Measures].[Sales]"} ON 0 FROM [Cube]', 'Quoted member in set'),
        
        # Additional edge cases
        ('SELECT "{[Measures].[Sales Amount]}" ON 0 FROM [Adventure Works]', 'Quoted measure reference'),
        ('SELECT \'[Product].[Category].Members\' ON 1 FROM [Adventure Works]', 'Single quoted dimension'),
        ('SELECT {"{}"} ON 0 FROM [Adventure Works]', 'Quoted brackets in set'),
    ]
    
    print("=== TESTING QUOTED BRACKETS (Agent #1 HIGH Priority) ===")
    passed = 0
    failed = 0
    
    for mdx, description in test_cases:
        try:
            result = parse_mdx(mdx)
            if result.parse_tree:
                print(f"✅ {description}: PASSED")
                passed += 1
            else:
                print(f"❌ {description}: FAILED - No parse tree")
                failed += 1
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:100]}...")
            failed += 1
    
    print(f"Quoted Brackets: {passed}/{len(test_cases)} passed")
    return passed, failed

def test_logical_expressions_where():
    """Test logical expressions in WHERE - Agent #1's HIGH priority issue"""
    test_cases = [
        # Agent #1's examples
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [A] AND [B]', 'Simple AND'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [A] OR [B]', 'Simple OR'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [A] AND [B] OR [C]', 'Mixed AND/OR'),
        
        # Additional edge cases
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE NOT [A]', 'NOT operator'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE ([A] AND [B]) OR [C]', 'Parenthesized logic'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Amount] > 1000', 'Comparison'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Date] IN {[2023], [2024]}', 'IN expression'),
    ]
    
    print("\n=== TESTING LOGICAL EXPRESSIONS IN WHERE (Agent #1 HIGH Priority) ===")
    passed = 0
    failed = 0
    
    for mdx, description in test_cases:
        try:
            result = parse_mdx(mdx)
            if result.parse_tree:
                print(f"✅ {description}: PASSED")
                passed += 1
            else:
                print(f"❌ {description}: FAILED - No parse tree")
                failed += 1
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:100]}...")
            failed += 1
    
    print(f"Logical WHERE: {passed}/{len(test_cases)} passed")
    return passed, failed

def test_nested_comments():
    """Test nested comments - Agent #1's MEDIUM priority issue"""
    test_cases = [
        # Agent #1's examples
        ('SELECT /* outer /* inner */ comment */ {[Measures].[Sales]} ON 0 FROM [Cube]', 'Nested /* */ comments'),
        ('SELECT /* first */ {[Measures].[Sales]} /* second */ ON 0 FROM [Cube]', 'Multiple comments'),
        ('SELECT {[Measures].[Sales]} /* comment with /* nested */ text */ ON 0 FROM [Cube]', 'Complex nesting'),
        
        # Mixed comment types
        ('SELECT -- line comment\n{[Measures].[Sales]} /* block */ ON 0 FROM [Cube]', 'Mixed comment types'),
        ('SELECT /* /* deeply /* nested */ */ */ {[Measures].[Sales]} ON 0 FROM [Cube]', 'Triple nested'),
    ]
    
    print("\n=== TESTING NESTED COMMENTS (Agent #1 MEDIUM Priority) ===")
    passed = 0
    failed = 0
    
    for mdx, description in test_cases:
        try:
            result = parse_mdx(mdx)
            if result.parse_tree:
                print(f"✅ {description}: PASSED")
                passed += 1
            else:
                print(f"❌ {description}: FAILED - No parse tree")
                failed += 1
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:100]}...")
            failed += 1
    
    print(f"Nested Comments: {passed}/{len(test_cases)} passed")
    return passed, failed

def test_additional_edge_cases():
    """Test additional edge cases Agent #1 might have missed"""
    test_cases = [
        # Currency and formatting
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Amount] > $1000', 'Currency symbol'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Amount] > 1,000.50', 'Number formatting'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Percent] > 50%', 'Percentage'),
        
        # Date/time literals
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Date] > #2023-01-01#', 'Date hash format'),
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Date] > '2023/01/01'", 'Date string format'),
        
        # Unicode and international
        ('SELECT {[Measures].[Verkäufe]} ON 0 FROM [Cube]', 'German umlauts'),
        ('SELECT {[Measures].[销售额]} ON 0 FROM [Cube]', 'Chinese characters'),
        ('SELECT {[Measures].[المبيعات]} ON 0 FROM [Cube]', 'Arabic text'),
        
        # Extreme values
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Amount] > 1E6', 'Scientific notation'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Amount] > -INF', 'Negative infinity'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Amount] <> NaN', 'Not a number'),
        
        # Empty and null cases
        ('SELECT {} ON 0 FROM [Cube]', 'Empty set'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Name] = ""', 'Empty string'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Value] IS NULL', 'NULL comparison'),
    ]
    
    print("\n=== TESTING ADDITIONAL EDGE CASES (Agent #2 Expansion) ===")
    passed = 0
    failed = 0
    
    for mdx, description in test_cases:
        try:
            result = parse_mdx(mdx)
            if result.parse_tree:
                print(f"✅ {description}: PASSED")
                passed += 1
            else:
                print(f"❌ {description}: FAILED - No parse tree")
                failed += 1
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:100]}...")
            failed += 1
    
    print(f"Additional Edge Cases: {passed}/{len(test_cases)} passed")
    return passed, failed

def test_tool_specific_patterns():
    """Test patterns specific to different MDX tools"""
    test_cases = [
        # Microsoft SSAS patterns
        ('SELECT {[Measures].[Sales]} ON 0 FROM [Adventure Works DW] WHERE [Date].[Calendar].[Calendar Year].&[2023]', 'SSAS key reference'),
        ('SELECT {[Measures].[Sales]} ON 0 FROM [$Cube] WHERE [Date].[All Date].[2023]', 'SSAS All member'),
        
        # IBM Cognos patterns
        ('SELECT {[Measures].[Sales]} ON 0 FROM [sales_and_marketing] WHERE [Years].[Years].[Year]->?[2023]?', 'Cognos syntax'),
        
        # Excel pivot patterns
        ('SELECT {[Measures].[Sum of Sales]} ON 0 FROM [WorksheetConnection_]', 'Excel generated'),
        
        # Mondrian/Pentaho patterns
        ('SELECT {[Measures].[Sales]} ON 0 FROM [FoodMart] WHERE [Time].[1997].[Q1]', 'Mondrian hierarchy'),
    ]
    
    print("\n=== TESTING TOOL-SPECIFIC PATTERNS (Agent #2 Research) ===")
    passed = 0
    failed = 0
    
    for mdx, description in test_cases:
        try:
            result = parse_mdx(mdx)
            if result.parse_tree:
                print(f"✅ {description}: PASSED")
                passed += 1
            else:
                print(f"❌ {description}: FAILED - No parse tree")
                failed += 1
        except Exception as e:
            print(f"❌ {description}: FAILED - {str(e)[:100]}...")
            failed += 1
    
    print(f"Tool-Specific: {passed}/{len(test_cases)} passed")
    return passed, failed

if __name__ == "__main__":
    print("🔍 AGENT #2 VALIDATION: Testing Agent #1's Edge Case Findings")
    print("=" * 80)
    
    # Test Agent #1's critical findings
    p1, f1 = test_quoted_brackets()
    p2, f2 = test_logical_expressions_where()
    p3, f3 = test_nested_comments()
    
    # Test additional edge cases
    p4, f4 = test_additional_edge_cases()
    p5, f5 = test_tool_specific_patterns()
    
    total_passed = p1 + p2 + p3 + p4 + p5
    total_failed = f1 + f2 + f3 + f4 + f5
    total_tests = total_passed + total_failed
    
    print(f"\n📊 FINAL VALIDATION RESULTS:")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {total_passed/total_tests*100:.1f}%")
    
    print(f"\n🎯 PRIORITY VALIDATION:")
    print(f"Agent #1 HIGH Priority (Quoted Brackets): {p1}/{p1+f1} passed")
    print(f"Agent #1 HIGH Priority (Logical WHERE): {p2}/{p2+f2} passed")
    print(f"Agent #1 MEDIUM Priority (Nested Comments): {p3}/{p3+f3} passed")
    print(f"Agent #2 Expansion (Additional): {p4}/{p4+f4} passed")
    print(f"Agent #2 Research (Tool-Specific): {p5}/{p5+f5} passed")