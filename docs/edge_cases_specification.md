# MDX Edge Cases Specification

**Document Version**: 1.0  
**Date**: 2025-07-05  
**Authors**: Claude Team Lead, Agent #1, Agent #2  
**Status**: Phase 5 Planning Document

## Overview

This document specifies uncommon but valid MDX patterns that the UnMDX v2 implementation must handle to achieve production readiness with real-world tools like Oracle Necto, Microsoft SSAS, Excel, and IBM TM1/Cognos.

## Executive Summary

**Current Compatibility**: 40% success rate on comprehensive edge case testing  
**Target Compatibility**: 90%+ success rate for production deployment  
**Implementation Phase**: Phase 5 (Weeks 11-12 of recovery plan)

## Critical Edge Cases (Must Fix for Production)

### 1. Quoted Bracket Syntax ⚠️ **CRITICAL**

**Issue**: Tools like Oracle Necto generate quoted curly braces and member names that cause total parser failure.

**Failing Examples**:
```mdx
-- Quoted empty sets (Oracle Necto common pattern)
SELECT "{}" ON ROWS FROM [Cube]
SELECT '{}' ON ROWS FROM [Cube]

-- Quoted member names (escaping special characters)
SELECT {"[Measures].[Sales]"} ON 0 FROM [Cube]
SELECT {'[Product].[Category].[Women\'s Clothing]'} ON 1 FROM [Cube]

-- Mixed quote patterns in same query
SELECT "{[Measures].[Sales]}" ON COLUMNS, '[Product].[Category].Members' ON ROWS
```

**Root Cause**: Grammar doesn't recognize quoted strings as valid set expressions or member references.

**Implementation Requirements**:
- Add string literal terminals to Lark grammar
- Support both single and double quotes
- Handle escaped quotes within strings
- Maintain backward compatibility with unquoted syntax

**Priority**: CRITICAL - User-reported blocker for Oracle Necto compatibility

### 2. Logical Expressions in WHERE Clauses ⚠️ **CRITICAL**

**Issue**: Complex WHERE clauses with boolean logic completely unsupported.

**Failing Examples**:
```mdx
-- Boolean operators
WHERE [ProductType] = 'Electronics' AND [Year] = 2023
WHERE [Sales] > 1000 OR [Quantity] > 100
WHERE NOT [Status] = 'Inactive'

-- Comparison operators  
WHERE [Amount] >= 500
WHERE [Date] BETWEEN '2023-01-01' AND '2023-12-31'
WHERE [Category] <> 'Discontinued'

-- IN expressions
WHERE [Year] IN {2022, 2023, 2024}
WHERE [Country] IN {'USA', 'Canada', 'Mexico'}

-- Complex logical combinations
WHERE ([Sales] > 1000 AND [Year] = 2023) OR ([Quantity] > 100 AND [Year] = 2024)
```

**Root Cause**: WHERE clause grammar only accepts tuple/member expressions, not logical expressions.

**Implementation Requirements**:
- Extend grammar to support logical operators (AND, OR, NOT)
- Add comparison operators (=, <>, >, <, >=, <=, BETWEEN)
- Implement operator precedence rules
- Generate correct DAX with proper CALCULATETABLE logic

**Priority**: CRITICAL - Essential for real-world filtering capabilities

### 3. WHERE Clause Transformation Issues ⚠️ **CRITICAL**

**Issue**: Even basic WHERE clauses generate incorrect DAX in production scenarios.

**Current Problem**:
```mdx
-- Input
WHERE ([Date].[Year].&[2023])

-- Current Output (WRONG)
FILTER(SUMMARIZECOLUMNS(...), 'Date'[Year] = 2023)

-- Required Output (CORRECT)  
CALCULATETABLE(SUMMARIZECOLUMNS(...), 'Date'[Year] = 2023)
```

**Implementation Requirements**:
- Fix transformer to generate CALCULATETABLE instead of FILTER
- Ensure proper filter context propagation
- Handle multiple filters correctly
- Validate DAX output against Power BI

**Priority**: CRITICAL - Breaks basic functionality in production

### 4. Data Type Literals ⚠️ **CRITICAL**

**Issue**: Missing support for common data type patterns used in real-world MDX.

**Failing Examples**:
```mdx
-- Currency values
WHERE [Sales] >= $1000
WHERE [Revenue] = €999.99
WHERE [Price] <= ¥5000

-- Date literals
WHERE [Date] = #2023-01-01#
WHERE [StartDate] >= '2023/01/01'
WHERE [EndDate] <= "2023-12-31"

-- Percentage values
WHERE [GrowthRate] >= 50%
WHERE [Margin] = 0.15

-- Scientific notation
WHERE [Population] >= 1.5E+6
WHERE [Precision] <= 1e-10

-- Special values
WHERE [Value] IS NULL
WHERE [Amount] = INF
WHERE [Error] = NaN
```

