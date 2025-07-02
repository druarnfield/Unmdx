"""
Unit tests for the exception hierarchy.

Tests all custom exception classes and their functionality.
"""

import pytest

from unmdx.exceptions import (
    UnMDXError, ParseError, TransformError, GenerationError,
    LintError, ExplanationError, ConfigurationError, ValidationError,
    create_parse_error_from_lark
)


class TestUnMDXError:
    """Test the base UnMDXError class."""
    
    def test_basic_initialization(self):
        """Test basic error initialization."""
        error = UnMDXError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}
        assert error.suggestions == []
    
    def test_initialization_with_details(self):
        """Test error initialization with details."""
        details = {"line": 5, "column": 10}
        suggestions = ["Check syntax", "Try again"]
        
        error = UnMDXError("Test error", details=details, suggestions=suggestions)
        
        assert error.details == details
        assert error.suggestions == suggestions
    
    def test_inheritance_from_exception(self):
        """Test that UnMDXError inherits from Exception properly."""
        error = UnMDXError("Test error")
        
        assert isinstance(error, Exception)
        assert isinstance(error, UnMDXError)


class TestParseError:
    """Test the ParseError class."""
    
    def test_basic_initialization(self):
        """Test basic parse error initialization."""
        error = ParseError("Syntax error in MDX")
        
        assert "Syntax error in MDX" in str(error)
        assert error.line is None
        assert error.column is None
        assert error.context is None
        assert error.original_error is None
    
    def test_initialization_with_location(self):
        """Test parse error with line and column information."""
        error = ParseError("Syntax error", line=10, column=5)
        
        error_str = str(error)
        assert "Syntax error" in error_str
        assert "line 10" in error_str
        assert "column 5" in error_str
        
        assert error.line == 10
        assert error.column == 5
    
    def test_initialization_with_context(self):
        """Test parse error with context information."""
        error = ParseError("Unexpected token", line=3, column=8, context="SELECT [Invalid")
        
        error_str = str(error)
        assert "Unexpected token" in error_str
        assert "line 3" in error_str
        assert "column 8" in error_str
        assert "SELECT [Invalid" in error_str
    
    def test_initialization_with_original_error(self):
        """Test parse error with original exception."""
        original = ValueError("Original error")
        error = ParseError("Parse failed", original_error=original)
        
        assert error.original_error == original
        assert "Original error" in str(error.details["original_error"])
    
    def test_initialization_with_suggestions(self):
        """Test parse error with suggestions."""
        suggestions = ["Check bracket matching", "Verify function names"]
        error = ParseError("Parse failed", suggestions=suggestions)
        
        assert error.suggestions == suggestions
    
    def test_details_population(self):
        """Test that details are properly populated."""
        error = ParseError(
            "Error message",
            line=5,
            column=10,
            context="SELECT",
            original_error=Exception("Original")
        )
        
        assert error.details["line"] == 5
        assert error.details["column"] == 10
        assert error.details["context"] == "SELECT"
        assert "Original" in error.details["original_error"]


class TestTransformError:
    """Test the TransformError class."""
    
    def test_basic_initialization(self):
        """Test basic transform error initialization."""
        error = TransformError("Failed to transform node")
        
        assert "Failed to transform node" in str(error)
        assert error.node_type is None
        assert error.context is None
    
    def test_initialization_with_node_type(self):
        """Test transform error with node type."""
        error = TransformError("Invalid node", node_type="with_clause")
        
        assert error.node_type == "with_clause"
        assert error.details["node_type"] == "with_clause"
    
    def test_initialization_with_context(self):
        """Test transform error with context."""
        error = TransformError("Transform failed", context="measure processing")
        
        error_str = str(error)
        assert "Transform failed" in error_str
        assert "measure processing" in error_str
        assert error.context == "measure processing"


