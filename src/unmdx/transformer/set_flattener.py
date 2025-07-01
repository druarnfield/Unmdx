"""Set flattening algorithms for MDX transformations."""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Set, Union, Dict, Any

from lark import Tree, Token

from ..ir import MemberSelection, MemberSelectionType
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SetOperationType(Enum):
    """Types of set operations in MDX."""
    CROSSJOIN = "CROSSJOIN"
    UNION = "UNION"
    INTERSECT = "INTERSECT"
    EXCEPT = "EXCEPT"
    FILTER = "FILTER"
    ORDER = "ORDER"
    TOPCOUNT = "TOPCOUNT"
    BOTTOMCOUNT = "BOTTOMCOUNT"
    HEAD = "HEAD"
    TAIL = "TAIL"
    SUBSET = "SUBSET"
    MEMBERS = "MEMBERS"
    CHILDREN = "CHILDREN"
    DESCENDANTS = "DESCENDANTS"
    ANCESTORS = "ANCESTORS"


@dataclass
class FlattenedSet:
    """Result of flattening a set expression."""
    members: List[str]
    operation_type: SetOperationType
    is_calculated: bool = False
    filters_applied: List[str] = None
    ordering_applied: bool = False
    limit_applied: Optional[int] = None
    
    def __post_init__(self):
        if self.filters_applied is None:
            self.filters_applied = []


@dataclass
class SetExpression:
    """Represents a set expression in the parse tree."""
    expression_type: SetOperationType
    operands: List[Union['SetExpression', str]]
    function_args: List[Any] = None
    
    def __post_init__(self):
        if self.function_args is None:
            self.function_args = []


