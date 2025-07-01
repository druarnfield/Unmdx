"""Rule for optimizing verbose function call patterns in MDX expressions."""

from typing import List, Tuple, Dict, Set
from lark import Tree, Token

from ..base import LintRule
from ..models import LintAction
from ..enums import LintActionType, OptimizationLevel


class FunctionOptimizer(LintRule):
    """
    Optimizes verbose function call patterns in MDX expressions.
    
    This rule simplifies common function patterns that can be redundant
    or overly verbose, such as:
    - IIF(condition, value, value) -> value (same true/false values)
    - UNION(set, {}) -> set (union with empty set)
    - FILTER(set, TRUE) -> set (filter with always-true condition)
    - Multiple nested IIF calls that can be simplified
    """
    
    def __init__(self, config):
        """Initialize with optimization patterns."""
        super().__init__(config)
        
        # Define optimization patterns for different functions
        self.optimization_patterns = {
            "IIF": self._optimize_iif,
            "UNION": self._optimize_union, 
            "FILTER": self._optimize_filter,
            "INTERSECT": self._optimize_intersect,
            "EXCEPT": self._optimize_except,
            "DISTINCT": self._optimize_distinct,
        }
    
    @property
    def name(self) -> str:
        """Return the rule name."""
        return "function_optimizer"
    
    @property
    def description(self) -> str:
        """Return rule description."""
        return "Optimizes verbose function call patterns and removes redundant function calls"
    
    @property
    def optimization_level(self) -> OptimizationLevel:
        """This rule applies at moderate level due to semantic changes."""
        return OptimizationLevel.MODERATE
    
    def can_apply(self, node: Tree) -> bool:
        """
        Check if this rule can be applied to the node.
        
        Args:
            node: The AST node to check
            
        Returns:
            True if optimizable function calls are found
        """
        # Look for function calls that can be optimized
        function_calls = self._find_nodes(node, "function_call")
        
        for func_node in function_calls:
            func_name = self._get_function_name(func_node)
            if func_name and func_name.upper() in self.optimization_patterns:
                if self._can_optimize_function(func_node, func_name.upper()):
                    return True
        
        return False
    
    def apply(self, node: Tree) -> Tuple[Tree, List[LintAction]]:
        """
        Apply the rule to optimize function calls.
        
        Args:
            node: The AST node to optimize
            
        Returns:
            Tuple of (modified_tree, list_of_actions)
        """
        actions = []
        modified_tree = self._copy_tree(node)
        
        # Process all optimizable function calls
        modified_tree = self._optimize_functions_recursive(modified_tree, actions)
        
        return modified_tree, actions
    
    def _get_function_name(self, func_node: Tree) -> str:
        """
        Extract function name from a function call node.
        
        Args:
            func_node: Function call node
            
        Returns:
            Function name or empty string if not found
        """
        if not isinstance(func_node, Tree) or func_node.data != "function_call":
            return ""
        
        # Look for function identifier
        for child in func_node.children:
            if isinstance(child, Token):
                return str(child)
            elif isinstance(child, Tree) and child.data == "identifier":
                if child.children:
                    return str(child.children[0])
        
        return ""
    
    def _can_optimize_function(self, func_node: Tree, func_name: str) -> bool:
        """
        Check if a specific function call can be optimized.
        
        Args:
            func_node: Function call node
            func_name: Name of the function
            
        Returns:
            True if the function can be optimized
        """
        if func_name not in self.optimization_patterns:
            return False
        
        args = self._get_function_arguments(func_node)
        
        # Check specific optimization conditions for each function type
        if func_name == "IIF":
            return self._can_optimize_iif(args)
        elif func_name == "UNION":
            return self._can_optimize_union(args)
        elif func_name == "FILTER":
            return self._can_optimize_filter(args)
        elif func_name == "INTERSECT":
            return self._can_optimize_intersect(args)
        elif func_name == "EXCEPT":
            return self._can_optimize_except(args)
        elif func_name == "DISTINCT":
            return self._can_optimize_distinct(args)
        
        return False
    
    def _optimize_functions_recursive(
        self, 
        node: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Recursively optimize function calls in the tree.
        
        Args:
            node: Current node being processed
            actions: List to accumulate actions performed
            
        Returns:
            Modified tree with optimized functions
        """
        if not isinstance(node, Tree):
            return node
        
        # Process children first (bottom-up approach)
        new_children = []
        for child in node.children:
            if isinstance(child, Tree):
                new_child = self._optimize_functions_recursive(child, actions)
                new_children.append(new_child)
            else:
                new_children.append(child)
        
        # Create new node with processed children
        result_node = Tree(node.data, new_children)
        
        # Check if this node is a function that can be optimized
        if result_node.data == "function_call":
            func_name = self._get_function_name(result_node)
            if func_name and func_name.upper() in self.optimization_patterns:
                if self._can_optimize_function(result_node, func_name.upper()):
                    optimized_node = self._optimize_single_function(result_node, func_name.upper(), actions)
                    return optimized_node
        
        return result_node
    
    def _optimize_single_function(
        self, 
        func_node: Tree, 
        func_name: str, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Optimize a single function call.
        
        Args:
            func_node: The function call to optimize
            func_name: Name of the function
            actions: List to accumulate actions
            
        Returns:
            Optimized node
        """
        optimizer = self.optimization_patterns.get(func_name)
        if optimizer:
            return optimizer(func_node, actions)
        
        return func_node
    
    # IIF optimizations
    
    def _can_optimize_iif(self, args: List[Tree]) -> bool:
        """Check if IIF can be optimized."""
        if len(args) != 3:
            return False
        
        condition, true_value, false_value = args
        
        # Can optimize if true and false values are identical
        return self._are_nodes_equivalent(true_value, false_value)
    
    def _optimize_iif(self, func_node: Tree, actions: List[LintAction]) -> Tree:
        """Optimize IIF function calls."""
        args = self._get_function_arguments(func_node)
        
        if len(args) == 3:
            condition, true_value, false_value = args
            
            # If true and false values are the same, return just the value
            if self._are_nodes_equivalent(true_value, false_value):
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Simplified IIF with identical true/false values",
                    node=func_node,
                    original_text=f"IIF({self._get_node_text(condition)}, {self._get_node_text(true_value)}, {self._get_node_text(false_value)})",
                    optimized_text=self._get_node_text(true_value)
                )
                actions.append(action)
                
                return true_value
        
        return func_node
    
    # UNION optimizations
    
    def _can_optimize_union(self, args: List[Tree]) -> bool:
        """Check if UNION can be optimized."""
        if len(args) != 2:
            return False
        
        # Can optimize if one argument is an empty set
        return (self._is_empty_set(args[0]) or 
                self._is_empty_set(args[1]) or
                self._are_nodes_equivalent(args[0], args[1]))
    
    def _optimize_union(self, func_node: Tree, actions: List[LintAction]) -> Tree:
        """Optimize UNION function calls."""
        args = self._get_function_arguments(func_node)
        
        if len(args) == 2:
            left_set, right_set = args
            
            # UNION(set, {}) -> set
            if self._is_empty_set(right_set):
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Removed union with empty set",
                    node=func_node,
                    original_text=f"UNION({self._get_node_text(left_set)}, {{}})",
                    optimized_text=self._get_node_text(left_set)
                )
                actions.append(action)
                return left_set
            
            # UNION({}, set) -> set
            elif self._is_empty_set(left_set):
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Removed union with empty set",
                    node=func_node,
                    original_text=f"UNION({{}}, {self._get_node_text(right_set)})",
                    optimized_text=self._get_node_text(right_set)
                )
                actions.append(action)
                return right_set
            
            # UNION(set, set) -> set (identical sets)
            elif self._are_nodes_equivalent(left_set, right_set):
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Removed union of identical sets",
                    node=func_node,
                    original_text=f"UNION({self._get_node_text(left_set)}, {self._get_node_text(right_set)})",
                    optimized_text=self._get_node_text(left_set)
                )
                actions.append(action)
                return left_set
        
        return func_node
    
    # FILTER optimizations
    
    def _can_optimize_filter(self, args: List[Tree]) -> bool:
        """Check if FILTER can be optimized."""
        if len(args) != 2:
            return False
        
        set_arg, condition_arg = args
        
        # Can optimize if condition is always true or always false
        return (self._is_always_true(condition_arg) or 
                self._is_always_false(condition_arg))
    
    def _optimize_filter(self, func_node: Tree, actions: List[LintAction]) -> Tree:
        """Optimize FILTER function calls."""
        args = self._get_function_arguments(func_node)
        
        if len(args) == 2:
            set_arg, condition_arg = args
            
            # FILTER(set, TRUE) -> set
            if self._is_always_true(condition_arg):
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Removed filter with always-true condition",
                    node=func_node,
                    original_text=f"FILTER({self._get_node_text(set_arg)}, TRUE)",
                    optimized_text=self._get_node_text(set_arg)
                )
                actions.append(action)
                return set_arg
            
            # FILTER(set, FALSE) -> {} (empty set)
            elif self._is_always_false(condition_arg):
                empty_set = Tree("empty_set", [])
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Replaced filter with always-false condition with empty set",
                    node=func_node,
                    original_text=f"FILTER({self._get_node_text(set_arg)}, FALSE)",
                    optimized_text="{}"
                )
                actions.append(action)
                return empty_set
        
        return func_node
    
    # INTERSECT optimizations
    
    def _can_optimize_intersect(self, args: List[Tree]) -> bool:
        """Check if INTERSECT can be optimized."""
        if len(args) != 2:
            return False
        
        # Can optimize if sets are identical or one is empty
        return (self._are_nodes_equivalent(args[0], args[1]) or
                self._is_empty_set(args[0]) or
                self._is_empty_set(args[1]))
    
    def _optimize_intersect(self, func_node: Tree, actions: List[LintAction]) -> Tree:
        """Optimize INTERSECT function calls."""
        args = self._get_function_arguments(func_node)
        
        if len(args) == 2:
            left_set, right_set = args
            
            # INTERSECT(set, set) -> set (identical sets)
            if self._are_nodes_equivalent(left_set, right_set):
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Simplified intersect of identical sets",
                    node=func_node,
                    original_text=f"INTERSECT({self._get_node_text(left_set)}, {self._get_node_text(right_set)})",
                    optimized_text=self._get_node_text(left_set)
                )
                actions.append(action)
                return left_set
            
            # INTERSECT(set, {}) -> {} or INTERSECT({}, set) -> {}
            elif self._is_empty_set(left_set) or self._is_empty_set(right_set):
                empty_set = Tree("empty_set", [])
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Replaced intersect with empty set",
                    node=func_node,
                    original_text=self._get_node_text(func_node),
                    optimized_text="{}"
                )
                actions.append(action)
                return empty_set
        
        return func_node
    
    # EXCEPT optimizations
    
    def _can_optimize_except(self, args: List[Tree]) -> bool:
        """Check if EXCEPT can be optimized."""
        if len(args) != 2:
            return False
        
        # Can optimize if sets are identical or second set is empty
        return (self._are_nodes_equivalent(args[0], args[1]) or
                self._is_empty_set(args[1]))
    
    def _optimize_except(self, func_node: Tree, actions: List[LintAction]) -> Tree:
        """Optimize EXCEPT function calls."""
        args = self._get_function_arguments(func_node)
        
        if len(args) == 2:
            left_set, right_set = args
            
            # EXCEPT(set, set) -> {} (identical sets)
            if self._are_nodes_equivalent(left_set, right_set):
                empty_set = Tree("empty_set", [])
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Replaced except of identical sets with empty set",
                    node=func_node,
                    original_text=f"EXCEPT({self._get_node_text(left_set)}, {self._get_node_text(right_set)})",
                    optimized_text="{}"
                )
                actions.append(action)
                return empty_set
            
            # EXCEPT(set, {}) -> set
            elif self._is_empty_set(right_set):
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Removed except with empty set",
                    node=func_node,
                    original_text=f"EXCEPT({self._get_node_text(left_set)}, {{}})",
                    optimized_text=self._get_node_text(left_set)
                )
                actions.append(action)
                return left_set
        
        return func_node
    
    # DISTINCT optimizations
    
    def _can_optimize_distinct(self, args: List[Tree]) -> bool:
        """Check if DISTINCT can be optimized."""
        if len(args) != 1:
            return False
        
        # Can optimize if the argument is already known to be distinct
        # For now, check if it's a simple member reference or empty set
        arg = args[0]
        return (self._is_empty_set(arg) or 
                self._is_single_member(arg))
    
    def _optimize_distinct(self, func_node: Tree, actions: List[LintAction]) -> Tree:
        """Optimize DISTINCT function calls."""
        args = self._get_function_arguments(func_node)
        
        if len(args) == 1:
            set_arg = args[0]
            
            # DISTINCT on single member or empty set is redundant
            if self._is_empty_set(set_arg) or self._is_single_member(set_arg):
                action = self._create_action(
                    action_type=LintActionType.OPTIMIZE_FUNCTION,
                    description="Removed redundant DISTINCT operation",
                    node=func_node,
                    original_text=f"DISTINCT({self._get_node_text(set_arg)})",
                    optimized_text=self._get_node_text(set_arg)
                )
                actions.append(action)
                return set_arg
        
        return func_node
    
    # Helper methods
    
    def _get_function_arguments(self, func_node: Tree) -> List[Tree]:
        """Extract arguments from a function call."""
        arguments = []
        
        for child in func_node.children:
            if isinstance(child, Tree):
                if child.data == "argument_list":
                    for arg_child in child.children:
                        if isinstance(arg_child, Tree) and arg_child.data == "argument":
                            arguments.append(arg_child)
                elif child.data == "argument":
                    arguments.append(child)
        
        return arguments
    
    def _are_nodes_equivalent(self, node1: Tree, node2: Tree) -> bool:
        """Check if two nodes are semantically equivalent."""
        # Simplified equivalence check
        # A full implementation would need deep structural comparison
        return str(node1) == str(node2)
    
    def _is_empty_set(self, node: Tree) -> bool:
        """Check if a node represents an empty set."""
        if isinstance(node, Tree):
            return node.data == "empty_set" or str(node).strip() == "{}"
        return False
    
    def _is_always_true(self, node: Tree) -> bool:
        """Check if a node represents a condition that's always true."""
        if isinstance(node, Tree):
            return (node.data == "boolean_literal" and 
                    str(node).upper() in ["TRUE", "1"])
        elif isinstance(node, Token):
            return str(node).upper() in ["TRUE", "1"]
        return False
    
    def _is_always_false(self, node: Tree) -> bool:
        """Check if a node represents a condition that's always false."""
        if isinstance(node, Tree):
            return (node.data == "boolean_literal" and 
                    str(node).upper() in ["FALSE", "0"])
        elif isinstance(node, Token):
            return str(node).upper() in ["FALSE", "0"]
        return False
    
    def _is_single_member(self, node: Tree) -> bool:
        """Check if a node represents a single member reference."""
        if isinstance(node, Tree):
            return node.data in ["member_reference", "bracketed_identifier"]
        return False
    
    def _get_node_text(self, node) -> str:
        """Get a text representation of the node."""
        if isinstance(node, Tree):
            if node.data == "argument":
                if node.children:
                    return self._get_node_text(node.children[0])
                return "arg"
            elif node.data == "empty_set":
                return "{}"
            elif node.data in ["identifier", "bracketed_identifier"]:
                return str(node.children[0]) if node.children else "identifier"
            else:
                return node.data
        else:
            return str(node)