class TestGenerationError:
    """Test the GenerationError class."""
    
    def test_basic_initialization(self):
        """Test basic generation error initialization."""
        error = GenerationError("DAX generation failed")
        
        assert "DAX generation failed" in str(error)
        assert error.ir_construct is None
        assert error.context is None
    
    def test_initialization_with_ir_construct(self):
        """Test generation error with IR construct."""
        error = GenerationError("Unsupported construct", ir_construct="calculated_member")
        
        assert error.ir_construct == "calculated_member"
        assert error.details["ir_construct"] == "calculated_member"
    
    def test_initialization_with_context(self):
        """Test generation error with context."""
        error = GenerationError("Generation failed", context="expression conversion")
        
        error_str = str(error)
        assert "Generation failed" in error_str
        assert "expression conversion" in error_str


class TestLintError:
    """Test the LintError class."""
    
    def test_basic_initialization(self):
        """Test basic lint error initialization."""
        error = LintError("Linting failed")
        
        assert "Linting failed" in str(error)
        assert error.rule_name is None
        assert error.optimization_level is None
    
    def test_initialization_with_rule_name(self):
        """Test lint error with rule name."""
        error = LintError("Rule failed", rule_name="ParenthesesCleaner")
        
        error_str = str(error)
        assert "Rule failed" in error_str
        assert "ParenthesesCleaner" in error_str
        assert error.rule_name == "ParenthesesCleaner"
    
    def test_initialization_with_optimization_level(self):
        """Test lint error with optimization level."""
        error = LintError("Optimization failed", optimization_level="aggressive")
        
        assert error.optimization_level == "aggressive"
        assert error.details["optimization_level"] == "aggressive"


class TestExplanationError:
    """Test the ExplanationError class."""
    
    def test_basic_initialization(self):
        """Test basic explanation error initialization."""
        error = ExplanationError("Explanation generation failed")
        
        assert "Explanation generation failed" in str(error)
        assert error.format_type is None
        assert error.context is None
    
    def test_initialization_with_format_type(self):
        """Test explanation error with format type."""
        error = ExplanationError("Format not supported", format_type="json")
        
        error_str = str(error)
        assert "Format not supported" in error_str
        assert "json" in error_str
        assert error.format_type == "json"


class TestConfigurationError:
    """Test the ConfigurationError class."""
    
    def test_basic_initialization(self):
        """Test basic configuration error initialization."""
        error = ConfigurationError("Invalid configuration")
        
        assert "Invalid configuration" in str(error)
        assert error.config_key is None
        assert error.config_value is None
        assert error.valid_values is None
    
    def test_initialization_with_config_details(self):
        """Test configuration error with detailed information."""
        error = ConfigurationError(
            "Invalid value",
            config_key="optimization_level",
            config_value="invalid",
            valid_values=["conservative", "moderate", "aggressive"]
        )
        
        error_str = str(error)
        assert "Invalid value" in error_str
        assert "optimization_level" in error_str
        assert "invalid" in error_str
        
        assert error.config_key == "optimization_level"
        assert error.config_value == "invalid"
        assert error.valid_values == ["conservative", "moderate", "aggressive"]


class TestValidationError:
    """Test the ValidationError class."""
    
    def test_basic_initialization(self):
        """Test basic validation error initialization."""
        error = ValidationError("Validation failed")
        
        assert "Validation failed" in str(error)
        assert error.field_name is None
        assert error.field_value is None
        assert error.constraints == {}
    
    def test_initialization_with_field_details(self):
        """Test validation error with field information."""
        constraints = {"min_length": 1, "max_length": 100}
        error = ValidationError(
            "Field too long",
            field_name="mdx_text",
            field_value="very long text...",
            constraints=constraints
        )
        
        error_str = str(error)
        assert "Field too long" in error_str
        assert "mdx_text" in error_str
        
        assert error.field_name == "mdx_text"
        assert error.field_value == "very long text..."
        assert error.constraints == constraints


