"""Unit tests for MDXLinter class."""

import pytest
from datetime import datetime
from lark import Tree, Token

from unmdx.linter.mdx_linter import MDXLinter
from unmdx.linter.models import LinterConfig, LintReport
from unmdx.linter.enums import OptimizationLevel


class TestMDXLinter:
    """Test cases for MDXLinter."""
    
    @pytest.fixture
    def conservative_config(self):
        """Create conservative configuration."""
        return LinterConfig(optimization_level=OptimizationLevel.CONSERVATIVE)
    
    @pytest.fixture
    def moderate_config(self):
        """Create moderate configuration."""
        return LinterConfig(optimization_level=OptimizationLevel.MODERATE)
    
    @pytest.fixture
    def aggressive_config(self):
        """Create aggressive configuration."""
        return LinterConfig(optimization_level=OptimizationLevel.AGGRESSIVE)
    
    @pytest.fixture
    def sample_tree(self):
        """Create a sample MDX parse tree for testing."""
        # Simple tree structure for testing
        return Tree("query", [
            Tree("select_clause", [
                Tree("parenthesized_expression", [
                    Tree("identifier", [Token("IDENTIFIER", "Measures")])
                ])
            ])
        ])
    
    def test_initialization_default_config(self):
        """Test linter initialization with default configuration."""
        linter = MDXLinter()
        
        assert linter.config is not None
        assert linter.config.optimization_level == OptimizationLevel.CONSERVATIVE
        assert isinstance(linter.rules, list)
    
    def test_initialization_custom_config(self, moderate_config):
        """Test linter initialization with custom configuration."""
        linter = MDXLinter(moderate_config)
        
        assert linter.config == moderate_config
        assert linter.config.optimization_level == OptimizationLevel.MODERATE
    
    def test_load_rules_conservative(self, conservative_config):
        """Test that conservative rules are loaded properly."""
        linter = MDXLinter(conservative_config)
        
        # Should load conservative-level rules
        rule_names = linter.get_available_rules()
        assert "parentheses_cleaner" in rule_names
        assert "crossjoin_optimizer" in rule_names
        assert "duplicate_remover" in rule_names
    
    def test_load_rules_moderate(self, moderate_config):
        """Test that moderate rules are loaded properly."""
        linter = MDXLinter(moderate_config)
        
        # Should load conservative + moderate rules
        rule_names = linter.get_available_rules()
        assert "parentheses_cleaner" in rule_names
        assert "crossjoin_optimizer" in rule_names
        assert "duplicate_remover" in rule_names
        assert "function_optimizer" in rule_names
    
    def test_lint_empty_tree(self, conservative_config):
        """Test linting with an empty tree."""
        linter = MDXLinter(conservative_config)
        empty_tree = Tree("query", [])
        
        result_tree, report = linter.lint(empty_tree)
        
        assert isinstance(result_tree, Tree)
        assert isinstance(report, LintReport)
        assert report.optimization_level == OptimizationLevel.CONSERVATIVE
        assert len(report.actions) == 0
    
    def test_lint_with_source_mdx(self, conservative_config, sample_tree):
        """Test linting with source MDX text."""
        linter = MDXLinter(conservative_config)
        source_mdx = "SELECT ([Measures].[Sales]) ON COLUMNS FROM [Sales]"
        
        result_tree, report = linter.lint(sample_tree, source_mdx)
        
        assert report.original_size == len(source_mdx)
        assert report.optimized_size >= 0
    
    def test_lint_report_timing(self, conservative_config, sample_tree):
        """Test that lint report includes timing information."""
        linter = MDXLinter(conservative_config)
        
        result_tree, report = linter.lint(sample_tree)
        
        assert report.start_time is not None
        assert report.end_time is not None
        assert report.duration_ms is not None
        assert report.duration_ms >= 0
    
    def test_lint_with_disabled_rules(self):
        """Test linting with specific rules disabled."""
        config = LinterConfig(
            optimization_level=OptimizationLevel.MODERATE,
            disabled_rules=["function_optimizer"]
        )
        linter = MDXLinter(config)
        
        rule_names = linter.get_available_rules()
        assert "function_optimizer" not in rule_names
        assert "parentheses_cleaner" in rule_names
    
    def test_lint_timeout_protection(self):
        """Test that linting respects timeout settings."""
        config = LinterConfig(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            max_processing_time_ms=1  # Very short timeout
        )
        linter = MDXLinter(config)
        
        # Create a complex tree that might take time to process
        complex_tree = Tree("query", [
            Tree("select_clause", []) for _ in range(100)
        ])
        
        result_tree, report = linter.lint(complex_tree)
        
        # Should complete without hanging
        assert isinstance(result_tree, Tree)
        assert isinstance(report, LintReport)
    
    def test_get_rule_descriptions(self, conservative_config):
        """Test getting rule descriptions."""
        linter = MDXLinter(conservative_config)
        
        descriptions = linter.get_rule_descriptions()
        
        assert isinstance(descriptions, dict)
        assert len(descriptions) > 0
        
        for rule_name, description in descriptions.items():
            assert isinstance(rule_name, str)
            assert isinstance(description, str)
            assert len(description) > 0
    
    def test_tree_copying(self, conservative_config, sample_tree):
        """Test that original tree is not modified during linting."""
        linter = MDXLinter(conservative_config)
        
        original_str = str(sample_tree)
        result_tree, report = linter.lint(sample_tree)
        
        # Original tree should be unchanged
        assert str(sample_tree) == original_str
        # Result might be different
        assert isinstance(result_tree, Tree)
    
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        config = LinterConfig(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            validate_after_optimizing=True,
            skip_on_validation_error=True
        )
        linter = MDXLinter(config)
        
        # This should not raise an exception even if validation fails
        result_tree, report = linter.lint(Tree("invalid", []))
        
        assert isinstance(result_tree, Tree)
        assert isinstance(report, LintReport)
    
    def test_error_recovery(self, conservative_config):
        """Test that linter recovers from rule errors."""
        linter = MDXLinter(conservative_config)
        
        # Create a tree that might cause rule errors
        problematic_tree = Tree("query", [None, "invalid_child"])
        
        # Should not raise exception, should return original tree
        result_tree, report = linter.lint(problematic_tree)
        
        assert isinstance(result_tree, Tree)
        assert isinstance(report, LintReport)
        # May have errors recorded
        # assert len(report.errors) >= 0  # Could be 0 if no errors actually occur


