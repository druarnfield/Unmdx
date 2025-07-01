"""Main MDX linter implementation."""

import time
from datetime import datetime
from typing import List, Tuple, Type, Optional
from lark import Tree

from ..utils.logging import get_logger
from .base import LintRule
from .models import LintReport, LinterConfig
from .enums import OptimizationLevel

logger = get_logger(__name__)


class MDXLinter:
    """
    Main linter class that orchestrates optimization rules.
    
    The linter applies a series of optimization rules to clean up
    MDX queries, particularly targeting patterns commonly found in
    Necto/Oracle Essbase output.
    """
    
    def __init__(self, config: Optional[LinterConfig] = None):
        """
        Initialize the linter with configuration.
        
        Args:
            config: Linter configuration. If None, uses default conservative config.
        """
        self.config = config or LinterConfig()
        self.logger = get_logger(__name__)
        
        # Initialize rules
        self.rules: List[LintRule] = []
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load and initialize all available linting rules."""
        # Import rule classes here to avoid circular imports
        from .rules.parentheses_cleaner import ParenthesesCleaner
        from .rules.crossjoin_optimizer import CrossJoinOptimizer
        from .rules.function_optimizer import FunctionOptimizer
        from .rules.duplicate_remover import DuplicateRemover
        
        # Create rule instances
        rule_classes = [
            ParenthesesCleaner,
            CrossJoinOptimizer, 
            FunctionOptimizer,
            DuplicateRemover,
        ]
        
        for rule_class in rule_classes:
            try:
                rule = rule_class(self.config)
                if rule.should_apply():
                    self.rules.append(rule)
                    self.logger.debug(f"Loaded rule: {rule.name}")
                else:
                    self.logger.debug(f"Skipped rule (disabled or wrong level): {rule.name}")
            except Exception as e:
                self.logger.error(f"Failed to load rule {rule_class.__name__}: {e}")
    
    def lint(self, tree: Tree, source_mdx: Optional[str] = None) -> Tuple[Tree, LintReport]:
        """
        Apply all applicable rules to the parse tree.
        
        Args:
            tree: The parsed MDX tree from Lark
            source_mdx: Original MDX source text for reporting
            
        Returns:
            Tuple of (optimized_tree, lint_report)
        """
        start_time = datetime.now()
        
        # Create report
        report = LintReport(
            optimization_level=self.config.optimization_level,
            start_time=start_time,
            original_size=len(source_mdx) if source_mdx else 0
        )
        
        # Start with a copy of the original tree
        current_tree = self._copy_tree(tree)
        
        try:
            # Apply rules in order
            for rule in self.rules:
                if self._should_process_rule(rule, report):
                    try:
                        rule_start = time.time()
                        
                        # Apply rule if it can be applied
                        if rule.can_apply(current_tree):
                            modified_tree, actions = rule.apply(current_tree)
                            
                            # Update tree and report
                            current_tree = modified_tree
                            for action in actions:
                                report.add_action(action)
                            
                            report.add_rule(rule.name)
                            
                            rule_duration = (time.time() - rule_start) * 1000
                            self.logger.debug(f"Applied rule {rule.name} in {rule_duration:.2f}ms")
                        
                        # Check for timeout
                        if self._is_timeout(start_time):
                            report.add_warning(f"Linting timeout after {self.config.max_processing_time_ms}ms")
                            break
                            
                    except Exception as e:
                        error_msg = f"Error applying rule {rule.name}: {str(e)}"
                        report.add_error(error_msg)
                        self.logger.error(error_msg)
                        
                        if self.config.skip_on_validation_error:
                            continue
                        else:
                            raise
            
            # Validate final result if configured
            if self.config.validate_after_optimizing:
                try:
                    self._validate_tree(current_tree)
                except Exception as e:
                    report.add_error(f"Post-optimization validation failed: {str(e)}")
                    if self.config.skip_on_validation_error:
                        # Return original tree if validation fails
                        current_tree = tree
                    else:
                        raise
            
            # Finalize report
            optimized_text = self._tree_to_text(current_tree)
            report.optimized_size = len(optimized_text)
            report.finish()
            
            self.logger.info(
                f"Linting completed: {len(report.actions)} actions, "
                f"{report.size_reduction:.1f}% size reduction"
            )
            
            return current_tree, report
            
        except Exception as e:
            report.add_error(f"Linting failed: {str(e)}")
            report.finish()
            self.logger.error(f"Linting failed: {e}")
            return tree, report  # Return original tree on error
    
    def _should_process_rule(self, rule: LintRule, report: LintReport) -> bool:
        """
        Check if a rule should be processed.
        
        Args:
            rule: The rule to check
            report: Current lint report
            
        Returns:
            True if the rule should be processed
        """
        # Check if rule is enabled
        if not rule.should_apply():
            return False
        
        # Could add additional logic here, such as:
        # - Skip rules if too many errors have occurred
        # - Skip rules based on previous rule outcomes
        # - Skip rules if processing time is getting too long
        
        return True
    
    def _is_timeout(self, start_time: datetime) -> bool:
        """
        Check if processing has exceeded the timeout.
        
        Args:
            start_time: When processing started
            
        Returns:
            True if timeout has been exceeded
        """
        if self.config.max_processing_time_ms <= 0:
            return False
        
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        return elapsed_ms > self.config.max_processing_time_ms
    
    def _validate_tree(self, tree: Tree) -> None:
        """
        Validate that the tree is still a valid MDX parse tree.
        
        Args:
            tree: The tree to validate
            
        Raises:
            ValueError: If the tree is invalid
        """
        # Basic validation - ensure tree structure is intact
        if not isinstance(tree, Tree):
            raise ValueError("Root node is not a Tree")
        
        # Could add more sophisticated validation here:
        # - Check that required nodes are present
        # - Validate MDX grammar rules
        # - Check for circular references
        # etc.
    
    def _copy_tree(self, tree: Tree) -> Tree:
        """
        Create a deep copy of a tree.
        
        Args:
            tree: The tree to copy
            
        Returns:
            Deep copy of the tree
        """
        if isinstance(tree, Tree):
            return Tree(tree.data, [self._copy_tree(child) for child in tree.children])
        else:
            return tree
    
    def _tree_to_text(self, tree: Tree) -> str:
        """
        Convert a tree back to text representation.
        
        Args:
            tree: The tree to convert
            
        Returns:
            Text representation of the tree
        """
        # This is a simplified implementation
        # In practice, you might want to use a proper tree-to-text converter
        # that reconstructs valid MDX syntax
        return str(tree)
    
    def get_available_rules(self) -> List[str]:
        """
        Get list of available rule names.
        
        Returns:
            List of rule names
        """
        return [rule.name for rule in self.rules]
    
    def get_rule_descriptions(self) -> dict:
        """
        Get descriptions of all available rules.
        
        Returns:
            Dictionary mapping rule names to descriptions
        """
        return {rule.name: rule.description for rule in self.rules}