class TestCreateParseErrorFromLark:
    """Test the utility function for creating ParseError from Lark exceptions."""
    
    def test_basic_lark_error_conversion(self):
        """Test converting basic Lark error to ParseError."""
        lark_error = Exception("Unexpected token")
        
        parse_error = create_parse_error_from_lark(lark_error)
        
        assert isinstance(parse_error, ParseError)
        assert "Unexpected token" in str(parse_error)
        assert parse_error.original_error == lark_error
    
    def test_lark_error_with_line_column(self):
        """Test converting Lark error with line/column info."""
        # Create mock Lark error with line/column attributes
        class MockLarkError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.line = 5
                self.column = 10
        
        lark_error = MockLarkError("Parse failed")
        parse_error = create_parse_error_from_lark(lark_error)
        
        assert parse_error.line == 5
        assert parse_error.column == 10
    
    def test_lark_error_with_context(self):
        """Test converting Lark error with context information."""
        # Create mock Lark error with context method
        class MockLarkError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.text = "SELECT [Invalid syntax here"
            
            def get_context(self, text):
                return "Invalid syntax here"
        
        lark_error = MockLarkError("Syntax error")
        parse_error = create_parse_error_from_lark(lark_error)
        
        assert parse_error.context == "Invalid syntax here"
    
    def test_lark_error_with_suggestions(self):
        """Test converting Lark error with custom suggestions."""
        lark_error = Exception("Parse failed")
        suggestions = ["Check syntax", "Verify brackets"]
        
        parse_error = create_parse_error_from_lark(lark_error, suggestions=suggestions)
        
        assert parse_error.suggestions == suggestions
    
    def test_lark_error_context_extraction_failure(self):
        """Test handling when context extraction fails."""
        # Create mock Lark error where get_context raises exception
        class MockLarkError(Exception):
            def get_context(self, text):
                raise AttributeError("No context available")
        
        lark_error = MockLarkError("Parse failed")
        parse_error = create_parse_error_from_lark(lark_error)
        
        # Should not raise exception, context should be None
        assert parse_error.context is None
        assert parse_error.original_error == lark_error


class TestExceptionHierarchy:
    """Test the overall exception hierarchy structure."""
    
    def test_all_exceptions_inherit_from_unmdx_error(self):
        """Test that all custom exceptions inherit from UnMDXError."""
        exception_classes = [
            ParseError, TransformError, GenerationError,
            LintError, ExplanationError, ConfigurationError, ValidationError
        ]
        
        for exc_class in exception_classes:
            instance = exc_class("Test message")
            assert isinstance(instance, UnMDXError)
            assert isinstance(instance, Exception)
    
    def test_exception_can_be_caught_by_base_class(self):
        """Test that specific exceptions can be caught by base UnMDXError."""
        errors = [
            ParseError("Parse failed"),
            TransformError("Transform failed"),
            GenerationError("Generation failed"),
            LintError("Lint failed"),
            ExplanationError("Explanation failed"),
            ConfigurationError("Config failed"),
            ValidationError("Validation failed")
        ]
        
        for error in errors:
            try:
                raise error
            except UnMDXError as e:
                assert isinstance(e, type(error))
            except Exception:
                pytest.fail(f"Exception {type(error)} not caught by UnMDXError")
    
    def test_exception_details_and_suggestions_preserved(self):
        """Test that all exceptions preserve details and suggestions."""
        exception_classes = [
            ParseError, TransformError, GenerationError,
            LintError, ExplanationError, ConfigurationError, ValidationError
        ]
        
        details = {"test": "value"}
        suggestions = ["suggestion1", "suggestion2"]
        
        for exc_class in exception_classes:
            if exc_class == ParseError:
                # ParseError has different constructor signature
                error = exc_class("Test", suggestions=suggestions)
            else:
                error = exc_class("Test", suggestions=suggestions)
            
            assert hasattr(error, 'suggestions')
            assert hasattr(error, 'details')
            assert error.suggestions == suggestions