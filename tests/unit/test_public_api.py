"""
Unit tests for the public API functions.

Tests the high-level API functions: mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from unmdx.api import mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx
from unmdx.config import UnMDXConfig, create_default_config, OptimizationLevel
from unmdx.exceptions import (
    ValidationError, ParseError, TransformError, GenerationError,
    LintError, ExplanationError
)
from unmdx.results import (
    ConversionResult, ParseResult, ExplanationResult, OptimizationResult
)


class TestMdxToDax:
    """Test the mdx_to_dax function."""
    
    def test_basic_conversion_success(self):
        """Test successful basic MDX to DAX conversion."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            
            # Execute
            result = mdx_to_dax(mdx_query)
            
            # Verify
            assert isinstance(result, ConversionResult)
            assert result.dax_query == mock_dax
            assert result.original_mdx is None  # Not included by default
            assert result.optimization_applied == True  # Default is to optimize
            assert result.performance.total_time > 0
            
            # Verify components were called
            mock_parser.return_value.parse.assert_called_once_with(mdx_query)
            mock_transformer.return_value.transform.assert_called_once_with(mock_tree)
            mock_generator.return_value.generate.assert_called_once_with(mock_ir)
    
    def test_conversion_with_custom_config(self):
        """Test conversion with custom configuration."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        config = create_default_config()
        config.dax.format_output = False
        config.linter.optimization_level = OptimizationLevel.AGGRESSIVE
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            mock_lint_report = Mock()
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            mock_lint_report.rules_applied = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute
            result = mdx_to_dax(mdx_query, config=config)
            
            # Verify config was used
            mock_generator.assert_called_once_with(format_output=False, debug=False)
            assert result.optimization_level == "aggressive"
    
    def test_conversion_without_optimization(self):
        """Test conversion with optimization disabled."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            
            # Execute with optimization disabled
            result = mdx_to_dax(mdx_query, optimize=False)
            
            # Verify linter was not called
            mock_linter.assert_not_called()
            assert result.optimization_applied == False
    
    def test_conversion_with_metadata(self):
        """Test conversion with metadata inclusion."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.tracemalloc') as mock_tracemalloc:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_dax = "EVALUATE SUMMARIZECOLUMNS('Sales'[Region], \"Total Sales\", SUM('Sales'[Amount]))"
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            
            # Setup memory tracking
            mock_tracemalloc.is_tracing.return_value = True
            mock_tracemalloc.get_traced_memory.return_value = (1000000, 2000000)
            
            # Execute with metadata
            result = mdx_to_dax(mdx_query, include_metadata=True)
            
            # Verify metadata is included
            assert result.original_mdx == mdx_query
            assert result.ir_query == mock_ir
            assert len(result.dax_functions_used) > 0
            assert result.performance.memory_peak_mb is not None
    
    def test_empty_mdx_text_validation(self):
        """Test validation of empty MDX text."""
        with pytest.raises(ValidationError) as exc_info:
            mdx_to_dax("")
        
        assert "MDX text cannot be empty" in str(exc_info.value)
        assert exc_info.value.field_name == "mdx_text"
    
    def test_parse_error_handling(self):
        """Test handling of parse errors."""
        mdx_query = "INVALID MDX SYNTAX"
        
        with patch('unmdx.api.MDXParser') as mock_parser:
            mock_parser.return_value.parse.side_effect = Exception("Parse failed")
            
            with pytest.raises(ParseError) as exc_info:
                mdx_to_dax(mdx_query)
            
            assert "Parse failed" in str(exc_info.value)
    
    def test_transform_error_handling(self):
        """Test handling of transformation errors."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer:
            
            mock_parser.return_value.parse.return_value = Mock()
            
            from unmdx.transformer.mdx_transformer import TransformationError
            mock_transformer.return_value.transform.side_effect = TransformationError("Transform failed")
            
            with pytest.raises(TransformError) as exc_info:
                mdx_to_dax(mdx_query)
            
            assert "Transform failed" in str(exc_info.value)
    
    def test_generation_error_handling(self):
        """Test handling of DAX generation errors."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator:
            
            mock_parser.return_value.parse.return_value = Mock()
            mock_transformer.return_value.transform.return_value = Mock()
            
            from unmdx.dax_generator.dax_generator import DAXGenerationError
            mock_generator.return_value.generate.side_effect = DAXGenerationError("Generation failed")
            
            with pytest.raises(GenerationError) as exc_info:
                mdx_to_dax(mdx_query)
            
            assert "Generation failed" in str(exc_info.value)


class TestParseMdx:
    """Test the parse_mdx function."""
    
    def test_basic_parsing_success(self):
        """Test successful MDX parsing."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            
            # Execute
            result = parse_mdx(mdx_query)
            
            # Verify
            assert isinstance(result, ParseResult)
            assert result.ir_query == mock_ir
            assert result.performance.total_time > 0
            assert result.complexity_score is not None
    
    def test_parsing_with_metadata(self):
        """Test parsing with metadata inclusion."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api._count_ast_nodes') as mock_count_ast, \
             patch('unmdx.api._count_ir_constructs') as mock_count_ir:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_count_ast.return_value = 25
            mock_count_ir.return_value = 5
            
            # Execute with metadata
            result = parse_mdx(mdx_query, include_metadata=True)
            
            # Verify metadata
            assert result.ast_node_count == 25
            assert result.ir_construct_count == 5
    
    def test_empty_mdx_validation(self):
        """Test validation of empty MDX text."""
        with pytest.raises(ValidationError) as exc_info:
            parse_mdx("   ")  # Whitespace only
        
        assert "MDX text cannot be empty" in str(exc_info.value)


class TestOptimizeMdx:
    """Test the optimize_mdx function."""
    
    def test_basic_optimization_success(self):
        """Test successful MDX optimization."""
        mdx_query = "SELECT (([Measures].[Sales])) ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            # Setup mocks
            mock_tree = Mock()
            mock_lint_report = Mock()
            mock_lint_report.rules_applied = ["ParenthesesCleaner"]
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute
            result = optimize_mdx(mdx_query)
            
            # Verify
            assert isinstance(result, OptimizationResult)
            assert result.original_mdx == mdx_query
            assert result.optimization_level == "conservative"  # Default
            assert "ParenthesesCleaner" in result.rules_applied
    
    def test_optimization_with_custom_level(self):
        """Test optimization with custom optimization level."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            # Setup mocks
            mock_tree = Mock()
            mock_lint_report = Mock()
            mock_lint_report.rules_applied = []
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute with aggressive optimization
            result = optimize_mdx(mdx_query, optimization_level="aggressive")
            
            # Verify optimization level was set
            assert result.optimization_level == "aggressive"
    
    def test_invalid_optimization_level(self):
        """Test validation of invalid optimization level."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with pytest.raises(ValidationError) as exc_info:
            optimize_mdx(mdx_query, optimization_level="invalid")
        
        assert "Invalid optimization level" in str(exc_info.value)
        assert exc_info.value.field_name == "optimization_level"


class TestExplainMdx:
    """Test the explain_mdx function."""
    
    def test_basic_explanation_success(self):
        """Test successful MDX explanation generation."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.ExplainerGenerator') as mock_explainer:
            
            # Setup mock
            mock_explanation = "This query selects Sales measure from Sales cube"
            mock_explainer.return_value.explain_mdx.return_value = mock_explanation
            
            # Execute
            result = explain_mdx(mdx_query)
            
            # Verify
            assert isinstance(result, ExplanationResult)
            assert result.sql_explanation == mock_explanation
            assert result.format_used == "sql"
            assert result.detail_level == "standard"
    
    def test_explanation_with_different_format(self):
        """Test explanation with different output format."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.ExplainerGenerator') as mock_explainer:
            
            # Setup mock
            mock_explanation = "**Query Analysis**\nThis query..."
            mock_explainer.return_value.explain_mdx.return_value = mock_explanation
            
            # Execute with markdown format
            result = explain_mdx(mdx_query, format_type="markdown", detail_level="detailed")
            
            # Verify
            assert result.markdown_explanation == mock_explanation
            assert result.format_used == "markdown"
            assert result.detail_level == "detailed"
    
    def test_explanation_with_dax_comparison(self):
        """Test explanation with DAX comparison included."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.ExplainerGenerator') as mock_explainer, \
             patch('unmdx.api.mdx_to_dax') as mock_mdx_to_dax:
            
            # Setup mocks
            mock_explanation = "Query explanation"
            mock_dax_result = Mock()
            mock_dax_result.dax_query = "EVALUATE SUMMARIZECOLUMNS(...)"
            
            mock_explainer.return_value.explain_mdx.return_value = mock_explanation
            mock_mdx_to_dax.return_value = mock_dax_result
            
            # Execute with DAX comparison
            result = explain_mdx(mdx_query, include_dax=True)
            
            # Verify DAX was included
            assert result.dax_query == "EVALUATE SUMMARIZECOLUMNS(...)"
            assert result.include_dax_comparison == True
    
    def test_invalid_format_validation(self):
        """Test validation of invalid explanation format."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with pytest.raises(ValidationError) as exc_info:
            explain_mdx(mdx_query, format_type="invalid")
        
        assert "Invalid explanation format" in str(exc_info.value)
        assert exc_info.value.field_name == "format_type"
    
    def test_invalid_detail_level_validation(self):
        """Test validation of invalid detail level."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with pytest.raises(ValidationError) as exc_info:
            explain_mdx(mdx_query, detail_level="invalid")
        
        assert "Invalid detail level" in str(exc_info.value)
        assert exc_info.value.field_name == "detail_level"


