"""Unit tests for ExpressionConverter."""

import pytest

from unmdx.ir.expressions import (
    Constant, MeasureReference, MemberReference, BinaryOperation,
    FunctionCall, IifExpression, CaseExpression, UnaryOperation, Expression
)
from unmdx.ir.enums import FunctionType
from unmdx.dax_generator.expression_converter import ExpressionConverter


class TestExpressionConverter:
    """Test cases for ExpressionConverter."""
    
    @pytest.fixture
    def converter(self):
        """Create an ExpressionConverter instance."""
        return ExpressionConverter()
    
    # Test Constant conversion
    
    def test_convert_string_constant(self, converter):
        """Test converting string constants to DAX."""
        expr = Constant(value="Hello World")
        result = converter.convert(expr)
        assert result == '"Hello World"'
    
    def test_convert_string_constant_with_quotes(self, converter):
        """Test converting strings with quotes."""
        expr = Constant(value='Say "Hello"')
        result = converter.convert(expr)
        assert result == '"Say ""Hello"""'  # Quotes are escaped
    
    def test_convert_numeric_constant(self, converter):
        """Test converting numeric constants."""
        # Integer
        expr = Constant(value=42)
        result = converter.convert(expr)
        assert result == "42"
        
        # Float
        expr = Constant(value=3.14)
        result = converter.convert(expr)
        assert result == "3.14"
    
    def test_convert_boolean_constant(self, converter):
        """Test converting boolean constants."""
        # True
        expr = Constant(value=True)
        result = converter.convert(expr)
        assert result == "TRUE"
        
        # False
        expr = Constant(value=False)
        result = converter.convert(expr)
        assert result == "FALSE"
    
    def test_convert_null_string_constant(self, converter):
        """Test converting empty string as null equivalent."""
        # The actual IR doesn't support None, so test with empty string
        expr = Constant(value="")
        result = converter.convert(expr)
        assert result == '""'
    
    # Test MeasureReference conversion
    
    def test_convert_measure_reference(self, converter):
        """Test converting measure references."""
        expr = MeasureReference(measure_name="Sales Amount")
        result = converter.convert(expr)
        assert result == "[Sales Amount]"
    
    def test_convert_measure_reference_special_chars(self, converter):
        """Test measure references with special characters."""
        expr = MeasureReference(measure_name="Sales % Growth")
        result = converter.convert(expr)
        assert result == "[Sales % Growth]"
    
    # Test MemberReference conversion
    
    def test_convert_member_reference_with_member(self, converter):
        """Test converting member references with specific member."""
        expr = MemberReference(
            dimension="Country",
            hierarchy="Geography",
            member="USA"
        )
        result = converter.convert(expr)
        assert result == '"USA"'
    
    def test_convert_member_reference_with_quotes(self, converter):
        """Test member references with quotes in member name."""
        expr = MemberReference(
            dimension="Product",
            hierarchy="Products",
            member='24" Monitor'
        )
        result = converter.convert(expr)
        assert result == '"24"" Monitor"'
    
    def test_convert_member_reference_without_member(self, converter):
        """Test converting member references without specific member."""
        expr = MemberReference(
            dimension="Country",
            hierarchy="Geography",
            member=""  # Empty string instead of None
        )
        result = converter.convert(expr)
        assert result == "Geography[Country]"
    
    # Test BinaryOperation conversion
    
    def test_convert_simple_binary_operation(self, converter):
        """Test converting simple binary operations."""
        # Addition
        expr = BinaryOperation(
            left=Constant(value=10),
            operator="+",
            right=Constant(value=20)
        )
        result = converter.convert(expr)
        assert result == "(10 + 20)"
    
    def test_convert_division_operation(self, converter):
        """Test division uses DIVIDE function."""
        expr = BinaryOperation(
            left=MeasureReference(measure_name="Profit"),
            operator="/",
            right=MeasureReference(measure_name="Sales")
        )
        result = converter.convert(expr)
        assert result == "DIVIDE([Profit], [Sales])"
    
    def test_convert_comparison_operations(self, converter):
        """Test comparison operations."""
        # Greater than
        expr = BinaryOperation(
            left=MeasureReference(measure_name="Sales"),
            operator=">",
            right=Constant(value=1000)
        )
        result = converter.convert(expr)
        assert result == "([Sales] > 1000)"
        
        # Not equal
        expr = BinaryOperation(
            left=MeasureReference(measure_name="Status"),
            operator="<>",
            right=Constant(value="Active")
        )
        result = converter.convert(expr)
        assert result == '([Status] <> "Active")'
    
    def test_convert_logical_operations(self, converter):
        """Test logical AND/OR operations."""
        # AND
        expr = BinaryOperation(
            left=BinaryOperation(
                left=MeasureReference(measure_name="Sales"),
                operator=">",
                right=Constant(value=100)
            ),
            operator="AND",
            right=BinaryOperation(
                left=MeasureReference(measure_name="Profit"),
                operator=">",
                right=Constant(value=0)
            )
        )
        result = converter.convert(expr)
        assert result == "(([Sales] > 100) && ([Profit] > 0))"
        
        # OR
        expr = BinaryOperation(
            left=MemberReference("Country", "Geography", "USA"),
            operator="OR",
            right=MemberReference("Country", "Geography", "Canada")
        )
        result = converter.convert(expr)
        assert result == '("USA" || "Canada")'
    
    def test_convert_nested_operations(self, converter):
        """Test nested binary operations."""
        expr = BinaryOperation(
            left=BinaryOperation(
                left=MeasureReference(measure_name="Sales"),
                operator="-",
                right=MeasureReference(measure_name="Cost")
            ),
            operator="/",
            right=MeasureReference(measure_name="Sales")
        )
        result = converter.convert(expr)
        assert result == "DIVIDE(([Sales] - [Cost]), [Sales])"
    
    # Test FunctionCall conversion
    
    def test_convert_sum_function(self, converter):
        """Test SUM function conversion."""
        expr = FunctionCall(
            function_type=FunctionType.SUM,
            function_name="SUM",
            arguments=[MeasureReference(measure_name="Sales")]
        )
        result = converter.convert(expr)
        assert result == "SUM([Sales])"
    
    def test_convert_average_function(self, converter):
        """Test AVERAGE function conversion."""
        expr = FunctionCall(
            function_type=FunctionType.AVG,
            function_name="AVG",
            arguments=[MeasureReference(measure_name="Score")]
        )
        result = converter.convert(expr)
        assert result == "AVERAGE([Score])"
    
    def test_convert_count_functions(self, converter):
        """Test COUNT and DISTINCTCOUNT functions."""
        # COUNT
        expr = FunctionCall(
            function_type=FunctionType.COUNT,
            function_name="COUNT",
            arguments=[MeasureReference(measure_name="ProductID")]
        )
        result = converter.convert(expr)
        assert result == "COUNT([ProductID])"
        
        # DISTINCTCOUNT
        expr = FunctionCall(
            function_type=FunctionType.DISTINCT_COUNT,
            function_name="DISTINCTCOUNT",
            arguments=[MeasureReference(measure_name="CustomerID")]
        )
        result = converter.convert(expr)
        assert result == "DISTINCTCOUNT([CustomerID])"
    
    def test_convert_iif_function(self, converter):
        """Test IIF to IF conversion."""
        expr = FunctionCall(
            function_type=FunctionType.IIF,
            function_name="IIF",
            arguments=[
                BinaryOperation(
                    left=MeasureReference(measure_name="Sales"),
                    operator=">",
                    right=Constant(value=1000)
                ),
                Constant(value="High"),
                Constant(value="Low")
            ]
        )
        result = converter.convert(expr)
        assert result == 'IF(([Sales] > 1000), "High", "Low")'
    
    def test_convert_iif_function_insufficient_args(self, converter):
        """Test IIF with insufficient arguments."""
        expr = FunctionCall(
            function_type=FunctionType.IIF,
            function_name="IIF",
            arguments=[
                BinaryOperation(
                    left=MeasureReference(measure_name="Sales"),
                    operator=">",
                    right=Constant(value=1000)
                ),
                Constant(value="High")
            ]
        )
        result = converter.convert(expr)
        # Should still generate something, even if not ideal
        assert "IIF" in result
    
    def test_convert_case_to_switch(self, converter):
        """Test CASE to SWITCH conversion."""
        expr = FunctionCall(
            function_type=FunctionType.CASE,
            function_name="CASE",
            arguments=[
                MeasureReference(measure_name="Category"),
                Constant(value="A"),
                Constant(value=100),
                Constant(value="B"),
                Constant(value=200),
                Constant(value=0)  # Default
            ]
        )
        result = converter.convert(expr)
        assert result == 'SWITCH([Category], "A", 100, "B", 200, 0)'
    
    def test_convert_coalesce_function(self, converter):
        """Test COALESCE conversion to nested IF."""
        expr = FunctionCall(
            function_type=FunctionType.COALESCE,
            function_name="COALESCE",
            arguments=[
                MeasureReference(measure_name="Value1"),
                MeasureReference(measure_name="Value2"),
                Constant(value=0)
            ]
        )
        result = converter.convert(expr)
        # Should generate nested IF with ISBLANK
        assert "IF(ISBLANK([Value1])" in result
        assert "[Value2]" in result
    
    def test_convert_format_function(self, converter):
        """Test FORMAT function."""
        expr = FunctionCall(
            function_type=FunctionType.FORMAT,
            function_name="FORMAT",
            arguments=[
                MeasureReference(measure_name="Date"),
                Constant(value="yyyy-MM-dd")
            ]
        )
        result = converter.convert(expr)
        assert result == 'FORMAT([Date], "yyyy-MM-dd")'
    
    def test_convert_math_functions(self, converter):
        """Test various math functions."""
        # ABS
        expr = FunctionCall(
            function_type=FunctionType.ABS,
            function_name="ABS",
            arguments=[MeasureReference(measure_name="Value")]
        )
        result = converter.convert(expr)
        assert result == "ABS([Value])"
        
        # ROUND
        expr = FunctionCall(
            function_type=FunctionType.ROUND,
            function_name="ROUND",
            arguments=[MeasureReference(measure_name="Value"), Constant(value=2)]
        )
        result = converter.convert(expr)
        assert result == "ROUND([Value], 2)"
    
    def test_convert_members_function(self, converter):
        """Test MEMBERS to VALUES conversion."""
        expr = FunctionCall(
            function_type=FunctionType.MEMBERS,
            function_name="MEMBERS",
            arguments=[MemberReference("Country", "Geography", None)]
        )
        result = converter.convert(expr)
        assert result == "VALUES(Geography[Country])"
    
    def test_convert_crossjoin_in_expression(self, converter):
        """Test CROSSJOIN in expression context."""
        expr = FunctionCall(
            function_type=FunctionType.CROSSJOIN,
            function_name="CROSSJOIN",
            arguments=[
                MemberReference("Country", "Geography", None),
                MemberReference("Category", "Product", None)
            ]
        )
        result = converter.convert(expr)
        # Should generate a comment since CROSSJOIN isn't used in expressions
        assert "-- CROSSJOIN" in result
    
    def test_convert_unknown_function(self, converter):
        """Test unknown/generic function."""
        expr = FunctionCall(
            function_type=FunctionType.MATH,
            function_name="CUSTOM_FUNC",
            arguments=[MeasureReference(measure_name="Value"), Constant(value=10)]
        )
        result = converter.convert(expr)
        assert result == "CUSTOM_FUNC([Value], 10)"
    
    # Test ConditionalExpression conversion
    
    def test_convert_iif_expression(self, converter):
        """Test IIF expression conversion."""
        expr = IifExpression(
            condition=BinaryOperation(
                left=MeasureReference(measure_name="Status"),
                operator="=",
                right=Constant(value="Active")
            ),
            true_value=MeasureReference(measure_name="ActiveValue"),
            false_value=MeasureReference(measure_name="InactiveValue")
        )
        result = converter.convert(expr)
        assert result == 'IF(([Status] = "Active"), [ActiveValue], [InactiveValue])'
    
    def test_convert_case_expression(self, converter):
        """Test CASE expression conversion."""
        expr = CaseExpression(
            when_conditions=[
                (BinaryOperation(
                    left=MeasureReference(measure_name="Sales"),
                    operator=">",
                    right=Constant(value=1000)
                ), Constant(value="High")),
                (BinaryOperation(
                    left=MeasureReference(measure_name="Sales"),
                    operator=">",
                    right=Constant(value=500)
                ), Constant(value="Medium"))
            ],
            else_value=Constant(value="Low")
        )
        result = converter.convert(expr)
        # Should generate nested IF statements
        assert "IF(" in result
        assert "High" in result
        assert "Medium" in result
        assert "Low" in result
    
    # Test validation
    
    def test_validate_valid_expression(self, converter):
        """Test validation of valid expressions."""
        expr = BinaryOperation(
            left=MeasureReference(measure_name="Sales"),
            operator="+",
            right=Constant(value=100)
        )
        issues = converter.validate_expression(expr)
        assert len(issues) == 0
    
    def test_validate_modulo_operator(self, converter):
        """Test validation warns about modulo operator."""
        expr = BinaryOperation(
            left=MeasureReference(measure_name="Value"),
            operator="%",
            right=Constant(value=10)
        )
        issues = converter.validate_expression(expr)
        assert len(issues) > 0
        assert "Modulo" in issues[0]
    
    def test_validate_unsupported_function(self, converter):
        """Test validation of potentially unsupported functions."""
        expr = FunctionCall(
            function_type=FunctionType.MATH,
            function_name="STDDEV",
            arguments=[MeasureReference(measure_name="Values")]
        )
        issues = converter.validate_expression(expr)
        assert len(issues) > 0
        assert "STDDEV" in issues[0]
    
    def test_validate_invalid_expression_type(self, converter):
        """Test validation of unsupported expression type."""
        # Create a mock unsupported expression type
        class UnsupportedExpression(Expression):
            def to_dax(self) -> str:
                return "UNSUPPORTED"
            
            def to_human_readable(self) -> str:
                return "unsupported"
            
            def get_dependencies(self):
                return []
        
        expr = UnsupportedExpression()
        issues = converter.validate_expression(expr)
        assert len(issues) > 0
        assert "conversion error" in issues[0]
    
    # Edge cases
    
    def test_convert_empty_string_constant(self, converter):
        """Test converting empty string."""
        expr = Constant(value="")
        result = converter.convert(expr)
        assert result == '""'
    
    def test_convert_very_long_identifier(self, converter):
        """Test converting very long identifiers."""
        long_name = "Very_Long_Measure_Name_" + "X" * 100
        expr = MeasureReference(measure_name=long_name)
        result = converter.convert(expr)
        assert result == f"[{long_name}]"
    
    def test_convert_special_characters_in_names(self, converter):
        """Test special characters in identifiers."""
        expr = MeasureReference(measure_name="Sales [USD] (2023)")
        result = converter.convert(expr)
        assert result == "[Sales [USD] (2023)]"
    
    def test_convert_deeply_nested_expression(self, converter):
        """Test deeply nested expressions."""
        # Create a deeply nested expression
        expr = Constant(value=1)
        for i in range(10):
            expr = BinaryOperation(
                left=expr,
                operator="+",
                right=Constant(value=1)
            )
        
        result = converter.convert(expr)
        # Should have many nested parentheses
        assert result.count("(") >= 10
        assert result.count(")") >= 10