"""Rule for removing redundant parentheses from MDX expressions."""

from typing import List, Tuple
from lark import Tree, Token

from ..base import LintRule
from ..models import LintAction
from ..enums import LintActionType, OptimizationLevel


class ParenthesesCleaner(LintRule):
    """
    Removes redundant parentheses from MDX expressions.
    
    This rule targets the excessive parentheses commonly generated
    by Necto/Oracle Essbase, such as:
    - Single expressions wrapped in unnecessary parentheses
    - Nested parentheses with no operators between them
    - Parentheses around simple identifiers or literals
    """
    
    @property
    def name(self) -> str:
        """Return the rule name."""
        return "parentheses_cleaner"
    
    @property
    def description(self) -> str:
        """Return rule description."""
        return "Removes redundant parentheses from expressions while preserving operator precedence"
    
    @property
    def optimization_level(self) -> OptimizationLevel:
        """This rule applies at conservative level."""
        return OptimizationLevel.CONSERVATIVE
    
    def can_apply(self, node: Tree) -> bool:
        """
        Check if this rule can be applied to the node.
        
        Args:
            node: The AST node to check
            
        Returns:
            True if redundant parentheses are found
        """
        # Look for parenthesized expressions
        parenthesized_nodes = self._find_nodes(node, "parenthesized_expression")
        
        for paren_node in parenthesized_nodes:
            if self._is_redundant_parentheses(paren_node):
                return True
        
        return False
    
    def apply(self, node: Tree) -> Tuple[Tree, List[LintAction]]:
        """
        Apply the rule to remove redundant parentheses.
        
        Args:
            node: The AST node to optimize
            
        Returns:
            Tuple of (modified_tree, list_of_actions)
        """
        actions = []
        modified_tree = self._copy_tree(node)
        
        # Process all parenthesized expressions
        modified_tree = self._remove_redundant_parentheses_recursive(
            modified_tree, actions
        )
        
        return modified_tree, actions
    
    def _is_redundant_parentheses(self, paren_node: Tree) -> bool:
        """
        Check if parentheses around an expression are redundant.
        
        Args:
            paren_node: A parenthesized expression node
            
        Returns:
            True if the parentheses are redundant
        """
        if not isinstance(paren_node, Tree) or paren_node.data != "parenthesized_expression":
            return False
        
        # If there's only one child, parentheses might be redundant
        if len(paren_node.children) == 1:
            child = paren_node.children[0]
            
            # Redundant if child is:
            # - A simple identifier
            # - A literal value
            # - Another parenthesized expression (nested parentheses)
            # - A function call (already has its own grouping)
            
            if isinstance(child, Tree):
                if child.data in [
                    "identifier", 
                    "bracketed_identifier",
                    "numeric_literal", 
                    "string_literal",
                    "parenthesized_expression",
                    "function_call"
                ]:
                    return True
            elif isinstance(child, Token):
                # Simple token doesn't need parentheses
                return True
        
        # Check for nested identical parentheses
        if len(paren_node.children) == 1:
            child = paren_node.children[0]
            if isinstance(child, Tree) and child.data == "parenthesized_expression":
                return True
        
        return False
    
    def _remove_redundant_parentheses_recursive(
        self, 
        node: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Recursively remove redundant parentheses from the tree.
        
        Args:
            node: Current node being processed
            actions: List to accumulate actions performed
            
        Returns:
            Modified tree with redundant parentheses removed
        """
        if not isinstance(node, Tree):
            return node
        
        # Process children first (bottom-up approach)
        new_children = []
        for child in node.children:
            if isinstance(child, Tree):
                new_child = self._remove_redundant_parentheses_recursive(child, actions)
                new_children.append(new_child)
            else:
                new_children.append(child)
        
        # Create new node with processed children
        result_node = Tree(node.data, new_children)
        
        # Check if this node itself has redundant parentheses
        if node.data == "parenthesized_expression" and self._is_redundant_parentheses(result_node):
            # Remove the parentheses by returning the inner expression
            if len(result_node.children) == 1:
                inner_expression = result_node.children[0]
                
                # Create action to record this optimization
                original_text = self._get_node_text(result_node)
                optimized_text = self._get_node_text(inner_expression)
                
                action = self._create_action(
                    action_type=LintActionType.REMOVE_PARENTHESES,
                    description=f"Removed redundant parentheses around {inner_expression.data if isinstance(inner_expression, Tree) else 'expression'}",
                    node=result_node,
                    original_text=original_text,
                    optimized_text=optimized_text
                )
                actions.append(action)
                
                return inner_expression
        
        return result_node
    
    def _requires_parentheses_for_precedence(
        self, 
        node: Tree, 
        parent_context: str
    ) -> bool:
        """
        Check if parentheses are required to maintain operator precedence.
        
        Args:
            node: The expression node
            parent_context: The context in which this expression appears
            
        Returns:
            True if parentheses are required for precedence
        """
        # This is a simplified implementation
        # A full implementation would need to understand MDX operator precedence
        
        if not isinstance(node, Tree):
            return False
        
        # Binary operations might need parentheses depending on context
        if node.data == "binary_operation":
            # Would need to check operator precedence rules here
            # For now, be conservative and keep parentheses around binary operations
            # in certain contexts
            return parent_context in ["binary_operation", "function_call"]
        
        return False
    
    def _get_node_text(self, node) -> str:
        """
        Get a text representation of the node for reporting.
        
        Args:
            node: The node to convert to text
            
        Returns:
            String representation
        """
        if isinstance(node, Tree):
            if node.data == "parenthesized_expression":
                inner = self._get_node_text(node.children[0]) if node.children else ""
                return f"({inner})"
            elif node.data == "identifier":
                return str(node.children[0]) if node.children else "identifier"
            elif node.data == "bracketed_identifier":
                inner = str(node.children[0]) if node.children else "identifier"
                return f"[{inner}]"
            else:
                return node.data
        else:
            return str(node)