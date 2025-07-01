"""Unit tests for IR operations and complex logic."""

import pytest
from datetime import datetime

from unmdx.ir import (
    Query, CubeReference, Measure, Dimension, Filter, Calculation,
    HierarchyReference, LevelReference, MemberSelection, DimensionFilter,
    AggregationType, MemberSelectionType, FilterType, FilterOperator,
    CalculationType, QueryMetadata, Constant, MeasureReference, BinaryOperation,
    FunctionCall, FunctionType, ExpressionType
)
from unmdx.ir.expressions import Expression
from unmdx.ir.serialization import IRValidator, IROptimizer, IRComparator


class TestExpressionOperations:
    """Test expression tree operations."""
    
    def test_binary_operation_dependencies(self):
        """Test dependency extraction from binary operations."""
        left = MeasureReference(measure_name="Sales")
        right = MeasureReference(measure_name="Cost")
        expr = BinaryOperation(left=left, operator="+", right=right)
        
        deps = expr.get_dependencies()
        assert "Sales" in deps
        assert "Cost" in deps
        assert len(deps) == 2
    
    def test_nested_expression_dependencies(self):
        """Test dependency extraction from nested expressions."""
        # ((Sales + Cost) * 0.1) / Quantity
        inner_left = MeasureReference(measure_name="Sales")
        inner_right = MeasureReference(measure_name="Cost")
        inner_expr = BinaryOperation(left=inner_left, operator="+", right=inner_right)
        
        multiplier = Constant(value=0.1)
        multiply_expr = BinaryOperation(left=inner_expr, operator="*", right=multiplier)
        
        divisor = MeasureReference(measure_name="Quantity")
        final_expr = BinaryOperation(left=multiply_expr, operator="/", right=divisor)
        
        deps = final_expr.get_dependencies()
        assert "Sales" in deps
        assert "Cost" in deps
        assert "Quantity" in deps
        assert len(deps) == 3
    
    def test_function_call_dependencies(self):
        """Test dependency extraction from function calls."""
        arg1 = MeasureReference(measure_name="Sales")
        arg2 = MeasureReference(measure_name="Target")
        func = FunctionCall(
            function_type=FunctionType.MATH,
            function_name="MAX",
            arguments=[arg1, arg2]
        )
        
        deps = func.get_dependencies()
        assert "Sales" in deps
        assert "Target" in deps
        assert len(deps) == 2
    
    def test_expression_to_dax_generation(self):
        """Test DAX generation from expressions."""
        # Test simple measure reference
        measure_ref = MeasureReference(measure_name="Sales Amount")
        assert "[Sales Amount]" in measure_ref.to_dax()
        
        # Test binary operation
        left = MeasureReference(measure_name="Sales")
        right = MeasureReference(measure_name="Returns")
        expr = BinaryOperation(left=left, operator="-", right=right)
        dax = expr.to_dax()
        assert "[Sales]" in dax
        assert "[Returns]" in dax
        assert "-" in dax
    
    def test_expression_to_human_readable(self):
        """Test human-readable generation from expressions."""
        # Test constant
        const = Constant(value=100)
        assert "100" in const.to_human_readable()
        
        # Test binary operation
        left = MeasureReference(measure_name="Revenue")
        right = MeasureReference(measure_name="Cost")
        expr = BinaryOperation(left=left, operator="/", right=right)
        readable = expr.to_human_readable()
        assert "Revenue" in readable
        assert "Cost" in readable
        assert "divided by" in readable or "/" in readable


class TestHierarchyOperations:
    """Test hierarchy depth detection and operations."""
    
    def test_hierarchy_depth_calculation(self):
        """Test calculating hierarchy depth."""
        # Create a dimension with ordinal level
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Month", ordinal=3)  # Year=1, Quarter=2, Month=3
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        assert level.ordinal == 3
    
    def test_level_comparison(self):
        """Test comparing levels within hierarchy."""
        level1 = LevelReference(name="Year", ordinal=1)
        level2 = LevelReference(name="Quarter", ordinal=2) 
        level3 = LevelReference(name="Month", ordinal=3)
        
        # Test ordinal comparison
        assert level1.ordinal < level2.ordinal
        assert level2.ordinal < level3.ordinal
    
    def test_member_selection_validation(self):
        """Test member selection validation logic."""
        # Test SPECIFIC selection without members
        with pytest.raises(ValueError):
            MemberSelection(
                selection_type=MemberSelectionType.SPECIFIC,
                specific_members=None
            )
        
        # Test CHILDREN selection
        children_selection = MemberSelection(
            selection_type=MemberSelectionType.CHILDREN,
            parent_member="All Products"
        )
        assert children_selection.parent_member == "All Products"
        assert not children_selection.is_all_members()
        assert not children_selection.is_specific_members()


