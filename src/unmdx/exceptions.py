"""
Comprehensive exception hierarchy for UnMDX package.

This module defines all custom exceptions used throughout the UnMDX package,
providing a clear hierarchy for different types of errors that can occur
during MDX parsing, transformation, DAX generation, and explanation.
"""

from typing import Any, Dict, List, Optional


class UnMDXError(Exception):
    """
    Base exception class for all UnMDX-related errors.
    
    All custom exceptions in the UnMDX package should inherit from this class.
    This allows users to catch all UnMDX-specific errors with a single except clause.
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error message
            details: Additional details about the error (line numbers, context, etc.)
            suggestions: List of suggested solutions or next steps
        """
        self.message = message
        self.details = details or {}
        self.suggestions = suggestions or []
        super().__init__(message)


class ParseError(UnMDXError):
    """
    Exception raised when MDX parsing fails.
    
    This includes syntax errors, malformed queries, unsupported constructs,
    and other issues encountered during the parsing phase.
    """
    
    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[str] = None,
        original_error: Optional[Exception] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize parsing error.
        
        Args:
            message: Human-readable error message
            line: Line number where error occurred
            column: Column number where error occurred
            context: Surrounding text context
            original_error: Original exception that caused this error
            suggestions: List of suggested fixes
        """
        details = {
            "line": line,
            "column": column, 
            "context": context,
            "original_error": str(original_error) if original_error else None
        }
        
        # Build enhanced error message
        error_parts = [message]
        if line is not None and column is not None:
            error_parts.append(f"at line {line}, column {column}")
        if context:
            error_parts.append(f"near '{context}'")
            
        enhanced_message = ": ".join(error_parts)
        
        super().__init__(enhanced_message, details, suggestions)
        self.line = line
        self.column = column
        self.context = context
        self.original_error = original_error


class TransformError(UnMDXError):
    """
    Exception raised during MDX to IR transformation.
    
    This includes issues with converting parsed MDX structures into the
    intermediate representation, such as unsupported constructs, invalid
    references, or logical inconsistencies.
    """
    
    def __init__(
        self,
        message: str,
        node_type: Optional[str] = None,
        context: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize transformation error.
        
        Args:
            message: Human-readable error message
            node_type: Type of AST node that caused the error
            context: Context where transformation failed
            suggestions: List of suggested fixes
        """
        details = {
            "node_type": node_type,
            "context": context
        }
        
        enhanced_message = f"{message}"
        if context:
            enhanced_message += f" in {context}"
            
        super().__init__(enhanced_message, details, suggestions)
        self.node_type = node_type
        self.context = context


class GenerationError(UnMDXError):
    """
    Exception raised during DAX generation.
    
    This includes issues with converting IR structures into valid DAX queries,
    such as unsupported IR constructs, invalid DAX syntax generation, or
    formatting problems.
    """
    
    def __init__(
        self,
        message: str,
        ir_construct: Optional[str] = None,
        context: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize DAX generation error.
        
        Args:
            message: Human-readable error message
            ir_construct: Type of IR construct that caused the error
            context: Context where generation failed
            suggestions: List of suggested fixes
        """
        details = {
            "ir_construct": ir_construct,
            "context": context
        }
        
        enhanced_message = f"{message}"
        if context:
            enhanced_message += f" in {context}"
            
        super().__init__(enhanced_message, details, suggestions)
        self.ir_construct = ir_construct
        self.context = context


class LintError(UnMDXError):
    """
    Exception raised during MDX linting and optimization.
    
    This includes issues with applying linting rules, optimization failures,
    or cases where optimization would break query semantics.
    """
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        optimization_level: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize linting error.
        
        Args:
            message: Human-readable error message
            rule_name: Name of the linting rule that failed
            optimization_level: Optimization level being applied
            suggestions: List of suggested fixes
        """
        details = {
            "rule_name": rule_name,
            "optimization_level": optimization_level
        }
        
        enhanced_message = f"{message}"
        if rule_name:
            enhanced_message += f" (rule: {rule_name})"
            
        super().__init__(enhanced_message, details, suggestions)
        self.rule_name = rule_name
        self.optimization_level = optimization_level


class ExplanationError(UnMDXError):
    """
    Exception raised during explanation generation.
    
    This includes issues with generating human-readable explanations,
    formatting problems, or unsupported explanation formats.
    """
    
    def __init__(
        self,
        message: str,
        format_type: Optional[str] = None,
        context: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize explanation error.
        
        Args:
            message: Human-readable error message
            format_type: Output format that caused the error
            context: Context where explanation failed
            suggestions: List of suggested fixes
        """
        details = {
            "format_type": format_type,
            "context": context
        }
        
        enhanced_message = f"{message}"
        if format_type:
            enhanced_message += f" for format '{format_type}'"
            
        super().__init__(enhanced_message, details, suggestions)
        self.format_type = format_type
        self.context = context


class ConfigurationError(UnMDXError):
    """
    Exception raised for configuration-related issues.
    
    This includes invalid configuration values, missing required settings,
    conflicting options, or unsupported configuration combinations.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        valid_values: Optional[List[Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Human-readable error message
            config_key: Configuration key that caused the error
            config_value: Invalid configuration value
            valid_values: List of valid values for this configuration
            suggestions: List of suggested fixes
        """
        details = {
            "config_key": config_key,
            "config_value": config_value,
            "valid_values": valid_values
        }
        
        enhanced_message = f"{message}"
        if config_key:
            enhanced_message += f" for key '{config_key}'"
        if config_value is not None:
            enhanced_message += f" (value: {config_value})"
            
        super().__init__(enhanced_message, details, suggestions)
        self.config_key = config_key
        self.config_value = config_value
        self.valid_values = valid_values


class ValidationError(UnMDXError):
    """
    Exception raised for validation failures.
    
    This includes input validation errors, data type mismatches,
    constraint violations, or other validation-related issues.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        constraints: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Human-readable error message
            field_name: Name of the field that failed validation
            field_value: Value that failed validation
            constraints: Validation constraints that were violated
            suggestions: List of suggested fixes
        """
        details = {
            "field_name": field_name,
            "field_value": field_value,
            "constraints": constraints or {}
        }
        
        enhanced_message = f"{message}"
        if field_name:
            enhanced_message += f" for field '{field_name}'"
            
        super().__init__(enhanced_message, details, suggestions)
        self.field_name = field_name
        self.field_value = field_value
        self.constraints = constraints or {}


# Convenience function for common error scenarios
def create_parse_error_from_lark(lark_error: Exception, suggestions: Optional[List[str]] = None) -> ParseError:
    """
    Create a ParseError from a Lark parsing exception.
    
    Args:
        lark_error: The original Lark exception
        suggestions: Optional list of suggested fixes
        
    Returns:
        ParseError with appropriate details extracted from the Lark error
    """
    message = str(lark_error)
    line = None
    column = None
    context = None
    
    # Extract line/column info if available
    if hasattr(lark_error, 'line'):
        line = lark_error.line
    if hasattr(lark_error, 'column'):
        column = lark_error.column
    if hasattr(lark_error, 'get_context'):
        try:
            context = lark_error.get_context(lark_error.text)
        except (AttributeError, TypeError):
            pass
    
    return ParseError(
        message=message,
        line=line,
        column=column,
        context=context,
        original_error=lark_error,
        suggestions=suggestions
    )