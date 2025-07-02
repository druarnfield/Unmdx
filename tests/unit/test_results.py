"""
Unit tests for result classes.

Tests all result classes and their functionality.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from unmdx.results import (
    PerformanceStats, Warning, ParseResult, ConversionResult,
    ExplanationResult, OptimizationResult
)


class TestPerformanceStats:
    """Test the PerformanceStats class."""
    
    def test_default_initialization(self):
        """Test default performance stats initialization."""
        stats = PerformanceStats()
        
        assert stats.total_time == 0.0
        assert stats.parse_time is None
        assert stats.transform_time is None
        assert stats.lint_time is None
        assert stats.generation_time is None
        assert stats.explanation_time is None
        assert stats.memory_peak_mb is None
        assert stats.memory_delta_mb is None
        assert stats.input_size_chars is None
        assert stats.output_size_chars is None
        assert stats.ast_nodes_processed is None
        assert stats.ir_constructs_created is None
    
    def test_add_timing(self):
        """Test adding timing information."""
        stats = PerformanceStats()
        
        stats.add_timing("parse", 0.15)
        stats.add_timing("transform", 0.08)
        stats.add_timing("generation", 0.12)
        
        assert stats.parse_time == 0.15
        assert stats.transform_time == 0.08
        assert stats.generation_time == 0.12
        assert stats.total_time == 0.35
    
    def test_get_summary(self):
        """Test getting performance summary."""
        stats = PerformanceStats()
        stats.add_timing("parse", 0.123)
        stats.add_timing("transform", 0.078)
        stats.memory_peak_mb = 25.5
        stats.input_size_chars = 1000
        stats.output_size_chars = 800
        
        summary = stats.get_summary()
        
        assert summary["total_time_ms"] == 201.0  # (0.123 + 0.078) * 1000
        assert summary["parse_time_ms"] == 123.0
        assert summary["transform_time_ms"] == 78.0
        assert summary["memory_peak_mb"] == 25.5
        assert summary["input_size_chars"] == 1000
        assert summary["output_size_chars"] == 800
        assert summary["generation_time_ms"] is None


class TestWarning:
    """Test the Warning class."""
    
    def test_basic_initialization(self):
        """Test basic warning initialization."""
        warning = Warning("This is a warning", "general")
        
        assert warning.message == "This is a warning"
        assert warning.category == "general"
        assert warning.severity == "warning"
        assert warning.location is None
        assert warning.suggestion is None
    
    def test_initialization_with_all_fields(self):
        """Test warning initialization with all fields."""
        location = {"line": 5, "column": 10, "context": "SELECT"}
        warning = Warning(
            "Deprecated syntax",
            "syntax",
            severity="deprecation",
            location=location,
            suggestion="Use modern syntax instead"
        )
        
        assert warning.message == "Deprecated syntax"
        assert warning.category == "syntax"
        assert warning.severity == "deprecation"
        assert warning.location == location
        assert warning.suggestion == "Use modern syntax instead"
    
    def test_string_representation(self):
        """Test warning string representation."""
        # Warning without location or suggestion
        warning1 = Warning("Simple warning", "general")
        assert str(warning1) == "Warning: Simple warning"
        
        # Warning with location
        location = {"line": 5}
        warning2 = Warning("Warning with location", "general", location=location)
        assert str(warning2) == "Warning: Warning with location (line 5)"
        
        # Warning with suggestion
        warning3 = Warning("Warning with suggestion", "general", suggestion="Try this")
        assert str(warning3) == "Warning: Warning with suggestion Suggestion: Try this"
        
        # Warning with different severity
        warning4 = Warning("Info message", "general", severity="info")
        assert str(warning4) == "Info: Info message"


class TestParseResult:
    """Test the ParseResult class."""
    
    def test_basic_initialization(self):
        """Test basic parse result initialization."""
        mock_ir = Mock()
        result = ParseResult(ir_query=mock_ir, query_hash="abc123")
        
        assert result.ir_query == mock_ir
        assert result.query_hash == "abc123"
        assert isinstance(result.parsed_at, datetime)
        assert result.parser_version == "1.0.0"
        assert result.warnings == []
        assert result.complexity_score is None
        assert result.estimated_performance is None
        assert isinstance(result.performance, PerformanceStats)
        assert result.ast_node_count is None
        assert result.ir_construct_count is None
    
    def test_add_warning(self):
        """Test adding warnings to parse result."""
        mock_ir = Mock()
        result = ParseResult(ir_query=mock_ir, query_hash="abc123")
        
        result.add_warning("First warning", "syntax")
        result.add_warning("Second warning", "performance", severity="info")
        
        assert len(result.warnings) == 2
        assert result.warnings[0].message == "First warning"
        assert result.warnings[0].category == "syntax"
        assert result.warnings[1].message == "Second warning"
        assert result.warnings[1].category == "performance"
        assert result.warnings[1].severity == "info"
    
    def test_has_warnings(self):
        """Test checking if result has warnings."""
        mock_ir = Mock()
        result = ParseResult(ir_query=mock_ir, query_hash="abc123")
        
        assert result.has_warnings() == False
        
        result.add_warning("Warning message", "general")
        assert result.has_warnings() == True
    
    def test_get_warning_summary(self):
        """Test getting warning summary by category."""
        mock_ir = Mock()
        result = ParseResult(ir_query=mock_ir, query_hash="abc123")
        
        result.add_warning("Syntax warning 1", "syntax")
        result.add_warning("Syntax warning 2", "syntax")
        result.add_warning("Performance warning", "performance")
        
        summary = result.get_warning_summary()
        
        assert summary["syntax"] == 2
        assert summary["performance"] == 1
        assert summary.get("other") is None


class TestConversionResult:
    """Test the ConversionResult class."""
    
    def test_basic_initialization(self):
        """Test basic conversion result initialization."""
        result = ConversionResult(dax_query="EVALUATE SUMMARIZECOLUMNS(...)")
        
        assert result.dax_query == "EVALUATE SUMMARIZECOLUMNS(...)"
        assert result.ir_query is None
        assert result.query_hash == ""
        assert isinstance(result.converted_at, datetime)
        assert result.converter_version == "1.0.0"
        assert result.original_mdx is None
        assert result.optimization_applied == False
        assert result.optimization_level is None
        assert result.warnings == []
        assert result.complexity_score is None
        assert result.estimated_performance is None
        assert result.semantic_equivalence_score is None
        assert isinstance(result.performance, PerformanceStats)
        assert result.dax_functions_used == []
        assert result.dax_tables_referenced == []
        assert result.dax_measures_created == 0
    
    def test_initialization_with_all_fields(self):
        """Test conversion result initialization with all fields."""
        mock_ir = Mock()
        result = ConversionResult(
            dax_query="EVALUATE SUMMARIZECOLUMNS(...)",
            ir_query=mock_ir,
            query_hash="def456",
            original_mdx="SELECT [Measures].[Sales] ON 0 FROM [Sales]",
            optimization_applied=True,
            optimization_level="moderate"
        )
        
        assert result.ir_query == mock_ir
        assert result.query_hash == "def456"
        assert result.original_mdx == "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        assert result.optimization_applied == True
        assert result.optimization_level == "moderate"
    
    def test_get_metadata(self):
        """Test getting comprehensive metadata."""
        result = ConversionResult(dax_query="EVALUATE SUMMARIZECOLUMNS(...)")
        result.query_hash = "abc123"
        result.optimization_applied = True
        result.optimization_level = "moderate"
        result.complexity_score = 0.5
        result.estimated_performance = "moderate"
        result.semantic_equivalence_score = 0.95
        result.dax_functions_used = ["EVALUATE", "SUMMARIZECOLUMNS"]
        result.dax_tables_referenced = ["Sales", "Products"]
        result.dax_measures_created = 2
        result.add_warning("Test warning", "general")
        result.performance.add_timing("parse", 0.1)
        
        metadata = result.get_metadata()
        
        assert metadata["query_hash"] == "abc123"
        assert metadata["optimization_applied"] == True
        assert metadata["optimization_level"] == "moderate"
        assert metadata["complexity_score"] == 0.5
        assert metadata["estimated_performance"] == "moderate"
        assert metadata["semantic_equivalence_score"] == 0.95
        assert metadata["dax_functions_used"] == ["EVALUATE", "SUMMARIZECOLUMNS"]
        assert metadata["dax_tables_referenced"] == ["Sales", "Products"]
        assert metadata["dax_measures_created"] == 2
        assert metadata["warning_count"] == 1
        assert "performance" in metadata
        assert metadata["performance"]["total_time_ms"] == 100.0


class TestExplanationResult:
    """Test the ExplanationResult class."""
    
    def test_basic_initialization(self):
        """Test basic explanation result initialization."""
        result = ExplanationResult()
        
        assert result.sql_explanation is None
        assert result.natural_explanation is None
        assert result.json_explanation is None
        assert result.markdown_explanation is None
        assert result.dax_query is None
        assert result.query_hash == ""
        assert isinstance(result.explained_at, datetime)
        assert result.explainer_version == "1.0.0"
        assert result.format_used == "sql"
        assert result.detail_level == "standard"
        assert result.include_dax_comparison == False
        assert result.include_metadata == False
        assert result.warnings == []
        assert result.explanation_quality_score is None
        assert result.readability_score is None
        assert isinstance(result.performance, PerformanceStats)
        assert result.query_complexity is None
        assert result.key_insights == []
        assert result.potential_issues == []
    
    def test_get_explanation_auto_format(self):
        """Test getting explanation in auto format."""
        result = ExplanationResult()
        result.format_used = "sql"
        result.sql_explanation = "This is SQL explanation"
        
        explanation = result.get_explanation("auto")
        assert explanation == "This is SQL explanation"
    
    def test_get_explanation_specific_format(self):
        """Test getting explanation in specific format."""
        result = ExplanationResult()
        result.sql_explanation = "SQL explanation"
        result.natural_explanation = "Natural explanation"
        result.markdown_explanation = "# Markdown explanation"
        result.json_explanation = {"explanation": "JSON explanation"}
        
        assert result.get_explanation("sql") == "SQL explanation"
        assert result.get_explanation("natural") == "Natural explanation"
        assert result.get_explanation("markdown") == "# Markdown explanation"
        assert "JSON explanation" in result.get_explanation("json")
    
    def test_get_explanation_unavailable_format(self):
        """Test getting explanation for unavailable format."""
        result = ExplanationResult()
        result.sql_explanation = "SQL explanation"
        
        assert result.get_explanation("natural") is None
        assert result.get_explanation("invalid") is None
    
    def test_get_available_formats(self):
        """Test getting list of available explanation formats."""
        result = ExplanationResult()
        
        # No formats available initially
        assert result.get_available_formats() == []
        
        # Add some explanations
        result.sql_explanation = "SQL explanation"
        result.markdown_explanation = "Markdown explanation"
        
        available = result.get_available_formats()
        assert "sql" in available
        assert "markdown" in available
        assert "natural" not in available
        assert "json" not in available
        assert len(available) == 2


class TestOptimizationResult:
    """Test the OptimizationResult class."""
    
    def test_basic_initialization(self):
        """Test basic optimization result initialization."""
        result = OptimizationResult(
            optimized_mdx="SELECT [Measures].[Sales] ON 0 FROM [Sales]",
            original_mdx="SELECT (([Measures].[Sales])) ON 0 FROM [Sales]"
        )
        
        assert result.optimized_mdx == "SELECT [Measures].[Sales] ON 0 FROM [Sales]"
        assert result.original_mdx == "SELECT (([Measures].[Sales])) ON 0 FROM [Sales]"
        assert result.optimization_level == "moderate"
        assert result.rules_applied == []
        assert result.query_hash == ""
        assert isinstance(result.optimized_at, datetime)
        assert result.optimizer_version == "1.0.0"
        assert result.size_reduction_percent is None
        assert result.complexity_reduction_score is None
        assert result.estimated_performance_improvement is None
        assert result.warnings == []
        assert result.semantic_equivalence_verified == False
        assert isinstance(result.performance, PerformanceStats)
        assert result.changes_summary == []
        assert result.removed_patterns == []
    
    def test_get_optimization_summary(self):
        """Test getting optimization summary."""
        result = OptimizationResult(
            optimized_mdx="SELECT [Measures].[Sales] ON 0 FROM [Sales]",
            original_mdx="SELECT (([Measures].[Sales])) ON 0 FROM [Sales]"
        )
        result.optimization_level = "aggressive"
        result.rules_applied = ["ParenthesesCleaner", "DuplicateRemover"]
        result.size_reduction_percent = 15.5
        result.complexity_reduction_score = 0.3
        result.estimated_performance_improvement = "moderate"
        result.semantic_equivalence_verified = True
        result.changes_summary = ["Removed redundant parentheses", "Cleaned up duplicates"]
        result.add_warning("Minor issue", "optimization")
        result.performance.add_timing("lint", 0.05)
        
        summary = result.get_optimization_summary()
        
        assert summary["optimization_level"] == "aggressive"
        assert summary["rules_applied"] == ["ParenthesesCleaner", "DuplicateRemover"]
        assert summary["size_reduction_percent"] == 15.5
        assert summary["complexity_reduction_score"] == 0.3
        assert summary["estimated_performance_improvement"] == "moderate"
        assert summary["semantic_equivalence_verified"] == True
        assert summary["changes_count"] == 2
        assert summary["warning_count"] == 1
        assert "performance" in summary
        assert summary["performance"]["total_time_ms"] == 50.0


class TestResultClassesCommonFunctionality:
    """Test common functionality across result classes."""
    
    def test_all_result_classes_have_warnings(self):
        """Test that all result classes support warnings."""
        mock_ir = Mock()
        result_classes = [
            (ParseResult, {"ir_query": mock_ir, "query_hash": "test"}),
            (ConversionResult, {"dax_query": "EVALUATE"}),
            (ExplanationResult, {}),
            (OptimizationResult, {"optimized_mdx": "SELECT", "original_mdx": "SELECT"})
        ]
        
        for result_class, kwargs in result_classes:
            result = result_class(**kwargs)
            
            # All should have warning methods
            assert hasattr(result, 'add_warning')
            assert hasattr(result, 'has_warnings')
            assert hasattr(result, 'warnings')
            
            # Test warning functionality
            assert result.has_warnings() == False
            result.add_warning("Test warning", "test")
            assert result.has_warnings() == True
            assert len(result.warnings) == 1
            assert result.warnings[0].message == "Test warning"
    
    def test_all_result_classes_have_performance_stats(self):
        """Test that all result classes have performance statistics."""
        mock_ir = Mock()
        result_classes = [
            (ParseResult, {"ir_query": mock_ir, "query_hash": "test"}),
            (ConversionResult, {"dax_query": "EVALUATE"}),
            (ExplanationResult, {}),
            (OptimizationResult, {"optimized_mdx": "SELECT", "original_mdx": "SELECT"})
        ]
        
        for result_class, kwargs in result_classes:
            result = result_class(**kwargs)
            
            assert hasattr(result, 'performance')
            assert isinstance(result.performance, PerformanceStats)
    
    def test_datetime_fields_are_populated(self):
        """Test that datetime fields are automatically populated."""
        mock_ir = Mock()
        result_classes = [
            (ParseResult, {"ir_query": mock_ir, "query_hash": "test"}, "parsed_at"),
            (ConversionResult, {"dax_query": "EVALUATE"}, "converted_at"),
            (ExplanationResult, {}, "explained_at"),
            (OptimizationResult, {"optimized_mdx": "SELECT", "original_mdx": "SELECT"}, "optimized_at")
        ]
        
        for result_class, kwargs, datetime_field in result_classes:
            result = result_class(**kwargs)
            
            assert hasattr(result, datetime_field)
            datetime_value = getattr(result, datetime_field)
            assert isinstance(datetime_value, datetime)
            # Should be recent (within last minute)
            assert (datetime.now() - datetime_value).total_seconds() < 60