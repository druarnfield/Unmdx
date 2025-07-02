"""
Integration tests for the public API.

These tests verify that the API functions work correctly in realistic scenarios
and properly integrate with all underlying components.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from unmdx import (
    mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx,
    UnMDXConfig, create_default_config, create_fast_config, create_comprehensive_config,
    ConversionResult, ParseResult, ExplanationResult, OptimizationResult,
    ParseError, ValidationError
)


class TestBasicApiIntegration:
    """Test basic API integration scenarios."""
    
    @pytest.mark.integration
    def test_simple_mdx_to_dax_workflow(self):
        """Test complete MDX to DAX conversion workflow."""
        mdx_query = """
        SELECT 
            [Measures].[Sales] ON COLUMNS,
            [Product].[Category].Members ON ROWS
        FROM [Sales]
        WHERE [Time].[Year].[2023]
        """
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            # Setup realistic mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = [Mock()]
            mock_ir.filters = [Mock()]
            mock_ir.calculations = []
            
            expected_dax = """
            EVALUATE
            SUMMARIZECOLUMNS(
                'Product'[Category],
                FILTER('Time', 'Time'[Year] = 2023),
                "Sales", [Measures].[Sales]
            )
            """
            
            mock_lint_report = Mock()
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            mock_lint_report.rules_applied = ["ParenthesesCleaner"]
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = expected_dax
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute conversion
            result = mdx_to_dax(mdx_query, include_metadata=True)
            
            # Verify result structure
            assert isinstance(result, ConversionResult)
            assert result.dax_query == expected_dax
            assert result.original_mdx == mdx_query
            assert result.optimization_applied == True
            assert result.ir_query == mock_ir
            assert result.performance.total_time > 0
            assert result.complexity_score is not None
            
            # Verify component integration
            mock_parser.return_value.parse.assert_called_once_with(mdx_query)
            mock_transformer.return_value.transform.assert_called_with(mock_tree)
            mock_generator.return_value.generate.assert_called_with(mock_ir)
            mock_linter.return_value.lint_tree.assert_called_once()
    
    @pytest.mark.integration
    def test_parse_mdx_workflow(self):
        """Test MDX parsing workflow."""
        mdx_query = "SELECT [Measures].[Revenue] ON 0 FROM [Finance]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer:
            
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            
            # Execute parsing
            result = parse_mdx(mdx_query, include_metadata=True)
            
            # Verify result
            assert isinstance(result, ParseResult)
            assert result.ir_query == mock_ir
            assert result.complexity_score is not None
            assert result.estimated_performance in ["fast", "moderate", "slow"]
            assert result.ast_node_count is not None
            assert result.ir_construct_count is not None
    
    @pytest.mark.integration
    def test_optimize_mdx_workflow(self):
        """Test MDX optimization workflow."""
        original_mdx = "SELECT (((([Measures].[Sales])))) ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
            mock_tree = Mock()
            mock_lint_report = Mock()
            mock_lint_report.rules_applied = ["ParenthesesCleaner", "DuplicateRemover"]
            mock_lint_report.actions = [
                Mock(description="Removed redundant parentheses", action_type=Mock(value="remove")),
                Mock(description="Cleaned duplicates", action_type=Mock(value="optimize"))
            ]
            mock_lint_report.warnings = ["Minor optimization applied"]
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Execute optimization
            result = optimize_mdx(original_mdx, optimization_level="aggressive")
            
            # Verify result
            assert isinstance(result, OptimizationResult)
            assert result.original_mdx == original_mdx
            assert result.optimization_level == "aggressive"
            assert "ParenthesesCleaner" in result.rules_applied
            assert "DuplicateRemover" in result.rules_applied
            assert len(result.changes_summary) == 2
            assert result.has_warnings() == True
    
    @pytest.mark.integration
    def test_explain_mdx_workflow(self):
        """Test MDX explanation workflow."""
        mdx_query = "SELECT [Measures].[Units] ON 0 FROM [Inventory]"
        
        with patch('unmdx.api.ExplainerGenerator') as mock_explainer, \
             patch('unmdx.api.parse_mdx') as mock_parse:
            
            # Setup explanation mock
            expected_explanation = """
            This query retrieves the Units measure from the Inventory data model.
            It returns a single value representing the total units in inventory.
            """
            
            mock_explainer.return_value.explain_mdx.return_value = expected_explanation
            
            # Setup parse mock for complexity analysis
            mock_parse_result = Mock()
            mock_parse_result.complexity_score = 0.2
            mock_parse_result.ir_query = Mock()
            mock_parse_result.ir_query.measures = [Mock()]
            mock_parse_result.ir_query.dimensions = []
            mock_parse_result.ir_query.filters = []
            mock_parse.return_value = mock_parse_result
            
            # Execute explanation
            result = explain_mdx(mdx_query, format_type="natural", detail_level="detailed")
            
            # Verify result
            assert isinstance(result, ExplanationResult)
            assert result.natural_explanation == expected_explanation
            assert result.format_used == "natural"
            assert result.detail_level == "detailed"
            assert result.query_complexity == "simple"  # Based on 0.2 complexity score
            assert len(result.key_insights) > 0


class TestConfigurationIntegration:
    """Test API integration with different configurations."""
    
    @pytest.mark.integration
    def test_conversion_with_custom_config(self):
        """Test conversion with custom configuration."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        # Create custom configuration
        config = create_default_config()
        config.debug = True
        config.dax.format_output = False
        config.dax.include_performance_hints = True
        config.linter.optimization_level.value = "aggressive"
        config.explanation.detail.value = "detailed"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
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
            
            # Execute with custom config
            result = mdx_to_dax(mdx_query, config=config)
            
            # Verify configuration was used
            mock_parser.assert_called_once()
            mock_generator.assert_called_once_with(format_output=False, debug=True)
            assert result.dax_query == mock_dax
    
    @pytest.mark.integration
    def test_fast_config_optimization(self):
        """Test that fast configuration actually optimizes for speed."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        config = create_fast_config()
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator:
            
            mock_tree = Mock()
            mock_ir = Mock()
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            
            # Execute with fast config (no optimization should be applied)
            result = mdx_to_dax(mdx_query, config=config, optimize=True)
            
            # Verify no optimization was applied (since level is NONE)
            assert result.optimization_applied == False
            # DAX generator should be called with format_output=False for speed
            mock_generator.assert_called_once_with(format_output=False, debug=False)
    
    @pytest.mark.integration 
    def test_comprehensive_config_features(self):
        """Test that comprehensive configuration enables all features."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        config = create_comprehensive_config()
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter:
            
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
            
            # Execute with comprehensive config
            result = mdx_to_dax(mdx_query, config=config, include_metadata=True)
            
            # Verify comprehensive features
            assert result.optimization_applied == True
            assert result.ir_query is not None
            assert result.original_mdx == mdx_query
            # Parser should be called with strict validation
            mock_parser.assert_called_once()
            # DAX generator should include all features
            mock_generator.assert_called_once_with(format_output=True, debug=False)