class SetFlattener:
    """
    Flattens complex set expressions into simple member lists.
    
    This component analyzes MDX set expressions and:
    - Resolves CrossJoin operations into dimensional combinations
    - Flattens Union/Intersect/Except operations
    - Handles set functions like Filter, TopCount, etc.
    - Extracts simple member lists where possible
    - Identifies when sets are too complex to flatten
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Function mapping for set operations
        self._function_map = {
            "CROSSJOIN": SetOperationType.CROSSJOIN,
            "UNION": SetOperationType.UNION,
            "INTERSECT": SetOperationType.INTERSECT,
            "EXCEPT": SetOperationType.EXCEPT,
            "FILTER": SetOperationType.FILTER,
            "ORDER": SetOperationType.ORDER,
            "TOPCOUNT": SetOperationType.TOPCOUNT,
            "BOTTOMCOUNT": SetOperationType.BOTTOMCOUNT,
            "HEAD": SetOperationType.HEAD,
            "TAIL": SetOperationType.TAIL,
            "SUBSET": SetOperationType.SUBSET,
            ".MEMBERS": SetOperationType.MEMBERS,
            ".CHILDREN": SetOperationType.CHILDREN,
            "DESCENDANTS": SetOperationType.DESCENDANTS,
            "ANCESTORS": SetOperationType.ANCESTORS,
        }
    
    def flatten_set_expression(self, set_node: Tree) -> FlattenedSet:
        """
        Flatten a set expression into a simple member list.
        
        Args:
            set_node: Parse tree node representing a set expression
            
        Returns:
            FlattenedSet with member list and metadata
        """
        self.logger.debug(f"Flattening set expression: {set_node.data}")
        
        # Parse the set expression
        set_expr = self._parse_set_expression(set_node)
        
        # Flatten the expression
        flattened = self._flatten_expression(set_expr)
        
        return flattened
    
    def can_flatten_to_simple_list(self, set_node: Tree) -> bool:
        """
        Check if a set expression can be flattened to a simple member list.
        
        Some complex expressions with filters or calculations cannot be
        simplified to a static list.
        """
        set_expr = self._parse_set_expression(set_node)
        return self._is_simple_flattening(set_expr)
    
    def extract_member_selection(self, set_node: Tree) -> MemberSelection:
        """
        Extract a MemberSelection IR object from a set expression.
        
        Args:
            set_node: Parse tree node representing a set expression
            
        Returns:
            MemberSelection object
        """
        flattened = self.flatten_set_expression(set_node)
        
        if not flattened.members:
            # Empty set or all members
            return MemberSelection(selection_type=MemberSelectionType.ALL)
        
        elif flattened.operation_type == SetOperationType.MEMBERS:
            # .MEMBERS operation typically means all members
            return MemberSelection(selection_type=MemberSelectionType.ALL)
        
        elif flattened.operation_type == SetOperationType.CHILDREN:
            # .CHILDREN operation
            parent_member = flattened.members[0] if flattened.members else None
            return MemberSelection(
                selection_type=MemberSelectionType.CHILDREN,
                parent_member=parent_member
            )
        
        elif len(flattened.members) == 1 and flattened.operation_type in [
            SetOperationType.DESCENDANTS, SetOperationType.ANCESTORS
        ]:
            # Hierarchical navigation from a single member
            return MemberSelection(
                selection_type=MemberSelectionType.CHILDREN,
                parent_member=flattened.members[0]
            )
        
        else:
            # Specific member list
            return MemberSelection(
                selection_type=MemberSelectionType.SPECIFIC,
                specific_members=flattened.members
            )
    
    def _parse_set_expression(self, set_node: Tree) -> SetExpression:
        """Parse a set expression into a structured representation."""
        
        if set_node.data == "function_call":
            return self._parse_function_call(set_node)
        
        elif set_node.data == "set_literal":
            return self._parse_set_literal(set_node)
        
        elif set_node.data == "member_reference":
            member_name = self._extract_member_name(set_node)
            return SetExpression(
                expression_type=SetOperationType.MEMBERS,
                operands=[member_name]
            )
        
        elif set_node.data == "hierarchy_members":
            return self._parse_hierarchy_members(set_node)
        
        elif set_node.data == "binary_set_operation":
            return self._parse_binary_set_operation(set_node)
        
        else:
            # Unknown set expression type
            self.logger.warning(f"Unknown set expression type: {set_node.data}")
            return SetExpression(
                expression_type=SetOperationType.MEMBERS,
                operands=[]
            )
    
    def _parse_function_call(self, func_node: Tree) -> SetExpression:
        """Parse a function call that returns a set."""
        
        # Extract function name
        func_name = self._extract_function_name(func_node)
        func_name_upper = func_name.upper()
        
        # Map to operation type
        operation_type = self._function_map.get(func_name_upper, SetOperationType.MEMBERS)
        
        # Extract arguments
        args = self._extract_function_arguments(func_node)
        
        # Parse operands based on function type
        operands = []
        function_args = []
        
        if operation_type == SetOperationType.CROSSJOIN:
            # CrossJoin takes two set expressions
            for arg in args[:2]:
                if self._is_set_expression(arg):
                    operands.append(self._parse_set_expression(arg))
                else:
                    operands.append(str(arg))
        
        elif operation_type in [SetOperationType.UNION, SetOperationType.INTERSECT, SetOperationType.EXCEPT]:
            # Binary set operations
            for arg in args[:2]:
                if self._is_set_expression(arg):
                    operands.append(self._parse_set_expression(arg))
                else:
                    operands.append(str(arg))
        
        elif operation_type == SetOperationType.FILTER:
            # Filter takes a set and a condition
            if args:
                if self._is_set_expression(args[0]):
                    operands.append(self._parse_set_expression(args[0]))
                function_args = args[1:]  # Filter conditions
        
        elif operation_type in [SetOperationType.TOPCOUNT, SetOperationType.BOTTOMCOUNT]:
            # TopCount/BottomCount take set, count, and optional expression
            if args:
                if self._is_set_expression(args[0]):
                    operands.append(self._parse_set_expression(args[0]))
                function_args = args[1:]  # Count and expression
        
        elif operation_type in [SetOperationType.HEAD, SetOperationType.TAIL]:
            # Head/Tail take set and count
            if args:
                if self._is_set_expression(args[0]):
                    operands.append(self._parse_set_expression(args[0]))
                function_args = args[1:]  # Count
        
        elif operation_type == SetOperationType.ORDER:
            # Order takes set and expression
            if args:
                if self._is_set_expression(args[0]):
                    operands.append(self._parse_set_expression(args[0]))
                function_args = args[1:]  # Ordering expression
        
        else:
            # Other functions - treat arguments as operands
            for arg in args:
                if self._is_set_expression(arg):
                    operands.append(self._parse_set_expression(arg))
                else:
                    operands.append(str(arg))
        
        return SetExpression(
            expression_type=operation_type,
            operands=operands,
            function_args=function_args
        )
    
    def _parse_set_literal(self, set_node: Tree) -> SetExpression:
        """Parse a set literal like {[Member1], [Member2]}."""
        
        members = []
        
        # Extract member references from the set
        for child in set_node.children:
            if isinstance(child, Tree) and child.data == "member_reference":
                member_name = self._extract_member_name(child)
                if member_name:
                    members.append(member_name)
            elif isinstance(child, Tree):
                # Also check nested children for member references
                nested_members = self._find_member_references_recursive(child)
                members.extend(nested_members)
        
        return SetExpression(
            expression_type=SetOperationType.MEMBERS,
            operands=members
        )
    
    def _parse_hierarchy_members(self, hierarchy_node: Tree) -> SetExpression:
        """Parse hierarchy.MEMBERS or similar expressions."""
        
        # Extract hierarchy name
        hierarchy_name = self._extract_hierarchy_name(hierarchy_node)
        
        # Check if this is .MEMBERS, .CHILDREN, etc.
        operation_type = SetOperationType.MEMBERS
        
        for child in hierarchy_node.children:
            if isinstance(child, Token):
                token_str = str(child).upper()
                if ".MEMBERS" in token_str:
                    operation_type = SetOperationType.MEMBERS
                elif ".CHILDREN" in token_str:
                    operation_type = SetOperationType.CHILDREN
        
        return SetExpression(
            expression_type=operation_type,
            operands=[hierarchy_name] if hierarchy_name else []
        )
    
    def _parse_binary_set_operation(self, binary_node: Tree) -> SetExpression:
        """Parse binary set operations like UNION, INTERSECT, etc."""
        
        children = list(binary_node.children)
        if len(children) < 3:
            return SetExpression(
                expression_type=SetOperationType.UNION,
                operands=[]
            )
        
        left_operand = children[0]
        operator = str(children[1]).upper()
        right_operand = children[2]
        
        # Map operator to operation type
        operation_type = self._function_map.get(operator, SetOperationType.UNION)
        
        # Parse operands
        operands = []
        if self._is_set_expression(left_operand):
            operands.append(self._parse_set_expression(left_operand))
        else:
            operands.append(str(left_operand))
        
        if self._is_set_expression(right_operand):
            operands.append(self._parse_set_expression(right_operand))
        else:
            operands.append(str(right_operand))
        
        return SetExpression(
            expression_type=operation_type,
            operands=operands
        )
    
    def _flatten_expression(self, set_expr: SetExpression) -> FlattenedSet:
        """Flatten a set expression into a member list."""
        
        if set_expr.expression_type == SetOperationType.MEMBERS:
            # Simple member list
            members = [op for op in set_expr.operands if isinstance(op, str)]
            return FlattenedSet(
                members=members,
                operation_type=set_expr.expression_type
            )
        
        elif set_expr.expression_type == SetOperationType.CROSSJOIN:
            # Flatten crossjoin by combining operand results
            all_members = []
            for operand in set_expr.operands:
                if isinstance(operand, SetExpression):
                    sub_flattened = self._flatten_expression(operand)
                    all_members.extend(sub_flattened.members)
                else:
                    all_members.append(operand)
            
            return FlattenedSet(
                members=all_members,
                operation_type=set_expr.expression_type
            )
        
        elif set_expr.expression_type == SetOperationType.UNION:
            # Flatten union by combining unique members
            all_members = set()
            for operand in set_expr.operands:
                if isinstance(operand, SetExpression):
                    sub_flattened = self._flatten_expression(operand)
                    all_members.update(sub_flattened.members)
                else:
                    all_members.add(operand)
            
            return FlattenedSet(
                members=list(all_members),
                operation_type=set_expr.expression_type
            )
        
        elif set_expr.expression_type == SetOperationType.INTERSECT:
            # Flatten intersect by finding common members
            if len(set_expr.operands) < 2:
                return FlattenedSet(members=[], operation_type=set_expr.expression_type)
            
            # Start with first operand
            result_members = set()
            first_operand = set_expr.operands[0]
            if isinstance(first_operand, SetExpression):
                first_flattened = self._flatten_expression(first_operand)
                result_members = set(first_flattened.members)
            else:
                result_members = {first_operand}
            
            # Intersect with remaining operands
            for operand in set_expr.operands[1:]:
                if isinstance(operand, SetExpression):
                    sub_flattened = self._flatten_expression(operand)
                    result_members &= set(sub_flattened.members)
                else:
                    result_members &= {operand}
            
            return FlattenedSet(
                members=list(result_members),
                operation_type=set_expr.expression_type
            )
        
        elif set_expr.expression_type == SetOperationType.EXCEPT:
            # Flatten except by removing members
            if len(set_expr.operands) < 2:
                return FlattenedSet(members=[], operation_type=set_expr.expression_type)
            
            # Start with first operand
            result_members = set()
            first_operand = set_expr.operands[0]
            if isinstance(first_operand, SetExpression):
                first_flattened = self._flatten_expression(first_operand)
                result_members = set(first_flattened.members)
            else:
                result_members = {first_operand}
            
            # Remove members from remaining operands
            for operand in set_expr.operands[1:]:
                if isinstance(operand, SetExpression):
                    sub_flattened = self._flatten_expression(operand)
                    result_members -= set(sub_flattened.members)
                else:
                    result_members.discard(operand)
            
            return FlattenedSet(
                members=list(result_members),
                operation_type=set_expr.expression_type
            )
        
        elif set_expr.expression_type in [SetOperationType.FILTER, SetOperationType.TOPCOUNT, 
                                        SetOperationType.BOTTOMCOUNT, SetOperationType.HEAD, 
                                        SetOperationType.TAIL, SetOperationType.ORDER]:
            # These operations modify the set but we can still extract base members
            base_members = []
            if set_expr.operands:
                first_operand = set_expr.operands[0]
                if isinstance(first_operand, SetExpression):
                    base_flattened = self._flatten_expression(first_operand)
                    base_members = base_flattened.members
                else:
                    base_members = [first_operand]
            
            # Mark as calculated since we can't determine the exact result
            return FlattenedSet(
                members=base_members,
                operation_type=set_expr.expression_type,
                is_calculated=True,
                filters_applied=[str(arg) for arg in set_expr.function_args] if set_expr.function_args else []
            )
        
        else:
            # Default case - treat as simple member list
            members = [op for op in set_expr.operands if isinstance(op, str)]
            return FlattenedSet(
                members=members,
                operation_type=set_expr.expression_type
            )
    
    def _is_simple_flattening(self, set_expr: SetExpression) -> bool:
        """Check if expression can be flattened to a simple static list."""
        
        # These operations produce static lists
        static_operations = {
            SetOperationType.MEMBERS,
            SetOperationType.UNION,
            SetOperationType.INTERSECT,
            SetOperationType.EXCEPT,
            SetOperationType.CROSSJOIN
        }
        
        if set_expr.expression_type in static_operations:
            # Check if all operands are also simple
            for operand in set_expr.operands:
                if isinstance(operand, SetExpression):
                    if not self._is_simple_flattening(operand):
                        return False
            return True
        
        # These operations require runtime calculation
        return False
    
    def _is_set_expression(self, node: Any) -> bool:
        """Check if a node represents a set expression."""
        if not isinstance(node, Tree):
            return False
        
        set_expression_types = {
            "function_call", "set_literal", "member_reference",
            "hierarchy_members", "binary_set_operation"
        }
        
        return node.data in set_expression_types
    
    def _extract_function_name(self, func_node: Tree) -> str:
        """Extract function name from function call node."""
        for child in func_node.children:
            if isinstance(child, Token):
                return str(child)
        return "UNKNOWN"
    
    def _extract_function_arguments(self, func_node: Tree) -> List[Tree]:
        """Extract arguments from function call node."""
        args = []
        
        # Look for argument list
        for child in func_node.children:
            if isinstance(child, Tree) and child.data == "argument_list":
                for arg in child.children:
                    if isinstance(arg, Tree):
                        args.append(arg)
        
        return args
    
    def _extract_member_name(self, member_node: Tree) -> Optional[str]:
        """Extract member name from member reference."""
        for child in member_node.children:
            if isinstance(child, Token):
                return str(child)
            elif isinstance(child, Tree) and child.data == "identifier":
                return self._extract_identifier_value(child)
        return None
    
    def _extract_hierarchy_name(self, hierarchy_node: Tree) -> Optional[str]:
        """Extract hierarchy name from hierarchy reference."""
        for child in hierarchy_node.children:
            if isinstance(child, Token):
                return str(child)
            elif isinstance(child, Tree) and child.data == "identifier":
                return self._extract_identifier_value(child)
        return None
    
    def _extract_identifier_value(self, node: Tree) -> str:
        """Extract identifier value from a node."""
        if node.children:
            return str(node.children[0])
        return str(node)
    
    def _find_member_references_recursive(self, node: Tree) -> List[str]:
        """Recursively find member references in a tree node."""
        members = []
        
        if isinstance(node, Tree):
            if node.data == "member_reference":
                member_name = self._extract_member_name(node)
                if member_name:
                    members.append(member_name)
            else:
                for child in node.children:
                    if isinstance(child, Tree):
                        members.extend(self._find_member_references_recursive(child))
        
        return members