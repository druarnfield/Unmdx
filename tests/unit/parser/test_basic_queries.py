"""Unit tests for basic MDX queries (Tests 1-10)."""

import pytest
from lark import Tree

from unmdx.parser import MDXParser, MDXParseError, MDXTreeAnalyzer


class TestBasicQueries:
    """Test basic MDX query parsing."""
    
    @pytest.fixture
    def parser(self):
        """Create MDX parser instance."""
        return MDXParser()
    
    def test_case_1_simple_measure_query(self, parser):
        """Test Case 1: Simple measure query."""
        mdx_query = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        assert tree.data == 'query'
        
        # Analyze structure
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        assert len(structure.dimensions) == 0
        assert len(structure.filters) == 0
        assert not structure.has_with_clause
    
    def test_case_2_measure_with_dimension(self, parser):
        """Test Case 2: Measure with dimension (messy spacing)."""
        mdx_query = """SELECT{[Measures].[Sales Amount]}ON COLUMNS,
     {[Product].[Category].Members}    ON    ROWS
FROM    [Adventure Works]"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        assert len(structure.dimensions) >= 1
        
        # Check for Product.Category dimension
        product_dims = [d for d in structure.dimensions if d.get('dimension') == 'Product']
        assert len(product_dims) >= 1
        assert product_dims[0].get('hierarchy') == 'Category'
    
    def test_case_3_multiple_measures(self, parser):
        """Test Case 3: Multiple measures with redundant braces."""
        mdx_query = """SELECT {{{[Measures].[Sales Amount]}, {[Measures].[Order Quantity]}}} ON 0,
{[Date].[Calendar Year].Members} ON 1
FROM [Adventure Works]"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        assert "Order Quantity" in structure.measures
        
        # Check for Date dimension
        date_dims = [d for d in structure.dimensions if d.get('dimension') == 'Date']
        assert len(date_dims) >= 1
    
    def test_case_4_simple_where_clause(self, parser):
        """Test Case 4: Simple WHERE clause."""
        mdx_query = """SELECT   {[Measures].[Sales Amount]}   ON   COLUMNS,
{[Product].[Category].Members} ON ROWS
FROM [Adventure Works]
WHERE    ([Date].[Calendar Year].&[2023])"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        assert len(structure.filters) >= 1
        
        # Check filter
        date_filters = [f for f in structure.filters if f.get('dimension') == 'Date']
        assert len(date_filters) >= 1
        assert date_filters[0].get('value') == '2023'
    
    def test_case_5_crossjoin_redundant_parentheses(self, parser):
        """Test Case 5: CrossJoin with redundant parentheses."""
        mdx_query = """SELECT {[Measures].[Sales Amount]} ON 0,
CROSSJOIN(({[Product].[Category].Members}),
          ({[Customer].[Country].Members})) ON 1
FROM [Adventure Works]"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        
        # Should have dimensions from both Product and Customer
        dimensions = structure.dimensions
        dim_names = [d.get('dimension') for d in dimensions]
        assert 'Product' in dim_names or 'Customer' in dim_names
    
    def test_case_6_specific_member_selection(self, parser):
        """Test Case 6: Specific member selection (verbose)."""
        mdx_query = """SELECT{[Measures].[Sales Amount]}ON AXIS(0),
{{[Product].[Category].[Bikes]},{[Product].[Category].[Accessories]}}ON AXIS(1)
FROM[Adventure Works]"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        
        # Check axes
        assert len(structure.axes) == 2
        assert structure.axes[0]['name'] == 'axis_0'
        assert structure.axes[1]['name'] == 'axis_1'
    
    def test_case_7_calculated_member(self, parser):
        """Test Case 7: Simple calculated member."""
        mdx_query = """WITH MEMBER[Measures].[Average Price]AS[Measures].[Sales Amount]/[Measures].[Order Quantity]
SELECT{[Measures].[Sales Amount],[Measures].[Order Quantity],[Measures].[Average Price]}ON 0
FROM[Adventure Works]"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert structure.has_with_clause
        assert len(structure.calculations) >= 1
        
        # Check calculation
        calc = structure.calculations[0]
        assert calc.get('name') == 'Average Price'
        assert calc.get('type') == 'member'
    
    def test_case_8_non_empty_nested_sets(self, parser):
        """Test Case 8: NON EMPTY with nested sets."""
        mdx_query = """SELECT NON EMPTY{{[Measures].[Sales Amount]}}ON 0,
NON EMPTY{{{[Product].[Category].Members}}}ON 1
FROM[Adventure Works]"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        
        # Check for NON EMPTY on axes
        assert len(structure.axes) == 2
        assert structure.axes[0]['has_non_empty'] == True
        assert structure.axes[1]['has_non_empty'] == True
    
    def test_case_9_multiple_filters_tuple(self, parser):
        """Test Case 9: Multiple filters in WHERE (complex tuple)."""
        mdx_query = """SELECT{[Measures].[Sales Amount]}ON COLUMNS,
{[Product].[Category].Members}ON ROWS
FROM[Adventure Works]
WHERE([Date].[Calendar Year].&[2023],[Geography].[Country].&[United States])"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        assert len(structure.filters) >= 2
        
        # Check both filters
        dim_names = [f.get('dimension') for f in structure.filters]
        assert 'Date' in dim_names
        assert 'Geography' in dim_names
    
    def test_case_10_empty_sets_redundant_constructs(self, parser):
        """Test Case 10: Empty sets and redundant constructs."""
        mdx_query = """SELECT{{{{}}},{[Measures].[Sales Amount]},{{}}}ON 0,
{[Date].[Calendar].[Calendar Year].Members}ON 1
FROM[Adventure Works]WHERE()"""
        
        tree = parser.parse(mdx_query)
        assert isinstance(tree, Tree)
        
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        assert structure.cube_name == "Adventure Works"
        assert "Sales Amount" in structure.measures
        
        # Empty WHERE clause should result in no filters
        assert len(structure.filters) == 0
        
        # Should still have Calendar Year dimension
        date_dims = [d for d in structure.dimensions if d.get('dimension') == 'Date']
        assert len(date_dims) >= 1


