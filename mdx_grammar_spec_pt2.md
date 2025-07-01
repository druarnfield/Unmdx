# MDX Grammar Specification for Lark Parser - Part 2

# Advanced features and complex constructs

mdx_grammar_part2 = r”””
// ===========================
// Advanced Set Functions
// ===========================

```
// Extend function_name from Part 1
function_name: "CROSSJOIN"i
             | "FILTER"i
             | "DESCENDANTS"i
             | "ANCESTORS"i
             | "ASCENDANTS"i
             | "MEMBERS"i
             | "ALLMEMBERS"i
             | "CHILDREN"i
             | "SIBLINGS"i
             | "FIRSTSIBLING"i
             | "LASTSIBLING"i
             | "TOPCOUNT"i
             | "BOTTOMCOUNT"i
             | "TOPN"i
             | "BOTTOMN"i
             | "TOPPERCENT"i
             | "BOTTOMPERCENT"i
             | "TOPSUM"i
             | "BOTTOMSUM"i
             | "ORDER"i
             | "HIERARCHIZE"i
             | "DISTINCT"i
             | "UNION"i
             | "INTERSECT"i
             | "EXCEPT"i
             | "GENERATE"i
             | "EXTRACT"i
             | "NONEMPTY"i
             | "NONEMPTYCROSSJOIN"i
             | "EXISTS"i
             | "MEMBERRANGE"i
             | "STRTOMEMBER"i
             | "STRTOSET"i
             | "SUBSET"i
             | "HEAD"i
             | "TAIL"i
             | "RANK"i
             | "AGGREGATE"i
             | "AVG"i
             | "COUNT"i
             | "MAX"i
             | "MIN"i
             | "MEDIAN"i
             | "SUM"i
             | "STDDEV"i
             | "VAR"i
             | "COVARIANCE"i
             | "CORRELATION"i
             | "LINREGINTERCEPT"i
             | "LINREGSLOPE"i
             | "DRILLDOWNLEVEL"i
             | "DRILLDOWNMEMBER"i
             | "DRILLUPLEVEL"i
             | "DRILLUPMEMBER"i
             | "TOGGLEDRILLSTATE"i
             | time_intelligence_function
             | identifier  // Allow custom functions

// ===========================
// Time Intelligence Functions
// ===========================

time_intelligence_function: "PARALLELPERIOD"i
                          | "PERIODSTODATE"i
                          | "YTD"i
                          | "QTD"i  
                          | "MTD"i
                          | "WTD"i
                          | "LASTPERIODS"i
                          | "OPENINGPERIOD"i
                          | "CLOSINGPERIOD"i
                          | "DATEADD"i
                          | "DATESBETWEEN"i
                          | "DATESINPERIOD"i
                          | "PARALLELPERIOD"i
                          | "SAMEPERIODLASTYEAR"i
                          | "PREVIOUSDAY"i
                          | "PREVIOUSMONTH"i
                          | "PREVIOUSQUARTER"i
                          | "PREVIOUSYEAR"i
                          | "NEXTDAY"i
                          | "NEXTMONTH"i
                          | "NEXTQUARTER"i
                          | "NEXTYEAR"i
                          | "STARTOFYEAR"i
                          | "STARTOFQUARTER"i
                          | "STARTOFMONTH"i
                          | "ENDOFYEAR"i
                          | "ENDOFQUARTER"i
                          | "ENDOFMONTH"i

// ===========================
// DESCENDANTS Function Flags
// ===========================

// Special handling for DESCENDANTS with flags
descendants_call: "DESCENDANTS"i "(" member_expression "," level_specification ("," descendants_flag)? ")"

descendants_flag: "SELF"i
                | "AFTER"i
                | "BEFORE"i
                | "BEFORE_AND_AFTER"i
                | "SELF_AND_AFTER"i
                | "SELF_AND_BEFORE"i
                | "SELF_BEFORE_AFTER"i
                | "LEAVES"i

// Add to function_call
function_call: descendants_call
             | function_name "(" function_args? ")"

// ===========================
// Advanced Expressions
// ===========================

// CASE expressions
case_expression: simple_case | searched_case

simple_case: "CASE"i value_expression when_clause+ else_clause? "END"i

searched_case: "CASE"i when_condition+ else_clause? "END"i

when_clause: "WHEN"i value_expression "THEN"i value_expression

when_condition: "WHEN"i logical_expression "THEN"i value_expression

else_clause: "ELSE"i value_expression

// IIF expressions
iif_expression: "IIF"i "(" logical_expression "," value_expression "," value_expression ")"

// IS expressions
is_expression: value_expression "IS"i is_condition

is_condition: "NULL"i | "EMPTY"i | "LEAF"i | "DATAMEMBER"i

// Properties
property_expression: member_expression ".Properties"i "(" string_literal ("," property_flag)? ")"

property_flag: "TYPED"i

// Extend value_expression from Part 1
?value_expression: numeric_expression
                 | string_expression
                 | member_expression
                 | tuple_expression
                 | calculation_expression
                 | case_expression      // NEW
                 | iif_expression       // NEW
                 | property_expression  // NEW

// ===========================
// Set Operators
// ===========================

// Set operations can use operators
set_expression: "{" set_content? "}"
              | "{" set_expression_nested "}"
              | function_call
              | member_expression
              | set_expression set_operator set_expression  // NEW
              | "(" set_expression ")"  // NEW - parenthesized sets

set_operator: "+"  // Union
            | "-"  // Except
            | "*"  // CrossJoin

// ===========================
// Advanced Member Specifications
// ===========================

// Current member references
current_member: hierarchy_expression ".CurrentMember"i
              | dimension_expression ".CurrentMember"i

// Default member
default_member: hierarchy_expression ".DefaultMember"i
              | dimension_expression ".DefaultMember"i

// Unknown member
unknown_member: dimension_expression ".UnknownMember"i

// Add to member_expression
member_expression: qualified_member
                 | bracketed_identifier
                 | member_function
                 | current_member   // NEW
                 | default_member   // NEW
                 | unknown_member   // NEW
                 | calculated_reference  // NEW

// Calculated member reference with dimension
calculated_reference: "[" dimension_name "]" "." "[" calculated_member_name "]"

dimension_name: BRACKETED_ID_CONTENT
calculated_member_name: BRACKETED_ID_CONTENT

// ===========================
// Numeric Value Expressions
// ===========================

// Extend numeric functions
numeric_function: aggregate_function
                | "RANK"i "(" tuple_expression "," set_expression ")"
                | "COUNT"i "(" set_expression ("," count_flag)? ")"
                | "DISTINCTCOUNT"i "(" set_expression ")"
                | "CELLVALUE"i
                | "ORDINAL"i "(" level_expression ")"
                | "LEVELS"i "(" dimension_expression ")"
                | "DIMENSION"i "." "Properties"i "(" string_literal ")"

aggregate_function: ("AGGREGATE"i | "AVG"i | "SUM"i | "MIN"i | "MAX"i | "MEDIAN"i) 
                    "(" set_expression ("," numeric_expression)? ")"

count_flag: "INCLUDEEMPTY"i | "EXCLUDEEMPTY"i

// ===========================
// String Functions
// ===========================

string_function: "NAME"i "(" member_expression ")"
               | "UNIQUENAME"i "(" member_expression ")"
               | "MEMBERTOSTR"i "(" member_expression ")"
               | "TUPLETOSTR"i "(" tuple_expression ")"
               | "SETTOSTR"i "(" set_expression ")"
               | "DIMENSIONNAME"i "(" member_expression ")"
               | "LEVELNAME"i "(" member_expression ")"
               | "USERNAME"i
               | "CUSTOMDATA"i
               | "CAPTION"i "(" member_expression ")"
               | "FORMAT"i "(" value_expression "," string_literal ")"
               | "FORMATCURRENCY"i "(" numeric_expression ("," numeric_expression)* ")"

// Add to string_expression
?string_expression: string_literal
                  | member_expression
                  | string_function  // NEW
                  | string_expression "&" string_expression  // String concatenation

// ===========================
// Logical Functions
// ===========================

logical_function: "ISEMPTY"i "(" value_expression ")"
                | "ISLEAF"i "(" member_expression ")"
                | "ISANCESTOR"i "(" member_expression "," member_expression ")"
                | "ISSIBLING"i "(" member_expression "," member_expression ")"
                | "ISGENERATION"i "(" member_expression "," numeric_expression ")"
                | "CONTAINS"i "(" string_expression "," string_expression ")"

// Add to logical_expression
logical_expression: comparison_expression
                  | logical_expression "AND"i logical_expression
                  | logical_expression "OR"i logical_expression  
                  | logical_expression "XOR"i logical_expression  // NEW
                  | "NOT"i logical_expression
                  | "(" logical_expression ")"
                  | logical_function  // NEW
                  | is_expression     // NEW

// ===========================
// Sub-Select (Nested SELECT)
// ===========================

// Allow sub-selects in FROM clause
cube_specification: bracketed_identifier
                  | identifier
                  | qualified_name
                  | "(" select_statement ")"  // NEW - sub-select

// ===========================
// CREATE and DROP Statements
// ===========================

// For session-scoped calculations
create_statement: create_member | create_set

create_member: "CREATE"i "SESSION"i? "MEMBER"i member_identifier "AS"i value_expression 
               ("," member_property)*

create_set: "CREATE"i "SESSION"i? "SET"i set_alias "AS"i set_expression

member_property: property_name "=" property_value

property_name: "FORMAT_STRING"i | "VISIBLE"i | "SOLVE_ORDER"i | identifier

property_value: string_literal | NUMBER | boolean_literal

boolean_literal: "TRUE"i | "FALSE"i

drop_statement: "DROP"i ("MEMBER"i member_identifier | "SET"i set_alias)

// Add to main query options
?start: query | create_statement | drop_statement

// ===========================
// Advanced Calculation Features
// ===========================

// Scope statements (for advanced calculations)
scope_statement: "SCOPE"i "(" scope_expression ")" ";" 
                 assignment_statement* 
                 "END"i "SCOPE"i ";"

scope_expression: set_expression | tuple_expression

assignment_statement: (tuple_expression | set_expression) "=" value_expression ";"

// THIS keyword for assignments
this_expression: "THIS"i

// Add THIS to value expressions
?value_expression: numeric_expression
                 | string_expression
                 | member_expression
                 | tuple_expression
                 | calculation_expression
                 | case_expression
                 | iif_expression
                 | property_expression
                 | this_expression  // NEW

// ===========================
// KPI Functions
// ===========================

kpi_function: "KPIValue"i "(" kpi_name ")"
            | "KPIGoal"i "(" kpi_name ")"  
            | "KPIStatus"i "(" kpi_name ")"
            | "KPITrend"i "(" kpi_name ")"
            | "KPIWeight"i "(" kpi_name ")"
            | "KPICurrentTimeMember"i "(" kpi_name ")"

kpi_name: string_literal | identifier

// Add to numeric/value expressions
numeric_expression: NUMBER
                  | member_expression
                  | calculation_expression
                  | "(" numeric_expression ")"
                  | numeric_function
                  | kpi_function  // NEW

// ===========================
// Error Recovery Rules
// ===========================

// Allow recovery from common errors
error_recovery: UNEXPECTED_CHAR+ -> skip_unexpected

// Add unexpected character handling
UNEXPECTED_CHAR: /[^\s\w\[\]\(\){},.:;"'=<>+\-*\/\\&|!]/

// ===========================
// Extended Comments
// ===========================

// Capture different comment styles and extract hints
OPTIMIZER_HINT: "/*" /\s*OPTIMIZER\s*:/ /[^*]*/ "*/"
HINT_COMMENT: "/*" /\s*HINT\s*:/ /[^*]*/ "*/"
EXECUTION_COMMENT: "/*" /\s*EXECUTION_MODE\s*:/ /[^*]*/ "*/"
CACHE_COMMENT: "/*" /\s*CACHE/ /[^*]*/ "*/"

// Keep all comment types
%ignore COMMENT
```

