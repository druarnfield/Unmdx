"""Basic MDX query fixtures for testing."""

# Test Case 1: Simple measure query
SIMPLE_MEASURE = """
SELECT {[Measures].[Sales Amount]} ON COLUMNS
FROM [Adventure Works]
"""

# Test Case 2: Measure with dimension
MEASURE_WITH_DIMENSION = """
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       {[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
"""

# Test Case 3: Multiple measures
MULTIPLE_MEASURES = """
SELECT {[Measures].[Sales Amount], [Measures].[Order Count]} ON COLUMNS
FROM [Adventure Works]
"""

# Test Case 4: WHERE clause
SIMPLE_WHERE = """
SELECT {[Measures].[Sales Amount]} ON COLUMNS
FROM [Adventure Works]
WHERE ([Date].[Calendar Year].[CY 2023])
"""

# Test Case 5: CrossJoin
SIMPLE_CROSSJOIN = """
SELECT {[Measures].[Sales Amount]} ON COLUMNS,
       CrossJoin([Product].[Category].Members, [Date].[Calendar Year].Members) ON ROWS
FROM [Adventure Works]
"""

# Expected DAX outputs for validation
EXPECTED_DAX = {
    "SIMPLE_MEASURE": """
EVALUATE
ROW("Sales Amount", [Sales Amount])
""".strip(),

    "MEASURE_WITH_DIMENSION": """
EVALUATE
SUMMARIZECOLUMNS(
    Product[Category],
    "Sales Amount", [Sales Amount]
)
""".strip(),
}

# Expected human-readable explanations
EXPECTED_EXPLANATIONS = {
    "SIMPLE_MEASURE": "Calculate total Sales Amount from Adventure Works data",
    "MEASURE_WITH_DIMENSION": "Calculate total Sales Amount for each Product Category from Adventure Works data",
}
