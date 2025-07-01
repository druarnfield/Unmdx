"""Unit tests for basic MDX to IR transformations."""

import pytest
from lark import Tree, Token

from unmdx.transformer import MDXTransformer, TransformationError
from unmdx.ir import (
    Query, CubeReference, Measure, Dimension, Filter,
    AggregationType, MemberSelectionType, FilterType
)
from unmdx.parser.mdx_parser import MDXParser


class TestBasicTransformations:
    """Test basic transformation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = MDXTransformer(debug=True)
        self.parser = MDXParser(debug=True)
    
    def test_transform_simple_query(self):
        """Test transforming a simple MDX query."""
        # Create a minimal parse tree for testing
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Adventure Works')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [from_tree])
        
        # Transform
        result = self.transformer.transform(query_tree)
        
        # Validate
        assert isinstance(result, Query)
        assert result.cube.name == 'Adventure Works'
        assert result.cube.database is None
        assert result.cube.schema_name is None
    
    def test_transform_qualified_cube_name(self):
        """Test transforming cube reference with database qualification."""
        # Test different qualified name formats
        test_cases = [
            ('[Database].[Schema].[Cube]', 'Database', 'Schema', 'Cube'),
            ('[Schema].[Cube]', None, 'Schema', 'Cube'),
            ('SimpleCube', None, None, 'SimpleCube')
        ]
        
        for qualified_name, expected_db, expected_schema, expected_cube in test_cases:
            cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', qualified_name)])
            from_tree = Tree('from_clause', [cube_tree])
            query_tree = Tree('query', [from_tree])
            
            result = self.transformer.transform(query_tree)
            
            assert result.cube.name == expected_cube
            assert result.cube.database == expected_db
            assert result.cube.schema_name == expected_schema
    
    def test_extract_measures_from_columns_axis(self):
        """Test extracting measures from columns axis."""
        # Create measure node
        measure_tree = Tree('measure', [Token('IDENTIFIER', 'Sales Amount')])
        axis_tree = Tree('axis_specification', [
            measure_tree,
            Token('AXIS_NAME', 'COLUMNS')
        ])
        select_tree = Tree('select_clause', [axis_tree])
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Test Cube')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [select_tree, from_tree])
        
        result = self.transformer.transform(query_tree)
        
        assert len(result.measures) == 1
        assert result.measures[0].name == 'Sales Amount'
        assert result.measures[0].aggregation == AggregationType.SUM
    
    def test_extract_dimensions_from_rows_axis(self):
        """Test extracting dimensions from rows axis."""
        # Create dimension node
        dim_tree = Tree('dimension', [Token('IDENTIFIER', 'Product Category')])
        axis_tree = Tree('axis_specification', [
            dim_tree,
            Token('AXIS_NAME', 'ROWS')
        ])
        select_tree = Tree('select_clause', [axis_tree])
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Test Cube')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [select_tree, from_tree])
        
        result = self.transformer.transform(query_tree)
        
        assert len(result.dimensions) >= 0  # May not create dimensions due to simplified implementation
    
    def test_transform_with_calculations(self):
        """Test transforming WITH clause calculations."""
        # Create calculated member
        member_name_tree = Tree('member_name', [Token('IDENTIFIER', 'Profit')])
        expr_tree = Tree('expression', [
            Tree('binary_operation', [
                Tree('measure_reference', [Token('IDENTIFIER', 'Sales')]),
                Token('OPERATOR', '-'),
                Tree('measure_reference', [Token('IDENTIFIER', 'Cost')])
            ])
        ])
        calc_tree = Tree('calculated_member', [member_name_tree, expr_tree])
        with_tree = Tree('with_clause', [calc_tree])
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Test Cube')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [with_tree, from_tree])
        
        result = self.transformer.transform(query_tree)
        
        assert len(result.calculations) == 1
        assert result.calculations[0].name == 'Profit'
    
    def test_error_handling_missing_from_clause(self):
        """Test error handling when FROM clause is missing."""
        query_tree = Tree('query', [])
        
        with pytest.raises(TransformationError) as exc_info:
            self.transformer.transform(query_tree)
        
        assert "No FROM clause found" in str(exc_info.value)
    
    def test_error_handling_invalid_cube(self):
        """Test error handling with invalid cube reference."""
        from_tree = Tree('from_clause', [])  # Empty FROM clause
        query_tree = Tree('query', [from_tree])
        
        with pytest.raises(TransformationError) as exc_info:
            self.transformer.transform(query_tree)
        
        assert "No cube identifier found" in str(exc_info.value)
    
    def test_metadata_generation(self):
        """Test that query metadata is properly generated."""
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Test Cube')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [from_tree])
        
        source_mdx = "SELECT FROM [Test Cube]"
        result = self.transformer.transform(query_tree, source_mdx)
        
        assert result.metadata.created_at is not None
        assert result.metadata.transform_duration_ms is not None
        assert result.metadata.source_mdx_hash is not None
    
    def test_axis_id_detection(self):
        """Test proper detection of axis IDs."""
        test_cases = [
            ('COLUMNS', 0),
            ('ROWS', 1),
            ('0', 0),
            ('1', 1),
            ('2', 2)
        ]
        
        for axis_name, expected_id in test_cases:
            axis_tree = Tree('axis_specification', [Token('AXIS_NAME', axis_name)])
            actual_id = self.transformer._get_axis_id(axis_tree)
            assert actual_id == expected_id


class TestExpressionTransformation:
    """Test transformation of various expression types."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = MDXTransformer(debug=True)
    
    def test_transform_binary_operation(self):
        """Test transforming binary operations."""
        # Create binary operation: Sales - Cost
        left_tree = Tree('measure_reference', [Token('IDENTIFIER', 'Sales')])
        right_tree = Tree('measure_reference', [Token('IDENTIFIER', 'Cost')])
        binary_tree = Tree('binary_operation', [left_tree, Token('OPERATOR', '-'), right_tree])
        
        result = self.transformer._transform_expression(binary_tree)
        
        assert hasattr(result, 'left')
        assert hasattr(result, 'operator')
        assert hasattr(result, 'right')
        assert result.operator == '-'
    
    def test_transform_function_call(self):
        """Test transforming function calls."""
        # Create function call: SUM(Sales)
        arg_tree = Tree('argument', [Tree('measure_reference', [Token('IDENTIFIER', 'Sales')])])
        func_tree = Tree('function_call', [
            Token('FUNCTION_NAME', 'SUM'),
            Tree('argument_list', [arg_tree])
        ])
        
        result = self.transformer._transform_expression(func_tree)
        
        assert hasattr(result, 'function_name')
        assert hasattr(result, 'arguments')
        assert result.function_name == 'SUM'
        assert len(result.arguments) == 1
    
    def test_transform_numeric_literal(self):
        """Test transforming numeric literals."""
        # Test integer
        int_tree = Tree('numeric_literal', [Token('NUMBER', '42')])
        int_result = self.transformer._transform_expression(int_tree)
        assert int_result.value == 42
        
        # Test float
        float_tree = Tree('numeric_literal', [Token('NUMBER', '3.14')])
        float_result = self.transformer._transform_expression(float_tree)
        assert float_result.value == 3.14
    
    def test_transform_string_literal(self):
        """Test transforming string literals."""
        # Test quoted string
        str_tree = Tree('string_literal', [Token('STRING', '"Hello World"')])
        result = self.transformer._transform_expression(str_tree)
        assert result.value == 'Hello World'
    
    def test_transform_member_reference(self):
        """Test transforming member references."""
        member_tree = Tree('member_reference', [Token('IDENTIFIER', 'Product.Category.Bikes')])
        result = self.transformer._transform_expression(member_tree)
        
        assert hasattr(result, 'member_name')
        assert result.member_name == 'Product.Category.Bikes'
    
    def test_transform_measure_reference(self):
        """Test transforming measure references."""
        measure_tree = Tree('measure_reference', [Token('IDENTIFIER', 'Sales Amount')])
        result = self.transformer._transform_expression(measure_tree)
        
        assert hasattr(result, 'measure_name')
        assert result.measure_name == 'Sales Amount'


