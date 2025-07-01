"""Integration tests for DAX generator with complete IR queries."""

import pytest

from unmdx.ir import (
    Query, CubeReference, Measure, Dimension, Filter, Calculation,
    OrderBy, Limit, HierarchyReference, LevelReference, MemberSelection,
    DimensionFilter, MeasureFilter, NonEmptyFilter, FilterType, FilterOperator,
    AggregationType, MemberSelectionType, CalculationType, SortDirection,
    QueryMetadata, Constant, MeasureReference, BinaryOperation,
    FunctionCall, IifExpression, MemberReference, FunctionType,
    ComparisonOperator
)
from unmdx.dax_generator import DAXGenerator


class TestDAXGeneratorIntegration:
    """Integration tests for DAX generator."""
    
    @pytest.fixture
    def generator(self):
        """Create a DAX generator with formatting enabled."""
        return DAXGenerator(format_output=True)
    
    def test_basic_sales_by_category(self, generator):
        """Test Case 1: Basic sales by category query."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(
                    name="Sales Amount",
                    aggregation=AggregationType.SUM,
                    alias="Total Sales"
                )
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            filters=[
                Filter(
                    filter_type=FilterType.DIMENSION,
                    target=DimensionFilter(
                        dimension=Dimension(
                            hierarchy=HierarchyReference(table="Date", name="Calendar"),
                            level=LevelReference(name="Calendar Year"),
                            members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                        ),
                        operator=FilterOperator.EQUALS,
                        values=["CY 2023"]
                    )
                )
            ]
        )
        
        result = generator.generate(query)
        
        # Verify structure
        assert "EVALUATE" in result
        assert "SUMMARIZECOLUMNS(" in result
        assert "Product[Category]" in result
        assert 'FILTER(ALL(Date), Date[Calendar Year] = "CY 2023")' in result
        assert '"Total Sales", [Sales Amount]' in result
        
        # Should be properly formatted
        lines = result.split('\n')
        assert len(lines) > 3  # Multiple lines
        assert any(line.strip().startswith("Product[Category]") for line in lines)
    
    def test_multiple_measures_and_dimensions(self, generator):
        """Test Case 2: Multiple measures and dimensions."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM),
                Measure(name="Order Quantity", aggregation=AggregationType.SUM),
                Measure(name="Tax Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                ),
                Dimension(
                    hierarchy=HierarchyReference(table="Customer", name="Customer"),
                    level=LevelReference(name="Country"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ]
        )
        
        result = generator.generate(query)
        
        assert "Product[Category]" in result
        assert "Customer[Country]" in result
        assert '"Sales Amount", [Sales Amount]' in result
        assert '"Order Quantity", [Order Quantity]' in result
        assert '"Tax Amount", [Tax Amount]' in result
    
    def test_calculated_measure_profit_margin(self, generator):
        """Test Case 3: Calculated measure for profit margin."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM),
                Measure(name="Total Cost", aggregation=AggregationType.SUM),
                Measure(name="Profit Margin", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            calculations=[
                Calculation(
                    name="Profit Margin",
                    calculation_type=CalculationType.MEASURE,
                    expression=BinaryOperation(
                        left=BinaryOperation(
                            left=BinaryOperation(
                                left=MeasureReference("Sales Amount"),
                                operator="-",
                                right=MeasureReference("Total Cost")
                            ),
                            operator="/",
                            right=MeasureReference("Sales Amount")
                        ),
                        operator="*",
                        right=Constant(100)
                    ),
                    format_string="0.00%"
                )
            ]
        )
        
        result = generator.generate(query)
        
        # Check DEFINE section
        assert "DEFINE" in result
        assert "MEASURE" in result
        assert "Profit Margin" in result
        
        # Check calculation
        assert "DIVIDE(([Sales Amount] - [Total Cost]), [Sales Amount])" in result
        assert "* 100" in result
        assert 'FORMAT_STRING = "0.00%"' in result
        
        # Check main query
        assert "EVALUATE" in result
        assert "SUMMARIZECOLUMNS" in result
    
    def test_complex_filtering(self, generator):
        """Test Case 4: Complex filtering with multiple conditions."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Product Name"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            filters=[
                Filter(
                    filter_type=FilterType.DIMENSION,
                    target=DimensionFilter(
                        dimension=Dimension(
                            hierarchy=HierarchyReference(table="Product", name="Product"),
                            level=LevelReference(name="Category"),
                            members=MemberSelection(selection_type=MemberSelectionType.ALL)
                        ),
                        operator=FilterOperator.IN,
                        values=["Bikes", "Accessories"]
                    )
                ),
                Filter(
                    filter_type=FilterType.DIMENSION,
                    target=DimensionFilter(
                        dimension=Dimension(
                            hierarchy=HierarchyReference(table="Date", name="Calendar"),
                            level=LevelReference(name="Calendar Year"),
                            members=MemberSelection(selection_type=MemberSelectionType.ALL)
                        ),
                        operator=FilterOperator.IN,
                        values=["CY 2022", "CY 2023"]
                    )
                )
            ]
        )
        
        result = generator.generate(query)
        
        # Check multiple filters
        assert result.count("FILTER(ALL(") >= 2
        assert 'Product[Category] IN {"Bikes", "Accessories"}' in result
        assert 'Date[Calendar Year] IN {"CY 2022", "CY 2023"}' in result
    
    def test_sorting_and_limiting(self, generator):
        """Test Case 5: Sorting and limiting results."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Product Name"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            order_by=[
                OrderBy(expression="Sales Amount", direction=SortDirection.DESC)
            ],
            limit=Limit(count=10, offset=0)
        )
        
        result = generator.generate(query)
        
        # Check TOP N
        assert "TOPN(10" in result
        
        # Check ORDER BY
        assert "ORDER BY" in result
        assert "[Sales Amount] DESC" in result
    
    def test_time_intelligence_ytd(self, generator):
        """Test Case 6: Time intelligence - Year to Date calculation."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Sales YTD", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Calendar"),
                    level=LevelReference(name="Month"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            calculations=[
                Calculation(
                    name="Sales YTD",
                    calculation_type=CalculationType.MEASURE,
                    expression=FunctionCall(
                        function_type=FunctionType.MATH,
                        function_name="TOTALYTD",
                        arguments=[
                            MeasureReference("Sales Amount"),
                            MemberReference("Date", "Calendar", "Date")
                        ]
                    )
                )
            ],
            filters=[
                Filter(
                    filter_type=FilterType.DIMENSION,
                    target=DimensionFilter(
                        dimension=Dimension(
                            hierarchy=HierarchyReference(table="Date", name="Calendar"),
                            level=LevelReference(name="Calendar Year"),
                            members=MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
                        ),
                        operator=FilterOperator.EQUALS,
                        values=["CY 2023"]
                    )
                )
            ]
        )
        
        result = generator.generate(query)
        
        # Check time intelligence function
        assert "TOTALYTD" in result
        assert "[Sales Amount]" in result
        assert "Calendar[Date]" in result
    
    def test_conditional_formatting(self, generator):
        """Test Case 7: Conditional measure with IF statement."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Sales Status", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            calculations=[
                Calculation(
                    name="Sales Status",
                    calculation_type=CalculationType.MEASURE,
                    expression=IifExpression(
                        condition=BinaryOperation(
                            left=MeasureReference("Sales Amount"),
                            operator=">",
                            right=Constant(1000000)
                        ),
                        true_value=Constant("High"),
                        false_value=IifExpression(
                            condition=BinaryOperation(
                                left=MeasureReference("Sales Amount"),
                                operator=">",
                                right=Constant(500000)
                            ),
                            true_value=Constant("Medium"),
                            false_value=Constant("Low")
                        )
                    )
                )
            ]
        )
        
        result = generator.generate(query)
        
        # Check nested IF statements
        assert result.count("IF(") >= 2
        assert "([Sales Amount] > 1000000)" in result
        assert "([Sales Amount] > 500000)" in result
        assert '"High"' in result
        assert '"Medium"' in result
        assert '"Low"' in result
    
    def test_aggregation_functions(self, generator):
        """Test Case 8: Different aggregation functions."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Total Sales", aggregation=AggregationType.SUM, alias="Sum of Sales"),
                Measure(name="Average Price", aggregation=AggregationType.AVG, alias="Avg Price"),
                Measure(name="Customer Count", aggregation=AggregationType.DISTINCT_COUNT, alias="Unique Customers"),
                Measure(name="Min Order", aggregation=AggregationType.MIN, alias="Minimum Order"),
                Measure(name="Max Order", aggregation=AggregationType.MAX, alias="Maximum Order")
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Calendar"),
                    level=LevelReference(name="Year"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ]
        )
        
        result = generator.generate(query)
        
        # Check all aggregation types are handled
        assert '"Sum of Sales", [Total Sales]' in result
        assert '"Avg Price", [Average Price]' in result
        assert '"Unique Customers", [Customer Count]' in result
        assert '"Minimum Order", [Min Order]' in result
        assert '"Maximum Order", [Max Order]' in result
    
    def test_cross_join_multiple_dimensions(self, generator):
        """Test Case 9: Multiple dimensions (CrossJoin equivalent)."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                ),
                Dimension(
                    hierarchy=HierarchyReference(table="Customer", name="Customer"),
                    level=LevelReference(name="Country"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                ),
                Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Calendar"),
                    level=LevelReference(name="Year"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ]
        )
        
        result = generator.generate(query)
        
        # All dimensions should be in SUMMARIZECOLUMNS
        assert "Product[Category]" in result
        assert "Customer[Country]" in result
        assert "Date[Year]" in result
        
        # Should be a single SUMMARIZECOLUMNS, not nested
        assert result.count("SUMMARIZECOLUMNS") == 1
    
    def test_complex_calculation_with_variables(self, generator):
        """Test Case 10: Complex calculation that might use variables."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Contribution Margin", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Product Name"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            calculations=[
                Calculation(
                    name="Contribution Margin",
                    calculation_type=CalculationType.MEASURE,
                    expression=BinaryOperation(
                        left=BinaryOperation(
                            left=MeasureReference("Sales Amount"),
                            operator="-",
                            right=BinaryOperation(
                                left=MeasureReference("Product Cost"),
                                operator="+",
                                right=MeasureReference("Shipping Cost")
                            )
                        ),
                        operator="/",
                        right=MeasureReference("Sales Amount")
                    )
                )
            ]
        )
        
        result = generator.generate(query)
        
        # Check complex calculation structure
        assert "Contribution Margin" in result
        assert "DIVIDE(" in result
        assert "[Sales Amount] - ([Product Cost] + [Shipping Cost])" in result
        assert "[Sales Amount]" in result
    
    def test_empty_query_handling(self, generator):
        """Test handling of edge case - empty query."""
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[],
            dimensions=[]
        )
        
        result = generator.generate(query)
        
        # Should generate valid DAX even for empty query
        assert "EVALUATE" in result
        assert 'ROW("Value", BLANK())' in result
    
    def test_special_characters_handling(self, generator):
        """Test handling of special characters in identifiers."""
        query = Query(
            cube=CubeReference(name="Sales & Marketing"),
            measures=[
                Measure(name="Sales $ (USD)", aggregation=AggregationType.SUM),
                Measure(name="Growth %", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product-Line", name="Products"),
                    level=LevelReference(name="Sub-Category (Level 2)"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ]
        )
        
        result = generator.generate(query)
        
        # Special characters should be properly handled
        assert "Sales $ (USD)" in result or "[Sales $ (USD)]" in result
        assert "Growth %" in result or "[Growth %]" in result
        assert "Sub-Category (Level 2)" in result or "[Sub-Category (Level 2)]" in result
    
    def test_measure_filter_warning(self, generator):
        """Test that measure filters generate appropriate warnings."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[measure],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            filters=[
                Filter(
                    filter_type=FilterType.MEASURE,
                    target=MeasureFilter(
                        measure=measure,
                        operator=ComparisonOperator.GT,
                        value=100000
                    )
                )
            ]
        )
        
        result = generator.generate(query)
        warnings = generator.get_warnings()
        
        # Should generate warning about measure filters
        assert len(warnings) > 0
        assert any("Measure filter" in w or "CALCULATETABLE" in w for w in warnings)
        
        # But should still generate valid DAX
        assert "EVALUATE" in result
        assert "[Sales Amount] > 100000" in result
    
    def test_performance_large_query(self, generator):
        """Test performance with a large number of measures and dimensions."""
        # Create many measures
        measures = []
        for i in range(50):
            measures.append(
                Measure(name=f"Measure_{i}", aggregation=AggregationType.SUM)
            )
        
        # Create multiple dimensions
        dimensions = []
        for table in ["Product", "Customer", "Date", "Geography"]:
            dimensions.append(
                Dimension(
                    hierarchy=HierarchyReference(table=table, name=table),
                    level=LevelReference(name=f"{table}_Level"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            )
        
        query = Query(
            cube=CubeReference(name="Large Dataset"),
            measures=measures,
            dimensions=dimensions
        )
        
        # Should complete without error
        result = generator.generate(query)
        
        # Verify all measures are included
        for i in range(50):
            assert f"Measure_{i}" in result
        
        # Verify all dimensions are included
        for table in ["Product", "Customer", "Date", "Geography"]:
            assert f"{table}[{table}_Level]" in result