class TestErrorHandlingIntegration:
    """Test error handling across the API integration."""
    
    @pytest.mark.integration
    def test_parse_error_propagation(self):
        """Test that parse errors are properly propagated through the API."""
        invalid_mdx = "INVALID MDX SYNTAX HERE"
        
        with patch('unmdx.api.MDXParser') as mock_parser:
            # Simulate parse failure
            mock_parser.return_value.parse.side_effect = Exception("Unexpected token")
            
            with pytest.raises(ParseError) as exc_info:
                mdx_to_dax(invalid_mdx)
            
            assert "Unexpected token" in str(exc_info.value)
            assert exc_info.value.original_error is not None
    
    @pytest.mark.integration
    def test_validation_error_handling(self):
        """Test validation error handling in API functions."""
        # Test empty MDX
        with pytest.raises(ValidationError) as exc_info:
            mdx_to_dax("")
        assert "MDX text cannot be empty" in str(exc_info.value)
        
        # Test invalid format in explain_mdx
        with pytest.raises(ValidationError) as exc_info:
            explain_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]", format_type="invalid")
        assert "Invalid explanation format" in str(exc_info.value)
        
        # Test invalid optimization level
        with pytest.raises(ValidationError) as exc_info:
            optimize_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]", optimization_level="invalid")
        assert "Invalid optimization level" in str(exc_info.value)
    
    @pytest.mark.integration
    def test_configuration_validation_integration(self):
        """Test configuration validation in API functions."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        # Create invalid configuration
        config = create_default_config()
        config.cache_size_mb = -100  # Invalid value
        
        with pytest.raises(ValidationError) as exc_info:
            mdx_to_dax(mdx_query, config=config)
        
        assert "Configuration validation failed" in str(exc_info.value)


class TestWorkflowIntegration:
    """Test complex workflows that combine multiple API functions."""
    
    @pytest.mark.integration
    def test_parse_optimize_convert_workflow(self):
        """Test workflow: parse -> optimize -> convert."""
        original_mdx = "SELECT (([Measures].[Sales])) ON 0 FROM [Sales]"
        
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
            mock_lint_report.rules_applied = ["ParenthesesCleaner"]
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Step 1: Parse the MDX
            parse_result = parse_mdx(original_mdx)
            assert isinstance(parse_result, ParseResult)
            assert parse_result.complexity_score is not None
            
            # Step 2: Optimize the MDX
            optimize_result = optimize_mdx(original_mdx, optimization_level="moderate")
            assert isinstance(optimize_result, OptimizationResult)
            assert "ParenthesesCleaner" in optimize_result.rules_applied
            
            # Step 3: Convert optimized MDX to DAX
            convert_result = mdx_to_dax(optimize_result.optimized_mdx)
            assert isinstance(convert_result, ConversionResult)
            assert convert_result.dax_query == mock_dax
            assert convert_result.optimization_applied == True
    
    @pytest.mark.integration
    def test_convert_and_explain_workflow(self):
        """Test workflow: convert to DAX and generate explanation."""
        mdx_query = "SELECT [Measures].[Revenue] ON 0 FROM [Finance]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter, \
             patch('unmdx.api.ExplainerGenerator') as mock_explainer:
            
            # Setup mocks for conversion
            mock_tree = Mock()
            mock_ir = Mock()
            mock_ir.measures = [Mock()]
            mock_ir.dimensions = []
            mock_ir.filters = []
            mock_ir.calculations = []
            
            mock_dax = "EVALUATE SUMMARIZECOLUMNS('Finance'[All], \"Revenue\", [Measures].[Revenue])"
            mock_lint_report = Mock()
            mock_lint_report.actions = []
            mock_lint_report.warnings = []
            mock_lint_report.rules_applied = []
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            mock_linter.return_value.lint_tree.return_value = mock_lint_report
            
            # Setup explanation mock
            mock_explanation = "This query retrieves revenue data from the Finance model."
            mock_explainer.return_value.explain_mdx.return_value = mock_explanation
            
            # Step 1: Convert MDX to DAX
            convert_result = mdx_to_dax(mdx_query, include_metadata=True)
            assert isinstance(convert_result, ConversionResult)
            assert convert_result.dax_query == mock_dax
            
            # Step 2: Generate explanation of the original MDX
            explain_result = explain_mdx(mdx_query, include_dax=True)
            assert isinstance(explain_result, ExplanationResult)
            assert explain_result.sql_explanation == mock_explanation
            # Should include DAX for comparison
            assert explain_result.dax_query is not None
    
    @pytest.mark.integration
    def test_configuration_file_workflow(self):
        """Test workflow using configuration loaded from file."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        # Create temporary config file
        config_data = {
            "parser": {"strict_mode": True},
            "linter": {"optimization_level": "moderate"},
            "dax": {"format_output": False},
            "explanation": {"format": "markdown", "detail": "detailed"},
            "global": {"debug": True}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file_path = f.name
        
        try:
            # Load configuration from file
            from unmdx.config import load_config_from_file
            config = load_config_from_file(config_file_path)
            
            # Verify config was loaded correctly
            assert config.parser.strict_mode == True
            assert config.linter.optimization_level.value == "moderate"
            assert config.dax.format_output == False
            assert config.explanation.format.value == "markdown"
            assert config.explanation.detail.value == "detailed"
            assert config.debug == True
            
            # Use config with API
            with patch('unmdx.api.MDXParser') as mock_parser, \
                 patch('unmdx.api.MDXTransformer') as mock_transformer, \
                 patch('unmdx.api.DAXGenerator') as mock_generator, \
                 patch('unmdx.api.MDXLinter') as mock_linter:
                
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
                
                # Execute conversion with file-based config
                result = mdx_to_dax(mdx_query, config=config)
                
                # Verify config was applied
                mock_generator.assert_called_once_with(format_output=False, debug=True)
                assert result.dax_query == mock_dax
                
        finally:
            # Clean up temporary file
            Path(config_file_path).unlink()


class TestPerformanceIntegration:
    """Test performance-related aspects of API integration."""
    
    @pytest.mark.integration
    def test_performance_tracking_integration(self):
        """Test that performance tracking works across the API."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.MDXLinter') as mock_linter, \
             patch('unmdx.api.time') as mock_time:
            
            # Setup timing simulation
            time_calls = [0.0, 0.1, 0.15, 0.2, 0.25, 0.3]  # Simulated time progression
            mock_time.time.side_effect = time_calls
            
            # Setup component mocks
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
            
            # Execute conversion
            result = mdx_to_dax(mdx_query)
            
            # Verify performance tracking
            assert result.performance.total_time > 0
            assert result.performance.parse_time is not None
            assert result.performance.transform_time is not None
            assert result.performance.lint_time is not None
            assert result.performance.generation_time is not None
            
            # Verify timing makes sense (each stage should have recorded time)
            assert result.performance.parse_time > 0
            assert result.performance.transform_time > 0
            assert result.performance.generation_time > 0
    
    @pytest.mark.integration
    def test_memory_tracking_integration(self):
        """Test memory tracking in API functions."""
        mdx_query = "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        
        with patch('unmdx.api.MDXParser') as mock_parser, \
             patch('unmdx.api.MDXTransformer') as mock_transformer, \
             patch('unmdx.api.DAXGenerator') as mock_generator, \
             patch('unmdx.api.tracemalloc') as mock_tracemalloc:
            
            # Setup memory tracking mock
            mock_tracemalloc.is_tracing.return_value = True
            mock_tracemalloc.get_traced_memory.return_value = (2000000, 5000000)  # current, peak
            
            # Setup component mocks
            mock_tree = Mock()
            mock_ir = Mock()
            mock_dax = "EVALUATE SUMMARIZECOLUMNS(...)"
            
            mock_parser.return_value.parse.return_value = mock_tree
            mock_transformer.return_value.transform.return_value = mock_ir
            mock_generator.return_value.generate.return_value = mock_dax
            
            # Execute with metadata tracking
            result = mdx_to_dax(mdx_query, include_metadata=True, optimize=False)
            
            # Verify memory tracking
            assert result.performance.memory_peak_mb is not None
            assert result.performance.memory_delta_mb is not None
            assert result.performance.memory_peak_mb > 0
            
            # Verify tracemalloc was used
            mock_tracemalloc.start.assert_called_once()
            mock_tracemalloc.stop.assert_called_once()