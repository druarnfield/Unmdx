"""Rule for optimizing CrossJoin operations in MDX expressions."""

from typing import List, Tuple
from lark import Tree, Token

from ..base import LintRule
from ..models import LintAction
from ..enums import LintActionType, OptimizationLevel


class CrossJoinOptimizer(LintRule):
    """
    Optimizes CrossJoin operations in MDX expressions.
    
    This rule simplifies complex CrossJoin patterns commonly generated
    by Necto/Oracle Essbase, such as:
    - CROSSJOIN({A}, {B}) -> (A, B) for simple tuples
    - CROSSJOIN(CROSSJOIN(A, B), C) -> A * B * C for flattened operations
    - Nested CrossJoins that can be simplified to multiplication syntax
    """
    
    @property
    def name(self) -> str:
        """Return the rule name."""
        return "crossjoin_optimizer"
    
    @property
    def description(self) -> str:
        """Return rule description."""
        return "Simplifies CrossJoin operations to more readable tuple and multiplication syntax"
    
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
            True if optimizable CrossJoin operations are found
        """
        # Look for function calls that are CrossJoins
        function_calls = self._find_nodes(node, "function_call")
        
        for func_node in function_calls:
            if self._is_crossjoin_function(func_node):
                if self._can_optimize_crossjoin(func_node):
                    return True
        
        return False
    
    def apply(self, node: Tree) -> Tuple[Tree, List[LintAction]]:
        """
        Apply the rule to optimize CrossJoin operations.
        
        Args:
            node: The AST node to optimize
            
        Returns:
            Tuple of (modified_tree, list_of_actions)
        """
        actions = []
        modified_tree = self._copy_tree(node)
        
        # Process all CrossJoin function calls
        modified_tree = self._optimize_crossjoins_recursive(modified_tree, actions)
        
        return modified_tree, actions
    
    def _is_crossjoin_function(self, func_node: Tree) -> bool:
        """
        Check if a function call is a CrossJoin.
        
        Args:
            func_node: Function call node to check
            
        Returns:
            True if this is a CrossJoin function
        """
        if not isinstance(func_node, Tree) or func_node.data != "function_call":
            return False
        
        # Look for function name
        for child in func_node.children:
            if isinstance(child, Token) or isinstance(child, Tree):
                func_name = str(child).upper()
                if "CROSSJOIN" in func_name:
                    return True
        
        return False
    
    def _can_optimize_crossjoin(self, crossjoin_node: Tree) -> bool:
        """
        Check if a CrossJoin can be optimized.
        
        Args:
            crossjoin_node: CrossJoin function call node
            
        Returns:
            True if the CrossJoin can be optimized
        """
        # Count arguments
        args = self._get_function_arguments(crossjoin_node)
        
        # Can optimize if:
        # 1. Has exactly 2 arguments (simple crossjoin)
        # 2. Arguments are simple enough to convert to tuple syntax
        # 3. One or both arguments are also CrossJoins (nested case)
        
        if len(args) == 2:
            # Check if arguments are simple sets or other CrossJoins
            for arg in args:
                if self._is_simple_set(arg) or self._is_crossjoin_function(arg):
                    return True
        
        return False
    
    def _get_function_arguments(self, func_node: Tree) -> List[Tree]:
        """
        Extract arguments from a function call.
        
        Args:
            func_node: Function call node
            
        Returns:
            List of argument nodes
        """
        arguments = []
        
        # Look for argument list or individual arguments
        for child in func_node.children:
            if isinstance(child, Tree):
                if child.data == "argument_list":
                    # Extract individual arguments from argument list
                    for arg_child in child.children:
                        if isinstance(arg_child, Tree) and arg_child.data == "argument":
                            arguments.append(arg_child)
                elif child.data == "argument":
                    arguments.append(child)
        
        return arguments
    
    def _is_simple_set(self, node: Tree) -> bool:
        """
        Check if a node represents a simple set that can be part of a tuple.
        
        Args:
            node: Node to check
            
        Returns:
            True if this is a simple set
        """
        if not isinstance(node, Tree):
            return False
        
        # Simple sets include:
        # - Member references
        # - Set expressions with simple members
        # - Bracketed identifiers
        
        simple_set_types = [
            "member_reference",
            "bracketed_identifier", 
            "identifier",
            "set_expression"
        ]
        
        return node.data in simple_set_types
    
    def _optimize_crossjoins_recursive(
        self, 
        node: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Recursively optimize CrossJoins in the tree.
        
        Args:
            node: Current node being processed
            actions: List to accumulate actions performed
            
        Returns:
            Modified tree with optimized CrossJoins
        """
        if not isinstance(node, Tree):
            return node
        
        # Process children first (bottom-up approach)
        new_children = []
        for child in node.children:
            if isinstance(child, Tree):
                new_child = self._optimize_crossjoins_recursive(child, actions)
                new_children.append(new_child)
            else:
                new_children.append(child)
        
        # Create new node with processed children
        result_node = Tree(node.data, new_children)
        
        # Check if this node is a CrossJoin that can be optimized
        if self._is_crossjoin_function(result_node) and self._can_optimize_crossjoin(result_node):
            optimized_node = self._optimize_single_crossjoin(result_node, actions)
            return optimized_node
        
        return result_node
    
    def _optimize_single_crossjoin(
        self, 
        crossjoin_node: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Optimize a single CrossJoin operation.
        
        Args:
            crossjoin_node: The CrossJoin function call to optimize
            actions: List to accumulate actions
            
        Returns:
            Optimized node
        """
        args = self._get_function_arguments(crossjoin_node)
        
        if len(args) == 2:
            left_arg = args[0]
            right_arg = args[1]
            
            # Check for nested CrossJoins
            if self._is_crossjoin_function(left_arg) or self._is_crossjoin_function(right_arg):
                # Flatten nested CrossJoins to multiplication syntax
                return self._create_multiplication_syntax(crossjoin_node, args, actions)
            else:
                # Convert simple CrossJoin to tuple syntax
                return self._create_tuple_syntax(crossjoin_node, args, actions)
        
        return crossjoin_node
    
    def _create_tuple_syntax(
        self, 
        crossjoin_node: Tree, 
        args: List[Tree], 
        actions: List[LintAction]
    ) -> Tree:
        """
        Convert CROSSJOIN(A, B) to (A, B) tuple syntax.
        
        Args:
            crossjoin_node: Original CrossJoin node
            args: Function arguments
            actions: List to accumulate actions
            
        Returns:
            Tuple expression node
        """
        if len(args) != 2:
            return crossjoin_node
        
        # Create tuple expression
        # This is a simplified representation - actual implementation would
        # need to match the MDX grammar for tuple expressions
        tuple_node = Tree("tuple_expression", [
            args[0],  # First member
            args[1]   # Second member
        ])
        
        # Record the action
        original_text = f"CROSSJOIN({self._get_node_text(args[0])}, {self._get_node_text(args[1])})"
        optimized_text = f"({self._get_node_text(args[0])}, {self._get_node_text(args[1])})"
        
        action = self._create_action(
            action_type=LintActionType.SIMPLIFY_CROSSJOIN,
            description="Converted simple CrossJoin to tuple syntax",
            node=crossjoin_node,
            original_text=original_text,
            optimized_text=optimized_text
        )
        actions.append(action)
        
        return tuple_node
    
    def _create_multiplication_syntax(
        self, 
        crossjoin_node: Tree, 
        args: List[Tree], 
        actions: List[LintAction]
    ) -> Tree:
        """
        Convert nested CrossJoins to multiplication syntax (A * B * C).
        
        Args:
            crossjoin_node: Original CrossJoin node  
            args: Function arguments
            actions: List to accumulate actions
            
        Returns:
            Multiplication expression node
        """
        # Flatten all CrossJoin arguments into a list
        flattened_args = []
        self._flatten_crossjoin_args(args, flattened_args)
        
        if len(flattened_args) >= 2:
            # Create multiplication expression
            # This would need to match actual MDX grammar for multiplication
            mult_node = Tree("multiplication_expression", flattened_args)
            
            # Record the action
            arg_texts = [self._get_node_text(arg) for arg in flattened_args]
            original_text = self._get_node_text(crossjoin_node)
            optimized_text = " * ".join(arg_texts)
            
            action = self._create_action(
                action_type=LintActionType.SIMPLIFY_CROSSJOIN,
                description=f"Flattened nested CrossJoins to multiplication syntax ({len(flattened_args)} operands)",
                node=crossjoin_node,
                original_text=original_text,
                optimized_text=optimized_text
            )
            actions.append(action)
            
            return mult_node
        
        return crossjoin_node
    
    def _flatten_crossjoin_args(self, args: List[Tree], result: List[Tree]) -> None:
        """
        Recursively flatten CrossJoin arguments.
        
        Args:
            args: Current list of arguments to process
            result: List to accumulate flattened arguments
        """
        for arg in args:
            if self._is_crossjoin_function(arg):
                # Recursively flatten nested CrossJoin
                nested_args = self._get_function_arguments(arg)
                self._flatten_crossjoin_args(nested_args, result)
            else:
                # Add non-CrossJoin argument directly
                result.append(arg)
    
    def _get_node_text(self, node) -> str:
        """
        Get a text representation of the node for reporting.
        
        Args:
            node: The node to convert to text
            
        Returns:
            String representation
        """
        if isinstance(node, Tree):
            if node.data == "argument":
                # Get the actual expression inside the argument
                if node.children:
                    return self._get_node_text(node.children[0])
                return "arg"
            elif node.data == "identifier":
                return str(node.children[0]) if node.children else "identifier"
            elif node.data == "bracketed_identifier":
                inner = str(node.children[0]) if node.children else "identifier"
                return f"[{inner}]"
            elif node.data == "member_reference":
                return "member"
            elif node.data == "set_expression":
                return "set"
            else:
                return node.data
        else:
            return str(node)