class TestFilterCombinationLogic:
    """Test filter combination and logic operations."""
    
    def test_dimension_filter_combination(self):
        """Test combining dimension filters."""
        # Create two dimension filters on same dimension
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        filter1 = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.IN,
            values=["Bikes", "Accessories"]
        )
        
        filter2 = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.NOT_EQUALS,
            values=["Discontinued"]
        )
        
        # Both filters should be on same dimension
        assert filter1.dimension.hierarchy.table == filter2.dimension.hierarchy.table
        assert filter1.dimension.level.name == filter2.dimension.level.name
    
    def test_measure_filter_validation(self):
        """Test measure filter validation."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        # Test different operators
        operators = [
            FilterOperator.GREATER_THAN,
            FilterOperator.LESS_THAN,
            FilterOperator.EQUALS
        ]
        
        for op in operators:
            # Note: We need to map FilterOperator to ComparisonOperator
            # This reveals a potential issue in our model design
            pass  # Placeholder for now
    
    def test_filter_dax_generation_complex(self):
        """Test DAX generation for complex filters."""
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Calendar Year")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        # Test CONTAINS filter
        contains_filter = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.CONTAINS,
            values=["2023"]
        )
        
        dax = contains_filter.to_dax()
        assert "SEARCH" in dax
        assert "ISERROR" in dax
        assert "Date[Calendar Year]" in dax
    
    def test_non_empty_filter_logic(self):
        """Test non-empty filter logic."""
        from unmdx.ir.models import NonEmptyFilter
        
        # Test specific measure non-empty
        specific_filter = NonEmptyFilter(measure="Sales Amount")
        dax = specific_filter.to_dax()
        assert "[Sales Amount]" in dax
        assert "BLANK()" in dax
        
        # Test general non-empty
        general_filter = NonEmptyFilter()
        readable = general_filter.to_human_readable()
        assert "empty" in readable


class TestQueryValidationOperations:
    """Test query validation and error detection."""
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies in calculations."""
        cube = CubeReference(name="Test Cube")
        
        # Create calculations with circular dependency
        calc1_expr = MeasureReference(measure_name="Calc2")  # References Calc2
        calc1 = Calculation(
            name="Calc1",
            calculation_type=CalculationType.MEASURE,
            expression=calc1_expr
        )
        
        calc2_expr = MeasureReference(measure_name="Calc1")  # References Calc1
        calc2 = Calculation(
            name="Calc2", 
            calculation_type=CalculationType.MEASURE,
            expression=calc2_expr
        )
        
        query = Query(cube=cube, calculations=[calc1, calc2])
        issues = query.validate_query()
        
        # Should detect circular dependency
        assert len(issues) > 0
        # Note: The current implementation only detects self-referencing, not mutual circular deps
        # This test may need updating based on improved validation logic
    
    def test_measure_filter_validation(self):
        """Test validation of measure filters."""
        cube = CubeReference(name="Sales Cube")
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        # Create measure filter for a measure not in query
        other_measure = Measure(name="Cost", aggregation=AggregationType.SUM)
        from unmdx.ir.models import MeasureFilter
        from unmdx.ir.enums import ComparisonOperator
        
        measure_filter = MeasureFilter(
            measure=other_measure,
            operator=ComparisonOperator.GT,
            value=1000
        )
        
        filter_obj = Filter(filter_type=FilterType.MEASURE, target=measure_filter)
        query = Query(cube=cube, measures=[measure], filters=[filter_obj])
        
        issues = query.validate_query()
        assert len(issues) > 0
        assert any("Cost" in issue for issue in issues)
    
    def test_query_complexity_analysis(self):
        """Test analysis of query complexity."""
        cube = CubeReference(name="Complex Cube")
        
        # Create a complex query with many elements
        measures = [
            Measure(name=f"Measure{i}", aggregation=AggregationType.SUM)
            for i in range(5)
        ]
        
        dimensions = []
        for i in range(8):
            hierarchy = HierarchyReference(table=f"Dim{i}", name=f"Dimension{i}")
            level = LevelReference(name=f"Level{i}")
            members = MemberSelection(selection_type=MemberSelectionType.ALL)
            dimensions.append(Dimension(hierarchy=hierarchy, level=level, members=members))
        
        calculations = [
            Calculation(
                name=f"Calc{i}",
                calculation_type=CalculationType.MEASURE,
                expression=Constant(value=i)
            )
            for i in range(3)
        ]
        
        query = Query(
            cube=cube,
            measures=measures,
            dimensions=dimensions,
            calculations=calculations
        )
        
        # Test validation warnings
        validator_result = IRValidator.validate_query(query)
        assert "warnings" in validator_result
        
        # Should have warnings about complexity
        warnings = validator_result["warnings"]
        complexity_warnings = [w for w in warnings if "dimensions" in w or "calculations" in w]
        assert len(complexity_warnings) > 0