class TestHelperFunctions:
    """Test helper functions used by the API."""
    
    def test_extract_dax_functions(self):
        """Test DAX function extraction."""
        from unmdx.api import _extract_dax_functions
        
        dax_query = """
        EVALUATE
        SUMMARIZECOLUMNS(
            'Sales'[Region],
            "Total Sales", SUM('Sales'[Amount]),
            "Avg Sales", AVERAGE('Sales'[Amount])
        )
        """
        
        functions = _extract_dax_functions(dax_query)
        
        assert "EVALUATE" in functions
        assert "SUMMARIZECOLUMNS" in functions
        assert "SUM" in functions
        assert "AVERAGE" in functions
    
    def test_extract_dax_tables(self):
        """Test DAX table extraction."""
        from unmdx.api import _extract_dax_tables
        
        dax_query = "SUMMARIZECOLUMNS('Sales'[Region], [Measures].[Total])"
        
        tables = _extract_dax_tables(dax_query)
        
        assert "Sales" in tables
        # Measures should be filtered out
        assert "Measures" not in tables
    
    def test_calculate_complexity_score(self):
        """Test complexity score calculation."""
        from unmdx.api import _calculate_complexity_score
        
        # Mock IR query with various constructs
        mock_ir = Mock()
        mock_ir.measures = [Mock(), Mock()]  # 2 measures
        mock_ir.dimensions = [Mock()]        # 1 dimension
        mock_ir.filters = [Mock(), Mock(), Mock()]  # 3 filters
        mock_ir.calculations = []            # No calculations
        
        score = _calculate_complexity_score(mock_ir)
        
        # Score should be: 0.1 + (2*0.1) + (1*0.15) + (3*0.2) + (0*0.3) = 0.95
        assert 0.9 <= score <= 1.0
    
    def test_estimate_performance(self):
        """Test performance estimation."""
        from unmdx.api import _estimate_performance
        
        assert _estimate_performance(0.2) == "fast"
        assert _estimate_performance(0.5) == "moderate"
        assert _estimate_performance(0.8) == "slow"
    
    def test_estimate_query_complexity(self):
        """Test query complexity estimation.""" 
        from unmdx.api import _estimate_query_complexity
        
        assert _estimate_query_complexity(0.2) == "simple"
        assert _estimate_query_complexity(0.5) == "moderate"
        assert _estimate_query_complexity(0.8) == "complex"


