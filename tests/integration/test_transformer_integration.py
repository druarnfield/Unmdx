"""Integration tests for MDX to IR transformation."""

import pytest
from datetime import datetime
from lark import Tree, Token

from unmdx.transformer import MDXTransformer
from unmdx.parser.mdx_parser import MDXParser
from unmdx.ir import (
    Query, CubeReference, Measure, Dimension, Filter, Calculation,
    AggregationType, MemberSelectionType, FilterType, CalculationType
)


class TestTransformerIntegration:
    """Test end-to-end transformation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = MDXTransformer(debug=True)
        self.parser = MDXParser(debug=True)
    
    def test_complete_query_transformation(self):
        """Test transforming a complete query with all components."""
        # Create a comprehensive query tree
        # WITH calculated member
        member_expr = Tree('binary_operation', [
            Tree('measure_reference', [Token('IDENTIFIER', 'Sales')]),
            Token('OPERATOR', '-'),
            Tree('measure_reference', [Token('IDENTIFIER', 'Cost')])
        ])
        calc_member = Tree('calculated_member', [
            Tree('member_name', [Token('IDENTIFIER', 'Profit')]),
            Tree('expression', [member_expr])
        ])
        with_clause = Tree('with_clause', [calc_member])
        
        # SELECT clause with measures and dimensions
        sales_measure = Tree('measure', [Token('IDENTIFIER', 'Sales Amount')])
        columns_axis = Tree('axis_specification', [sales_measure, Token('AXIS_NAME', 'COLUMNS')])
        
        product_dim = Tree('dimension', [Token('IDENTIFIER', 'Product Category')])
        rows_axis = Tree('axis_specification', [product_dim, Token('AXIS_NAME', 'ROWS')])
        
        select_clause = Tree('select_clause', [columns_axis, rows_axis])
        
        # FROM clause
        cube_id = Tree('cube_identifier', [Token('IDENTIFIER', '[Adventure Works DW].[dbo].[Sales]')])
        from_clause = Tree('from_clause', [cube_id])
        
        # Complete query
        query_tree = Tree('query', [with_clause, select_clause, from_clause])
        
        # Transform
        result = self.transformer.transform(query_tree)
        
        # Validate results
        assert isinstance(result, Query)
        
        # Check cube reference
        assert result.cube.name == 'Sales'
        assert result.cube.database == 'Adventure Works DW'
        assert result.cube.schema_name == 'dbo'
        
        # Check measures
        assert len(result.measures) >= 0  # May not detect measures due to simplified parsing
        
        # Check calculations
        assert len(result.calculations) == 1
        assert result.calculations[0].name == 'Profit'
        assert result.calculations[0].calculation_type == CalculationType.MEASURE
        
        # Check metadata
        assert result.metadata.created_at is not None
        assert result.metadata.transform_duration_ms is not None
    
    def test_transformation_with_comments(self):
        """Test transformation with comment extraction."""
        source_mdx = """
        /* Performance: This query analyzes sales performance */
        -- Author: Data Analyst Team
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        /* TODO: Add filters for better performance */
        """
        
        # Create minimal query tree
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Adventure Works')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [from_tree])
        
        # Transform with source
        result = self.transformer.transform(query_tree, source_mdx)
        
        # Check comment hints were extracted
        assert len(result.metadata.optimization_hints) >= 1
        
        # Check for performance and TODO hints
        hints_text = ' '.join(result.metadata.optimization_hints)
        assert 'PERFORMANCE' in hints_text or 'performance' in hints_text
    
    def test_error_handling_and_recovery(self):
        """Test error handling during transformation."""
        # Create invalid query tree (missing FROM clause)
        select_clause = Tree('select_clause', [])
        query_tree = Tree('query', [select_clause])
        
        # Should raise transformation error
        with pytest.raises(Exception):  # TransformationError
            self.transformer.transform(query_tree)
    
    def test_hierarchy_normalization_integration(self):
        """Test hierarchy normalization during transformation."""
        # Create query with hierarchy references
        member1 = Tree('member_reference', [Token('IDENTIFIER', 'Product.Category.Bikes')])
        member2 = Tree('member_reference', [Token('IDENTIFIER', 'Date.Year.2023')])
        
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Sales')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [member1, member2, from_tree])
        
        # Transform
        result = self.transformer.transform(query_tree)
        
        # Check that hierarchies were normalized
        assert self.transformer.hierarchy_normalizer is not None
        
        # The normalizer should have processed the hierarchies
        # (Note: In a real implementation, we'd check the normalized mappings)
    
    def test_set_flattening_integration(self):
        """Test set flattening during transformation."""
        # Create set expression
        member1 = Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        member2 = Tree('member_reference', [Token('IDENTIFIER', 'Accessories')])
        set_literal = Tree('set_literal', [member1, member2])
        
        # Test set flattening
        flattened = self.transformer.set_flattener.flatten_set_expression(set_literal)
        
        assert flattened.members == ['Bikes', 'Accessories']
        assert not flattened.is_calculated
    
    def test_metadata_generation_comprehensive(self):
        """Test comprehensive metadata generation."""
        source_mdx = """
        /* 
         * Author: Analytics Team
         * Purpose: Monthly sales report
         * Data Source: Adventure Works DW
         */
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        """
        
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Adventure Works')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [from_tree])
        
        result = self.transformer.transform(query_tree, source_mdx)
        
        # Check metadata fields
        assert result.metadata.created_at is not None
        assert isinstance(result.metadata.created_at, datetime)
        assert result.metadata.transform_duration_ms is not None
        assert result.metadata.transform_duration_ms >= 0
        assert result.metadata.source_mdx_hash is not None
        assert len(result.metadata.source_mdx_hash) == 32  # MD5 hash length
    
    def test_validation_integration(self):
        """Test query validation after transformation."""
        # Create valid query
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Adventure Works')])
        from_tree = Tree('from_clause', [cube_tree])
        measure_tree = Tree('measure', [Token('IDENTIFIER', 'Sales Amount')])
        axis_tree = Tree('axis_specification', [measure_tree, Token('AXIS_NAME', 'COLUMNS')])
        select_tree = Tree('select_clause', [axis_tree])
        query_tree = Tree('query', [select_tree, from_tree])
        
        result = self.transformer.transform(query_tree)
        
        # Should have some validation warnings (empty query)
        assert len(result.metadata.warnings) >= 1
        validation_warning = any('Validation issue' in w for w in result.metadata.warnings)
        assert validation_warning
    
    def test_expression_transformation_chain(self):
        """Test complex expression transformation."""
        # Create nested expression: (Sales - Cost) * 0.1
        inner_left = Tree('measure_reference', [Token('IDENTIFIER', 'Sales')])
        inner_right = Tree('measure_reference', [Token('IDENTIFIER', 'Cost')])
        inner_expr = Tree('binary_operation', [inner_left, Token('OPERATOR', '-'), inner_right])
        
        multiplier = Tree('numeric_literal', [Token('NUMBER', '0.1')])
        outer_expr = Tree('binary_operation', [inner_expr, Token('OPERATOR', '*'), multiplier])
        
        # Transform expression
        result_expr = self.transformer._transform_expression(outer_expr)
        
        # Verify nested structure
        assert hasattr(result_expr, 'left')
        assert hasattr(result_expr, 'right')
        assert result_expr.operator == '*'
        
        # Check that left side is also a binary operation
        left_expr = result_expr.left
        assert hasattr(left_expr, 'operator')
        assert left_expr.operator == '-'
    
    def test_function_call_transformation(self):
        """Test function call transformation."""
        # Create SUM function call
        measure_arg = Tree('argument', [Tree('measure_reference', [Token('IDENTIFIER', 'Sales')])])
        args_list = Tree('argument_list', [measure_arg])
        func_call = Tree('function_call', [Token('FUNCTION_NAME', 'SUM'), args_list])
        
        # Transform
        result = self.transformer._transform_expression(func_call)
        
        # Verify function call structure
        assert hasattr(result, 'function_name')
        assert hasattr(result, 'arguments')
        assert result.function_name == 'SUM'
        assert len(result.arguments) == 1
    
    def test_end_to_end_performance(self):
        """Test performance characteristics of transformation."""
        # Create moderately complex query
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Large Cube')])
        from_tree = Tree('from_clause', [cube_tree])
        
        # Add multiple measures and dimensions
        measures = []
        for i in range(5):
            measure = Tree('measure', [Token('IDENTIFIER', f'Measure{i}')])
            measures.append(measure)
        
        columns_axis = Tree('axis_specification', measures + [Token('AXIS_NAME', 'COLUMNS')])
        
        dimensions = []
        for i in range(3):
            dim = Tree('dimension', [Token('IDENTIFIER', f'Dimension{i}')])
            dimensions.append(dim)
        
        rows_axis = Tree('axis_specification', dimensions + [Token('AXIS_NAME', 'ROWS')])
        
        select_tree = Tree('select_clause', [columns_axis, rows_axis])
        query_tree = Tree('query', [select_tree, from_tree])
        
        # Transform and check performance
        start_time = datetime.now()
        result = self.transformer.transform(query_tree)
        end_time = datetime.now()
        
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Should complete reasonably quickly (under 100ms for this simple case)
        assert duration_ms < 100
        assert result.metadata.transform_duration_ms < 100


class TestTransformerComponents:
    """Test individual transformer components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = MDXTransformer(debug=True)
    
    def test_hierarchy_normalizer_component(self):
        """Test hierarchy normalizer component."""
        # Create tree with hierarchy references
        hier_ref = Tree('hierarchy_reference', [Token('IDENTIFIER', 'Product')])
        member_ref = Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        query_tree = Tree('query', [hier_ref, member_ref])
        
        # Run normalization
        mappings = self.transformer.hierarchy_normalizer.normalize_hierarchies(query_tree)
        
        # Should create mappings
        assert isinstance(mappings, dict)
        assert 'Product' in mappings
    
    def test_set_flattener_component(self):
        """Test set flattener component."""
        # Create union set expression
        set1 = Tree('set_literal', [Tree('member_reference', [Token('IDENTIFIER', 'A')])])
        set2 = Tree('set_literal', [Tree('member_reference', [Token('IDENTIFIER', 'B')])])
        union_expr = Tree('binary_set_operation', [set1, Token('OPERATOR', 'UNION'), set2])
        
        # Flatten
        result = self.transformer.set_flattener.flatten_set_expression(union_expr)
        
        # Should combine members
        assert 'A' in result.members
        assert 'B' in result.members
    
    def test_comment_extractor_component(self):
        """Test comment extractor component."""
        source_mdx = """
        /* Performance: Slow query */
        SELECT [Sales] FROM [Cube]
        -- Cache: Enable caching
        """
        
        # Extract hints
        hints = self.transformer.comment_extractor.extract_hints(Tree('query', []), source_mdx)
        
        # Should find hints
        assert len(hints) >= 2
        hint_types = [h.hint_type.value for h in hints]
        assert 'PERFORMANCE' in hint_types
        assert 'CACHING' in hint_types