“””

# Combine Part 1 and Part 2

complete_mdx_grammar = mdx_grammar + “\n\n” + mdx_grammar_part2

# Example advanced query test

if **name** == “**main**”:
from lark import Lark, Transformer, v_args

```
# Create parser with complete grammar
parser = Lark(complete_mdx_grammar,
              parser='earley',
              ambiguity='resolve',
              propagate_positions=True,
              maybe_placeholders=True)

# Test advanced features
advanced_queries = [
    # CASE expression
    """
    WITH MEMBER [Measures].[Price Group] AS
        CASE 
            WHEN [Measures].[Unit Price] < 10 THEN "Low"
            WHEN [Measures].[Unit Price] < 50 THEN "Medium"
            ELSE "High"
        END
    SELECT {[Measures].[Price Group]} ON 0
    FROM [Adventure Works]
    """,
    
    # Set operators
    """
    SELECT {[Measures].[Sales Amount]} ON COLUMNS,
           {[Product].[Category].[Bikes]} + {[Product].[Category].[Accessories]} ON ROWS
    FROM [Adventure Works]
    """,
    
    # Time intelligence with DESCENDANTS
    """
    SELECT {[Measures].[Sales Amount]} ON 0,
           DESCENDANTS([Date].[Calendar].[Calendar Year].&[2023], 
                      [Date].[Calendar].[Month], 
                      SELF_AND_AFTER) ON 1
    FROM [Adventure Works]
    """,
    
    # Sub-select
    """
    SELECT {[Measures].[Sales Amount]} ON COLUMNS,
           {[Product].[Category].Members} ON ROWS
    FROM (
        SELECT {[Customer].[Country].[United States]} ON 0
        FROM [Adventure Works]
    )
    """,
    
    # Complex with properties and KPI
    """
    WITH MEMBER [Measures].[Member Caption] AS
        [Product].CurrentMember.Properties("MEMBER_CAPTION", TYPED)
    SELECT {[Measures].[Sales Amount], 
            [Measures].[Member Caption],
            KPIValue("Revenue Growth")} ON 0,
           NONEMPTY([Product].[Product].Members, [Measures].[Sales Amount]) ON 1
    FROM [Adventure Works]
    """
]

for i, query in enumerate(advanced_queries, 1):
    try:
        tree = parser.parse(query)
        print(f"Advanced query {i} parsed successfully!")
    except Exception as e:
        print(f"Advanced query {i} failed: {e}")

# Test error recovery with invalid query
invalid_query = """
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       {[Product].[Category].Members} + @ + {[Customer].[Country].Members} ON ROWS
FROM [Adventure Works]
"""

try:
    tree = parser.parse(invalid_query)
    print("\nInvalid query parsed (with error recovery)")
except Exception as e:
    print(f"\nInvalid query failed as expected: {e}")
```
