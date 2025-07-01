"""Unit tests for DAXGenerator."""

import pytest
from datetime import datetime

from unmdx.ir import (
    Query, CubeReference, Measure, Dimension, Filter, Calculation,
    OrderBy, Limit, HierarchyReference, LevelReference, MemberSelection,
    DimensionFilter, MeasureFilter, NonEmptyFilter, FilterType, FilterOperator,
    AggregationType, MemberSelectionType, CalculationType, SortDirection,
    QueryMetadata, Constant, MeasureReference, BinaryOperation,
    ComparisonOperator
)
from unmdx.dax_generator import DAXGenerator, DAXGenerationError


class TestDAXGenerator:
    """Test cases for DAXGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create a DAXGenerator instance."""
        return DAXGenerator(format_output=False)  # Disable formatting for easier testing
    
    @pytest.fixture
    def formatted_generator(self):
        """Create a DAXGenerator with formatting enabled."""
        return DAXGenerator(format_output=True)
    
    @pytest.fixture
    def simple_query(self):
        """Create a simple query for testing."""
        return Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Total Sales", aggregation=AggregationType.SUM)
            ],
            dimensions=[],
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
    
    @pytest.fixture
    def dimensional_query(self):
        """Create a query with dimensions."""
        return Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM),
                Measure(name="Order Count", aggregation=AggregationType.COUNT)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                ),
                Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Calendar"),
                    level=LevelReference(name="Year"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
    
    # Basic query generation tests
    
    def test_generate_simple_measure_query(self, generator, simple_query):
        """Test generating a simple measure-only query."""
        result = generator.generate(simple_query)
        
        assert "EVALUATE" in result
        assert "ROW(" in result
        assert '"Total Sales"' in result
        assert "[Total Sales]" in result
    
    def test_generate_empty_query(self, generator):
        """Test generating an empty query."""
        query = Query(
            cube=CubeReference(name="Test"),
            measures=[],
            dimensions=[],
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert "EVALUATE" in result
        assert "ROW(" in result
        assert "BLANK()" in result
    
    def test_generate_dimensional_query(self, generator, dimensional_query):
        """Test generating a query with dimensions."""
        result = generator.generate(dimensional_query)
        
        assert "EVALUATE" in result
        assert "SUMMARIZECOLUMNS(" in result
        assert "Product[Category]" in result
        assert "Date[Year]" in result
        assert '"Sales Amount"' in result
        assert '"Order Count"' in result
    
    # Measure generation tests
    
    def test_generate_measure_with_alias(self, generator):
        """Test generating measures with aliases."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(
                    name="Sales Amount",
                    aggregation=AggregationType.SUM,
                    alias="Total Revenue"
                )
            ],
            dimensions=[],
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert '"Total Revenue"' in result
        assert "[Sales Amount]" in result
    
    def test_generate_measure_with_aggregation(self, generator):
        """Test generating measures with different aggregations."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Amount", aggregation=AggregationType.SUM),
                Measure(name="Quantity", aggregation=AggregationType.AVG),
                Measure(name="CustomerID", aggregation=AggregationType.DISTINCT_COUNT)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        # Aggregations should be handled appropriately
        assert "[Amount]" in result
        assert "[Quantity]" in result
        assert "[CustomerID]" in result
    
    # Dimension generation tests
    
    def test_generate_dimension_with_specific_members(self, generator):
        """Test generating dimensions with specific member selection."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(
                        selection_type=MemberSelectionType.SPECIFIC,
                        specific_members=["Bikes", "Accessories"]
                    )
                )
            ],
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert "FILTER(ALL(Product)" in result
        assert "Bikes" in result
        assert "Accessories" in result
        assert " IN " in result
    
    # Filter generation tests
    
    def test_generate_dimension_filter(self, generator):
        """Test generating dimension filters."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Geography", name="Geography"),
            level=LevelReference(name="Country"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
        
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[],
            filters=[
                Filter(
                    filter_type=FilterType.DIMENSION,
                    target=DimensionFilter(
                        dimension=dimension,
                        operator=FilterOperator.EQUALS,
                        values=["USA"]
                    )
                )
            ],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert "FILTER(ALL(Geography)" in result
        assert 'Geography[Country] = "USA"' in result
    
    def test_generate_dimension_filter_in_operator(self, generator):
        """Test generating dimension filters with IN operator."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Color"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
        
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[],
            filters=[
                Filter(
                    filter_type=FilterType.DIMENSION,
                    target=DimensionFilter(
                        dimension=dimension,
                        operator=FilterOperator.IN,
                        values=["Red", "Blue", "Green"]
                    )
                )
            ],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert "FILTER(ALL(Product)" in result
        assert "Product[Color] IN {" in result
        assert '"Red"' in result
        assert '"Blue"' in result
        assert '"Green"' in result
    
    def test_generate_measure_filter(self, generator):
        """Test generating measure filters."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[measure],
            dimensions=[],
            filters=[
                Filter(
                    filter_type=FilterType.MEASURE,
                    target=MeasureFilter(
                        measure=measure,
                        operator=ComparisonOperator.GT,
                        value=1000
                    )
                )
            ],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        # Measure filters should generate warnings
        assert len(generator.get_warnings()) > 0
        assert "Measure filters" in generator.get_warnings()[0]
    
    def test_generate_non_empty_filter(self, generator):
        """Test generating non-empty filters."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[],
            filters=[
                Filter(
                    filter_type=FilterType.NON_EMPTY,
                    target=NonEmptyFilter(measure="Sales Amount")
                )
            ],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        # NON EMPTY should generate warnings
        assert len(generator.get_warnings()) > 0
        assert "NON EMPTY" in generator.get_warnings()[0]
    
    # Calculation generation tests
    
    def test_generate_calculated_measure(self, generator):
        """Test generating calculated measures."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Profit Margin", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[],
            filters=[],
            calculations=[
                Calculation(
                    name="Profit Margin",
                    calculation_type=CalculationType.MEASURE,
                    expression=BinaryOperation(
                        left=BinaryOperation(
                            left=MeasureReference("Profit"),
                            operator="/",
                            right=MeasureReference("Revenue")
                        ),
                        operator="*",
                        right=Constant(100)
                    )
                )
            ],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert "DEFINE" in result
        assert "MEASURE" in result
        assert "Profit Margin" in result
        assert "DIVIDE([Profit], [Revenue])" in result
        assert "* 100" in result
    
    def test_generate_calculated_measure_with_format(self, generator):
        """Test generating calculated measures with format strings."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Growth Rate", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[],
            filters=[],
            calculations=[
                Calculation(
                    name="Growth Rate",
                    calculation_type=CalculationType.MEASURE,
                    expression=MeasureReference("YoY Growth"),
                    format_string="0.00%"
                )
            ],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert "FORMAT_STRING = \"0.00%\"" in result
    
    # Order By generation tests
    
    def test_generate_order_by(self, generator):
        """Test generating ORDER BY clause."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Date", name="Calendar"),
                    level=LevelReference(name="Year"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            filters=[],
            calculations=[],
            order_by=[
                OrderBy(expression="Year", direction=SortDirection.DESC),
                OrderBy(expression="Sales Amount", direction=SortDirection.ASC)
            ],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert "ORDER BY" in result
        assert "[Year] DESC" in result
        assert "[Sales Amount]" in result
    
    # Limit generation tests
    
    def test_generate_limit(self, generator):
        """Test generating LIMIT/TOP clause."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[],
            filters=[],
            calculations=[],
            order_by=[],
            limit=Limit(count=10, offset=0),
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert "TOPN(10" in result
    
    def test_generate_limit_with_offset(self, generator):
        """Test generating LIMIT with offset (unsupported)."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM)
            ],
            dimensions=[],
            filters=[],
            calculations=[],
            order_by=[],
            limit=Limit(count=10, offset=5),
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        # Should generate warning about OFFSET
        warnings = generator.get_warnings()
        assert len(warnings) > 0
        assert "OFFSET" in warnings[0]
    
    # Complex query tests
    
    def test_generate_complex_query(self, generator):
        """Test generating a complex query with multiple features."""
        # Create dimensions
        product_dim = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(
                selection_type=MemberSelectionType.SPECIFIC,
                specific_members=["Bikes", "Accessories"]
            )
        )
        
        date_dim = Dimension(
            hierarchy=HierarchyReference(table="Date", name="Calendar"),
            level=LevelReference(name="Year"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL)
        )
        
        # Create query
        query = Query(
            cube=CubeReference(name="Adventure Works", database="AW", schema="dbo"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM, alias="Total Sales"),
                Measure(name="Order Count", aggregation=AggregationType.COUNT),
                Measure(name="Avg Discount", aggregation=AggregationType.AVG, alias="Average Discount"),
                Measure(name="Profit Margin", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[product_dim, date_dim],
            filters=[
                Filter(
                    filter_type=FilterType.DIMENSION,
                    target=DimensionFilter(
                        dimension=Dimension(
                            hierarchy=HierarchyReference(table="Geography", name="Geography"),
                            level=LevelReference(name="Country"),
                            members=MemberSelection(selection_type=MemberSelectionType.ALL)
                        ),
                        operator=FilterOperator.IN,
                        values=["USA", "Canada", "Mexico"]
                    )
                )
            ],
            calculations=[
                Calculation(
                    name="Profit Margin",
                    calculation_type=CalculationType.MEASURE,
                    expression=BinaryOperation(
                        left=BinaryOperation(
                            left=MeasureReference("Total Profit"),
                            operator="/",
                            right=MeasureReference("Sales Amount")
                        ),
                        operator="*",
                        right=Constant(100)
                    ),
                    format_string="0.00%"
                )
            ],
            order_by=[
                OrderBy(expression="Year", direction=SortDirection.DESC),
                OrderBy(expression="Total Sales", direction=SortDirection.DESC)
            ],
            limit=Limit(count=100, offset=0),
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        
        # Check all components are present
        assert "DEFINE" in result
        assert "MEASURE" in result
        assert "Profit Margin" in result
        assert "EVALUATE" in result
        assert "SUMMARIZECOLUMNS(" in result
        assert "Product[Category]" in result
        assert "Date[Year]" in result
        assert "FILTER(ALL(Product)" in result  # For specific members
        assert "FILTER(ALL(Geography)" in result  # For country filter
        assert '"Total Sales"' in result
        assert "ORDER BY" in result
        assert "TOPN(100" in result
    
    # Formatting tests
    
    def test_generate_with_formatting(self, formatted_generator, dimensional_query):
        """Test generating with formatting enabled."""
        result = formatted_generator.generate(dimensional_query)
        
        # Should have newlines and indentation
        assert "\n" in result
        lines = result.split("\n")
        assert len(lines) > 1
        
        # Check for proper structure
        assert any("EVALUATE" in line for line in lines)
        assert any("SUMMARIZECOLUMNS" in line for line in lines)
    
    # Error handling tests
    
    def test_generate_with_validation_warnings(self, generator):
        """Test query with validation warnings."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[],  # No measures
            dimensions=[],  # No dimensions
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        warnings = generator.get_warnings()
        assert len(warnings) > 0
        assert "Validation warning" in warnings[0]
    
    def test_generate_with_circular_dependency(self, generator):
        """Test query with circular dependency in calculations."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Calc1", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[],
            filters=[],
            calculations=[
                Calculation(
                    name="Calc1",
                    calculation_type=CalculationType.MEASURE,
                    expression=MeasureReference("Calc1")  # Self-reference
                )
            ],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        warnings = generator.get_warnings()
        assert any("Circular dependency" in w for w in warnings)
    
    def test_generate_with_invalid_calculation(self, generator):
        """Test handling invalid calculations."""
        # Create a mock expression that will fail
        class BadExpression:
            def __str__(self):
                raise ValueError("Bad expression")
        
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[],
            dimensions=[],
            filters=[],
            calculations=[
                Calculation(
                    name="Bad Calc",
                    calculation_type=CalculationType.MEASURE,
                    expression=BadExpression()  # This will fail
                )
            ],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        # Should handle the error gracefully
        with pytest.raises(DAXGenerationError):
            generator.generate(query)
    
    # Validation tests
    
    def test_validate_for_dax(self, generator):
        """Test DAX validation method."""
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="Sales", aggregation=AggregationType.SUM)
            ],
            dimensions=[],
            filters=[],
            calculations=[],
            order_by=[],
            limit=Limit(count=10, offset=5),  # Offset not supported
            metadata=QueryMetadata()
        )
        
        issues = generator.validate_for_dax(query)
        assert len(issues) > 0
        assert any("OFFSET" in issue for issue in issues)
    
    # Edge cases
    
    def test_generate_with_special_characters(self, generator):
        """Test handling special characters in names."""
        query = Query(
            cube=CubeReference(name="Sales [2023]"),
            measures=[
                Measure(name="Sales $ Amount", aggregation=AggregationType.SUM),
                Measure(name="Profit %", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product-Category", name="Product"),
                    level=LevelReference(name="Sub Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        # Should handle special characters properly
        assert "[Sales $ Amount]" in result or "Sales $ Amount" in result
        assert "[Sub Category]" in result
    
    def test_generate_with_very_long_names(self, generator):
        """Test handling very long identifiers."""
        long_name = "Very_Long_Measure_Name_That_Exceeds_Normal_Length_" + "X" * 100
        
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name=long_name, aggregation=AggregationType.SUM)
            ],
            dimensions=[],
            filters=[],
            calculations=[],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        result = generator.generate(query)
        assert long_name in result
    
    def test_get_warnings_returns_copy(self, generator, simple_query):
        """Test that get_warnings returns a copy of the warnings list."""
        generator.generate(simple_query)
        warnings1 = generator.get_warnings()
        warnings2 = generator.get_warnings()
        
        # Should be different objects
        assert warnings1 is not warnings2
        
        # But same content
        assert warnings1 == warnings2
    
    def test_context_tracking(self, generator):
        """Test that context is properly tracked during generation."""
        # This is more of an internal test, but ensures error messages have context
        query = Query(
            cube=CubeReference(name="Sales"),
            measures=[
                Measure(name="BadMeasure", aggregation=AggregationType.CUSTOM)
            ],
            dimensions=[],
            filters=[],
            calculations=[
                Calculation(
                    name="BadCalc",
                    calculation_type=CalculationType.MEASURE,
                    expression=None  # Invalid - will cause error
                )
            ],
            order_by=[],
            limit=None,
            metadata=QueryMetadata()
        )
        
        try:
            generator.generate(query)
        except DAXGenerationError as e:
            # Should have context information
            assert e.context or "context" in str(e)