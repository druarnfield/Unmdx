"""Base classes for MDX linting rules."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from lark import Tree

from .models import LintAction, LinterConfig
from .enums import OptimizationLevel


class LintRule(ABC):
    """Base class for all linting rules."""
    
    def __init__(self, config: LinterConfig):
        """Initialize the rule with configuration."""
        self.config = config
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the rule name for reporting."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what this rule does."""
        pass
    
    @property
    def optimization_level(self) -> OptimizationLevel:
        """Minimum optimization level required for this rule."""
        return OptimizationLevel.CONSERVATIVE
    
    @abstractmethod
    def can_apply(self, node: Tree) -> bool:
        """
        Check if this rule can be applied to the given node.
        
        Args:
            node: The AST node to check
            
        Returns:
            True if the rule can be applied, False otherwise
        """
        pass
    
    @abstractmethod
    def apply(self, node: Tree) -> Tuple[Tree, List[LintAction]]:
        """
        Apply the rule to the given node and return the modified tree.
        
        Args:
            node: The AST node to optimize
            
        Returns:
            Tuple of (modified_tree, list_of_actions_performed)
        """
        pass
    
    def should_apply(self) -> bool:
        """
        Check if this rule should be applied based on configuration.
        
        Returns:
            True if the rule should be applied, False otherwise
        """
        # Check if rule is explicitly disabled
        if not self.config.is_rule_enabled(self.name):
            return False
        
        # Check optimization level requirements
        required_level = self.optimization_level
        current_level = self.config.optimization_level
        
        level_order = {
            OptimizationLevel.CONSERVATIVE: 0,
            OptimizationLevel.MODERATE: 1,
            OptimizationLevel.AGGRESSIVE: 2
        }
        
        return level_order[current_level] >= level_order[required_level]
    
    def _create_action(
        self,
        action_type,
        description: str,
        node: Tree,
        original_text: str,
        optimized_text: str
    ) -> LintAction:
        """
        Helper method to create a LintAction.
        
        Args:
            action_type: Type of action performed
            description: Human-readable description
            node: The AST node that was modified
            original_text: Original text representation
            optimized_text: Optimized text representation
            
        Returns:
            LintAction object
        """
        return LintAction(
            action_type=action_type,
            description=description,
            node_type=node.data if hasattr(node, 'data') else str(type(node).__name__),
            original_text=original_text,
            optimized_text=optimized_text
        )
    
    def _get_node_text(self, node: Tree) -> str:
        """
        Get text representation of a node.
        
        Args:
            node: The AST node
            
        Returns:
            String representation of the node
        """
        # This is a simplified implementation
        # In practice, you might want to reconstruct the original MDX text
        return str(node)
    
    def _find_nodes(self, tree: Tree, node_type: str) -> List[Tree]:
        """
        Find all nodes of a specific type in the tree.
        
        Args:
            tree: The tree to search
            node_type: The node type to find
            
        Returns:
            List of matching nodes
        """
        nodes = []
        
        if isinstance(tree, Tree):
            if tree.data == node_type:
                nodes.append(tree)
            
            for child in tree.children:
                if isinstance(child, Tree):
                    nodes.extend(self._find_nodes(child, node_type))
        
        return nodes
    
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