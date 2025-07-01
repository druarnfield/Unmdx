"""Unit tests for DAX generator core functionality."""

import pytest
from unittest.mock import Mock

from unmdx.dax_generator import DAXGenerator, DAXGenerationOptions
from unmdx.ir.models import Query, Measure, Dimension, CubeReference, HierarchyReference, LevelReference, MemberSelection
from unmdx.ir.enums import AggregationType, MemberSelectionType
from unmdx.ir.expressions import MeasureReference, BinaryOperation, Constant


class TestDAXGenerationOptions:
    """Test DAX generation options."""
    
    def test_default_options(self):
        """Test default configuration options."""
        options = DAXGenerationOptions()
        
        assert options.use_summarizecolumns is True
        assert options.optimize_filters is True
        assert options.include_comments is True
        assert options.format_output is True
        assert options.max_line_length == 120
    
    def test_custom_options(self):
        """Test custom configuration options."""
        options = DAXGenerationOptions(
            use_summarizecolumns=False,
            optimize_filters=False,
            max_line_length=80
        )
        
        assert options.use_summarizecolumns is False
        assert options.optimize_filters is False
        assert options.max_line_length == 80


class TestDAXGenerator:
    """Test DAX generator functionality."""
    
    @pytest.fixture
    def generator(self):
        """Create DAX generator instance."""
        return DAXGenerator()
    
    @pytest.fixture
    def basic_options(self):
        """Create basic options for testing."""
        return DAXGenerationOptions(
            include_comments=False,
            format_output=False
        )
    
    @pytest.fixture
    def sample_cube(self):
        """Create sample cube reference."""
        return CubeReference(name="Adventure Works")
    
    @pytest.fixture
    def sample_measure(self):
        """Create sample measure."""
        return Measure(
            name="Sales Amount",
            aggregation=AggregationType.SUM,
            expression=MeasureReference(measure_name="Sales Amount")
        )
    
    @pytest.fixture
    def sample_dimension(self):
        """Create sample dimension."""
        hierarchy = HierarchyReference(table="Product", name="Category")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        
        return Dimension(
            hierarchy=hierarchy,
            level=level,
            members=members
        )
    
    def test_generator_initialization(self, generator):
        """Test generator initialization."""
        assert generator.options is not None
        assert isinstance(generator.options, DAXGenerationOptions)
    
    def test_single_measure_query(self, generator, sample_cube, sample_measure):
        """Test generating DAX for single measure query."""
        query = Query(
            cube=sample_cube,
            measures=[sample_measure]
        )
        
        dax = generator.generate(query)
        
        assert "EVALUATE" in dax
        assert "[Sales Amount]" in dax
        assert "SUMMARIZECOLUMNS" not in dax  # Should use simple table for single measure
    
    def test_multiple_measures_query(self, generator, sample_cube):
        """Test generating DAX for multiple measures query."""
        measures = [
            Measure(
                name="Sales Amount", 
                aggregation=AggregationType.SUM,
                expression=MeasureReference(measure_name="Sales Amount")
            ),
            Measure(
                name="Order Quantity", 
                aggregation=AggregationType.SUM,
                expression=MeasureReference(measure_name="Order Quantity")
            )
        ]
        
        query = Query(
            cube=sample_cube,
            measures=measures
        )
        
        dax = generator.generate(query)
        
        assert "EVALUATE" in dax
        assert "ROW(" in dax
        assert "[Sales Amount]" in dax
        assert "[Order Quantity]" in dax
    
    def test_dimensional_query(self, generator, sample_cube, sample_measure, sample_dimension):
        """Test generating DAX for query with dimensions."""
        query = Query(
            cube=sample_cube,
            measures=[sample_measure],
            dimensions=[sample_dimension]
        )
        
        dax = generator.generate(query)
        
        assert "EVALUATE" in dax
        assert "SUMMARIZECOLUMNS(" in dax
        assert "'Product'[Category]" in dax
        assert "[Sales Amount]" in dax
    
    def test_query_with_filters(self, generator):
        """Test generating DAX for query with filters."""
        measure = Measure(
            name="Sales Amount",
            expression=MeasureReference(measure_name="Sales Amount")
        )
        
        dimension = Dimension(
            dimension="Product",
            hierarchy="Category"
        )
        
        filter_obj = Filter(
            dimension="Date",
            level="Calendar Year",
            operator="equals",
            value="2023"
        )
        
        query = Query(
            measures=[measure],
            dimensions=[dimension],
            filters=[filter_obj],
            cube_name="Adventure Works"
        )
        
        dax = generator.generate(query)
        
        assert "EVALUATE" in dax
        assert "SUMMARIZECOLUMNS(" in dax
        assert "FILTER(" in dax
        assert "'Date'[Calendar Year] = \"2023\"" in dax
    
    def test_calculated_measure(self, generator):
        """Test generating DAX for query with calculated measures."""
        # Create calculated measure
        calculated_expr = BinaryOperation(
            left=MeasureReference(measure_name="Sales Amount"),
            operator="-",
            right=MeasureReference(measure_name="Total Cost")
        )
        
        calculated_measure = Measure(
            name="Profit",
            expression=calculated_expr,
            is_calculated=True
        )
        
        base_measure = Measure(
            name="Sales Amount",
            expression=MeasureReference(measure_name="Sales Amount")
        )
        
        query = Query(
            measures=[base_measure, calculated_measure],
            dimensions=[],
            filters=[],
            cube_name="Adventure Works"
        )
        
        dax = generator.generate(query)
        
        assert "DEFINE" in dax
        assert "MEASURE [Profit] =" in dax
        assert "EVALUATE" in dax
        assert "[Sales Amount] - [Total Cost]" in dax
    
    def test_generator_with_custom_options(self):
        """Test generator with custom options."""
        options = DAXGenerationOptions(
            use_summarizecolumns=False,
            format_output=False
        )
        
        generator = DAXGenerator(options)
        
        measure = Measure(
            name="Sales Amount",
            expression=MeasureReference(measure_name="Sales Amount")
        )
        
        dimension = Dimension(
            dimension="Product",
            hierarchy="Category"
        )
        
        query = Query(
            measures=[measure],
            dimensions=[dimension],
            filters=[],
            cube_name="Adventure Works"
        )
        
        dax = generator.generate(query)
        
        # Should not use SUMMARIZECOLUMNS when disabled
        assert "SUMMARIZECOLUMNS" not in dax
    
    def test_dimension_column_generation(self, generator):
        """Test dimension column reference generation."""
        # Test with hierarchy different from dimension
        dimension1 = Dimension(
            dimension="Date",
            hierarchy="Calendar Year"
        )
        
        column_ref1 = generator._generate_dimension_column(dimension1)
        assert column_ref1 == "'Date'[Calendar Year]"
        
        # Test with hierarchy same as dimension
        dimension2 = Dimension(
            dimension="Product",
            hierarchy="Product"
        )
        
        column_ref2 = generator._generate_dimension_column(dimension2)
        assert column_ref2 == "'Product'[Product]"
    
    def test_filter_expression_generation(self, generator):
        """Test filter expression generation."""
        # Test equals filter
        filter1 = Filter(
            dimension="Date",
            level="Calendar Year",
            operator="equals",
            value="2023"
        )
        
        filter_expr1 = generator._generate_filter_expression(filter1)
        assert filter_expr1 == "'Date'[Calendar Year] = \"2023\""
        
        # Test in filter
        filter2 = Filter(
            dimension="Product",
            level="Category",
            operator="in",
            value=["Bikes", "Accessories"]
        )
        
        filter_expr2 = generator._generate_filter_expression(filter2)
        assert "'Product'[Category] IN" in filter_expr2
        assert "\"Bikes\"" in filter_expr2
        assert "\"Accessories\"" in filter_expr2
    
    def test_measure_expression_generation(self, generator):
        """Test measure expression generation."""
        # Test simple measure reference
        measure1 = Measure(
            name="Sales Amount",
            expression=MeasureReference(measure_name="Sales Amount")
        )
        
        measure_expr1 = generator._generate_measure_expression(measure1)
        assert measure_expr1 == "[Sales Amount]"
        
        # Test measure without expression
        measure2 = Measure(name="Order Quantity")
        
        measure_expr2 = generator._generate_measure_expression(measure2)
        assert measure_expr2 == "[Order Quantity]"


class TestDAXGeneratorEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def generator(self):
        return DAXGenerator()
    
    def test_empty_query(self, generator):
        """Test generating DAX for empty query."""
        query = Query(
            measures=[],
            dimensions=[],
            filters=[],
            cube_name="Test Cube"
        )
        
        dax = generator.generate(query)
        
        assert "EVALUATE" in dax
        # Should handle empty measures gracefully
    
    def test_query_without_cube_name(self, generator):
        """Test query without cube name."""
        measure = Measure(
            name="Sales Amount",
            expression=MeasureReference(measure_name="Sales Amount")
        )
        
        query = Query(
            measures=[measure],
            dimensions=[],
            filters=[],
            cube_name=""
        )
        
        dax = generator.generate(query)
        
        assert "EVALUATE" in dax
        assert "[Sales Amount]" in dax
    
    def test_complex_calculated_measure(self, generator):
        """Test complex calculated measure with nested expressions."""
        # Create nested expression: (Sales - Cost) / Sales * 100
        sales_ref = MeasureReference(measure_name="Sales Amount")
        cost_ref = MeasureReference(measure_name="Total Cost")
        hundred = Constant(value=100)
        
        profit = BinaryOperation(
            left=sales_ref,
            operator="-",
            right=cost_ref
        )
        
        profit_margin = BinaryOperation(
            left=profit,
            operator="/",
            right=sales_ref
        )
        
        profit_percentage = BinaryOperation(
            left=profit_margin,
            operator="*",
            right=hundred
        )
        
        calculated_measure = Measure(
            name="Profit Margin %",
            expression=profit_percentage,
            is_calculated=True
        )
        
        query = Query(
            measures=[calculated_measure],
            dimensions=[],
            filters=[],
            cube_name="Adventure Works"
        )
        
        dax = generator.generate(query)
        
        assert "DEFINE" in dax
        assert "MEASURE [Profit Margin %] =" in dax
        assert "EVALUATE" in dax
        # Should contain the complex expression
        assert "[Sales Amount]" in dax
        assert "[Total Cost]" in dax