# Integration-style tests that verify the complete flow works
class TestApiIntegration:
    """Integration tests for API functions working together."""
    
    @pytest.mark.integration
    def test_parse_then_convert_workflow(self):
        """Test parsing MDX then converting to DAX in separate steps."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            
            # First parse
            parse_result = parse_mdx(mdx_query)
            
            # Then convert (would use the same IR in real scenario)
            convert_result = mdx_to_dax(mdx_query)
            
            # Verify both operations succeeded
            assert isinstance(parse_result, ParseResult)
            assert isinstance(convert_result, ConversionResult)
            assert convert_result.dax_query == mock_dax
    
    @pytest.mark.integration 
    def test_optimize_then_convert_workflow(self):
        """Test optimizing MDX then converting to DAX."""
        mdx_query = "SELECT (([Measures].[Sales])) ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXLinter') as mock_linter, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            mock_lint_report = Mock()
            mock_lint_report.rules_applied = []
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            
            # First optimize
            optimize_result = optimize_mdx(mdx_query)
            
            # Then convert optimized MDX
            convert_result = mdx_to_dax(optimize_result.optimized_mdx)
            
            # Verify workflow
            assert isinstance(optimize_result, OptimizationResult)
            assert isinstance(convert_result, ConversionResult)
            assert convert_result.optimization_applied == True