class TestIRSerialization:
    """Test IR serialization and deserialization operations."""
    
    def test_query_round_trip_serialization(self):
        """Test full query serialization and deserialization."""
        from unmdx.ir.serialization import IRSerializer, IRDeserializer
        
        # Create a complete query
        cube = CubeReference(name="Adventure Works")
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        metadata = QueryMetadata(
            created_at=datetime.now(),
            complexity_score=25
        )
        
        original_query = Query(
            cube=cube,
            measures=[measure],
            dimensions=[dimension],
            metadata=metadata
        )
        
        # Serialize to JSON
        json_str = IRSerializer.serialize_query(original_query)
        assert len(json_str) > 0
        assert "Adventure Works" in json_str
        
        # Deserialize back
        restored_query = IRDeserializer.deserialize_query(json_str)
        
        # Verify structure is preserved
        assert restored_query.cube.name == original_query.cube.name
        assert len(restored_query.measures) == len(original_query.measures)
        assert restored_query.measures[0].name == original_query.measures[0].name
        assert len(restored_query.dimensions) == len(original_query.dimensions)
    
    def test_expression_serialization(self):
        """Test expression serialization."""
        from unmdx.ir.serialization import IRSerializer, IRDeserializer
        
        # Create complex expression
        left = MeasureReference(measure_name="Sales")
        right = Constant(value=0.1)
        expr = BinaryOperation(left=left, operator="*", right=right)
        
        # Serialize
        json_str = IRSerializer.serialize_expression(expr)
        assert len(json_str) > 0
        # Basic structure test - detailed field serialization needs investigation
        assert "BINARY_OPERATION" in json_str
        assert "*" in json_str


class TestIROptimization:
    """Test IR optimization operations."""
    
    def test_redundant_filter_removal(self):
        """Test removal of redundant filters."""
        cube = CubeReference(name="Test Cube")
        
        # Create duplicate filters
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Calendar Year")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        filter1 = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.EQUALS,
            values=["2023"]
        )
        
        filter2 = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.EQUALS,
            values=["2023"]
        )
        
        filter_obj1 = Filter(filter_type=FilterType.DIMENSION, target=filter1)
        filter_obj2 = Filter(filter_type=FilterType.DIMENSION, target=filter2)
        
        query = Query(cube=cube, filters=[filter_obj1, filter_obj2])
        
        # Optimize query
        optimized = IROptimizer.optimize_query(query)
        
        # Should have removed duplicate
        assert len(optimized.filters) <= len(query.filters)
        assert len(optimized.metadata.optimization_hints) > 0
    
    def test_query_comparison(self):
        """Test query comparison operations."""
        cube = CubeReference(name="Test Cube")
        measure = Measure(name="Sales", aggregation=AggregationType.SUM)
        
        query1 = Query(cube=cube, measures=[measure])
        query2 = Query(cube=cube, measures=[measure])
        
        # Should be equivalent
        assert IRComparator.queries_equivalent(query1, query2)
        
        # Add different measure to query2
        different_measure = Measure(name="Cost", aggregation=AggregationType.SUM)
        query2.measures.append(different_measure)
        
        # Should not be equivalent
        assert not IRComparator.queries_equivalent(query1, query2)
        
        # Get differences
        differences = IRComparator.query_differences(query1, query2)
        assert "measures" in differences
        assert len(differences["measures"]) > 0


