"""
API consistency and performance tests.

This module contains tests that verify the API design is consistent,
follows best practices, and performs well under various conditions.
"""

import inspect
import time
from typing import get_type_hints
from unittest.mock import patch, Mock

import pytest

from unmdx import (
    mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx,
    UnMDXConfig, ConversionResult, ParseResult, ExplanationResult, OptimizationResult,
    UnMDXError, ParseError, TransformError, GenerationError, ValidationError
)
from unmdx.api import (
    _extract_dax_functions, _extract_dax_tables, _calculate_complexity_score,
    _estimate_performance, _estimate_query_complexity
)


class TestApiConsistency:
    """Test API consistency across all functions."""
    
    def test_all_api_functions_have_type_hints(self):
        """Test that all public API functions have complete type hints."""
        api_functions = [mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx]
        
        for func in api_functions:
            type_hints = get_type_hints(func)
            
            # Should have return type hint
            assert 'return' in type_hints, f"{func.__name__} missing return type hint"
            
            # Get function signature
            sig = inspect.signature(func)
            
            # All parameters should have type hints (except 'self' if present)
            for param_name, param in sig.parameters.items():
                if param_name != 'self':
                    assert param_name in type_hints, f"{func.__name__} parameter '{param_name}' missing type hint"
    
    def test_all_api_functions_have_docstrings(self):
        """Test that all public API functions have comprehensive docstrings."""
        api_functions = [mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx]
        
        for func in api_functions:
            assert func.__doc__ is not None, f"{func.__name__} missing docstring"
            
            docstring = func.__doc__
            
            # Should contain key sections
            assert "Args:" in docstring, f"{func.__name__} docstring missing Args section"
            assert "Returns:" in docstring, f"{func.__name__} docstring missing Returns section"
            assert "Raises:" in docstring, f"{func.__name__} docstring missing Raises section"
            assert "Example:" in docstring, f"{func.__name__} docstring missing Example section"
    
    def test_consistent_parameter_naming(self):
        """Test that parameter names are consistent across API functions."""
        # Get signatures of all API functions
        signatures = {
            'mdx_to_dax': inspect.signature(mdx_to_dax),
            'parse_mdx': inspect.signature(parse_mdx),
            'optimize_mdx': inspect.signature(optimize_mdx),
            'explain_mdx': inspect.signature(explain_mdx)
        }
        
        # All functions should have mdx_text as first parameter
        for func_name, sig in signatures.items():
            params = list(sig.parameters.keys())
            assert params[0] == 'mdx_text', f"{func_name} should have 'mdx_text' as first parameter"
        
        # Functions that accept config should name it 'config'
        config_functions = ['mdx_to_dax', 'parse_mdx', 'optimize_mdx', 'explain_mdx']
        for func_name in config_functions:
            if func_name == 'optimize_mdx':
                continue  # optimize_mdx takes config in different position
            sig = signatures[func_name]
            if 'config' in sig.parameters:
                param = sig.parameters['config']
                # Should be Optional[UnMDXConfig]
                assert param.default is None, f"{func_name} config parameter should default to None"
    
    def test_consistent_result_types(self):
        """Test that all API functions return consistent result types."""
        # Each function should return a specific result type
        expected_returns = {
            mdx_to_dax: ConversionResult,
            parse_mdx: ParseResult,
            optimize_mdx: OptimizationResult,
            explain_mdx: ExplanationResult
        }
        
        for func, expected_type in expected_returns.items():
            type_hints = get_type_hints(func)
            return_type = type_hints.get('return')
            
            # Should return the expected result type
            assert return_type == expected_type, f"{func.__name__} should return {expected_type.__name__}"
    
    def test_consistent_error_handling(self):
        """Test that all API functions handle errors consistently."""
        api_functions = [mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx]
        
        for func in api_functions:
            # All should validate empty input
            with pytest.raises((ValidationError, ValueError, TypeError)) as exc_info:
                func("")
            
            # Error should be informative
            error_msg = str(exc_info.value)
            assert len(error_msg) > 0, f"{func.__name__} should provide informative error message"
    
    def test_all_result_classes_have_performance_stats(self):
        """Test that all result classes include performance statistics."""
        result_classes = [ConversionResult, ParseResult, ExplanationResult, OptimizationResult]
        
        for result_class in result_classes:
            # Create instance with minimal required args
            if result_class == ConversionResult:
                instance = result_class(dax_query="test")
            elif result_class == ParseResult:
                instance = result_class(ir_query=Mock(), query_hash="test")
            elif result_class == ExplanationResult:
                instance = result_class()
            elif result_class == OptimizationResult:
                instance = result_class(optimized_mdx="test", original_mdx="test")
            
            # Should have performance attribute
            assert hasattr(instance, 'performance'), f"{result_class.__name__} missing performance attribute"
            
            # Should have warning-related methods
            assert hasattr(instance, 'add_warning'), f"{result_class.__name__} missing add_warning method"
            assert hasattr(instance, 'has_warnings'), f"{result_class.__name__} missing has_warnings method"
            assert hasattr(instance, 'warnings'), f"{result_class.__name__} missing warnings attribute"