**Implementation Requirements**:
- Add currency symbol recognition ($, €, ¥, £, etc.)
- Support multiple date literal formats
- Handle percentage notation
- Add scientific notation support
- Support special values (NULL, INF, NaN)

**Priority**: CRITICAL - Common in business intelligence queries

## High Priority Edge Cases

### 5. Advanced MDX Statements 🔺 **HIGH**

**Issue**: Modern MDX uses advanced statements not currently supported.

**Failing Examples**:
```mdx
-- SCOPE statements (common in SSAS)
SCOPE([Date].[Year].[2023]);
  [Measures].[Sales] = [Measures].[Sales] * 1.1;
END SCOPE;

-- DRILLTHROUGH statements
DRILLTHROUGH MAXROWS 1000
SELECT [Measures].[Sales] ON 0 FROM [Cube]
WHERE [Product].[Category].[Bikes]

-- Calculated member with advanced functions
WITH MEMBER [Measures].[Growth] AS
  ([Measures].[Sales], [Date].[Year].CurrentMember) - 
  ([Measures].[Sales], [Date].[Year].CurrentMember.Lag(1))
```

**Implementation Requirements**:
- Add SCOPE statement grammar and DAX conversion
- Implement DRILLTHROUGH statement support
- Add member navigation functions (Lag, Lead, CurrentMember)
- Support calculated member advanced expressions

**Priority**: HIGH - Required for SSAS compatibility

### 6. Nested Comments 🔺 **HIGH**

**Issue**: Some tools generate nested comments that break parsing.

**Failing Examples**:
```mdx
-- Nested block comments
SELECT /* outer /* inner comment */ still outer */ [Measures].[Sales] ON 0

-- Comments with special characters
SELECT [Measures].[Sales] /* Price in $/€/¥ */ ON 0

-- Multiple comment styles mixed
SELECT -- Single line comment
  /* Block comment */ [Measures].[Sales] ON 0
```

**Implementation Requirements**:
- Update comment regex to handle nested /* */ properly
- Support mixed comment styles
- Handle special characters in comments

**Priority**: HIGH - Automated tool compatibility

### 7. Member Navigation Functions 🔺 **HIGH**

**Issue**: Time intelligence and hierarchy navigation functions missing.

**Failing Examples**:
```mdx
-- Time intelligence
[Date].[Year].CurrentMember.Lag(1)
[Date].[Month].FirstChild
[Date].[Quarter].LastChild

-- Hierarchy navigation
[Product].[Category].Parent
[Geography].[Country].[USA].Children
[Employee].[Manager].Ancestors(2)

-- Set functions with navigation
DESCENDANTS([Geography].[Country].[USA], [Geography].[State])
ASCENDANTS([Product].[SubCategory].[Mountain Bikes])
```

**Implementation Requirements**:
- Add member navigation function grammar
- Implement DAX equivalents for time intelligence
- Support hierarchy traversal functions
- Generate appropriate DAX with RELATED/RELATEDTABLE

**Priority**: HIGH - Common in analytical queries

## Medium Priority Edge Cases

### 8. Tool-Specific Syntax Variations 🔶 **MEDIUM**

**Issue**: Different tools have slight syntax variations.

**Examples by Tool**:

**Excel MDX**:
```mdx
-- Excel uses AXIS() function consistently
SELECT [Measures].[Sales] ON AXIS(0),
       [Product].[Category].Members ON AXIS(1)

-- Excel generates verbose member keys
WHERE [Date].[Calendar Year].&[2023]&[1]&[1]
```

**IBM TM1/Cognos**:
```mdx
-- TM1 uses string dimensions differently
SELECT [}Measures].[Revenue] ON 0
FROM [}tm1srv01:Sales]

-- Cognos uses quoted dimension names
SELECT '[Measures].[Sales Amount]' ON COLUMNS
```

**Microsoft SSAS**:
```mdx
-- SSAS supports user-defined functions
SELECT MyCustomFunction([Product], [Date]) ON 0

-- SSAS has specific KPI syntax
SELECT KPIGoal("Sales Growth") ON 0
```

### 9. Internationalization Patterns 🔶 **MEDIUM**

**Issue**: Non-English member names and special characters.

**Examples**:
```mdx
-- Right-to-left languages
SELECT [المنتجات].[الفئة].Members ON 0

-- Asian languages
SELECT [製品].[カテゴリ].Members ON 0
SELECT [产品].[类别].Members ON 0

-- European diacritics
SELECT [Produits].[Catégorie].Members ON 0
SELECT [Ürünler].[Kategorie].Members ON 0

-- Mixed scripts in same query
SELECT [Product].[Catégorie].Members ON COLUMNS,
       [地域].[国家].Members ON ROWS
```

