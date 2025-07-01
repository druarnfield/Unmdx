"""Enums for the MDX linter module."""

from enum import Enum


class OptimizationLevel(Enum):
    """Optimization levels for the MDX linter."""
    
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class LintActionType(Enum):
    """Types of linting actions that can be performed."""
    
    REMOVE_PARENTHESES = "remove_parentheses"
    SIMPLIFY_CROSSJOIN = "simplify_crossjoin"
    REMOVE_DUPLICATE = "remove_duplicate"
    OPTIMIZE_FUNCTION = "optimize_function"
    NORMALIZE_MEMBER = "normalize_member"
    CLEAN_EXPRESSION = "clean_expression"
    FLATTEN_SET = "flatten_set"