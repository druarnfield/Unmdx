#!/usr/bin/env python3
"""
Debug script to test various MDX edge cases to understand parsing behavior.
This will help identify what edge cases are and aren't handled.
"""

from unmdx.api import parse_mdx
from unmdx.parser.mdx_parser import MDXParser

def test_edge_case(description, mdx, expected_to_parse=True):
    """Test a single edge case and report results"""
    print(f"\n=== {description} ===")
    print(f"MDX: {repr(mdx)}")
    
    try:
        # Test with parse_mdx API
        result = parse_mdx(mdx)
        if result.parse_tree is not None:
            print("✅ PARSED successfully")
            return True
        else:
            print("❌ FAILED to parse (no parse tree)")
            return False
    except Exception as e:
        print(f"❌ PARSING ERROR: {str(e)[:200]}")
        return False

def main():
    """Test comprehensive edge cases"""
    
    print("🔍 Testing MDX Edge Cases for UnMDX Parser")
    print("=" * 70)
    
    # 1. STRING QUOTING AND ESCAPING EDGE CASES
    print("\n📝 1. STRING QUOTING AND ESCAPING")
    
    edge_cases = [
        # Quoted brackets (user mentioned these)
        ("Quoted brackets - double quotes", 'SELECT "{}" ON ROWS FROM [Cube]'),
        ("Quoted brackets - single quotes", "SELECT '{}' ON ROWS FROM [Cube]"),
        ("Quoted member name", 'SELECT {"[Measures].[Sales]"} ON 0 FROM [Cube]'),
        ("Mixed quotes", """SELECT '[Measures].[Sales "Special"]' ON 0 FROM [Cube]"""),
        
        # Escaped quotes
        ("Escaped double quotes", '''SELECT {"He said \\"hello\\""} ON 0 FROM [Cube]'''),
        ("Escaped single quotes", """SELECT {'He said \\'hello\\''} ON 0 FROM [Cube]"""),
        
        # Unicode and special characters
        ("Unicode in member name", "SELECT {[Measures].[Café]} ON 0 FROM [Cube]"),
        ("Special chars in brackets", "SELECT {[Product].[Women's Clothing]} ON 0 FROM [Cube]"),
        ("Numbers as member names", "SELECT {[Year].[2024]} ON 0 FROM [Cube]"),
        ("Reserved words as members", "SELECT {[SELECT].[FROM]} ON 0 FROM [Cube]"),
    ]
    
    for desc, mdx in edge_cases:
        test_edge_case(desc, mdx)
    
    # 2. COMMENT VARIATIONS
    print("\n💬 2. COMMENT VARIATIONS")
    
    comment_cases = [
        ("Single line comment //", "SELECT {[Measures].[Sales]} ON 0 // comment\nFROM [Cube]"),
        ("Single line comment --", "SELECT {[Measures].[Sales]} ON 0 -- comment\nFROM [Cube]"),
        ("Multi-line comment", "SELECT /* comment */ {[Measures].[Sales]} ON 0 FROM [Cube]"),
        ("Comment in expression", "SELECT {[Measures]./* comment */[Sales]} ON 0 FROM [Cube]"),
        ("Nested comments", "SELECT /* outer /* inner */ comment */ {[Measures].[Sales]} ON 0 FROM [Cube]"),
        ("Comment with special chars", "SELECT {[Measures].[Sales]} ON 0 /* €$@#% */ FROM [Cube]"),
    ]
    
    for desc, mdx in comment_cases:
        test_edge_case(desc, mdx)
    
    # 3. WHITESPACE AND FORMATTING EDGE CASES
    print("\n🔲 3. WHITESPACE AND FORMATTING")
    
    whitespace_cases = [
        ("Excessive whitespace", "SELECT     {[Measures].[Sales]}     ON     0     FROM     [Cube]"),
        ("No whitespace", "SELECT{[Measures].[Sales]}ON 0FROM[Cube]"),
        ("Mixed tabs and spaces", "SELECT\t{[Measures].[Sales]}\tON\t0\tFROM\t[Cube]"),
        ("Trailing whitespace", "SELECT {[Measures].[Sales]} ON 0 FROM [Cube]   \n   "),
        ("Multiple newlines", "SELECT\n\n{[Measures].[Sales]}\n\nON\n\n0\n\nFROM\n\n[Cube]"),
    ]
    
    for desc, mdx in whitespace_cases:
        test_edge_case(desc, mdx)
    
    # 4. KEYWORD VARIATIONS
    print("\n🔤 4. KEYWORD CASE VARIATIONS")
    
    keyword_cases = [
        ("All lowercase", "select {[measures].[sales]} on 0 from [cube]"),
        ("Mixed case", "SeLeCt {[MeAsUrEs].[SaLeS]} oN 0 fRoM [CuBe]"),
        ("AXIS syntax", "SELECT {[Measures].[Sales]} ON AXIS(0) FROM [Cube]"),
        ("Alternative axis names", "SELECT {[Measures].[Sales]} ON COLUMNS, {[Product].Members} ON ROWS FROM [Cube]"),
        ("Boolean operators", "SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Date].[Year].&[2023] AND [Product].[Category].&[Bikes]"),
    ]
    
    for desc, mdx in keyword_cases:
        test_edge_case(desc, mdx)
    
    # 5. NUMBER AND VALUE FORMATTING
    print("\n🔢 5. NUMBER AND VALUE FORMATTING")
    
    number_cases = [
        ("Scientific notation", "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Cube] WHERE [Measures].[Amount] > 1.23E+10"),
        ("Negative scientific", "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Cube] WHERE [Measures].[Amount] > 1e-5"),
        ("European number format", "SELECT {[Measures].[Amount].&[1 000,50]} ON 0 FROM [Cube]"),
        ("Hexadecimal", "SELECT {[Color].&[0xFF]} ON 0 FROM [Cube]"),
        ("Boolean literals", "SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [IsActive] = true"),
        ("NULL values", "SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Field] IS NULL"),
    ]
    
    for desc, mdx in number_cases:
        test_edge_case(desc, mdx)
    
    # 6. MEMBER NAME EDGE CASES
    print("\n👤 6. MEMBER NAME EDGE CASES")
    
    member_cases = [
        ("Empty member name", "SELECT {[].} ON 0 FROM [Cube]"),
        ("Very long member name", f"SELECT {{[Product].[{'A' * 1000}]}} ON 0 FROM [Cube]"),
        ("Member with dots", "SELECT {[Version].[1.0.2]} ON 0 FROM [Cube]"),
        ("Member with slashes", "SELECT {[Path].[C:/Users/Data]} ON 0 FROM [Cube]"),
        ("Member with backslashes", "SELECT {[Path].[C:\\\\Users\\\\Data]} ON 0 FROM [Cube]"),
    ]
    
    for desc, mdx in member_cases:
        test_edge_case(desc, mdx)
    
    # 7. SET EXPRESSION EDGE CASES  
    print("\n📦 7. SET EXPRESSION EDGE CASES")
    
    set_cases = [
        ("Empty set", "SELECT {} ON 0 FROM [Cube]"),
        ("Set with only spaces", "SELECT {   } ON 0 FROM [Cube]"),
        ("Deeply nested sets", "SELECT {{{{{{[Measures].[Sales]}}}}}} ON 0 FROM [Cube]"),
        ("Mixed set patterns", "SELECT {{{[A]}, {[B], [C]}}} ON 0 FROM [Cube]"),
        ("Set with comments", "SELECT {/* comment */} ON 0 FROM [Cube]"),
        ("Trailing commas", "SELECT {[A], [B], [C],} ON 0 FROM [Cube]"),
    ]
    
    for desc, mdx in set_cases:
        test_edge_case(desc, mdx)
    
    # 8. FUNCTION CALL EDGE CASES
    print("\n⚙️ 8. FUNCTION CALL EDGE CASES")
    
    function_cases = [
        ("Function with no params", "SELECT FUNCTION() ON 0 FROM [Cube]"),
        ("Many parameters", "SELECT CROSSJOIN([A], [B], [C], [D], [E], [F]) ON 0 FROM [Cube]"),
        ("Nested functions", "SELECT FILTER(CROSSJOIN([A], [B]), [Measure] > 0) ON 0 FROM [Cube]"),
        ("Custom function", "SELECT MyCustomFunction([A], [B]) ON 0 FROM [Cube]"),
    ]
    
    for desc, mdx in function_cases:
        test_edge_case(desc, mdx)
    
    # 9. WHERE CLAUSE EDGE CASES
    print("\n🔍 9. WHERE CLAUSE EDGE CASES")
    
    where_cases = [
        ("Complex boolean", "SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE ([A] AND [B]) OR ([C] AND [D])"),
        ("IN expression", "SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE [Date] IN {[2023], [2024]}"),
        ("Empty WHERE", "SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE ()"),
        ("Subquery in WHERE", "SELECT {[Measures].[Sales]} ON 0 FROM [Cube] WHERE EXISTS([Date].Members)"),
    ]
    
    for desc, mdx in where_cases:
        test_edge_case(desc, mdx)
    
    # 10. CALCULATED MEMBER EDGE CASES
    print("\n🧮 10. CALCULATED MEMBER EDGE CASES")
    
    calc_cases = [
        ("String concatenation", "WITH MEMBER [Measures].[FullName] AS [FirstName] + ' ' + [LastName] SELECT {[Measures].[FullName]} ON 0 FROM [Cube]"),
        ("Conditional expression", "WITH MEMBER [Measures].[SafeSales] AS IIF([Sales] > 0, [Sales], 0) SELECT {[Measures].[SafeSales]} ON 0 FROM [Cube]"),
        ("Complex math", "WITH MEMBER [Measures].[Complex] AS ([A] + [B]) * ([C] / [D]) SELECT {[Measures].[Complex]} ON 0 FROM [Cube]"),
    ]
    
    for desc, mdx in calc_cases:
        test_edge_case(desc, mdx)

    print(f"\n🏁 Edge case testing complete!")

if __name__ == "__main__":
    main()