### 10. Performance Edge Cases 🔶 **MEDIUM**

**Issue**: Queries with extreme complexity that test parser limits.

**Examples**:
```mdx
-- Very long member names (1000+ characters)
SELECT [VeryLongDimensionNameThatGoesOnForever...] ON 0

-- Deeply nested sets (50+ levels)
SELECT {{{{{{{{{{[Measures].[Sales]}}}}}}}}} ON 0

-- Many parameters in functions (100+ arguments)
CROSSJOIN([A], [B], [C], ... [ZZ], [AAA], [BBB])

-- Complex calculated members (500+ line expressions)
WITH MEMBER [Measures].[Complex] AS
  CASE WHEN ... (very long expression) ... END
```

## Low Priority Edge Cases

### 11. Legacy MDX Patterns 🔹 **LOW**

**Issue**: Deprecated but still valid MDX syntax.

**Examples**:
```mdx
-- Old-style axis syntax
SELECT [Measures].[Sales] ON 0,
       [Product].Members ON 1,
       [Date].Members ON 2

-- Legacy function names
SELECT SUBSET([Product].Members, 10) ON 0

-- Deprecated operators
WHERE [Amount] IS NOT EMPTY
```

### 12. Security Edge Cases 🔹 **LOW**

**Issue**: Malicious input patterns that could cause issues.

**Examples**:
```mdx
-- Potential injection attempts
SELECT '; DROP TABLE Measures; --' ON 0

-- Buffer overflow attempts  
SELECT [AAAA...] (10000+ A's) ON 0

-- XML injection
SELECT '<script>alert("xss")</script>' ON 0
```

## Implementation Roadmap

### Phase 5 Week 11: Critical Edge Cases
1. **Quoted bracket syntax** - Essential for Oracle Necto
2. **Logical expressions in WHERE** - Essential for filtering
3. **WHERE clause transformation fixes** - Critical bug fixes
4. **Basic data type literals** - Currency, dates, percentages

### Phase 5 Week 12: Advanced Patterns  
1. **Advanced MDX statements** - SCOPE, DRILLTHROUGH
2. **Member navigation functions** - Lag, Lead, hierarchy traversal
3. **Nested comments** - Tool compatibility
4. **Tool-specific variations** - Excel, TM1, SSAS quirks

### Future Phases (Post-Production)
1. **Internationalization** - Full Unicode support
2. **Performance edge cases** - Extreme complexity handling
3. **Legacy patterns** - Backward compatibility
4. **Security hardening** - Malicious input protection

## Success Criteria

### Minimum Viable Production (Phase 5 Completion)
- ✅ **90%+ success rate** on comprehensive edge case test suite
- ✅ **Oracle Necto compatibility** - Handle quoted brackets and tool output
- ✅ **Logical WHERE clauses** - Support boolean expressions and comparisons
- ✅ **Correct DAX transformation** - Fix WHERE clause generation issues

### Full Production Readiness (Future)
- ✅ **95%+ success rate** on all edge cases including low priority
- ✅ **Multi-tool compatibility** - Excel, SSAS, TM1, Cognos support
- ✅ **Performance guarantees** - Handle extreme complexity gracefully
- ✅ **Security validation** - Resist malicious input patterns

## Testing Strategy

### Edge Case Test Suite
1. **Automated regression tests** for all documented patterns
2. **Real-world MDX samples** from production tools
3. **Property-based testing** for unusual input combinations
4. **Performance benchmarks** for complex edge cases
5. **Security penetration testing** for malicious patterns

### Tool Validation
1. **Oracle Necto** - Test with actual Necto-generated MDX
2. **Microsoft SSAS** - Validate against SSAS query samples
3. **Excel Pivot Tables** - Test Excel-generated MDX patterns
4. **IBM TM1/Cognos** - Verify TM1-specific syntax support

### DAX Output Validation
1. **Power BI compatibility** - All generated DAX must execute successfully
2. **Semantic equivalence** - MDX and DAX results must match
3. **Performance optimization** - DAX should be efficient and readable
4. **Error handling** - Graceful failures with helpful error messages

## Conclusion

The edge case investigation reveals that while UnMDX v2 has a solid foundation, critical gaps prevent production deployment. The proposed Phase 5 implementation plan addresses the most important real-world compatibility issues identified by comprehensive testing with two specialized agents.

**Priority Order**:
1. **CRITICAL** - Quoted brackets, logical WHERE, data types (Production blockers)
2. **HIGH** - Advanced statements, member navigation (Full feature parity) 
3. **MEDIUM** - Tool variations, internationalization (Enhanced compatibility)
4. **LOW** - Legacy patterns, security (Future hardening)

This specification provides a roadmap for achieving production-ready MDX compatibility with real-world tools and edge cases.