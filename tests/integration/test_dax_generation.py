"""Integration tests for full MDX to DAX pipeline."""

import pytest

from unmdx.parser import MDXParser
from unmdx.transformer import MDXTransformer
from unmdx.dax_generator import DAXGenerator
from unmdx.dax_generator.utils import validate_dax_syntax


class TestMDXToDAXPipeline:
    """Test complete MDX to DAX conversion pipeline."""
    
    @pytest.fixture
    def parser(self):
        """Create MDX parser instance."""
        return MDXParser()
    
    @pytest.fixture
    def transformer(self):
        """Create MDX transformer instance."""
        return MDXTransformer()
    
    @pytest.fixture
    def generator(self):
        """Create DAX generator instance."""
        return DAXGenerator()
    
    def test_simple_measure_conversion(self, parser, transformer, generator):
        """Test converting simple measure query from MDX to DAX."""
        mdx_query = "SELECT {[Measures].[Sales Amount]} ON 0 FROM [Adventure Works]"
        
        # Parse MDX
        tree = parser.parse(mdx_query)
        
        # Transform to IR
        ir_query = transformer.transform(tree)
        
        # Generate DAX
        dax_query = generator.generate(ir_query)
        
        # Validate result
        assert "EVALUATE" in dax_query
        assert "[Sales Amount]" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True
    
    def test_dimensional_query_conversion(self, parser, transformer, generator):
        """Test converting dimensional query from MDX to DAX."""
        mdx_query = """SELECT {[Measures].[Sales Amount]} ON 0,
                      {[Product].[Category].Members} ON 1
                      FROM [Adventure Works]"""
        
        # Parse MDX
        tree = parser.parse(mdx_query)
        
        # Transform to IR
        ir_query = transformer.transform(tree)
        
        # Generate DAX
        dax_query = generator.generate(ir_query)
        
        # Validate result
        assert "EVALUATE" in dax_query
        assert "SUMMARIZECOLUMNS(" in dax_query
        assert "'Product'" in dax_query
        assert "[Sales Amount]" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True
    
    def test_filtered_query_conversion(self, parser, transformer, generator):
        """Test converting filtered query from MDX to DAX."""
        mdx_query = """SELECT {[Measures].[Sales Amount]} ON 0,
                      {[Product].[Category].Members} ON 1
                      FROM [Adventure Works]
                      WHERE ([Date].[Calendar Year].&[2023])"""
        
        # Parse MDX
        tree = parser.parse(mdx_query)
        
        # Transform to IR
        ir_query = transformer.transform(tree)
        
        # Generate DAX
        dax_query = generator.generate(ir_query)
        
        # Validate result
        assert "EVALUATE" in dax_query
        assert "SUMMARIZECOLUMNS(" in dax_query
        assert "FILTER(" in dax_query
        assert "2023" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True
    
    def test_multiple_measures_conversion(self, parser, transformer, generator):
        """Test converting query with multiple measures from MDX to DAX."""
        mdx_query = """SELECT {[Measures].[Sales Amount], [Measures].[Order Quantity]} ON 0,
                      {[Product].[Category].Members} ON 1
                      FROM [Adventure Works]"""
        
        # Parse MDX
        tree = parser.parse(mdx_query)
        
        # Transform to IR
        ir_query = transformer.transform(tree)
        
        # Generate DAX
        dax_query = generator.generate(ir_query)
        
        # Validate result
        assert "EVALUATE" in dax_query
        assert "SUMMARIZECOLUMNS(" in dax_query
        assert "[Sales Amount]" in dax_query
        assert "[Order Quantity]" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True
    
    def test_calculated_member_conversion(self, parser, transformer, generator):
        """Test converting calculated member from MDX to DAX."""
        mdx_query = """WITH MEMBER [Measures].[Profit] AS [Measures].[Sales Amount] - [Measures].[Total Cost]
                      SELECT {[Measures].[Sales Amount], [Measures].[Profit]} ON 0
                      FROM [Adventure Works]"""
        
        # Parse MDX
        tree = parser.parse(mdx_query)
        
        # Transform to IR
        ir_query = transformer.transform(tree)
        
        # Generate DAX
        dax_query = generator.generate(ir_query)
        
        # Validate result
        assert "DEFINE" in dax_query
        assert "MEASURE [Profit]" in dax_query
        assert "EVALUATE" in dax_query
        assert "[Sales Amount]" in dax_query
        assert "[Total Cost]" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True
    
    def test_crossjoin_conversion(self, parser, transformer, generator):
        """Test converting CrossJoin query from MDX to DAX."""
        mdx_query = """SELECT {[Measures].[Sales Amount]} ON 0,
                      CROSSJOIN({[Product].[Category].Members}, {[Date].[Calendar Year].Members}) ON 1
                      FROM [Adventure Works]"""
        
        # Parse MDX
        tree = parser.parse(mdx_query)
        
        # Transform to IR
        ir_query = transformer.transform(tree)
        
        # Generate DAX
        dax_query = generator.generate(ir_query)
        
        # Validate result
        assert "EVALUATE" in dax_query
        assert "SUMMARIZECOLUMNS(" in dax_query
        assert "'Product'" in dax_query
        assert "'Date'" in dax_query
        assert "[Sales Amount]" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True


