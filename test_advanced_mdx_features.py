#!/usr/bin/env python3
"""
Test advanced MDX features that Agent #1 might have missed
"""

from unmdx.api import parse_mdx
from unmdx.config import create_default_config

def test_advanced_mdx_features():
    """Test sophisticated MDX patterns Agent #1 might have missed"""
    
    advanced_cases = [
        # SCOPE statements - not in grammar
        ('SCOPE([Date].[Year].[2023]); [Measures].[Sales] = [Measures].[Sales] * 1.1; END SCOPE;', 'SCOPE statement'),
        
        # KPI functions - not in grammar
        ('SELECT KPIGoal("Sales KPI") ON 0 FROM [Adventure Works]', 'KPI function'),
        ('SELECT KPIValue("Revenue KPI") ON 0 FROM [Adventure Works]', 'KPI value'),
        
        # DRILLTHROUGH - not in grammar
        ('DRILLTHROUGH SELECT {[Measures].[Sales]} ON 0 FROM [Adventure Works]', 'DRILLTHROUGH'),
        
        # CELL CALCULATION - not in grammar
        ('CALCULATE; [Measures].[Sales] = [Measures].[Sales] * 1.1; END CALCULATE;', 'CELL CALCULATION'),
        
        # Named sets in WITH clause - should work
        ('WITH SET [Top Products] AS TopCount([Product].[Product].Members, 10, [Measures].[Sales]) SELECT {[Measures].[Sales]} ON 0, [Top Products] ON 1 FROM [Adventure Works]', 'Named set'),
        
        # Complex FILTER function - should work
        ('SELECT {[Measures].[Sales]} ON 0, Filter([Product].[Product].Members, [Measures].[Sales] > 1000) ON 1 FROM [Adventure Works]', 'Complex FILTER'),
        
        # Multiple WITH clauses - should work
        ('''WITH
            MEMBER [Measures].[Profit] AS [Measures].[Sales] - [Measures].[Cost]
            SET [Top Markets] AS TopCount([Geography].[Country].Members, 5, [Measures].[Sales])
        SELECT {[Measures].[Sales], [Measures].[Profit]} ON 0, [Top Markets] ON 1 FROM [Adventure Works]''', 'Multiple WITH'),
        
        # IIF function - should work
        ('WITH MEMBER [Measures].[Sales Category] AS IIF([Measures].[Sales] > 1000, "High", "Low") SELECT {[Measures].[Sales Category]} ON 0 FROM [Adventure Works]', 'IIF function'),
        
        # CASE expressions - should work
        ('''WITH MEMBER [Measures].[Sales Level] AS
            CASE 
                WHEN [Measures].[Sales] > 10000 THEN "High"
                WHEN [Measures].[Sales] > 5000 THEN "Medium"
                ELSE "Low"
            END
        SELECT {[Measures].[Sales Level]} ON 0 FROM [Adventure Works]''', 'CASE expression'),
        
        # Complex member functions - should work
        ('SELECT {[Measures].[Sales]} ON 0, [Date].[Calendar].[Calendar Year].[2023].Lead(1) ON 1 FROM [Adventure Works]', 'Lead function'),
        ('SELECT {[Measures].[Sales]} ON 0, [Date].[Calendar].[Calendar Year].[2023].Lag(1) ON 1 FROM [Adventure Works]', 'Lag function'),
        
        # PARALLELPERIOD function - should work
        ('WITH MEMBER [Measures].[Prior Year] AS ([Measures].[Sales], ParallelPeriod([Date].[Calendar].[Calendar Year], 1)) SELECT {[Measures].[Sales], [Measures].[Prior Year]} ON 0 FROM [Adventure Works]', 'PARALLELPERIOD'),
        
        # GENERATE function - should work
        ('SELECT {[Measures].[Sales]} ON 0, Generate([Product].[Category].Members, [Product].[Product].Members) ON 1 FROM [Adventure Works]', 'GENERATE function'),
        
        # Complex set operations - should work
        ('SELECT {[Measures].[Sales]} ON 0, ([Product].[Category].[Bikes] + [Product].[Category].[Accessories]) * [Geography].[Country].Members ON 1 FROM [Adventure Works]', 'Complex set operations'),
        
        # DESCENDANTS function - should work
        ('SELECT {[Measures].[Sales]} ON 0, Descendants([Geography].[Country].[United States], [Geography].[State-Province]) ON 1 FROM [Adventure Works]', 'DESCENDANTS function'),
        
        # String concatenation - should work
        ('WITH MEMBER [Measures].[Full Name] AS [Customer].[Customer].[First Name] & " " & [Customer].[Customer].[Last Name] SELECT {[Measures].[Full Name]} ON 0 FROM [Adventure Works]', 'String concatenation'),
    ]
    
    print("=== TESTING ADVANCED MDX FEATURES (Agent #2 Deep Dive) ===")
    passed = 0
    failed = 0
    
    for mdx, description in advanced_cases:
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
    
    print(f"\nAdvanced Features: {passed}/{len(advanced_cases)} passed")
    return passed, failed

