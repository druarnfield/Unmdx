"""Unit tests for DAX generator utilities."""

import pytest

from unmdx.dax_generator.utils import DAXOptimizer, DAXFormatter, validate_dax_syntax
from unmdx.ir.models import Query, Measure, Dimension, Filter
from unmdx.ir.expressions import MeasureReference, BinaryOperation, FunctionCall
from unmdx.ir.enums import FunctionType


class TestDAXOptimizer:
    """Test DAX optimizer functionality."""
    
    @pytest.fixture
    def optimizer(self):
        """Create DAX optimizer instance."""
        return DAXOptimizer()
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer is not None
    
    def test_optimize_empty_query(self, optimizer):
        """Test optimizing empty query."""
        query = Query(
            measures=[],
            dimensions=[],
            filters=[],
            cube_name="Test"
        )
        
        optimized = optimizer.optimize_query(query)
        
        assert len(optimized.measures) == 0
        assert len(optimized.dimensions) == 0
        assert len(optimized.filters) == 0
        assert optimized.cube_name == "Test"
    
    def test_optimize_measures(self, optimizer):
        """Test measure optimization."""
        measures = [
            Measure(
                name="Sales",
                expression=MeasureReference(measure_name="Sales Amount")
            ),
            Measure(
                name="Cost",
                expression=MeasureReference(measure_name="Total Cost")
            )
        ]
        
        query = Query(
            measures=measures,
            dimensions=[],
            filters=[],
            cube_name="Test"
        )
        
        optimized = optimizer.optimize_query(query)
        
        assert len(optimized.measures) == 2
        assert optimized.measures[0].name == "Sales"
        assert optimized.measures[1].name == "Cost"
    
    def test_optimize_duplicate_dimensions(self, optimizer):
        """Test removing duplicate dimensions."""
        dimensions = [
            Dimension(dimension="Product", hierarchy="Category"),
            Dimension(dimension="Date", hierarchy="Calendar Year"),
            Dimension(dimension="Product", hierarchy="Category"),  # Duplicate
            Dimension(dimension="Customer", hierarchy="Country")
        ]
        
        query = Query(
            measures=[],
            dimensions=dimensions,
            filters=[],
            cube_name="Test"
        )
        
        optimized = optimizer.optimize_query(query)
        
        # Should remove duplicate
        assert len(optimized.dimensions) == 3
        
        # Should preserve order
        assert optimized.dimensions[0].dimension == "Product"
        assert optimized.dimensions[1].dimension == "Date"
        assert optimized.dimensions[2].dimension == "Customer"
    
    def test_optimize_filters(self, optimizer):
        """Test filter optimization."""
        filters = [
            Filter(dimension="Date", level="Calendar Year", operator="equals", value="2023"),
            Filter(dimension="Product", level="Category", operator="equals", value="Bikes"),
            Filter(dimension="Date", level="Calendar Year", operator="equals", value="2024")  # Same dimension/level
        ]
        
        query = Query(
            measures=[],
            dimensions=[],
            filters=filters,
            cube_name="Test"
        )
        
        optimized = optimizer.optimize_query(query)
        
        # Should combine filters on same dimension/level
        assert len(optimized.filters) == 2  # Date filters combined, Product filter separate
    
    def test_optimize_binary_operation(self, optimizer):
        """Test binary operation optimization."""
        left_expr = MeasureReference(measure_name="Sales")
        right_expr = MeasureReference(measure_name="Cost")
        
        binary_op = BinaryOperation(
            left=left_expr,
            operator="-",
            right=right_expr
        )
        
        optimized = optimizer._optimize_expression(binary_op)
        
        assert isinstance(optimized, BinaryOperation)
        assert optimized.operator == "-"
        assert isinstance(optimized.left, MeasureReference)
        assert isinstance(optimized.right, MeasureReference)
    
    def test_optimize_function_call(self, optimizer):
        """Test function call optimization."""
        arg_expr = MeasureReference(measure_name="Sales Amount")
        
        func_call = FunctionCall(
            function_type=FunctionType.SUM,
            arguments=[arg_expr]
        )
        
        optimized = optimizer._optimize_expression(func_call)
        
        assert isinstance(optimized, FunctionCall)
        assert optimized.function_type == FunctionType.SUM
        assert len(optimized.arguments) == 1


