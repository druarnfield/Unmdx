"""Unit tests for set flattening algorithms."""

import pytest
from lark import Tree, Token

from unmdx.transformer.set_flattener import (
    SetFlattener, FlattenedSet, SetExpression, SetOperationType
)
from unmdx.ir import MemberSelectionType


class TestSetFlattener:
    """Test set flattening functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.flattener = SetFlattener()
    
    def test_flatten_simple_member_list(self):
        """Test flattening a simple member list."""
        # Create set literal: {[Bikes], [Accessories]}
        member1_tree = Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        member2_tree = Tree('member_reference', [Token('IDENTIFIER', 'Accessories')])
        set_tree = Tree('set_literal', [member1_tree, member2_tree])
        
        result = self.flattener.flatten_set_expression(set_tree)
        
        assert isinstance(result, FlattenedSet)
        assert result.operation_type == SetOperationType.MEMBERS
        assert 'Bikes' in result.members
        assert 'Accessories' in result.members
        assert not result.is_calculated
    
    def test_flatten_crossjoin_operation(self):
        """Test flattening CrossJoin operations."""
        # Create CrossJoin function call
        set1_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        ])
        set2_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', '2023')])
        ])
        
        args_tree = Tree('argument_list', [set1_tree, set2_tree])
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'CROSSJOIN'),
            args_tree
        ])
        
        result = self.flattener.flatten_set_expression(func_tree)
        
        assert result.operation_type == SetOperationType.CROSSJOIN
        assert 'Bikes' in result.members
        assert '2023' in result.members
    
    def test_flatten_union_operation(self):
        """Test flattening Union operations."""
        # Create Union function call
        set1_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        ])
        set2_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Accessories')])
        ])
        
        args_tree = Tree('argument_list', [set1_tree, set2_tree])
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'UNION'),
            args_tree
        ])
        
        result = self.flattener.flatten_set_expression(func_tree)
        
        assert result.operation_type == SetOperationType.UNION
        assert 'Bikes' in result.members
        assert 'Accessories' in result.members
    
    def test_flatten_intersect_operation(self):
        """Test flattening Intersect operations."""
        # Create overlapping sets for intersection
        set1_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Bikes')]),
            Tree('member_reference', [Token('IDENTIFIER', 'Cars')])
        ])
        set2_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Bikes')]),
            Tree('member_reference', [Token('IDENTIFIER', 'Boats')])
        ])
        
        args_tree = Tree('argument_list', [set1_tree, set2_tree])
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'INTERSECT'),
            args_tree
        ])
        
        result = self.flattener.flatten_set_expression(func_tree)
        
        assert result.operation_type == SetOperationType.INTERSECT
        assert 'Bikes' in result.members  # Common member
        assert 'Cars' not in result.members  # Should be excluded
        assert 'Boats' not in result.members  # Should be excluded
    
    def test_flatten_except_operation(self):
        """Test flattening Except operations."""
        # Create sets for except operation
        set1_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Bikes')]),
            Tree('member_reference', [Token('IDENTIFIER', 'Cars')])
        ])
        set2_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        ])
        
        args_tree = Tree('argument_list', [set1_tree, set2_tree])
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'EXCEPT'),
            args_tree
        ])
        
        result = self.flattener.flatten_set_expression(func_tree)
        
        assert result.operation_type == SetOperationType.EXCEPT
        assert 'Cars' in result.members  # Should remain
        assert 'Bikes' not in result.members  # Should be removed
    
    def test_flatten_filter_operation(self):
        """Test flattening Filter operations."""
        # Create Filter function call
        base_set_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Bikes')]),
            Tree('member_reference', [Token('IDENTIFIER', 'Accessories')])
        ])
        filter_expr_tree = Tree('expression', [Token('CONDITION', 'Sales > 1000')])
        
        args_tree = Tree('argument_list', [base_set_tree, filter_expr_tree])
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'FILTER'),
            args_tree
        ])
        
        result = self.flattener.flatten_set_expression(func_tree)
        
        assert result.operation_type == SetOperationType.FILTER
        assert result.is_calculated  # Filter results can't be statically determined
        assert len(result.filters_applied) > 0
        assert 'Bikes' in result.members  # Base members
        assert 'Accessories' in result.members
    
    def test_flatten_topcount_operation(self):
        """Test flattening TopCount operations."""
        # Create TopCount function call
        base_set_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'Product1')]),
            Tree('member_reference', [Token('IDENTIFIER', 'Product2')])
        ])
        count_tree = Tree('expression', [Token('NUMBER', '5')])
        measure_tree = Tree('expression', [Token('MEASURE', 'Sales')])
        
        args_tree = Tree('argument_list', [base_set_tree, count_tree, measure_tree])
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'TOPCOUNT'),
            args_tree
        ])
        
        result = self.flattener.flatten_set_expression(func_tree)
        
        assert result.operation_type == SetOperationType.TOPCOUNT
        assert result.is_calculated
        assert 'Product1' in result.members
        assert 'Product2' in result.members
    
    def test_flatten_hierarchy_members(self):
        """Test flattening hierarchy.MEMBERS expressions."""
        # Create hierarchy.MEMBERS expression
        hierarchy_tree = Tree('hierarchy_members', [
            Token('IDENTIFIER', 'Product'),
            Token('OPERATOR', '.MEMBERS')
        ])
        
        result = self.flattener.flatten_set_expression(hierarchy_tree)
        
        assert result.operation_type == SetOperationType.MEMBERS
        assert 'Product' in result.members
    
    def test_flatten_hierarchy_children(self):
        """Test flattening hierarchy.CHILDREN expressions."""
        # Create hierarchy.CHILDREN expression
        hierarchy_tree = Tree('hierarchy_members', [
            Token('IDENTIFIER', 'Product.Category'),
            Token('OPERATOR', '.CHILDREN')
        ])
        
        result = self.flattener.flatten_set_expression(hierarchy_tree)
        
        assert result.operation_type == SetOperationType.CHILDREN
        assert 'Product.Category' in result.members
    
    def test_can_flatten_to_simple_list(self):
        """Test checking if expressions can be flattened to simple lists."""
        # Simple member list - can flatten
        member_tree = Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        set_tree = Tree('set_literal', [member_tree])
        assert self.flattener.can_flatten_to_simple_list(set_tree)
        
        # Filter operation - cannot flatten to simple list
        base_set_tree = Tree('set_literal', [member_tree])
        filter_expr = Tree('expression', [Token('CONDITION', 'Sales > 1000')])
        args_tree = Tree('argument_list', [base_set_tree, filter_expr])
        filter_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'FILTER'),
            args_tree
        ])
        assert not self.flattener.can_flatten_to_simple_list(filter_tree)
    
    def test_extract_member_selection_all_members(self):
        """Test extracting MemberSelection for all members."""
        # Create .MEMBERS expression
        hierarchy_tree = Tree('hierarchy_members', [
            Token('IDENTIFIER', 'Product'),
            Token('OPERATOR', '.MEMBERS')
        ])
        
        result = self.flattener.extract_member_selection(hierarchy_tree)
        
        assert result.selection_type == MemberSelectionType.ALL
    
    def test_extract_member_selection_children(self):
        """Test extracting MemberSelection for children."""
        # Create .CHILDREN expression
        hierarchy_tree = Tree('hierarchy_members', [
            Token('IDENTIFIER', 'Product.Category'),
            Token('OPERATOR', '.CHILDREN')
        ])
        
        result = self.flattener.extract_member_selection(hierarchy_tree)
        
        assert result.selection_type == MemberSelectionType.CHILDREN
        assert result.parent_member == 'Product.Category'
    
    def test_extract_member_selection_specific_members(self):
        """Test extracting MemberSelection for specific members."""
        # Create set literal with specific members
        member1_tree = Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        member2_tree = Tree('member_reference', [Token('IDENTIFIER', 'Accessories')])
        set_tree = Tree('set_literal', [member1_tree, member2_tree])
        
        result = self.flattener.extract_member_selection(set_tree)
        
        assert result.selection_type == MemberSelectionType.SPECIFIC
        assert 'Bikes' in result.specific_members
        assert 'Accessories' in result.specific_members
    
    def test_binary_set_operation_parsing(self):
        """Test parsing binary set operations."""
        # Create binary union: Set1 UNION Set2
        set1_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'A')])
        ])
        set2_tree = Tree('set_literal', [
            Tree('member_reference', [Token('IDENTIFIER', 'B')])
        ])
        
        binary_tree = Tree('binary_set_operation', [
            set1_tree,
            Token('OPERATOR', 'UNION'),
            set2_tree
        ])
        
        result = self.flattener.flatten_set_expression(binary_tree)
        
        assert result.operation_type == SetOperationType.UNION
        assert 'A' in result.members
        assert 'B' in result.members


class TestSetExpression:
    """Test SetExpression data class."""
    
    def test_set_expression_creation(self):
        """Test creating SetExpression."""
        expr = SetExpression(
            expression_type=SetOperationType.UNION,
            operands=['Set1', 'Set2']
        )
        
        assert expr.expression_type == SetOperationType.UNION
        assert len(expr.operands) == 2
        assert expr.function_args == []  # Default value
    
    def test_set_expression_with_function_args(self):
        """Test SetExpression with function arguments."""
        expr = SetExpression(
            expression_type=SetOperationType.FILTER,
            operands=['BaseSet'],
            function_args=['Sales > 1000', 'ASC']
        )
        
        assert expr.expression_type == SetOperationType.FILTER
        assert len(expr.operands) == 1
        assert len(expr.function_args) == 2


class TestFlattenedSet:
    """Test FlattenedSet data class."""
    
    def test_flattened_set_creation(self):
        """Test creating FlattenedSet."""
        flattened = FlattenedSet(
            members=['A', 'B', 'C'],
            operation_type=SetOperationType.UNION
        )
        
        assert len(flattened.members) == 3
        assert flattened.operation_type == SetOperationType.UNION
        assert not flattened.is_calculated  # Default value
        assert flattened.filters_applied == []  # Default value
        assert not flattened.ordering_applied  # Default value
        assert flattened.limit_applied is None  # Default value
    
    def test_flattened_set_with_metadata(self):
        """Test FlattenedSet with additional metadata."""
        flattened = FlattenedSet(
            members=['Product1', 'Product2'],
            operation_type=SetOperationType.TOPCOUNT,
            is_calculated=True,
            filters_applied=['Sales > 1000'],
            ordering_applied=True,
            limit_applied=10
        )
        
        assert flattened.is_calculated
        assert len(flattened.filters_applied) == 1
        assert flattened.ordering_applied
        assert flattened.limit_applied == 10


class TestSetFlattenerHelpers:
    """Test helper methods in SetFlattener."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.flattener = SetFlattener()
    
    def test_is_set_expression(self):
        """Test identifying set expressions."""
        # Valid set expression types
        valid_types = [
            'function_call', 'set_literal', 'member_reference',
            'hierarchy_members', 'binary_set_operation'
        ]
        
        for node_type in valid_types:
            tree = Tree(node_type, [])
            assert self.flattener._is_set_expression(tree)
        
        # Invalid type
        invalid_tree = Tree('other_node', [])
        assert not self.flattener._is_set_expression(invalid_tree)
        
        # Non-tree
        assert not self.flattener._is_set_expression("not a tree")
    
    def test_extract_function_name(self):
        """Test extracting function names."""
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'CROSSJOIN'),
            Tree('argument_list', [])
        ])
        
        name = self.flattener._extract_function_name(func_tree)
        assert name == 'CROSSJOIN'
    
    def test_extract_function_arguments(self):
        """Test extracting function arguments."""
        arg1_tree = Tree('argument', [Token('VALUE', 'arg1')])
        arg2_tree = Tree('argument', [Token('VALUE', 'arg2')])
        args_tree = Tree('argument_list', [arg1_tree, arg2_tree])
        
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'TEST'),
            args_tree
        ])
        
        args = self.flattener._extract_function_arguments(func_tree)
        assert len(args) == 2
    
    def test_extract_member_name(self):
        """Test extracting member names."""
        # Direct token
        member_tree = Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        name = self.flattener._extract_member_name(member_tree)
        assert name == 'Bikes'
        
        # Through identifier tree
        id_tree = Tree('identifier', [Token('VALUE', 'Accessories')])
        member_tree = Tree('member_reference', [id_tree])
        name = self.flattener._extract_member_name(member_tree)
        assert name == 'Accessories'
    
    def test_extract_hierarchy_name(self):
        """Test extracting hierarchy names."""
        hierarchy_tree = Tree('hierarchy_reference', [Token('IDENTIFIER', 'Product')])
        name = self.flattener._extract_hierarchy_name(hierarchy_tree)
        assert name == 'Product'
    
    def test_is_simple_flattening(self):
        """Test checking for simple flattening capability."""
        # Simple operations
        simple_expr = SetExpression(
            expression_type=SetOperationType.MEMBERS,
            operands=['Member1', 'Member2']
        )
        assert self.flattener._is_simple_flattening(simple_expr)
        
        union_expr = SetExpression(
            expression_type=SetOperationType.UNION,
            operands=[simple_expr, simple_expr]
        )
        assert self.flattener._is_simple_flattening(union_expr)
        
        # Complex operations
        filter_expr = SetExpression(
            expression_type=SetOperationType.FILTER,
            operands=['BaseSet'],
            function_args=['Sales > 1000']
        )
        assert not self.flattener._is_simple_flattening(filter_expr)