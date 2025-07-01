# MDX Grammar Specification for Lark Parser - Part 1

# Designed to handle poorly formatted MDX from Necto SSAS cubes

mdx_grammar = r”””
// ===========================
// Main Query Structure
// ===========================

```
?start: query

query: with_clause? select_statement

// WITH clause for calculated members and named sets
with_clause: "WITH"i with_item+

with_item: member_definition
         | set_definition

member_definition: "MEMBER"i member_identifier "AS"i value_expression format_clause?

set_definition: "SET"i set_alias "AS"i set_expression

format_clause: ","? "FORMAT_STRING"i "=" string_literal

// SELECT statement - the core of MDX
select_statement: "SELECT"i axis_specification_list 
                  "FROM"i cube_specification 
                  where_clause?

axis_specification_list: axis_specification ("," axis_specification)*

axis_specification: non_empty? set_expression "ON"i axis

non_empty: "NON"i "EMPTY"i

axis: "COLUMNS"i -> axis_columns
    | "ROWS"i -> axis_rows  
    | "PAGES"i -> axis_pages
    | "CHAPTERS"i -> axis_chapters
    | "SECTIONS"i -> axis_sections
    | "AXIS"i "(" NUMBER ")" -> axis_number
    | NUMBER -> axis_number_short  // Allow "ON 0" syntax

// WHERE clause (slicer)
where_clause: "WHERE"i slicer_specification

slicer_specification: tuple_expression
                    | member_expression
                    | "(" ")"  // Empty WHERE clause (from test cases)

// ===========================
// Cube Specification
// ===========================

cube_specification: bracketed_identifier
                  | identifier
                  | qualified_name

// ===========================
// Set Expressions
// ===========================

set_expression: "{" set_content? "}"  // Allow empty sets
              | "{" set_expression_nested "}"  // Handle nested sets
              | function_call
              | member_expression  // Single member is a valid set

// Handle arbitrary nesting like {{{{[Measures].[Sales]}}}}
set_expression_nested: set_expression ("," set_expression)*

set_content: set_element ("," set_element)* ","?  // Allow trailing comma

?set_element: tuple_expression
            | member_expression
            | set_expression  // Allow nested sets
            | member_range
            |  // Allow empty elements (from spaghetti MDX)

member_range: member_expression ":" member_expression

// ===========================
// Tuple Expressions
// ===========================

tuple_expression: "(" tuple_content ")"

tuple_content: member_expression ("," member_expression)*

// ===========================
// Member Expressions
// ===========================

member_expression: qualified_member
                 | bracketed_identifier
                 | member_function

// Handle various member reference formats
qualified_member: hierarchy_expression "." level_expression "." member_identifier
                | hierarchy_expression "." member_identifier
                | dimension_expression "." hierarchy_expression "." member_identifier
                | dimension_expression "." member_identifier

// Member functions
member_function: member_expression "." "Members"i
               | member_expression "." "Children"i
               | member_expression "." "Parent"i
               | member_expression "." "FirstChild"i
               | member_expression "." "LastChild"i
               | member_expression "." "Lead"i "(" numeric_expression ")"
               | member_expression "." "Lag"i "(" numeric_expression ")"
               | member_expression "." "&" bracketed_identifier  // Key reference like .&[2023]

// ===========================
// Function Calls
// ===========================

function_call: function_name "(" function_args? ")"

function_name: "CROSSJOIN"i
             | "FILTER"i
             | "DESCENDANTS"i
             | "MEMBERS"i
             | "CHILDREN"i
             | "TOPCOUNT"i
             | "BOTTOMCOUNT"i
             | "TOPN"i
             | "ORDER"i
             | "HIERARCHIZE"i
             | "DISTINCT"i
             | "AGGREGATE"i
             | "AVG"i
             | "COUNT"i
             | "MAX"i
             | "MIN"i
             | "SUM"i
             | "PARALLELPERIOD"i
             | identifier  // Allow custom functions

function_args: function_arg ("," function_arg)*

?function_arg: set_expression
             | value_expression
             | numeric_expression
             | logical_expression
             | level_specification

// ===========================
// Value Expressions
// ===========================

?value_expression: numeric_expression
                 | string_expression
                 | member_expression
                 | tuple_expression
                 | calculation_expression

calculation_expression: value_expression arithmetic_op value_expression
                      | "(" calculation_expression ")"
                      | function_call

arithmetic_op: "+" | "-" | "*" | "/"

?numeric_expression: NUMBER
                   | member_expression
                   | calculation_expression
                   | "(" numeric_expression ")"

?string_expression: string_literal
                  | member_expression

// ===========================
// Logical Expressions
// ===========================

logical_expression: comparison_expression
                  | logical_expression "AND"i logical_expression
                  | logical_expression "OR"i logical_expression
                  | "NOT"i logical_expression
                  | "(" logical_expression ")"

comparison_expression: value_expression comparison_op value_expression

comparison_op: "=" | "<>" | "<" | ">" | "<=" | ">="

// ===========================
// Identifiers and Literals
// ===========================

// Dimension/hierarchy/level specifications
dimension_expression: bracketed_identifier | identifier
hierarchy_expression: bracketed_identifier | identifier
level_expression: bracketed_identifier | identifier
level_specification: bracketed_identifier | identifier | NUMBER

// Member identifiers can be complex
member_identifier: bracketed_identifier
                 | identifier
                 | compound_identifier

compound_identifier: identifier ("." identifier)+

// Qualified names for cubes
qualified_name: bracketed_identifier "." bracketed_identifier
              | identifier "." identifier

// Set aliases for WITH SET
set_alias: bracketed_identifier | identifier

// Bracketed identifiers - the most common form
bracketed_identifier: "[" BRACKETED_ID_CONTENT "]"

// Simple identifiers
identifier: CNAME

// String literals
string_literal: ESCAPED_STRING

// ===========================
// Comments (including optimizer hints)
// ===========================

COMMENT: "/*" /(.|\n|\r)*?/ "*/"
       | "--" /[^\n\r]*/
       | "//" /[^\n\r]*/

// ===========================
// Terminals
// ===========================

// Content inside brackets - very permissive
BRACKETED_ID_CONTENT: /[^\[\]]+/

// Standard identifier
CNAME: /[a-zA-Z_][a-zA-Z0-9_]*/

// Numbers
NUMBER: /[+-]?[0-9]+(\.[0-9]+)?/

// Strings
ESCAPED_STRING: /"[^"]*"/
              | /'[^']*'/

// ===========================
// Whitespace and Ignored
// ===========================

%import common.WS
%ignore WS

// Keep comments as tokens for optimizer hints
// Parser can extract these during transformation
```