class TestDAXOptimization:
    """Test DAX optimization in the pipeline."""
    
    @pytest.fixture
    def parser(self):
        return MDXParser()
    
    @pytest.fixture
    def transformer(self):
        return MDXTransformer()
    
    @pytest.fixture
    def generator(self):
        return DAXGenerator()
    
    def test_redundant_nesting_optimization(self, parser, transformer, generator):
        """Test optimization of redundantly nested MDX sets."""
        mdx_query = "SELECT {{{[Measures].[Sales Amount]}}} ON 0 FROM [Adventure Works]"
        
        # Parse and transform
        tree = parser.parse(mdx_query)
        ir_query = transformer.transform(tree)
        
        # Generate DAX
        dax_query = generator.generate(ir_query)
        
        # Should generate clean DAX without redundant nesting
        assert "EVALUATE" in dax_query
        assert "[Sales Amount]" in dax_query
        
        # Should not contain excessive brackets or complexity
        assert dax_query.count('{') <= 2  # Only essential brackets
    
    def test_filter_consolidation(self, parser, transformer, generator):
        """Test consolidation of multiple filters on same dimension."""
        # This would need MDX with multiple filters, which might be complex to construct
        # For now, test with simple filter
        mdx_query = """SELECT {[Measures].[Sales Amount]} ON 0
                      FROM [Adventure Works]
                      WHERE ([Date].[Calendar Year].&[2023])"""
        
        tree = parser.parse(mdx_query)
        ir_query = transformer.transform(tree)
        dax_query = generator.generate(ir_query)
        
        # Should have clean filter expression
        assert "FILTER(" in dax_query
        assert "2023" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True


class TestEdgeCases:
    """Test edge cases in MDX to DAX conversion."""
    
    @pytest.fixture
    def parser(self):
        return MDXParser()
    
    @pytest.fixture
    def transformer(self):
        return MDXTransformer()
    
    @pytest.fixture
    def generator(self):
        return DAXGenerator()
    
    def test_empty_set_handling(self, parser, transformer, generator):
        """Test handling of empty sets in MDX."""
        mdx_query = "SELECT {} ON 0 FROM [Adventure Works]"
        
        tree = parser.parse(mdx_query)
        ir_query = transformer.transform(tree)
        dax_query = generator.generate(ir_query)
        
        # Should generate valid DAX even with empty measures
        assert "EVALUATE" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True
    
    def test_member_function_conversion(self, parser, transformer, generator):
        """Test conversion of member functions like .Members."""
        mdx_query = """SELECT {[Measures].[Sales Amount]} ON 0,
                      {[Product].[Category].Members} ON 1
                      FROM [Adventure Works]"""
        
        tree = parser.parse(mdx_query)
        ir_query = transformer.transform(tree)
        dax_query = generator.generate(ir_query)
        
        # Should handle .Members function appropriately in DAX
        assert "EVALUATE" in dax_query
        assert "SUMMARIZECOLUMNS(" in dax_query
        assert "'Product'" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True
    
    def test_axis_specification_handling(self, parser, transformer, generator):
        """Test handling of different axis specifications."""
        mdx_query = """SELECT {[Measures].[Sales Amount]} ON AXIS(0),
                      {[Product].[Category].Members} ON AXIS(1)
                      FROM [Adventure Works]"""
        
        tree = parser.parse(mdx_query)
        ir_query = transformer.transform(tree)
        dax_query = generator.generate(ir_query)
        
        # Should generate valid DAX regardless of axis specification format
        assert "EVALUATE" in dax_query
        assert "SUMMARIZECOLUMNS(" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True


class TestPerformance:
    """Test performance aspects of DAX generation."""
    
    @pytest.fixture
    def parser(self):
        return MDXParser()
    
    @pytest.fixture
    def transformer(self):
        return MDXTransformer()
    
    @pytest.fixture
    def generator(self):
        return DAXGenerator()
    
    def test_large_query_performance(self, parser, transformer, generator):
        """Test performance with larger, more complex queries."""
        # Create a more complex MDX query
        mdx_query = """WITH MEMBER [Measures].[Profit] AS [Measures].[Sales Amount] - [Measures].[Total Cost]
                      MEMBER [Measures].[Profit Margin] AS [Measures].[Profit] / [Measures].[Sales Amount]
                      SELECT {[Measures].[Sales Amount], [Measures].[Total Cost], [Measures].[Profit], [Measures].[Profit Margin]} ON 0,
                      CROSSJOIN({[Product].[Category].Members}, {[Date].[Calendar Year].Members}) ON 1
                      FROM [Adventure Works]
                      WHERE ([Customer].[Country].&[United States])"""
        
        import time
        start_time = time.time()
        
        # Parse and transform
        tree = parser.parse(mdx_query)
        ir_query = transformer.transform(tree)
        dax_query = generator.generate(ir_query)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (< 1 second for this size)
        assert processing_time < 1.0
        
        # Should generate valid DAX
        assert "DEFINE" in dax_query
        assert "EVALUATE" in dax_query
        assert "SUMMARIZECOLUMNS(" in dax_query
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True
    
    def test_generated_dax_readability(self, parser, transformer, generator):
        """Test that generated DAX is readable and well-formatted."""
        mdx_query = """SELECT {[Measures].[Sales Amount], [Measures].[Order Quantity]} ON 0,
                      {[Product].[Category].Members} ON 1
                      FROM [Adventure Works]
                      WHERE ([Date].[Calendar Year].&[2023])"""
        
        tree = parser.parse(mdx_query)
        ir_query = transformer.transform(tree)
        dax_query = generator.generate(ir_query)
        
        # Check for readable formatting
        lines = dax_query.split('\n')
        
        # Should have multiple lines for readability
        assert len(lines) > 1
        
        # Should have proper indentation (look for leading spaces)
        indented_lines = [line for line in lines if line.startswith('    ')]
        assert len(indented_lines) > 0
        
        # Should not have excessively long lines
        for line in lines:
            assert len(line) <= 150  # Reasonable line length
        
        # Validate syntax
        validation = validate_dax_syntax(dax_query)
        assert validation["valid"] is True