class TestLintReport:
    """Test cases for LintReport functionality."""
    
    def test_report_initialization(self):
        """Test LintReport initialization."""
        start_time = datetime.now()
        report = LintReport(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            start_time=start_time
        )
        
        assert report.optimization_level == OptimizationLevel.CONSERVATIVE
        assert report.start_time == start_time
        assert report.end_time is None
        assert len(report.actions) == 0
        assert len(report.rules_applied) == 0
        assert len(report.errors) == 0
        assert len(report.warnings) == 0
    
    def test_report_size_reduction_calculation(self):
        """Test size reduction percentage calculation."""
        report = LintReport(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            start_time=datetime.now(),
            original_size=1000,
            optimized_size=800
        )
        
        assert report.size_reduction == 20.0
    
    def test_report_size_reduction_no_change(self):
        """Test size reduction when no optimization occurred."""
        report = LintReport(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            start_time=datetime.now(),
            original_size=1000,
            optimized_size=1000
        )
        
        assert report.size_reduction == 0.0
    
    def test_report_size_reduction_zero_original(self):
        """Test size reduction with zero original size."""
        report = LintReport(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            start_time=datetime.now(),
            original_size=0,
            optimized_size=0
        )
        
        assert report.size_reduction == 0.0
    
    def test_report_duration_calculation(self):
        """Test duration calculation."""
        start_time = datetime.now()
        report = LintReport(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            start_time=start_time
        )
        
        # Initially no duration
        assert report.duration_ms is None
        
        # After finishing
        report.finish()
        assert report.duration_ms is not None
        assert report.duration_ms >= 0
    
    def test_report_summary_generation(self):
        """Test summary string generation."""
        report = LintReport(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            start_time=datetime.now(),
            original_size=1000,
            optimized_size=800
        )
        report.finish()
        
        summary = report.summary()
        
        assert "MDX Linting Report" in summary
        assert "conservative" in summary
        assert "1,000" in summary  # Original size with comma
        assert "800" in summary    # Optimized size
        assert "20.0%" in summary  # Size reduction
    
    def test_report_with_actions(self):
        """Test report with actions recorded."""
        from unmdx.linter.models import LintAction
        from unmdx.linter.enums import LintActionType
        
        report = LintReport(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            start_time=datetime.now()
        )
        
        action = LintAction(
            action_type=LintActionType.REMOVE_PARENTHESES,
            description="Test action",
            node_type="test_node",
            original_text="original",
            optimized_text="optimized"
        )
        
        report.add_action(action)
        report.add_rule("test_rule")
        
        assert len(report.actions) == 1
        assert "test_rule" in report.rules_applied
        
        summary = report.summary()
        assert "Actions Performed: 1" in summary
        assert "test_rule" in summary


class TestLinterConfig:
    """Test cases for LinterConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LinterConfig()
        
        assert config.optimization_level == OptimizationLevel.CONSERVATIVE
        assert config.remove_redundant_parentheses == True
        assert config.optimize_crossjoins == True
        assert config.remove_duplicates == True
        assert config.normalize_member_references == True
        assert config.optimize_calculated_members == False  # Conservative
        assert config.simplify_function_calls == False      # Conservative
    
    def test_moderate_config_auto_settings(self):
        """Test that moderate level automatically enables appropriate rules."""
        config = LinterConfig(optimization_level=OptimizationLevel.MODERATE)
        
        assert config.optimize_calculated_members == True
        assert config.simplify_function_calls == True
    
    def test_aggressive_config_auto_settings(self):
        """Test that aggressive level automatically enables all rules."""
        config = LinterConfig(optimization_level=OptimizationLevel.AGGRESSIVE)
        
        assert config.optimize_calculated_members == True
        assert config.simplify_function_calls == True
        assert config.max_crossjoin_depth == 5  # Increased for aggressive
    
    def test_rule_enabled_check(self):
        """Test rule enabled/disabled checking."""
        config = LinterConfig(disabled_rules=["test_rule"])
        
        assert config.is_rule_enabled("other_rule") == True
        assert config.is_rule_enabled("test_rule") == False
    
    def test_optimization_level_checks(self):
        """Test optimization level helper methods."""
        conservative_config = LinterConfig(optimization_level=OptimizationLevel.CONSERVATIVE)
        moderate_config = LinterConfig(optimization_level=OptimizationLevel.MODERATE)
        aggressive_config = LinterConfig(optimization_level=OptimizationLevel.AGGRESSIVE)
        
        # Conservative
        assert conservative_config.should_apply_moderate_rules() == False
        assert conservative_config.should_apply_aggressive_rules() == False
        
        # Moderate
        assert moderate_config.should_apply_moderate_rules() == True
        assert moderate_config.should_apply_aggressive_rules() == False
        
        # Aggressive
        assert aggressive_config.should_apply_moderate_rules() == True
        assert aggressive_config.should_apply_aggressive_rules() == True