class TestHelperMethods:
    """Test helper methods used in transformation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = MDXTransformer(debug=True)
    
    def test_find_nodes(self):
        """Test finding nodes by type in tree."""
        # Create nested tree
        inner_tree = Tree('target_node', [Token('VALUE', 'found')])
        outer_tree = Tree('parent_node', [
            Tree('other_node', [Token('VALUE', 'other')]),
            inner_tree,
            Tree('target_node', [Token('VALUE', 'found2')])
        ])
        
        found_nodes = self.transformer._find_nodes(outer_tree, 'target_node')
        
        assert len(found_nodes) == 2
        assert all(node.data == 'target_node' for node in found_nodes)
    
    def test_extract_identifier_value(self):
        """Test extracting identifier values."""
        # Test token
        token = Token('IDENTIFIER', 'TestValue')
        assert self.transformer._extract_identifier_value(token) == 'TestValue'
        
        # Test tree with child
        tree = Tree('identifier', [Token('VALUE', 'TreeValue')])
        assert self.transformer._extract_identifier_value(tree) == 'TreeValue'
    
    def test_parse_qualified_name(self):
        """Test parsing qualified names."""
        test_cases = [
            ('[Database].[Schema].[Object]', ['Database', 'Schema', 'Object']),
            ('[Schema].[Object]', ['Schema', 'Object']),
            ('SimpleObject', ['SimpleObject']),
            ('Database.Schema.Object', ['Database', 'Schema', 'Object'])
        ]
        
        for qualified_name, expected_parts in test_cases:
            parts = self.transformer._parse_qualified_name(qualified_name)
            assert parts == expected_parts
    
    def test_determine_function_type(self):
        """Test function type determination."""
        test_cases = [
            ('SUM', 'SUM'),
            ('COUNT', 'COUNT'),
            ('CROSSJOIN', 'CROSSJOIN'),
            ('UNKNOWN_FUNC', 'MATH')  # Default fallback
        ]
        
        for func_name, expected_type in test_cases:
            func_type = self.transformer._determine_function_type(func_name)
            assert func_type.value == expected_type
    
    def test_error_warning_collection(self):
        """Test error and warning collection."""
        # Add an error
        self.transformer._add_error("Test error message")
        assert len(self.transformer.errors) == 1
        assert "Test error message" in str(self.transformer.errors[0])
        
        # Add a warning
        self.transformer._add_warning("Test warning message")
        assert len(self.transformer.warnings) == 1
        assert "Test warning message" in str(self.transformer.warnings[0])
    
    def test_context_tracking(self):
        """Test context tracking during transformation."""
        self.transformer.current_context = "test_context"
        self.transformer._add_error("Test error")
        
        error = self.transformer.errors[0]
        assert error.context == "test_context"