def test_security_injection_patterns():
    """Test security and injection patterns"""
    
    security_cases = [
        # SQL injection attempts
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube]; DROP TABLE Users; --", 'SQL injection attempt'),
        ("SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Name] = 'test'; DELETE FROM Users; --'", 'SQL injection in WHERE'),
        
        # XML/Script injection
        ("SELECT {[Measures].[<script>alert('xss')</script>]} ON 0 FROM [Cube]", 'XSS in measure name'),
        ("SELECT {[Measures].[Sales]} ON 0 FROM [<script>alert('xss')</script>]", 'XSS in cube name'),
        
        # Buffer overflow attempts
        ("SELECT {[Measures].[Sales]} ON 0 FROM [" + "A" * 10000 + "]", 'Buffer overflow attempt'),
        
        # Unicode normalization
        ("SELECT {[Measures].[Salés]} ON 0 FROM [Cube]", 'Unicode normalization'),
        
        # Null bytes
        ("SELECT {[Measures].[Sales\x00]} ON 0 FROM [Cube]", 'Null byte injection'),
    ]
    
    print("\n=== TESTING SECURITY/INJECTION PATTERNS (Agent #2 Security) ===")
    passed = 0
    failed = 0
    
    for mdx, description in security_cases:
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
    
    print(f"\nSecurity Patterns: {passed}/{len(security_cases)} passed")
    return passed, failed

def test_real_world_complexity():
    """Test real-world complex MDX queries"""
    
    real_world_cases = [
        # Oracle Essbase style query
        ('''SELECT 
            {[Measures].[Sales], [Measures].[Cost], [Measures].[Profit]} ON COLUMNS,
            CROSSJOIN(
                DESCENDANTS([Geography].[All Geography], [Geography].[Country]),
                DESCENDANTS([Product].[All Products], [Product].[Category])
            ) ON ROWS
        FROM [Sales]
        WHERE ([Time].[2023], [Scenario].[Actual])''', 'Oracle Essbase style'),
        
        # Microsoft SSAS style with multiple dimensions
        ('''SELECT 
            NON EMPTY {[Measures].[Internet Sales Amount], [Measures].[Internet Order Quantity]} ON COLUMNS,
            NON EMPTY CROSSJOIN(
                HIERARCHIZE(
                    DRILLDOWNLEVEL({[Date].[Calendar].[All Periods]})
                ),
                TOPCOUNT(
                    [Product].[Product Categories].[Category].MEMBERS,
                    5,
                    [Measures].[Internet Sales Amount]
                )
            ) ON ROWS
        FROM [Adventure Works]
        WHERE ([Sales Territory].[Sales Territory Country].&[United States])''', 'Microsoft SSAS complex'),
        
        # IBM Cognos style
        ('''SELECT 
            {[Measures].[Revenue]} ON 0,
            {TM1FILTERBYLEVEL(
                {TM1DRILLDOWNMEMBER({[Time].[Time].[All Years]}, ALL, RECURSIVE)},
                0
            )} ON 1
        FROM [sales_and_marketing]''', 'IBM Cognos/TM1 style'),
        
        # Mondrian/Pentaho style
        ('''SELECT 
            {[Measures].[Store Sales]} ON COLUMNS,
            HIERARCHIZE(
                UNION(
                    CROSSJOIN(
                        [Time].[1997].Children,
                        [Store].[All Stores].[USA].Children
                    ),
                    CROSSJOIN(
                        [Time].[1998].Children,
                        [Store].[All Stores].[USA].Children
                    )
                )
            ) ON ROWS
        FROM [Sales]''', 'Mondrian/Pentaho style'),
    ]
    
    print("\n=== TESTING REAL-WORLD COMPLEXITY (Agent #2 Production) ===")
    passed = 0
    failed = 0
    
    for mdx, description in real_world_cases:
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
    
    print(f"\nReal-World Complexity: {passed}/{len(real_world_cases)} passed")
    return passed, failed

if __name__ == "__main__":
    print("🔬 AGENT #2 DEEP DIVE: Advanced MDX Features & Real-World Patterns")
    print("=" * 80)
    
    # Test advanced features
    p1, f1 = test_advanced_mdx_features()
    
    # Test security patterns
    p2, f2 = test_security_injection_patterns()
    
    # Test real-world complexity
    p3, f3 = test_real_world_complexity()
    
    total_passed = p1 + p2 + p3
    total_failed = f1 + f2 + f3
    total_tests = total_passed + total_failed
    
    print(f"\n📊 DEEP DIVE RESULTS:")
    print(f"Advanced Features: {p1}/{p1+f1} passed")
    print(f"Security Patterns: {p2}/{p2+f2} passed")
    print(f"Real-World Complexity: {p3}/{p3+f3} passed")
    print(f"Total: {total_passed}/{total_tests} passed ({total_passed/total_tests*100:.1f}%)")