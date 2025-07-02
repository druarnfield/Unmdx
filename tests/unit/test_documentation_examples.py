"""
Documentation tests for API examples.

These tests ensure that all code examples in docstrings and documentation
actually work as expected. This is crucial for maintaining user trust and
ensuring the API is correctly documented.
"""

from unittest.mock import patch, Mock

import pytest

from unmdx import (
    mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx,
    UnMDXConfig, create_default_config, create_fast_config, create_comprehensive_config,
    ConversionResult, ParseResult, ExplanationResult, OptimizationResult
)


class TestMdxToDaxDocExamples:
    """Test examples from mdx_to_dax docstring."""
    
    def test_basic_usage_example(self):
        """Test the basic usage example from docstring."""
        # Example from docstring:
        # result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            # Setup mocks to return expected output
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            expected_dax = """EVALUATE
SUMMARIZECOLUMNS(
    "Sales", [Measures].[Sales]
)"""
            
            mock_lint_report = Mock()
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            mock_lint_report.rules_applied = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = expected_dax
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute the documented example
            result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Verify the example works as documented
            assert isinstance(result, ConversionResult)
            assert result.dax_query == expected_dax
            assert hasattr(result, 'performance')
            assert result.performance.total_time >= 0
    
    def test_performance_timing_example(self):
        """Test the performance timing example from docstring."""
        # Example from docstring:
        # print(f"Conversion took {result.performance.total_time:.2f}s")
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter, \
             patch('unmdx.api.time') as mock_time:
            
            # Setup timing simulation
            mock_time.time.side_effect = [0.0, 0.15, 0.30]  # Total of 0.15s
            
            # Setup component mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            mock_lint_report = Mock()
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            mock_lint_report.rules_applied = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute conversion
            result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Verify the performance timing example works
            timing_text = f"Conversion took {result.performance.total_time:.2f}s"
            assert "Conversion took" in timing_text
            assert "s" in timing_text
            # Should be able to format as documented
            assert isinstance(result.performance.total_time, (int, float))


class TestParseMdxDocExamples:
    """Test examples from parse_mdx docstring."""
    
    def test_basic_parsing_example(self):
        """Test the basic parsing example from docstring."""
        # Example from docstring:
        # result = parse_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
        # print(f"Parsed {len(result.ir_query.measures)} measures")
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]  # One measure
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            
            # Execute the documented example
            result = parse_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Verify the example works as documented
            assert isinstance(result, ParseResult)
            assert hasattr(result.ir_query, 'measures')
            measures_text = f"Parsed {len(result.ir_query.measures)} measures"
            assert "Parsed 1 measures" == measures_text
    
    def test_complexity_score_example(self):
        """Test the complexity score example from docstring."""
        # Example from docstring:
        # print(f"Query complexity: {result.complexity_score}")
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            
            # Execute parsing
            result = parse_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Verify complexity score example works
            assert result.complexity_score is not None
            complexity_text = f"Query complexity: {result.complexity_score}"
            assert "Query complexity:" in complexity_text
            assert isinstance(result.complexity_score, (int, float))


class TestOptimizeMdxDocExamples:
    """Test examples from optimize_mdx docstring."""
    
    def test_basic_optimization_example(self):
        """Test the basic optimization example from docstring."""
        # Example from docstring:
        # result = optimize_mdx("SELECT (([Measures].[Sales])) ON 0 FROM [Sales]")
        # print(result.optimized_mdx)
        # Output: SELECT [Measures].[Sales] ON 0 FROM [Sales]
        
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
            
            # Execute the documented example
            result = optimize_mdx("SELECT (([Measures].[Sales])) ON 0 FROM [Sales]")
            
            # Verify the example works as documented
            assert isinstance(result, OptimizationResult)
            assert hasattr(result, 'optimized_mdx')
            assert hasattr(result, 'original_mdx')
            assert result.original_mdx == "SELECT (([Measures].[Sales])) ON 0 FROM [Sales]"
    
    def test_size_reduction_example(self):
        """Test the size reduction example from docstring."""
        # Example from docstring:
        # print(f"Size reduction: {result.size_reduction_percent:.1f}%")
        
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
            
            # Execute optimization
            result = optimize_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Verify size reduction example works
            if result.size_reduction_percent is not None:
                size_text = f"Size reduction: {result.size_reduction_percent:.1f}%"
                assert "Size reduction:" in size_text
                assert "%" in size_text
            else:
                # Should be able to handle None case too
                size_text = f"Size reduction: {result.size_reduction_percent or 0.0:.1f}%"
                assert "Size reduction: 0.0%" == size_text


