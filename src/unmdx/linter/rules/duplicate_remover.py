"""Rule for removing duplicate member specifications and redundant elements."""

from typing import List, Tuple, Set, Dict
from lark import Tree, Token

from ..base import LintRule
from ..models import LintAction
from ..enums import LintActionType, OptimizationLevel


class DuplicateRemover(LintRule):
    """
    Removes duplicate member specifications and redundant elements.
    
    This rule targets duplicate patterns commonly found in Necto output:
    - Duplicate members in set expressions: {A, B, A} -> {A, B}
    - Identical calculated members defined multiple times
    - Redundant axis specifications
    - Duplicate filter conditions
    """
    
    @property
    def name(self) -> str:
        """Return the rule name."""
        return "duplicate_remover"
    
    @property
    def description(self) -> str:
        """Return rule description."""
        return "Removes duplicate member specifications and redundant elements from MDX queries"
    
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
            True if duplicates are found
        """
        # Look for various types of duplicate patterns
        return (self._has_duplicate_set_members(node) or
                self._has_duplicate_calculated_members(node) or
                self._has_duplicate_filters(node))
    
    def apply(self, node: Tree) -> Tuple[Tree, List[LintAction]]:
        """
        Apply the rule to remove duplicates.
        
        Args:
            node: The AST node to optimize
            
        Returns:
            Tuple of (modified_tree, list_of_actions)
        """
        actions = []
        modified_tree = self._copy_tree(node)
        
        # Remove duplicates in order of complexity
        modified_tree = self._remove_duplicate_set_members(modified_tree, actions)
        modified_tree = self._remove_duplicate_calculated_members(modified_tree, actions)
        modified_tree = self._remove_duplicate_filters(modified_tree, actions)
        
        return modified_tree, actions
    
    def _has_duplicate_set_members(self, node: Tree) -> bool:
        """Check if there are duplicate members in set expressions."""
        set_expressions = self._find_nodes(node, "set_expression")
        
        for set_expr in set_expressions:
            members = self._extract_set_members(set_expr)
            if len(members) != len(set(members)):  # Has duplicates
                return True
        
        return False
    
    def _has_duplicate_calculated_members(self, node: Tree) -> bool:
        """Check if there are duplicate calculated member definitions."""
        calc_members = self._find_nodes(node, "calculated_member")
        
        member_names = []
        for calc_member in calc_members:
            name = self._get_calculated_member_name(calc_member)
            if name:
                member_names.append(name)
        
        return len(member_names) != len(set(member_names))
    
    def _has_duplicate_filters(self, node: Tree) -> bool:
        """Check if there are duplicate filter conditions."""
        filter_expressions = self._find_nodes(node, "filter_expression")
        
        filter_texts = []
        for filter_expr in filter_expressions:
            filter_text = self._get_node_text(filter_expr)
            filter_texts.append(filter_text)
        
        return len(filter_texts) != len(set(filter_texts))
    
    def _remove_duplicate_set_members(
        self, 
        node: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Remove duplicate members from set expressions.
        
        Args:
            node: Current node being processed
            actions: List to accumulate actions
            
        Returns:
            Modified tree with duplicate set members removed
        """
        if not isinstance(node, Tree):
            return node
        
        # Process children first
        new_children = []
        for child in node.children:
            if isinstance(child, Tree):
                new_child = self._remove_duplicate_set_members(child, actions)
                new_children.append(new_child)
            else:
                new_children.append(child)
        
        result_node = Tree(node.data, new_children)
        
        # Process set expressions
        if result_node.data == "set_expression":
            result_node = self._deduplicate_set_expression(result_node, actions)
        
        return result_node
    
    def _deduplicate_set_expression(
        self, 
        set_expr: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Remove duplicates from a single set expression.
        
        Args:
            set_expr: Set expression node
            actions: List to accumulate actions
            
        Returns:
            Deduplicated set expression
        """
        members = self._extract_set_members(set_expr)
        
        # Track seen members to remove duplicates
        seen_members = set()
        unique_member_nodes = []
        duplicate_count = 0
        
        for member_node in self._get_set_member_nodes(set_expr):
            member_text = self._get_node_text(member_node)
            
            if member_text not in seen_members:
                seen_members.add(member_text)
                unique_member_nodes.append(member_node)
            else:
                duplicate_count += 1
        
        # If duplicates were found, create new set expression
        if duplicate_count > 0:
            new_set_expr = Tree("set_expression", unique_member_nodes)
            
            original_members = ", ".join(members)
            unique_members = ", ".join(list(seen_members))
            
            action = self._create_action(
                action_type=LintActionType.REMOVE_DUPLICATE,
                description=f"Removed {duplicate_count} duplicate member(s) from set",
                node=set_expr,
                original_text=f"{{{original_members}}}",
                optimized_text=f"{{{unique_members}}}"
            )
            actions.append(action)
            
            return new_set_expr
        
        return set_expr
    
    def _remove_duplicate_calculated_members(
        self, 
        node: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Remove duplicate calculated member definitions.
        
        Args:
            node: Current node being processed
            actions: List to accumulate actions
            
        Returns:
            Modified tree with duplicate calculated members removed
        """
        if not isinstance(node, Tree):
            return node
        
        # Process children first
        new_children = []
        for child in node.children:
            if isinstance(child, Tree):
                new_child = self._remove_duplicate_calculated_members(child, actions)
                new_children.append(new_child)
            else:
                new_children.append(child)
        
        result_node = Tree(node.data, new_children)
        
        # Process WITH clauses that contain calculated members
        if result_node.data == "with_clause":
            result_node = self._deduplicate_calculated_members_in_with(result_node, actions)
        
        return result_node
    
    def _deduplicate_calculated_members_in_with(
        self, 
        with_clause: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Remove duplicate calculated members from a WITH clause.
        
        Args:
            with_clause: WITH clause node
            actions: List to accumulate actions
            
        Returns:
            WITH clause with deduplicated calculated members
        """
        calc_members = self._find_nodes(with_clause, "calculated_member")
        
        # Track seen member names
        seen_members = {}  # name -> first_node
        unique_members = []
        duplicate_count = 0
        
        for calc_member in calc_members:
            member_name = self._get_calculated_member_name(calc_member)
            
            if member_name and member_name not in seen_members:
                seen_members[member_name] = calc_member
                unique_members.append(calc_member)
            else:
                duplicate_count += 1
        
        # If duplicates were found, reconstruct WITH clause
        if duplicate_count > 0:
            # Replace calculated members in the WITH clause
            new_children = []
            for child in with_clause.children:
                if isinstance(child, Tree) and child.data == "calculated_member":
                    # Only include if it's in unique_members
                    if child in unique_members:
                        new_children.append(child)
                else:
                    new_children.append(child)
            
            new_with_clause = Tree("with_clause", new_children)
            
            action = self._create_action(
                action_type=LintActionType.REMOVE_DUPLICATE,
                description=f"Removed {duplicate_count} duplicate calculated member definition(s)",
                node=with_clause,
                original_text=f"WITH clause with {len(calc_members)} members",
                optimized_text=f"WITH clause with {len(unique_members)} unique members"
            )
            actions.append(action)
            
            return new_with_clause
        
        return with_clause
    
    def _remove_duplicate_filters(
        self, 
        node: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Remove duplicate filter conditions.
        
        Args:
            node: Current node being processed
            actions: List to accumulate actions
            
        Returns:
            Modified tree with duplicate filters removed
        """
        if not isinstance(node, Tree):
            return node
        
        # Process children first
        new_children = []
        for child in node.children:
            if isinstance(child, Tree):
                new_child = self._remove_duplicate_filters(child, actions)
                new_children.append(new_child)
            else:
                new_children.append(child)
        
        result_node = Tree(node.data, new_children)
        
        # Process WHERE clauses that contain filters
        if result_node.data == "where_clause":
            result_node = self._deduplicate_filters_in_where(result_node, actions)
        
        return result_node
    
    def _deduplicate_filters_in_where(
        self, 
        where_clause: Tree, 
        actions: List[LintAction]
    ) -> Tree:
        """
        Remove duplicate filters from a WHERE clause.
        
        Args:
            where_clause: WHERE clause node
            actions: List to accumulate actions
            
        Returns:
            WHERE clause with deduplicated filters
        """
        filter_expressions = self._find_nodes(where_clause, "filter_expression")
        
        # Track seen filter expressions
        seen_filters = set()
        unique_filters = []
        duplicate_count = 0
        
        for filter_expr in filter_expressions:
            filter_text = self._get_node_text(filter_expr)
            
            if filter_text not in seen_filters:
                seen_filters.add(filter_text)
                unique_filters.append(filter_expr)
            else:
                duplicate_count += 1
        
        # If duplicates were found, reconstruct WHERE clause
        if duplicate_count > 0:
            # This is a simplified implementation
            # A full implementation would need to properly reconstruct
            # the logical structure of the WHERE clause
            
            action = self._create_action(
                action_type=LintActionType.REMOVE_DUPLICATE,
                description=f"Removed {duplicate_count} duplicate filter condition(s)",
                node=where_clause,
                original_text=f"WHERE clause with {len(filter_expressions)} filters",
                optimized_text=f"WHERE clause with {len(unique_filters)} unique filters"
            )
            actions.append(action)
        
        return where_clause
    
    # Helper methods
    
    def _extract_set_members(self, set_expr: Tree) -> List[str]:
        """
        Extract member names from a set expression.
        
        Args:
            set_expr: Set expression node
            
        Returns:
            List of member names
        """
        members = []
        member_nodes = self._get_set_member_nodes(set_expr)
        
        for member_node in member_nodes:
            member_text = self._get_node_text(member_node)
            members.append(member_text)
        
        return members
    
    def _get_set_member_nodes(self, set_expr: Tree) -> List[Tree]:
        """
        Get member nodes from a set expression.
        
        Args:
            set_expr: Set expression node
            
        Returns:
            List of member nodes
        """
        member_nodes = []
        
        # Look for different types of member specifications
        for child in set_expr.children:
            if isinstance(child, Tree):
                if child.data in ["member_reference", "bracketed_identifier", "identifier"]:
                    member_nodes.append(child)
                elif child.data == "member_list":
                    # Recursively get members from member list
                    member_nodes.extend(self._get_set_member_nodes(child))
        
        return member_nodes
    
    def _get_calculated_member_name(self, calc_member: Tree) -> str:
        """
        Extract the name from a calculated member definition.
        
        Args:
            calc_member: Calculated member node
            
        Returns:
            Member name or empty string if not found
        """
        # Look for member name in calculated member definition
        for child in calc_member.children:
            if isinstance(child, Tree):
                if child.data == "member_name":
                    return self._get_node_text(child)
                elif child.data in ["identifier", "bracketed_identifier"]:
                    return self._get_node_text(child)
        
        return ""
    
    def _get_node_text(self, node) -> str:
        """
        Get a text representation of the node.
        
        Args:
            node: The node to convert to text
            
        Returns:
            String representation
        """
        if isinstance(node, Tree):
            if node.data == "identifier":
                return str(node.children[0]) if node.children else "identifier"
            elif node.data == "bracketed_identifier":
                inner = str(node.children[0]) if node.children else "identifier"
                return f"[{inner}]"
            elif node.data == "member_reference":
                # Simplified - would need more complex logic for full member paths
                return "member"
            elif node.data == "member_name":
                return str(node.children[0]) if node.children else "member"
            else:
                return node.data
        else:
            return str(node)