class TestDAXFormatter:
    """Test DAX formatter functionality."""
    
    @pytest.fixture
    def formatter(self):
        """Create DAX formatter instance."""
        return DAXFormatter(max_line_length=80, indent_size=4)
    
    def test_formatter_initialization(self, formatter):
        """Test formatter initialization."""
        assert formatter.max_line_length == 80
        assert formatter.indent_size == 4
    
    def test_format_simple_dax(self, formatter):
        """Test formatting simple DAX code."""
        dax_code = "EVALUATE{[Sales Amount]}"
        
        formatted = formatter.format(dax_code)
        
        assert "EVALUATE" in formatted
        assert "[Sales Amount]" in formatted
        # Should have proper line breaks
        assert "\n" in formatted
    
    def test_format_with_indentation(self, formatter):
        """Test formatting with proper indentation."""
        dax_code = """EVALUATE
SUMMARIZECOLUMNS(
'Product'[Category],
[Sales Amount]
)"""
        
        formatted = formatter.format(dax_code)
        
        lines = formatted.split('\n')
        
        # Check indentation
        assert lines[0].strip() == "EVALUATE"
        assert lines[1].strip() == "SUMMARIZECOLUMNS("
        # Inner content should be indented
        assert len(lines) >= 3
    
    def test_format_long_lines(self, formatter):
        """Test breaking long lines."""
        long_line = "SUMMARIZECOLUMNS('Product'[Category], 'Date'[Calendar Year], 'Customer'[Country], [Sales Amount], [Order Quantity], [Total Cost])"
        
        formatted = formatter.format(long_line)
        
        lines = formatted.split('\n')
        
        # Should break into multiple lines
        assert len(lines) > 1
        
        # Each line should be within max length (allowing some tolerance for indentation)
        for line in lines:
            assert len(line) <= formatter.max_line_length + 20  # Allow some tolerance
    
    def test_format_nested_functions(self, formatter):
        """Test formatting nested function calls."""
        dax_code = """EVALUATE
SUMMARIZECOLUMNS(
'Product'[Category],
FILTER(ALL('Date'), 'Date'[Calendar Year] = 2023),
[Sales Amount]
)"""
        
        formatted = formatter.format(dax_code)
        
        # Should maintain structure
        assert "EVALUATE" in formatted
        assert "SUMMARIZECOLUMNS(" in formatted
        assert "FILTER(" in formatted
        assert "[Sales Amount]" in formatted
    
    def test_break_line_at_commas(self, formatter):
        """Test line breaking at commas."""
        line = "    SUMMARIZECOLUMNS('Product'[Category], 'Date'[Year], [Sales], [Cost])"
        
        broken_lines = formatter._break_long_line(line, 4)
        
        # Should break at commas
        assert len(broken_lines) > 1
        
        # First line should end with comma
        assert broken_lines[0].endswith(',')
        
        # Last line should not end with comma
        assert not broken_lines[-1].endswith(',')


class TestDAXValidation:
    """Test DAX syntax validation."""
    
    def test_validate_valid_dax(self):
        """Test validation of valid DAX code."""
        dax_code = """EVALUATE
SUMMARIZECOLUMNS(
    'Product'[Category],
    [Sales Amount]
)"""
        
        result = validate_dax_syntax(dax_code)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_unbalanced_parentheses(self):
        """Test validation with unbalanced parentheses."""
        dax_code = "EVALUATE SUMMARIZECOLUMNS('Product'[Category], [Sales Amount]"
        
        result = validate_dax_syntax(dax_code)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "parentheses" in result["errors"][0].lower()
    
    def test_validate_unbalanced_brackets(self):
        """Test validation with unbalanced brackets."""
        dax_code = "EVALUATE {'Product'[Category, [Sales Amount]}"
        
        result = validate_dax_syntax(dax_code)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "brackets" in result["errors"][0].lower()
    
    def test_validate_missing_evaluate(self):
        """Test validation with missing EVALUATE keyword."""
        dax_code = "SUMMARIZECOLUMNS('Product'[Category], [Sales Amount])"
        
        result = validate_dax_syntax(dax_code)
        
        # Should be valid syntax but warn about missing EVALUATE
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert "EVALUATE" in result["warnings"][0]
    
    def test_validate_complex_expression(self):
        """Test validation of complex DAX expression."""
        dax_code = """DEFINE
MEASURE [Profit Margin] = DIVIDE([Sales Amount] - [Total Cost], [Sales Amount])
EVALUATE
SUMMARIZECOLUMNS(
    'Product'[Category],
    'Date'[Calendar Year],
    FILTER(ALL('Date'), 'Date'[Calendar Year] >= 2020),
    [Sales Amount],
    [Total Cost],
    [Profit Margin]
)"""
        
        result = validate_dax_syntax(dax_code)
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_multiple_issues(self):
        """Test validation with multiple syntax issues."""
        dax_code = "SUMMARIZECOLUMNS('Product'[Category, [Sales Amount]"
        
        result = validate_dax_syntax(dax_code)
        
        assert result["valid"] is False
        
        # Should catch both unbalanced brackets and parentheses
        error_text = " ".join(result["errors"]).lower()
        assert "bracket" in error_text
        assert "parenthes" in error_text