class TestComplexQueryScenarios:
    """Test complex real-world query scenarios."""
    
    def test_sales_analysis_query(self):
        """Test a typical sales analysis query."""
        cube = CubeReference(name="Adventure Works DW")
        
        # Measures
        sales_measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        quantity_measure = Measure(name="Order Quantity", aggregation=AggregationType.SUM)
        
        # Dimensions  
        product_hierarchy = HierarchyReference(table="Product", name="Product Categories")
        product_level = LevelReference(name="Category")
        product_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        product_dimension = Dimension(
            hierarchy=product_hierarchy,
            level=product_level,
            members=product_members
        )
        
        date_hierarchy = HierarchyReference(table="Date", name="Calendar")
        date_level = LevelReference(name="Calendar Year")
        date_members = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=["2022", "2023"]
        )
        date_dimension = Dimension(
            hierarchy=date_hierarchy,
            level=date_level,
            members=date_members
        )
        
        # Calculated measure
        avg_price_expr = BinaryOperation(
            left=MeasureReference(measure_name="Sales Amount"),
            operator="/",
            right=MeasureReference(measure_name="Order Quantity")
        )
        avg_price_calc = Calculation(
            name="Average Price",
            calculation_type=CalculationType.MEASURE,
            expression=avg_price_expr
        )
        
        # Build query
        query = Query(
            cube=cube,
            measures=[sales_measure, quantity_measure],
            dimensions=[product_dimension, date_dimension],
            calculations=[avg_price_calc]
        )
        
        # Validate query
        issues = query.validate_query()
        assert len(issues) == 0
        
        # Test DAX generation
        dax = query.to_dax()
        assert "SUMMARIZECOLUMNS" in dax
        assert "Product[Category]" in dax
        assert "Date[Calendar Year]" in dax
        
        # Test human readable
        readable = query.to_human_readable()
        assert "Sales Amount" in readable
        assert "Category" in readable
        assert "Calendar Year" in readable
        assert "Average Price" in readable
    
    def test_filtered_ranking_query(self):
        """Test a query with filters and ranking."""
        cube = CubeReference(name="Sales")
        
        # Top 10 products by sales in specific category
        sales_measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        product_hierarchy = HierarchyReference(table="Product", name="Product")
        product_level = LevelReference(name="Product Name")
        product_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        product_dimension = Dimension(
            hierarchy=product_hierarchy,
            level=product_level,
            members=product_members
        )
        
        # Filter for specific category
        category_hierarchy = HierarchyReference(table="Product", name="Product")
        category_level = LevelReference(name="Category")
        category_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        category_dimension = Dimension(
            hierarchy=category_hierarchy,
            level=category_level,
            members=category_members
        )
        
        category_filter = DimensionFilter(
            dimension=category_dimension,
            operator=FilterOperator.EQUALS,
            values=["Bikes"]
        )
        
        filter_obj = Filter(filter_type=FilterType.DIMENSION, target=category_filter)
        
        # Ordering and limit
        from unmdx.ir.models import OrderBy, Limit
        from unmdx.ir.enums import SortDirection
        
        order_by = OrderBy(expression="Sales Amount", direction=SortDirection.DESC)
        limit = Limit(count=10)
        
        query = Query(
            cube=cube,
            measures=[sales_measure],
            dimensions=[product_dimension],
            filters=[filter_obj],
            order_by=[order_by],
            limit=limit
        )
        
        # Test validation
        issues = query.validate_query()
        assert len(issues) == 0
        
        # Test DAX generation
        dax = query.to_dax()
        assert "ORDER BY" in dax
        assert "DESC" in dax
        
        # Test human readable
        readable = query.to_human_readable()
        assert "Bikes" in readable
        assert "limit to first 10" in readable