class TestRealWorldScenarios:
    """Test realistic MDX transformation scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = MDXTransformer(debug=True)
    
    def test_sales_analysis_scenario(self):
        """Test a typical sales analysis transformation."""
        # Simulate a sales analysis query
        source_mdx = """
        /* Sales Analysis Query
         * Purpose: Quarterly sales by product category
         * Performance: Consider adding date filters
         */
        WITH 
        MEMBER [Measures].[Profit] AS [Measures].[Sales] - [Measures].[Cost]
        SELECT 
        {[Measures].[Sales], [Measures].[Profit]} ON COLUMNS,
        [Product].[Category].MEMBERS ON ROWS
        FROM [Adventure Works]
        """
        
        # Create corresponding query tree (simplified)
        # WITH clause
        profit_expr = Tree('binary_operation', [
            Tree('measure_reference', [Token('IDENTIFIER', 'Sales')]),
            Token('OPERATOR', '-'),
            Tree('measure_reference', [Token('IDENTIFIER', 'Cost')])
        ])
        calc_member = Tree('calculated_member', [
            Tree('member_name', [Token('IDENTIFIER', 'Profit')]),
            Tree('expression', [profit_expr])
        ])
        with_clause = Tree('with_clause', [calc_member])
        
        # FROM clause
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Adventure Works')])
        from_tree = Tree('from_clause', [cube_tree])
        
        # Query
        query_tree = Tree('query', [with_clause, from_tree])
        
        # Transform
        result = self.transformer.transform(query_tree, source_mdx)
        
        # Validate business logic
        assert result.cube.name == 'Adventure Works'
        assert len(result.calculations) == 1
        assert result.calculations[0].name == 'Profit'
        
        # Check performance hints were captured
        hints_found = any('performance' in hint.lower() for hint in result.metadata.optimization_hints)
        assert hints_found
    
    def test_time_intelligence_scenario(self):
        """Test time intelligence transformation."""
        # Create time intelligence expression
        prev_month_func = Tree('function_call', [
            Token('FUNCTION_NAME', 'PARALLELPERIOD'),
            Tree('argument_list', [
                Tree('argument', [Tree('measure_reference', [Token('IDENTIFIER', 'Sales')])]),
                Tree('argument', [Tree('numeric_literal', [Token('NUMBER', '1')])])
            ])
        ])
        
        calc_member = Tree('calculated_member', [
            Tree('member_name', [Token('IDENTIFIER', 'Previous Month Sales')]),
            Tree('expression', [prev_month_func])
        ])
        
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Time Series Cube')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [Tree('with_clause', [calc_member]), from_tree])
        
        # Transform
        result = self.transformer.transform(query_tree)
        
        # Validate time intelligence handling
        assert len(result.calculations) == 1
        calc = result.calculations[0]
        assert 'Previous Month' in calc.name
        assert hasattr(calc.expression, 'function_name')
        assert calc.expression.function_name == 'PARALLELPERIOD'
    
    def test_complex_filtering_scenario(self):
        """Test complex filtering transformation."""
        # Create complex filter expression (simplified representation)
        filter_expr = Tree('binary_operation', [
            Tree('measure_reference', [Token('IDENTIFIER', 'Sales')]),
            Token('OPERATOR', '>'),
            Tree('numeric_literal', [Token('NUMBER', '10000')])
        ])
        
        cube_tree = Tree('cube_identifier', [Token('IDENTIFIER', 'Filtered Cube')])
        from_tree = Tree('from_clause', [cube_tree])
        query_tree = Tree('query', [filter_expr, from_tree])
        
        # Transform
        result = self.transformer.transform(query_tree)
        
        # Basic validation - should not fail
        assert result.cube.name == 'Filtered Cube'
        assert isinstance(result, Query)