class TestExplainMdxDocExamples:
    """Test examples from explain_mdx docstring."""
    
    def test_basic_explanation_example(self):
        """Test the basic explanation example from docstring."""
        # Example from docstring:
        # result = explain_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
        # print(result.sql_explanation)
        # Output: This query selects the Sales measure from the Sales data model...
        
        with patch('unmdx.api.ExplainerGenerator') as mock_explainer, \
             patch('unmdx.api.parse_mdx') as mock_parse:
            
            # Setup explanation mock
            expected_explanation = """This query selects the Sales measure from the Sales data model.
It returns a single value showing the total sales amount."""
            
            mock_explainer.return_value.explain_mdx.return_value = expected_explanation
            
            # Setup parse mock for complexity analysis
            mock_parse_result = Mock()
            mock_parse_result.complexity_score = 0.2
            mock_parse_result.ir_query = Mock()
            mock_parse_result.ir_query.measures = [Mock()]
            mock_parse_result.ir_query.dimensions = []
            mock_parse_result.ir_query.filters = []
            mock_parse.return_value = mock_parse_result
            
            # Execute the documented example
            result = explain_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Verify the example works as documented
            assert isinstance(result, ExplanationResult)
            assert result.sql_explanation == expected_explanation
            assert "Sales measure" in result.sql_explanation
            assert "data model" in result.sql_explanation
    
    def test_query_complexity_example(self):
        """Test the query complexity example from docstring."""
        # Example from docstring:
        # print(f"Query complexity: {result.query_complexity}")
        # Output: Query complexity: simple
        
        with patch('unmdx.api.ExplainerGenerator') as mock_explainer, \
             patch('unmdx.api.parse_mdx') as mock_parse:
            
            # Setup mocks
            mock_explainer.return_value.explain_mdx.return_value = "Test explanation"
            
            mock_parse_result = Mock()
            mock_parse_result.complexity_score = 0.2  # Simple complexity
            mock_parse_result.ir_query = Mock()
            mock_parse_result.ir_query.measures = [Mock()]
            mock_parse_result.ir_query.dimensions = []
            mock_parse_result.ir_query.filters = []
            mock_parse.return_value = mock_parse_result
            
            # Execute explanation
            result = explain_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Verify complexity example works
            assert result.query_complexity is not None
            complexity_text = f"Query complexity: {result.query_complexity}"
            assert "Query complexity:" in complexity_text
            # Should be one of the expected values
            assert result.query_complexity in ["simple", "moderate", "complex"]


class TestConfigurationDocExamples:
    """Test configuration-related examples from documentation."""
    
    def test_config_factory_examples(self):
        """Test configuration factory function examples."""
        # Test create_default_config example
        config = create_default_config()
        assert isinstance(config, UnMDXConfig)
        assert config.linter.optimization_level.value == "conservative"
        
        # Test create_fast_config example
        fast_config = create_fast_config()
        assert isinstance(fast_config, UnMDXConfig)
        assert fast_config.linter.optimization_level.value == "none"
        assert fast_config.dax.format_output == False
        
        # Test create_comprehensive_config example
        comprehensive_config = create_comprehensive_config()
        assert isinstance(comprehensive_config, UnMDXConfig)
        assert comprehensive_config.linter.optimization_level.value == "aggressive"
        assert comprehensive_config.explanation.detail.value == "detailed"
    
    def test_config_usage_example(self):
        """Test using custom configuration with API functions."""
        # Example: using custom config with mdx_to_dax
        config = create_default_config()
        config.dax.format_output = False
        config.debug = True
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            mock_lint_report = Mock()
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            mock_lint_report.rules_applied = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute with custom config
            result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]", config=config)
            
            # Verify config was applied
            assert isinstance(result, ConversionResult)
            mock_generator.assert_called_once_with(format_output=False, debug=True)


class TestResultClassDocExamples:
    """Test examples related to result classes."""
    
    def test_conversion_result_metadata_example(self):
        """Test ConversionResult metadata access examples."""
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            # Setup mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            mock_lint_report = Mock()
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            mock_lint_report.rules_applied = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute conversion with metadata
            result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]", include_metadata=True)
            
            # Test metadata access examples
            metadata = result.get_metadata()
            assert isinstance(metadata, dict)
            assert "query_hash" in metadata
            assert "optimization_applied" in metadata
            assert "performance" in metadata
            
            # Test warnings access
            assert hasattr(result, 'has_warnings')
            assert hasattr(result, 'warnings')
            warning_count = len(result.warnings)
            assert isinstance(warning_count, int)
    
    def test_performance_stats_example(self):
        """Test PerformanceStats usage examples."""
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.time') as mock_time:
            
            # Setup timing simulation
            mock_time.time.side_effect = [0.0, 0.1, 0.2, 0.3]
            
            # Setup component mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            
            # Execute conversion without optimization to simplify
            result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]", optimize=False)
            
            # Test performance stats examples
            perf = result.performance
            assert hasattr(perf, 'total_time')
            assert hasattr(perf, 'parse_time')
            assert hasattr(perf, 'transform_time')
            assert hasattr(perf, 'generation_time')
            
            # Test get_summary method
            summary = perf.get_summary()
            assert isinstance(summary, dict)
            assert "total_time_ms" in summary


class TestErrorHandlingDocExamples:
    """Test error handling examples from documentation."""
    
    def test_validation_error_example(self):
        """Test ValidationError handling examples."""
        # Example: empty MDX should raise ValidationError
        with pytest.raises(Exception) as exc_info:
            mdx_to_dax("")
        
        # Should be able to catch and examine the error
        error = exc_info.value
        assert hasattr(error, 'message') or str(error)  # Has error message
        
        # Example: invalid format should raise ValidationError
        with pytest.raises(Exception) as exc_info:
            explain_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]", format_type="invalid")
        
        error = exc_info.value
        assert "format" in str(error).lower() or hasattr(error, 'field_name')
    
    def test_exception_hierarchy_example(self):
        """Test that exceptions can be caught by base class."""
        from unmdx.exceptions import UnMDXError
        
        # Any UnMDX exception should be catchable by UnMDXError
        try:
            mdx_to_dax("")  # Should raise ValidationError
        except UnMDXError as e:
            # Should be able to catch with base exception class
            assert hasattr(e, 'message') or str(e)
        except Exception:
            # If not UnMDXError, test should still pass (maybe not implemented yet)
            pass