“””

# Example usage and test

if **name** == “**main**”:
from lark import Lark

```
# Create parser with error handling
parser = Lark(mdx_grammar, 
              parser='earley',  # More tolerant of ambiguity
              ambiguity='resolve',  # Auto-resolve ambiguities
              propagate_positions=True,  # Track line/column for errors
              maybe_placeholders=True)  # Allow optional elements

# Test with a simple query
test_query = """
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       {[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].&[2023])
"""

try:
    tree = parser.parse(test_query)
    print("Parse successful!")
    print(tree.pretty())
except Exception as e:
    print(f"Parse failed: {e}")

# Test with complex nested query
complex_query = """
/* OPTIMIZER: USE_AGGREGATE_AWARE */
WITH MEMBER [Measures].[Avg Price] AS 
    [Measures].[Sales Amount] / [Measures].[Order Quantity],
    FORMAT_STRING = "Currency"
SELECT NON EMPTY {{{[Measures].[Sales Amount]}, {[Measures].[Avg Price]}}} ON 0,
       CROSSJOIN({[Product].[Category].Members}, 
                 {[Customer].[Country].Members}) ON 1
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].&[2023], [Geography].[Country].&[United States])
"""

try:
    tree = parser.parse(complex_query)
    print("\nComplex query parsed successfully!")
except Exception as e:
    print(f"\nComplex query parse failed: {e}")
```
