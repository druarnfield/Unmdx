"""Integration tests for IR with complex query scenarios."""

import pytest
from datetime import datetime

from unmdx.ir import (
    Query, CubeReference, Measure, Dimension, Filter, Calculation,
    HierarchyReference, LevelReference, MemberSelection, DimensionFilter,
    AggregationType, MemberSelectionType, FilterType, FilterOperator,
    CalculationType, QueryMetadata, Constant, MeasureReference, BinaryOperation,
    FunctionCall, FunctionType, OrderBy, Limit, SortDirection, ComparisonOperator
)
from unmdx.ir.models import MeasureFilter, NonEmptyFilter
from unmdx.ir.serialization import IRValidator, IROptimizer, IRSerializer, IRDeserializer


class TestComplexQueryIntegration:
    """Test integration of multiple IR components in complex queries."""
    
    def test_multi_dimensional_sales_analysis(self):
        """Test a complex sales analysis with multiple dimensions and calculations."""
        # Build a comprehensive sales analysis query
        cube = CubeReference(name="Adventure Works DW 2019")
        
        # Define measures
        sales_amount = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        order_quantity = Measure(name="Order Quantity", aggregation=AggregationType.SUM)
        product_cost = Measure(name="Total Product Cost", aggregation=AggregationType.SUM)
        
        # Define dimensions
        # Product dimension
        product_hierarchy = HierarchyReference(table="Product", name="Product")
        product_level = LevelReference(name="Product Category")
        product_members = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=["Bikes", "Accessories", "Clothing"]
        )
        product_dimension = Dimension(
            hierarchy=product_hierarchy,
            level=product_level,
            members=product_members,
            alias="Product Categories"
        )
        
        # Date dimension
        date_hierarchy = HierarchyReference(table="Date", name="Calendar")
        date_level = LevelReference(name="Calendar Year")
        date_members = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=["2017", "2018", "2019"]
        )
        date_dimension = Dimension(
            hierarchy=date_hierarchy,
            level=date_level,
            members=date_members
        )
        
        # Geography dimension
        geo_hierarchy = HierarchyReference(table="Geography", name="Geography")
        geo_level = LevelReference(name="Country")
        geo_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        geo_dimension = Dimension(
            hierarchy=geo_hierarchy,
            level=geo_level,
            members=geo_members
        )
        
        # Define calculated measures
        # Profit = Sales Amount - Total Product Cost
        profit_expr = BinaryOperation(
            left=MeasureReference(measure_name="Sales Amount"),
            operator="-",
            right=MeasureReference(measure_name="Total Product Cost")
        )
        profit_calc = Calculation(
            name="Profit",
            calculation_type=CalculationType.MEASURE,
            expression=profit_expr
        )
        
        # Profit Margin = Profit / Sales Amount
        profit_margin_expr = BinaryOperation(
            left=MeasureReference(measure_name="Profit"),
            operator="/",
            right=MeasureReference(measure_name="Sales Amount")
        )
        profit_margin_calc = Calculation(
            name="Profit Margin %",
            calculation_type=CalculationType.MEASURE,
            expression=profit_margin_expr,
            format_string="Percent"
        )
        
        # Average Order Value = Sales Amount / Order Quantity
        aov_expr = BinaryOperation(
            left=MeasureReference(measure_name="Sales Amount"),
            operator="/",
            right=MeasureReference(measure_name="Order Quantity")
        )
        aov_calc = Calculation(
            name="Average Order Value",
            calculation_type=CalculationType.MEASURE,
            expression=aov_expr,
            format_string="Currency"
        )
        
        # Define filters
        # Filter for significant sales amounts
        sales_filter = MeasureFilter(
            measure=sales_amount,
            operator=ComparisonOperator.GT,
            value=10000
        )
        sales_filter_obj = Filter(filter_type=FilterType.MEASURE, target=sales_filter)
        
        # Filter for specific countries
        country_filter = DimensionFilter(
            dimension=geo_dimension,
            operator=FilterOperator.IN,
            values=["United States", "Canada", "Australia"]
        )
        country_filter_obj = Filter(filter_type=FilterType.DIMENSION, target=country_filter)
        
        # Non-empty filter
        non_empty_filter = NonEmptyFilter()
        non_empty_filter_obj = Filter(filter_type=FilterType.NON_EMPTY, target=non_empty_filter)
        
        # Define ordering
        order_by_sales = OrderBy(expression="Sales Amount", direction=SortDirection.DESC)
        order_by_category = OrderBy(expression="Product Category", direction=SortDirection.ASC)
        
        # Define limit
        limit = Limit(count=100)
        
        # Create metadata
        metadata = QueryMetadata(
            created_at=datetime.now(),
            complexity_score=85,
            estimated_result_size=300
        )
        metadata.add_warning("Complex query with multiple calculations")
        
        # Build the complete query
        query = Query(
            cube=cube,
            measures=[sales_amount, order_quantity, product_cost],
            dimensions=[product_dimension, date_dimension, geo_dimension],
            filters=[sales_filter_obj, country_filter_obj, non_empty_filter_obj],
            calculations=[profit_calc, profit_margin_calc, aov_calc],
            order_by=[order_by_sales, order_by_category],
            limit=limit,
            metadata=metadata
        )
        
        # Test query validation
        issues = query.validate_query()
        assert len(issues) == 0, f"Query validation failed: {issues}"
        
        # Test dependency analysis
        dependencies = query.get_all_dependencies()
        assert "measures" in dependencies
        assert "dimensions" in dependencies
        assert "calculations" in dependencies
        
        # Check calculation dependencies (which reference measures)
        calc_deps = dependencies["calculations"]
        assert "Sales Amount" in calc_deps  # From calculations
        assert "Total Product Cost" in calc_deps
        assert "Order Quantity" in calc_deps
        assert "Profit" in calc_deps  # Dependency chain
        
        # Check dimension dependencies
        dim_deps = dependencies["dimensions"]
        assert "Product.Product Category" in dim_deps
        assert "Date.Calendar Year" in dim_deps
        assert "Geography.Country" in dim_deps
        
        # Test DAX generation
        dax = query.to_dax()
        
        # Verify DEFINE section for calculations
        assert "DEFINE" in dax
        assert "MEASURE" in dax
        assert "Profit" in dax
        assert "Profit Margin %" in dax
        assert "Average Order Value" in dax
        
        # Verify SUMMARIZECOLUMNS structure
        assert "SUMMARIZECOLUMNS" in dax
        assert "Product[Product Category]" in dax
        assert "Date[Calendar Year]" in dax
        assert "Geography[Country]" in dax
        
        # Verify filters in DAX
        assert "FILTER" in dax
        assert "Geography" in dax  # Country filter
        
        # Verify measures in DAX
        assert "Sales Amount" in dax
        assert "Order Quantity" in dax
        assert "Total Product Cost" in dax
        
        # Verify ordering
        assert "ORDER BY" in dax
        assert "DESC" in dax
        
        # Test human-readable generation
        readable = query.to_human_readable()
        
        # Verify main sections
        assert "This query will:" in readable
        assert "Calculate:" in readable
        assert "Grouped by:" in readable
        assert "Where:" in readable
        assert "With these calculations:" in readable
        assert "Sorted by:" in readable
        assert "limit to first 100" in readable
        
        # Verify SQL-like representation
        assert "SQL-like representation:" in readable
        assert "SELECT" in readable
        assert "FROM" in readable
        assert "WHERE" in readable
        assert "GROUP BY" in readable
        assert "HAVING" in readable
        assert "ORDER BY" in readable
        assert "LIMIT" in readable
        
        # Test basic serialization (round-trip test would need polymorphic handling)
        json_str = IRSerializer.serialize_query(query)
        assert len(json_str) > 0
        assert "Adventure Works DW 2019" in json_str
        assert "Profit" in json_str
        
        # Test optimization
        optimized_query = IROptimizer.optimize_query(query)
        assert len(optimized_query.metadata.optimization_hints) > 0
        
        # Test validation with warnings
        validation_result = IRValidator.validate_query(query)
        assert validation_result["valid"] is True
        assert len(validation_result["warnings"]) > 0  # Should have complexity warnings
    
    def test_time_series_analysis_query(self):
        """Test a time series analysis query with period-over-period calculations."""
        cube = CubeReference(name="Sales Cube")
        
        # Base measures
        current_sales = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        # Time dimension at month level
        date_hierarchy = HierarchyReference(table="Date", name="Calendar")
        month_level = LevelReference(name="Month", ordinal=3)
        month_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        month_dimension = Dimension(
            hierarchy=date_hierarchy,
            level=month_level,
            members=month_members
        )
        
        # Year dimension for filtering
        year_level = LevelReference(name="Year", ordinal=1)
        year_members = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=["2023"]
        )
        year_dimension = Dimension(
            hierarchy=date_hierarchy,
            level=year_level,
            members=year_members
        )
        
        # Previous period calculation (simplified - would need time intelligence in real DAX)
        prev_month_expr = FunctionCall(
            function_type=FunctionType.TIME,
            function_name="PREVIOUSMONTH",
            arguments=[MeasureReference(measure_name="Sales Amount")]
        )
        prev_month_calc = Calculation(
            name="Previous Month Sales",
            calculation_type=CalculationType.MEASURE,
            expression=prev_month_expr
        )
        
        # Growth calculation
        growth_expr = BinaryOperation(
            left=BinaryOperation(
                left=MeasureReference(measure_name="Sales Amount"),
                operator="-",
                right=MeasureReference(measure_name="Previous Month Sales")
            ),
            operator="/",
            right=MeasureReference(measure_name="Previous Month Sales")
        )
        growth_calc = Calculation(
            name="Month over Month Growth %",
            calculation_type=CalculationType.MEASURE,
            expression=growth_expr,
            format_string="Percent"
        )
        
        # Moving average (3-month)
        moving_avg_expr = FunctionCall(
            function_type=FunctionType.AGGREGATE,
            function_name="AVERAGEX",
            arguments=[
                MeasureReference(measure_name="Sales Amount"),
                Constant(value=3)  # Simplified representation
            ]
        )
        moving_avg_calc = Calculation(
            name="3-Month Moving Average",
            calculation_type=CalculationType.MEASURE,
            expression=moving_avg_expr
        )
        
        # Build query
        query = Query(
            cube=cube,
            measures=[current_sales],
            dimensions=[month_dimension, year_dimension],
            calculations=[prev_month_calc, growth_calc, moving_avg_calc],
            order_by=[OrderBy(expression="Month", direction=SortDirection.ASC)]
        )
        
        # Test validation
        issues = query.validate_query()
        assert len(issues) == 0
        
        # Test that time intelligence calculations are properly structured
        calc_names = [calc.name for calc in query.calculations]
        assert "Previous Month Sales" in calc_names
        assert "Month over Month Growth %" in calc_names
        assert "3-Month Moving Average" in calc_names
        
        # Test dependency chain
        dependencies = query.get_all_dependencies()
        calc_deps = dependencies["calculations"]
        assert "Sales Amount" in calc_deps
        assert "Previous Month Sales" in calc_deps
        
        # Test DAX generation includes time functions
        dax = query.to_dax()
        assert "PREVIOUSMONTH" in dax
        assert "AVERAGEX" in dax
        
        # Test human readable includes time concepts
        readable = query.to_human_readable()
        assert "Previous Month" in readable
        assert "Growth" in readable
        assert "Moving Average" in readable
    
    def test_cross_cube_analysis_query(self):
        """Test a query that conceptually involves multiple cubes/models."""
        # This tests the flexibility of our IR to handle complex scenarios
        main_cube = CubeReference(name="Sales", database="AdventureWorks", schema="dbo")
        
        # Sales measures from main cube
        sales_measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        # Customer dimension
        customer_hierarchy = HierarchyReference(table="Customer", name="Customer")
        customer_level = LevelReference(name="Customer Key")
        customer_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        customer_dimension = Dimension(
            hierarchy=customer_hierarchy,
            level=customer_level,
            members=customer_members
        )
        
        # Product dimension
        product_hierarchy = HierarchyReference(table="Product", name="Product")
        product_level = LevelReference(name="Product Key")
        product_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        product_dimension = Dimension(
            hierarchy=product_hierarchy,
            level=product_level,
            members=product_members
        )
        
        # Complex calculation that might involve lookup to other tables
        # Customer Lifetime Value (simplified)
        clv_expr = FunctionCall(
            function_type=FunctionType.AGGREGATE,
            function_name="SUMX",
            arguments=[
                MeasureReference(measure_name="Sales Amount"),
                FunctionCall(
                    function_type=FunctionType.LOOKUP,
                    function_name="RELATED",
                    arguments=[MeasureReference(measure_name="Customer.LifetimeValue")]
                )
            ]
        )
        clv_calc = Calculation(
            name="Customer Lifetime Value",
            calculation_type=CalculationType.MEASURE,
            expression=clv_expr
        )
        
        # Product affinity score (conceptual)
        affinity_expr = FunctionCall(
            function_type=FunctionType.STATISTICAL,
            function_name="CORRELATION",
            arguments=[
                MeasureReference(measure_name="Sales Amount"),
                MeasureReference(measure_name="Product.AffinityScore")
            ]
        )
        affinity_calc = Calculation(
            name="Product Affinity",
            calculation_type=CalculationType.MEASURE,
            expression=affinity_expr
        )
        
        # Filters for high-value analysis
        high_value_filter = MeasureFilter(
            measure=sales_measure,
            operator=ComparisonOperator.GT,
            value=50000
        )
        high_value_filter_obj = Filter(filter_type=FilterType.MEASURE, target=high_value_filter)
        
        # Build comprehensive query
        query = Query(
            cube=main_cube,
            measures=[sales_measure],
            dimensions=[customer_dimension, product_dimension],
            calculations=[clv_calc, affinity_calc],
            filters=[high_value_filter_obj],
            limit=Limit(count=50)
        )
        
        # Test validation
        issues = query.validate_query()
        assert len(issues) == 0
        
        # Test that complex functions are handled
        dax = query.to_dax()
        assert "SUMX" in dax
        assert "RELATED" in dax
        assert "CORRELATION" in dax
        
        # Test metadata tracking
        query.metadata.add_warning("Cross-table calculations may require relationship validation")
        assert query.metadata.has_warnings()
        
        # Test optimization doesn't break complex expressions
        optimized = IROptimizer.optimize_query(query)
        assert len(optimized.calculations) == len(query.calculations)
    
    def test_hierarchical_query_with_drill_down(self):
        """Test a query with hierarchical drill-down scenarios."""
        cube = CubeReference(name="Adventure Works")
        
        # Measures
        sales_measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        unit_measure = Measure(name="Units Sold", aggregation=AggregationType.SUM)
        
        # Multi-level product hierarchy
        product_hierarchy = HierarchyReference(table="Product", name="Product Categories")
        
        # Category level (level 1)
        category_level = LevelReference(name="Category", ordinal=1)
        category_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        category_dimension = Dimension(
            hierarchy=product_hierarchy,
            level=category_level,
            members=category_members,
            alias="Product Category"
        )
        
        # Subcategory level (level 2)
        subcategory_level = LevelReference(name="Subcategory", ordinal=2)
        subcategory_members = MemberSelection(
            selection_type=MemberSelectionType.CHILDREN,
            parent_member="Bikes"  # Drill down into Bikes category
        )
        subcategory_dimension = Dimension(
            hierarchy=product_hierarchy,
            level=subcategory_level,
            members=subcategory_members,
            alias="Product Subcategory"
        )
        
        # Product level (level 3) - specific products
        product_level = LevelReference(name="Product Name", ordinal=3)
        product_members = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=["Mountain-200 Black, 38", "Mountain-200 Silver, 42"]
        )
        product_dimension = Dimension(
            hierarchy=product_hierarchy,
            level=product_level,
            members=product_members,
            alias="Product"
        )
        
        # Geography hierarchy
        geo_hierarchy = HierarchyReference(table="Geography", name="Geography")
        country_level = LevelReference(name="Country", ordinal=1)
        country_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        country_dimension = Dimension(
            hierarchy=geo_hierarchy,
            level=country_level,
            members=country_members
        )
        
        # Date hierarchy - quarterly analysis
        date_hierarchy = HierarchyReference(table="Date", name="Fiscal")
        quarter_level = LevelReference(name="Fiscal Quarter", ordinal=2)
        quarter_members = MemberSelection(selection_type=MemberSelectionType.ALL)
        quarter_dimension = Dimension(
            hierarchy=date_hierarchy,
            level=quarter_level,
            members=quarter_members
        )
        
        # Calculation: Market Share by Category
        market_share_expr = BinaryOperation(
            left=MeasureReference(measure_name="Sales Amount"),
            operator="/",
            right=FunctionCall(
                function_type=FunctionType.AGGREGATE,
                function_name="CALCULATE",
                arguments=[
                    MeasureReference(measure_name="Sales Amount"),
                    FunctionCall(
                        function_type=FunctionType.FILTER,
                        function_name="ALL",
                        arguments=[MeasureReference(measure_name="Product[Category]")]
                    )
                ]
            )
        )
        market_share_calc = Calculation(
            name="Market Share %",
            calculation_type=CalculationType.MEASURE,
            expression=market_share_expr,
            format_string="Percent"
        )
        
        # Build hierarchical query
        query = Query(
            cube=cube,
            measures=[sales_measure, unit_measure],
            dimensions=[category_dimension, subcategory_dimension, product_dimension, 
                       country_dimension, quarter_dimension],
            calculations=[market_share_calc],
            order_by=[
                OrderBy(expression="Product Category", direction=SortDirection.ASC),
                OrderBy(expression="Sales Amount", direction=SortDirection.DESC)
            ]
        )
        
        # Test hierarchical structure validation
        issues = query.validate_query()
        assert len(issues) == 0
        
        # Test that hierarchy levels are properly represented
        dimensions_by_table = {}
        for dim in query.dimensions:
            table = dim.hierarchy.table
            if table not in dimensions_by_table:
                dimensions_by_table[table] = []
            dimensions_by_table[table].append(dim)
        
        # Should have multiple levels from Product hierarchy
        assert "Product" in dimensions_by_table
        product_dims = dimensions_by_table["Product"]
        assert len(product_dims) == 3  # Category, Subcategory, Product
        
        # Test ordinal relationships
        ordinals = [dim.level.ordinal for dim in product_dims if dim.level.ordinal]
        assert 1 in ordinals  # Category
        assert 2 in ordinals  # Subcategory
        assert 3 in ordinals  # Product
        
        # Test different member selection types
        selection_types = [dim.members.selection_type for dim in product_dims]
        assert MemberSelectionType.ALL in selection_types
        assert MemberSelectionType.CHILDREN in selection_types
        assert MemberSelectionType.SPECIFIC in selection_types
        
        # Test DAX generation handles hierarchy
        dax = query.to_dax()
        assert "Product[Category]" in dax
        assert "Product[Subcategory]" in dax
        assert "Product[Product Name]" in dax
        assert "ALL" in dax  # From market share calculation
        
        # Test human readable explains hierarchy
        readable = query.to_human_readable()
        assert "Product Category" in readable
        assert "Product Subcategory" in readable
        assert "children of Bikes" in readable or "Bikes" in readable
        assert "Mountain-200" in readable
    
    def test_query_validation_comprehensive(self):
        """Test comprehensive validation scenarios."""
        cube = CubeReference(name="Test Cube")
        
        # Create query with potential issues
        measure1 = Measure(name="Sales", aggregation=AggregationType.SUM)
        measure2 = Measure(name="Cost", aggregation=AggregationType.SUM)
        
        # Create many dimensions (should trigger warning)
        dimensions = []
        for i in range(12):  # More than 10, should trigger warning
            hierarchy = HierarchyReference(table=f"Dim{i}", name=f"Dimension{i}")
            level = LevelReference(name=f"Level{i}")
            members = MemberSelection(selection_type=MemberSelectionType.ALL)
            dimensions.append(Dimension(hierarchy=hierarchy, level=level, members=members))
        
        # Create many calculations (should trigger warning)
        calculations = []
        for i in range(7):  # More than 5, should trigger warning
            calc = Calculation(
                name=f"Calc{i}",
                calculation_type=CalculationType.MEASURE,
                expression=Constant(value=i)
            )
            calculations.append(calc)
        
        # Create measure filter for measure not in query (should be error)
        other_measure = Measure(name="Profit", aggregation=AggregationType.SUM)
        measure_filter = MeasureFilter(
            measure=other_measure,
            operator=ComparisonOperator.GT,
            value=100
        )
        filter_obj = Filter(filter_type=FilterType.MEASURE, target=measure_filter)
        
        query = Query(
            cube=cube,
            measures=[measure1, measure2],
            dimensions=dimensions,
            calculations=calculations,
            filters=[filter_obj]
        )
        
        # Test built-in validation
        issues = query.validate_query()
        assert len(issues) > 0
        profit_issue = any("Profit" in issue for issue in issues)
        assert profit_issue
        
        # Test validator with warnings
        validation_result = IRValidator.validate_query(query)
        assert not validation_result["valid"]  # Should be invalid due to measure filter issue
        assert len(validation_result["errors"]) > 0
        assert len(validation_result["warnings"]) > 0
        
        # Check specific warnings
        warnings = validation_result["warnings"]
        dimension_warning = any("dimensions" in w for w in warnings)
        calculation_warning = any("calculations" in w for w in warnings)
        assert dimension_warning
        assert calculation_warning