class TestApiPerformance:
    """Test API performance characteristics."""
    
    def test_helper_functions_performance(self):
        """Test that helper functions perform well."""
        # Test DAX function extraction performance
        large_dax = "EVALUATE SUMMARIZECOLUMNS(" + "SUM('Table'[Column]), " * 100 + ")"
        
        start_time = time.time()
        functions = _extract_dax_functions(large_dax)
        extraction_time = time.time() - start_time
        
        # Should complete quickly (within 100ms)
        assert extraction_time < 0.1, "DAX function extraction too slow"
        assert isinstance(functions, list)
        assert "EVALUATE" in functions
        assert "SUMMARIZECOLUMNS" in functions
        assert "SUM" in functions
    
    def test_dax_table_extraction_performance(self):
        """Test DAX table extraction performance."""
        large_dax = "SUMMARIZECOLUMNS(" + "'Table'[Column], " * 50 + ")"
        
        start_time = time.time()
        tables = _extract_dax_tables(large_dax)
        extraction_time = time.time() - start_time
        
        # Should complete quickly
        assert extraction_time < 0.1, "DAX table extraction too slow"
        assert isinstance(tables, list)
        assert "Table" in tables
    
    def test_complexity_calculation_performance(self):
        """Test complexity score calculation performance."""
        # Create mock IR with many constructs
        mock_ir = Mock()
        mock_ir.measures = [Mock() for _ in range(50)]
        mock_ir.dimensions = [Mock() for _ in range(20)]
        mock_ir.filters = [Mock() for _ in range(30)]
        mock_ir.calculations = [Mock() for _ in range(10)]
        
        start_time = time.time()
        score = _calculate_complexity_score(mock_ir)
        calc_time = time.time() - start_time
        
        # Should be very fast
        assert calc_time < 0.01, "Complexity calculation too slow"
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
    
    def test_performance_estimation_consistency(self):
        """Test that performance estimation is consistent."""
        test_scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        for score in test_scores:
            performance = _estimate_performance(score)
            complexity = _estimate_query_complexity(score)
            
            # Should return valid values
            assert performance in ["fast", "moderate", "slow"]
            assert complexity in ["simple", "moderate", "complex"]
            
            # Should be consistent (low scores = fast/simple)
            if score < 0.3:
                assert performance == "fast"
                assert complexity == "simple"
            elif score > 0.7:
                assert performance == "slow"
                assert complexity == "complex"
    
    @pytest.mark.performance
    def test_api_function_response_times(self):
        """Test that API functions respond within reasonable time limits."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter, \
             patch('unmdx.api.ExplainerGenerator') as mock_explainer:
            
            # Setup fast-responding mocks
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
            mock_explainer.return_value.explain_mdx.return_value = "Test explanation"
            
            # Test each API function response time
            functions_to_test = [
                ('mdx_to_dax', lambda: mdx_to_dax(mdx_query)),
                ('parse_mdx', lambda: parse_mdx(mdx_query)),
                ('optimize_mdx', lambda: optimize_mdx(mdx_query)),
                ('explain_mdx', lambda: explain_mdx(mdx_query))
            ]
            
            for func_name, func_call in functions_to_test:
                start_time = time.time()
                result = func_call()
                response_time = time.time() - start_time
                
                # Should respond quickly (within 1 second for mocked calls)
                assert response_time < 1.0, f"{func_name} response time too slow: {response_time:.3f}s"
                
                # Should return appropriate result type
                assert result is not None
                assert hasattr(result, 'performance')


class TestApiUsability:
    """Test API usability and developer experience."""
    
    def test_import_convenience(self):
        """Test that common imports work as expected."""
        # Test that main functions can be imported directly
        from unmdx import mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx
        
        # Test that config classes can be imported
        from unmdx import UnMDXConfig, create_default_config
        
        # Test that result classes can be imported
        from unmdx import ConversionResult, ParseResult
        
        # Test that exceptions can be imported
        from unmdx import UnMDXError, ValidationError
        
        # All imports should succeed without error
        assert callable(mdx_to_dax)
        assert callable(create_default_config)
        assert issubclass(ConversionResult, object)
        assert issubclass(UnMDXError, Exception)
    
    def test_default_behavior_sensible(self):
        """Test that default behavior is sensible for most users."""
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
            
            # Test default behavior
            result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Defaults should be reasonable
            assert result.optimization_applied == True  # Should optimize by default
            assert result.dax_query == mock_dax
            assert result.original_mdx is None  # Don't include by default (save memory)
            
            # Should use formatted output by default
            mock_generator.assert_called_once_with(format_output=True, debug=False)
    
    def test_progressive_disclosure(self):
        """Test that API supports progressive disclosure (simple to advanced)."""
        # Level 1: Simplest possible usage
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
            
            # Simple usage - just conversion
            simple_result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            assert simple_result.dax_query is not None
            
            # Intermediate usage - with options
            intermediate_result = mdx_to_dax(
                "SELECT [Measures].[Sales] ON 0 FROM [Sales]",
                optimize=False,
                include_metadata=True
            )
            assert intermediate_result.original_mdx is not None
            assert intermediate_result.optimization_applied == False
            
            # Advanced usage - with custom config
            from unmdx import create_comprehensive_config
            config = create_comprehensive_config()
            advanced_result = mdx_to_dax(
                "SELECT [Measures].[Sales] ON 0 FROM [Sales]",
                config=config,
                include_metadata=True
            )
            assert advanced_result.ir_query is not None
    
    def test_error_messages_helpful(self):
        """Test that error messages are helpful for developers."""
        # Test validation errors have helpful messages
        try:
            mdx_to_dax("")
        except Exception as e:
            error_msg = str(e)
            # Should mention what's wrong and how to fix it
            assert "empty" in error_msg.lower() or "cannot be" in error_msg.lower()
        
        try:
            explain_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]", format_type="invalid")
        except Exception as e:
            error_msg = str(e)
            # Should mention valid options
            assert "format" in error_msg.lower()
            # Should ideally suggest valid values (if ValidationError is used properly)
    
    def test_result_objects_informative(self):
        """Test that result objects provide useful information."""
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
            
            # Get result
            result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
            
            # Should provide useful information
            assert hasattr(result, 'dax_query')
            assert hasattr(result, 'performance')
            assert hasattr(result, 'complexity_score')
            assert hasattr(result, 'estimated_performance')
            assert hasattr(result, 'optimization_applied')
            
            # Performance info should be accessible
            assert result.performance.total_time >= 0
            
            # Should be able to get metadata
            if hasattr(result, 'get_metadata'):
                metadata = result.get_metadata()
                assert isinstance(metadata, dict)
                assert len(metadata) > 0