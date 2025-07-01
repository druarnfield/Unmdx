"""Unit tests for DAXFormatter."""

import pytest

from unmdx.dax_generator.dax_formatter import DAXFormatter


class TestDAXFormatter:
    """Test cases for DAXFormatter."""
    
    @pytest.fixture
    def formatter(self):
        """Create a DAXFormatter instance."""
        return DAXFormatter()
    
    @pytest.fixture
    def custom_formatter(self):
        """Create a DAXFormatter with custom indent size."""
        return DAXFormatter(indent_size=2)
    
    # Test basic formatting
    
    def test_format_simple_query(self, formatter):
        """Test formatting a simple DAX query."""
        dax = "EVALUATE Sales"
        result = formatter.format(dax)
        assert result == "EVALUATE\nSales"
    
    def test_format_with_define(self, formatter):
        """Test formatting query with DEFINE section."""
        dax = "DEFINE MEASURE Sales[Total] = SUM(Sales[Amount]) EVALUATE Sales"
        result = formatter.format(dax)
        lines = result.split('\n')
        assert lines[0] == "DEFINE"
        assert "MEASURE" in lines[1]
        assert lines[2] == "EVALUATE"
        assert lines[3] == "Sales"
    
    def test_format_summarizecolumns(self, formatter):
        """Test formatting SUMMARIZECOLUMNS function."""
        dax = 'EVALUATE SUMMARIZECOLUMNS(Product[Category], "Total", SUM(Sales[Amount]))'
        result = formatter.format(dax)
        assert "EVALUATE" in result
        assert "SUMMARIZECOLUMNS(" in result
        # Should have proper indentation
        lines = result.split('\n')
        assert any(line.strip().startswith("Product[Category]") for line in lines)
    
    def test_format_with_order_by(self, formatter):
        """Test formatting with ORDER BY clause."""
        dax = "EVALUATE Sales ORDER BY Sales[Date] DESC"
        result = formatter.format(dax)
        lines = result.split('\n')
        assert "EVALUATE" in lines[0]
        assert "ORDER BY" in result
        assert "DESC" in result
    
    def test_format_multiple_measures(self, formatter):
        """Test formatting multiple measures."""
        dax = 'EVALUATE SUMMARIZECOLUMNS(Product[Category], "Sales", SUM(Sales[Amount]), "Count", COUNT(Sales[ID]))'
        result = formatter.format(dax)
        # Should maintain measure definitions
        assert '"Sales"' in result
        assert '"Count"' in result
    
    # Test indentation
    
    def test_custom_indent_size(self, custom_formatter):
        """Test custom indentation size."""
        dax = "DEFINE MEASURE Sales[Total] = SUM(Sales[Amount]) EVALUATE Sales"
        result = custom_formatter.format(dax)
        lines = result.split('\n')
        # Check that indentation uses 2 spaces
        indented_line = next(line for line in lines if line.startswith(' '))
        assert indented_line.startswith('  ')  # 2 spaces
        assert not indented_line.startswith('    ')  # Not 4 spaces
    
    def test_nested_functions_indentation(self, formatter):
        """Test indentation of nested functions."""
        dax = "EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS(Product[Category], Sales), Sales[Year] = 2023)"
        result = formatter.format(dax)
        # Should have proper nesting
        assert "CALCULATETABLE(" in result
        assert "SUMMARIZECOLUMNS(" in result
    
    # Test identifier formatting
    
    def test_format_identifier_simple(self, formatter):
        """Test formatting simple identifiers."""
        assert formatter.format_identifier("Sales") == "Sales"
        assert formatter.format_identifier("ProductID") == "ProductID"
    
    def test_format_identifier_with_spaces(self, formatter):
        """Test formatting identifiers with spaces."""
        assert formatter.format_identifier("Sales Amount") == "[Sales Amount]"
        assert formatter.format_identifier("Product Category") == "[Product Category]"
    
    def test_format_identifier_with_special_chars(self, formatter):
        """Test formatting identifiers with special characters."""
        assert formatter.format_identifier("Sales-2023") == "[Sales-2023]"
        assert formatter.format_identifier("Sales.Amount") == "[Sales.Amount]"
        assert formatter.format_identifier("Sales%Growth") == "[Sales%Growth]"
    
    def test_format_identifier_starting_with_digit(self, formatter):
        """Test formatting identifiers starting with digit."""
        assert formatter.format_identifier("2023Sales") == "[2023Sales]"
        assert formatter.format_identifier("1stQuarter") == "[1stQuarter]"
    
    def test_format_identifier_reserved_keyword(self, formatter):
        """Test formatting DAX reserved keywords."""
        assert formatter.format_identifier("SUM") == "[SUM]"
        assert formatter.format_identifier("CALCULATE") == "[CALCULATE]"
        assert formatter.format_identifier("FILTER") == "[FILTER]"
    
    def test_format_identifier_already_bracketed(self, formatter):
        """Test identifiers that are already bracketed."""
        assert formatter.format_identifier("[Sales Amount]") == "[Sales Amount]"
        assert formatter.format_identifier("[Product Category]") == "[Product Category]"
    
    def test_format_identifier_with_brackets_inside(self, formatter):
        """Test identifiers with brackets inside name."""
        assert formatter.format_identifier("Sales]Amount") == "[Sales]]Amount]"
        assert formatter.format_identifier("Product[Category]") == "[Product[Category]]]"
    
    # Test string escaping
    
    def test_escape_string_simple(self, formatter):
        """Test escaping simple strings."""
        assert formatter.escape_string("Hello") == '"Hello"'
        assert formatter.escape_string("World") == '"World"'
    
    def test_escape_string_with_quotes(self, formatter):
        """Test escaping strings with quotes."""
        assert formatter.escape_string('Say "Hello"') == '"Say ""Hello"""'
        assert formatter.escape_string('He said "Yes"') == '"He said ""Yes"""'
    
    def test_escape_string_empty(self, formatter):
        """Test escaping empty string."""
        assert formatter.escape_string("") == '""'
    
    def test_escape_string_with_newlines(self, formatter):
        """Test escaping strings with newlines."""
        assert formatter.escape_string("Line1\nLine2") == '"Line1\nLine2"'
    
    # Test tokenization
    
    def test_tokenize_simple(self, formatter):
        """Test simple tokenization."""
        tokens = formatter._tokenize("EVALUATE Sales")
        assert tokens == ["EVALUATE", "Sales"]
    
    def test_tokenize_with_brackets(self, formatter):
        """Test tokenization with square brackets."""
        tokens = formatter._tokenize("Sales[Amount]")
        assert tokens == ["Sales", "[Amount]"]
    
    def test_tokenize_with_strings(self, formatter):
        """Test tokenization with quoted strings."""
        tokens = formatter._tokenize('"Total Sales", SUM(Sales[Amount])')
        assert '"Total Sales"' in tokens
        assert "SUM" in tokens
        assert "(" in tokens
        assert "Sales" in tokens
        assert "[Amount]" in tokens
    
    def test_tokenize_with_operators(self, formatter):
        """Test tokenization with operators."""
        tokens = formatter._tokenize("Sales > 1000 AND Profit >= 0")
        assert ">" in tokens
        assert ">=" in tokens
        assert "AND" in tokens
    
    def test_tokenize_numbers(self, formatter):
        """Test tokenization of numbers."""
        tokens = formatter._tokenize("123 + 45.67")
        assert "123" in tokens
        assert "+" in tokens
        assert "45.67" in tokens
    
    # Test line splitting
    
    def test_split_into_lines_keywords(self, formatter):
        """Test splitting based on keywords."""
        lines = formatter._split_into_lines("DEFINE MEASURE Sales[Total] = 100 EVALUATE Sales")
        assert any("DEFINE" in line for line in lines)
        assert any("EVALUATE" in line for line in lines)
    
    def test_split_into_lines_functions(self, formatter):
        """Test splitting function calls."""
        lines = formatter._split_into_lines("CALCULATE(SUM(Sales), FILTER(ALL(Product), Product[Category] = 'Bikes'))")
        # Should keep function calls together by default
        assert len(lines) >= 1
    
    # Test final cleanup
    
    def test_final_cleanup_trailing_whitespace(self, formatter):
        """Test removal of trailing whitespace."""
        dax = "EVALUATE Sales   \nORDER BY Date   "
        result = formatter.format(dax)
        lines = result.split('\n')
        for line in lines:
            assert line == line.rstrip()
    
    def test_final_cleanup_empty_lines(self, formatter):
        """Test removal of leading/trailing empty lines."""
        dax = "\n\nEVALUATE Sales\n\n"
        result = formatter.format(dax)
        assert not result.startswith('\n')
        assert not result.endswith('\n')
    
    def test_final_cleanup_section_separation(self, formatter):
        """Test proper separation between major sections."""
        dax = "DEFINE MEASURE Sales[Total] = 100 EVALUATE Sales"
        result = formatter.format(dax)
        # Should have proper separation between DEFINE and EVALUATE
        assert "\nEVALUATE" in result or "\n\nEVALUATE" in result
    
    # Test complex queries
    
    def test_format_complex_query(self, formatter):
        """Test formatting a complex query."""
        dax = """DEFINE MEASURE Sales[Profit Margin] = DIVIDE(Sales[Profit], Sales[Revenue]) 
                 MEASURE Sales[YoY Growth] = DIVIDE(Sales[This Year] - Sales[Last Year], Sales[Last Year])
                 EVALUATE SUMMARIZECOLUMNS(Date[Year], Product[Category], 
                 FILTER(ALL(Geography), Geography[Country] = "USA"),
                 "Total Sales", SUM(Sales[Amount]),
                 "Profit Margin", Sales[Profit Margin])
                 ORDER BY Date[Year] DESC, Product[Category]"""
        
        result = formatter.format(dax)
        
        # Check structure
        assert "DEFINE" in result
        assert "EVALUATE" in result
        assert "ORDER BY" in result
        
        # Check measures are defined
        assert "Profit Margin" in result
        assert "YoY Growth" in result
        
        # Check formatting preserved important elements
        assert "SUMMARIZECOLUMNS" in result
        assert "FILTER" in result
    
    def test_format_with_var_return(self, formatter):
        """Test formatting VAR/RETURN pattern."""
        dax = "DEFINE MEASURE Sales[Complex] = VAR TotalSales = SUM(Sales[Amount]) VAR TotalCost = SUM(Sales[Cost]) RETURN DIVIDE(TotalSales - TotalCost, TotalSales)"
        result = formatter.format(dax)
        
        # Should handle VAR/RETURN blocks
        assert "VAR" in result
        assert "RETURN" in result
    
    # Edge cases
    
    def test_format_empty_query(self, formatter):
        """Test formatting empty query."""
        assert formatter.format("") == ""
        assert formatter.format("   ") == ""
    
    def test_format_whitespace_only(self, formatter):
        """Test formatting whitespace-only input."""
        assert formatter.format("\n\n\t\t  \n") == ""
    
    def test_format_very_long_line(self, formatter):
        """Test formatting very long lines."""
        long_measure_list = ", ".join([f'"Measure{i}", SUM(Sales[Field{i}])' for i in range(50)])
        dax = f"EVALUATE SUMMARIZECOLUMNS(Product[Category], {long_measure_list})"
        result = formatter.format(dax)
        
        # Should still format without error
        assert "EVALUATE" in result
        assert "SUMMARIZECOLUMNS" in result
    
    def test_format_malformed_query(self, formatter):
        """Test formatting malformed/incomplete query."""
        dax = "EVALUATE SUMMARIZECOLUMNS("
        result = formatter.format(dax)
        # Should not crash, return something
        assert "EVALUATE" in result
    
    def test_format_unicode_content(self, formatter):
        """Test formatting with unicode characters."""
        dax = 'EVALUATE FILTER(Sales, Sales[Country] = "España")'
        result = formatter.format(dax)
        assert "España" in result
    
    def test_format_mixed_quotes(self, formatter):
        """Test formatting with mixed quote types."""
        dax = """EVALUATE FILTER(Sales, Sales[Type] = "Product's \"Best\" Seller")"""
        result = formatter.format(dax)
        # Should preserve the complex string
        assert "Product" in result
    
    def test_get_first_token(self, formatter):
        """Test getting first token from line."""
        assert formatter._get_first_token("EVALUATE Sales") == "EVALUATE"
        assert formatter._get_first_token("   FILTER(ALL(Product))") == "FILTER"
        assert formatter._get_first_token("") == ""
        assert formatter._get_first_token("[Sales Amount]") == "[Sales Amount]"
    
    def test_should_start_new_line(self, formatter):
        """Test logic for starting new lines."""
        tokens = ["EVALUATE", "SUMMARIZECOLUMNS", "("]
        assert formatter._should_start_new_line("EVALUATE", tokens, 0) == True
        assert formatter._should_start_new_line("(", tokens, 2) == False
        
        tokens = ["DEFINE", "MEASURE", "Sales"]
        assert formatter._should_start_new_line("DEFINE", tokens, 0) == True
        assert formatter._should_start_new_line("MEASURE", tokens, 1) == False
    
    def test_should_end_line(self, formatter):
        """Test logic for ending lines."""
        tokens = ["Sales", "ORDER", "BY", "Date"]
        assert formatter._should_end_line("Sales", tokens, 0) == True  # Next is ORDER BY
        
        tokens = ["SUM", "(", "Sales", ")"]
        assert formatter._should_end_line(")", tokens, 3) == False
    
    def test_in_measure_list(self, formatter):
        """Test detection of measure list context."""
        tokens = ['"Total"', ",", "[Sales]", ",", '"Count"', ",", "[Items]"]
        assert formatter._in_measure_list(tokens, 1) == True
        assert formatter._in_measure_list(tokens, 5) == True
        assert formatter._in_measure_list(tokens, 0) == False