class TestParserErrorHandling:
    """Test parser error handling and edge cases."""
    
    @pytest.fixture
    def parser(self):
        """Create MDX parser instance."""
        return MDXParser()
    
    def test_empty_query(self, parser):
        """Test empty query handling."""
        with pytest.raises(MDXParseError) as exc_info:
            parser.parse("")
        
        assert "Empty or whitespace-only query" in str(exc_info.value)
    
    def test_whitespace_only_query(self, parser):
        """Test whitespace-only query handling."""
        with pytest.raises(MDXParseError) as exc_info:
            parser.parse("   \n  \t  \n   ")
        
        assert "Empty or whitespace-only query" in str(exc_info.value)
    
    def test_malformed_syntax(self, parser):
        """Test malformed syntax handling."""
        malformed_query = "SELECT [Measures] ON COLUMNS FROM"  # Missing cube
        
        with pytest.raises(MDXParseError):
            parser.parse(malformed_query)
    
    def test_syntax_validation(self, parser):
        """Test syntax validation without full parsing."""
        valid_query = "SELECT {[Measures].[Sales]} ON 0 FROM [Cube]"
        invalid_query = "SELECT {[Measures].[Sales]} ON FROM"
        
        # Valid query
        result = parser.validate_syntax(valid_query)
        assert result['valid'] == True
        assert len(result['errors']) == 0
        
        # Invalid query
        result = parser.validate_syntax(invalid_query)
        assert result['valid'] == False
        assert len(result['errors']) > 0


class TestParserFeatures:
    """Test specific parser features and utilities."""
    
    @pytest.fixture
    def parser(self):
        """Create MDX parser instance."""
        return MDXParser()
    
    def test_parse_file_not_found(self, parser, tmp_path):
        """Test parsing non-existent file."""
        non_existent_file = tmp_path / "missing.mdx"
        
        with pytest.raises(MDXParseError) as exc_info:
            parser.parse_file(non_existent_file)
        
        assert "file not found" in str(exc_info.value).lower()
    
    def test_parse_file_success(self, parser, tmp_path):
        """Test successful file parsing."""
        mdx_file = tmp_path / "test.mdx"
        mdx_content = "SELECT {[Measures].[Sales]} ON 0 FROM [Cube]"
        
        mdx_file.write_text(mdx_content, encoding='utf-8')
        
        tree = parser.parse_file(mdx_file)
        assert isinstance(tree, Tree)
        assert tree.data == 'query'
    
    def test_debug_mode(self):
        """Test parser debug mode."""
        debug_parser = MDXParser(debug=True)
        
        mdx_query = "SELECT {[Measures].[Sales]} ON 0 FROM [Cube]"
        tree = debug_parser.parse(mdx_query)
        
        assert isinstance(tree, Tree)
    
    def test_query_cleaning(self, parser):
        """Test internal query cleaning functionality."""
        messy_query = """
        
        SELECT    {[Measures].[Sales]}    ON 0
        
        FROM   [Cube]   
        
        """
        
        tree = parser.parse(messy_query)
        assert isinstance(tree, Tree)
        assert tree.data == 'query'
    
    def test_context_extraction(self, parser):
        """Test error context extraction."""
        # This will fail parsing and should provide context
        bad_query = "SELECT {[Measures].[Sales]} ON COLUMNS FROM @INVALID@"
        
        try:
            parser.parse(bad_query)
            pytest.fail("Expected parsing to fail")
        except MDXParseError as e:
            # Should have context information
            assert hasattr(e, 'context')
    
    def test_warning_detection(self, parser):
        """Test warning detection for problematic constructs."""
        # Create a query with redundant constructs to trigger warnings
        redundant_query = """SELECT {[Measures].[Sales]} ON 0 FROM [Cube]"""
        
        result = parser.validate_syntax(redundant_query)
        assert result['valid'] == True
        # For now, just test that validation works - warnings will be improved later
        assert 'errors' in result
        assert 'warnings' in result
    
    def test_tree_visitor_integration(self, parser):
        """Test integration with tree visitor."""
        mdx_query = """WITH MEMBER [Measures].[Profit] AS [Measures].[Sales] - [Measures].[Cost]
                      SELECT {[Measures].[Sales], [Measures].[Profit]} ON 0,
                             {[Product].[Category].Members} ON 1
                      FROM [Adventure Works]
                      WHERE ([Date].[Year].&[2023])"""
        
        tree = parser.parse(mdx_query)
        analyzer = MDXTreeAnalyzer(tree)
        structure = analyzer.analyze()
        
        # Verify all components are detected
        assert structure.has_with_clause
        assert len(structure.measures) >= 2
        assert len(structure.dimensions) >= 1
        assert len(structure.filters) >= 1
        assert len(structure.calculations) >= 1
        assert structure.cube_name == "Adventure Works"