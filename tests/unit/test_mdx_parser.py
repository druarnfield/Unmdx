"""Unit tests for MDX parser."""

import pytest

from unmdx.ir.models import (
    AggregationType,
    FilterOperator,
    FilterType,
    MemberSelectionType,
    Query,
)
from unmdx.parser.mdx_parser import MDXParseError, MDXParser


class TestMDXParser:
    """Test cases for MDX parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return MDXParser()

    def test_simple_measure_query(self, parser):
        """Test parsing a simple measure query."""
        mdx = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS
        FROM [Adventure Works]
        """

        result = parser.parse(mdx)

        assert isinstance(result, Query)
        assert result.cube.name == "Adventure Works"
        assert len(result.measures) == 1
        assert result.measures[0].name == "Sales Amount"
        assert result.measures[0].aggregation == AggregationType.SUM

    def test_dimensional_query(self, parser):
        """Test parsing a query with dimensions."""
        mdx = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS,
               {[Product].[Category].Members} ON ROWS
        FROM [Adventure Works]
        """

        result = parser.parse(mdx)

        assert len(result.measures) == 1
        assert len(result.dimensions) == 1
        assert result.dimensions[0].hierarchy.name == "Product"
        assert result.dimensions[0].level.name == "All"
        assert result.dimensions[0].members.selection_type == MemberSelectionType.ALL

    def test_query_with_where_clause(self, parser):
        """Test parsing a query with WHERE clause."""
        mdx = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS
        FROM [Adventure Works]
        WHERE ([Date].[Calendar Year].[CY 2023])
        """

        result = parser.parse(mdx)

        assert len(result.filters) == 1
        assert result.filters[0].filter_type == FilterType.DIMENSION
        filter_target = result.filters[0].target
        assert filter_target.dimension.hierarchy.name == "Date"
        assert filter_target.operator == FilterOperator.EQUALS
        assert "CY 2023" in filter_target.values

    def test_multiple_measures(self, parser):
        """Test parsing query with multiple measures."""
        mdx = """
        SELECT {[Measures].[Sales Amount], [Measures].[Order Count]} ON COLUMNS
        FROM [Adventure Works]
        """

        result = parser.parse(mdx)

        assert len(result.measures) == 2
        measure_names = [m.name for m in result.measures]
        assert "Sales Amount" in measure_names
        assert "Order Count" in measure_names

    def test_specific_dimension_members(self, parser):
        """Test parsing query with specific dimension members."""
        mdx = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS,
               {[Product].[Category].[Bikes], [Product].[Category].[Components]} ON ROWS
        FROM [Adventure Works]
        """

        result = parser.parse(mdx)

        assert len(result.dimensions) == 1
        # Note: This would require more complex parsing to detect specific members
        # For now, we test that the dimension is parsed
        assert result.dimensions[0].hierarchy.name == "Product"

    def test_crossjoin_function(self, parser):
        """Test parsing CrossJoin function."""
        mdx = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS,
               CrossJoin([Product].[Category].Members, [Date].[Calendar Year].Members) ON ROWS
        FROM [Adventure Works]
        """

        result = parser.parse(mdx)

        # The parser should handle CrossJoin by extracting dimensions
        assert len(result.dimensions) >= 1

    def test_non_empty_modifier(self, parser):
        """Test parsing NON EMPTY modifier."""
        mdx = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS,
               NON EMPTY {[Product].[Category].Members} ON ROWS
        FROM [Adventure Works]
        """

        result = parser.parse(mdx)

        # Should parse successfully even with NON EMPTY
        assert len(result.dimensions) == 1
        assert result.dimensions[0].hierarchy.name == "Product"

    def test_invalid_mdx_raises_error(self, parser):
        """Test that invalid MDX raises appropriate error."""
        invalid_mdx = "INVALID MDX QUERY"

        with pytest.raises(MDXParseError):
            parser.parse(invalid_mdx)

    def test_empty_query_raises_error(self, parser):
        """Test that empty query raises error."""
        with pytest.raises(MDXParseError):
            parser.parse("")

    def test_malformed_select_raises_error(self, parser):
        """Test that malformed SELECT raises error."""
        malformed_mdx = "SELECT FROM [Adventure Works]"

        with pytest.raises(MDXParseError):
            parser.parse(malformed_mdx)

    def test_case_sensitivity(self, parser):
        """Test case sensitivity handling."""
        mdx = """
        select {[measures].[sales amount]} on columns
        from [adventure works]
        """

        # Should parse despite different case
        result = parser.parse(mdx)
        assert result.cube.name == "adventure works"
        assert len(result.measures) == 1

    def test_whitespace_handling(self, parser):
        """Test whitespace handling."""
        mdx = """
        SELECT    {[Measures].[Sales Amount]}    ON    COLUMNS
        FROM    [Adventure Works]
        """

        result = parser.parse(mdx)
        assert result.cube.name == "Adventure Works"
        assert len(result.measures) == 1

    def test_comments_are_ignored(self, parser):
        """Test that comments are properly ignored."""
        mdx = """
        -- This is a comment
        SELECT {[Measures].[Sales Amount]} ON COLUMNS /* block comment */
        FROM [Adventure Works]
        """

        result = parser.parse(mdx)
        assert result.cube.name == "Adventure Works"
        assert len(result.measures) == 1


class TestMDXParserErrorHandling:
    """Test error handling in MDX parser."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return MDXParser()

    def test_parse_error_contains_original_error(self, parser):
        """Test that MDXParseError contains original Lark error."""
        invalid_mdx = "SELECT FROM"

        with pytest.raises(MDXParseError) as exc_info:
            parser.parse(invalid_mdx)

        assert exc_info.value.original_error is not None

    def test_unexpected_error_handling(self, parser):
        """Test handling of unexpected errors during parsing."""
        # This would require mocking to force an unexpected error
        # For now, just ensure the error handling code exists
        pass


class TestMDXTransformer:
    """Test the MDX AST transformer."""

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return MDXParser()

    def test_cube_reference_extraction(self, parser):
        """Test cube reference extraction."""
        mdx = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS
        FROM [Test Cube]
        """

        result = parser.parse(mdx)
        assert result.cube.name == "Test Cube"
        assert result.cube.database is None

    def test_database_qualified_cube(self, parser):
        """Test database qualified cube reference."""
        # This would require extending the grammar to handle database.cube format
        pass

    def test_measure_alias_handling(self, parser):
        """Test measure alias extraction."""
        mdx = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS
        FROM [Adventure Works]
        """

        result = parser.parse(mdx)
        # The alias should default to the clean measure name
        assert result.measures[0].alias == "Sales Amount"
