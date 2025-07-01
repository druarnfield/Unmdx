"""Unit tests for IR construction."""

import pytest
from datetime import datetime

from unmdx.ir import (
    Query, CubeReference, Measure, Dimension, Filter, Calculation,
    HierarchyReference, LevelReference, MemberSelection, DimensionFilter,
    AggregationType, MemberSelectionType, FilterType, FilterOperator,
    CalculationType, QueryMetadata, Constant, MeasureReference, BinaryOperation
)


class TestCubeReference:
    """Test CubeReference construction and methods."""
    
    def test_simple_cube_reference(self):
        """Test creating a simple cube reference."""
        cube = CubeReference(name="Adventure Works")
        
        assert cube.name == "Adventure Works"
        assert cube.database is None
        assert cube.schema_name is None
    
    def test_cube_reference_with_database(self):
        """Test creating cube reference with database."""
        cube = CubeReference(name="Sales", database="AdventureWorks", schema="dbo")
        
        assert cube.name == "Sales"
        assert cube.database == "AdventureWorks"
        assert cube.schema_name == "dbo"
    
    def test_cube_to_dax(self):
        """Test cube DAX generation."""
        cube = CubeReference(name="Adventure Works")
        dax = cube.to_dax()
        
        assert "Adventure Works" in dax
        assert dax.startswith("--")  # Should be a comment
    
    def test_cube_to_human_readable(self):
        """Test cube human-readable generation."""
        cube = CubeReference(name="Adventure Works")
        readable = cube.to_human_readable()
        
        assert "Adventure Works" in readable
        assert "data model" in readable


class TestHierarchyReference:
    """Test HierarchyReference construction and methods."""
    
    def test_hierarchy_reference(self):
        """Test creating hierarchy reference."""
        hierarchy = HierarchyReference(table="Product", name="Product Category")
        
        assert hierarchy.table == "Product"
        assert hierarchy.name == "Product Category"
    
    def test_hierarchy_to_dax(self):
        """Test hierarchy DAX generation."""
        hierarchy = HierarchyReference(table="Product", name="Product Category")
        dax = hierarchy.to_dax()
        
        assert dax == "Product"
    
    def test_hierarchy_to_human_readable(self):
        """Test hierarchy human-readable generation."""
        hierarchy = HierarchyReference(table="Product", name="Product Category")
        readable = hierarchy.to_human_readable()
        
        assert "Product Category" in readable
        assert "hierarchy" in readable


class TestLevelReference:
    """Test LevelReference construction and methods."""
    
    def test_level_reference(self):
        """Test creating level reference."""
        level = LevelReference(name="Category")
        
        assert level.name == "Category"
        assert level.ordinal is None
    
    def test_level_reference_with_ordinal(self):
        """Test creating level reference with ordinal."""
        level = LevelReference(name="Category", ordinal=2)
        
        assert level.name == "Category"
        assert level.ordinal == 2
    
    def test_level_to_dax(self):
        """Test level DAX generation."""
        level = LevelReference(name="Category")
        dax = level.to_dax()
        
        assert dax == "Category"
    
    def test_level_to_human_readable(self):
        """Test level human-readable generation."""
        level = LevelReference(name="Category")
        readable = level.to_human_readable()
        
        assert readable == "Category"


class TestMemberSelection:
    """Test MemberSelection construction and methods."""
    
    def test_all_members_selection(self):
        """Test creating selection for all members."""
        selection = MemberSelection(selection_type=MemberSelectionType.ALL)
        
        assert selection.selection_type == MemberSelectionType.ALL
        assert selection.is_all_members()
        assert not selection.is_specific_members()
        assert selection.get_member_list() == []
    
    def test_specific_members_selection(self):
        """Test creating selection for specific members."""
        members = ["Bikes", "Accessories", "Clothing"]
        selection = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=members
        )
        
        assert selection.selection_type == MemberSelectionType.SPECIFIC
        assert not selection.is_all_members()
        assert selection.is_specific_members()
        assert selection.get_member_list() == members
    
    def test_specific_members_validation(self):
        """Test validation for specific members selection."""
        with pytest.raises(ValueError):
            MemberSelection(selection_type=MemberSelectionType.SPECIFIC)
    
    def test_children_selection(self):
        """Test creating selection for children of a member."""
        selection = MemberSelection(
            selection_type=MemberSelectionType.CHILDREN,
            parent_member="All Products"
        )
        
        assert selection.selection_type == MemberSelectionType.CHILDREN
        assert selection.parent_member == "All Products"


class TestMeasure:
    """Test Measure construction and methods."""
    
    def test_simple_measure(self):
        """Test creating a simple measure."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        assert measure.name == "Sales Amount"
        assert measure.aggregation == AggregationType.SUM
        assert measure.alias is None
        assert measure.format_string is None
        assert measure.expression is None
    
    def test_measure_with_alias(self):
        """Test creating measure with alias."""
        measure = Measure(
            name="Sales Amount",
            aggregation=AggregationType.SUM,
            alias="Total Sales"
        )
        
        assert measure.name == "Sales Amount"
        assert measure.alias == "Total Sales"
    
    def test_measure_with_format(self):
        """Test creating measure with format string."""
        measure = Measure(
            name="Sales Amount",
            aggregation=AggregationType.SUM,
            format_string="Currency"
        )
        
        assert measure.format_string == "Currency"
    
    def test_measure_to_dax(self):
        """Test measure DAX generation."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        dax = measure.to_dax()
        
        assert '"Sales Amount"' in dax
        assert "[Sales Amount]" in dax
    
    def test_measure_to_dax_with_alias(self):
        """Test measure DAX generation with alias."""
        measure = Measure(
            name="Sales Amount",
            aggregation=AggregationType.SUM,
            alias="Total Sales"
        )
        dax = measure.to_dax()
        
        assert '"Total Sales"' in dax
        assert "[Sales Amount]" in dax
    
    def test_measure_to_human_readable(self):
        """Test measure human-readable generation."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        readable = measure.to_human_readable()
        
        assert "total" in readable
        assert "Sales Amount" in readable
    
    def test_measure_different_aggregations(self):
        """Test measures with different aggregation types."""
        test_cases = [
            (AggregationType.AVG, "average"),
            (AggregationType.COUNT, "count of"),
            (AggregationType.MIN, "minimum"),
            (AggregationType.MAX, "maximum"),
            (AggregationType.CUSTOM, "")
        ]
        
        for agg_type, expected_text in test_cases:
            measure = Measure(name="Test Measure", aggregation=agg_type)
            readable = measure.to_human_readable()
            
            if expected_text:
                assert expected_text in readable


class TestDimension:
    """Test Dimension construction and methods."""
    
    def test_simple_dimension(self):
        """Test creating a simple dimension."""
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        assert dimension.hierarchy == hierarchy
        assert dimension.level == level
        assert dimension.members == members
        assert dimension.alias is None
    
    def test_dimension_with_alias(self):
        """Test creating dimension with alias."""
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        
        dimension = Dimension(
            hierarchy=hierarchy,
            level=level,
            members=members,
            alias="Product Categories"
        )
        
        assert dimension.alias == "Product Categories"
    
    def test_dimension_to_dax(self):
        """Test dimension DAX generation."""
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        dax = dimension.to_dax()
        
        assert "Product[Category]" == dax
    
    def test_dimension_to_human_readable_all_members(self):
        """Test dimension human-readable for all members."""
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        readable = dimension.to_human_readable()
        
        assert "each Category" == readable
    
    def test_dimension_to_human_readable_specific_members(self):
        """Test dimension human-readable for specific members."""
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=["Bikes", "Accessories"]
        )
        
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        readable = dimension.to_human_readable()
        
        assert "Category" in readable
        assert "Bikes" in readable
        assert "Accessories" in readable


class TestDimensionFilter:
    """Test DimensionFilter construction and methods."""
    
    def test_equals_filter(self):
        """Test creating equals filter."""
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Calendar Year")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        filter_obj = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.EQUALS,
            values=["2023"]
        )
        
        assert filter_obj.operator == FilterOperator.EQUALS
        assert filter_obj.values == ["2023"]
    
    def test_in_filter(self):
        """Test creating IN filter."""
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        filter_obj = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.IN,
            values=["Bikes", "Accessories"]
        )
        
        assert filter_obj.operator == FilterOperator.IN
        assert len(filter_obj.values) == 2
    
    def test_dimension_filter_to_dax_equals(self):
        """Test dimension filter DAX generation for equals."""
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Calendar Year")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        filter_obj = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.EQUALS,
            values=["2023"]
        )
        
        dax = filter_obj.to_dax()
        assert "Date[Calendar Year]" in dax
        assert "= \"2023\"" in dax
    
    def test_dimension_filter_to_dax_in(self):
        """Test dimension filter DAX generation for IN."""
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        filter_obj = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.IN,
            values=["Bikes", "Accessories"]
        )
        
        dax = filter_obj.to_dax()
        assert "Product[Category]" in dax
        assert "IN" in dax
        assert "\"Bikes\"" in dax
        assert "\"Accessories\"" in dax
    
    def test_dimension_filter_to_human_readable(self):
        """Test dimension filter human-readable generation."""
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Calendar Year")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        filter_obj = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.EQUALS,
            values=["2023"]
        )
        
        readable = filter_obj.to_human_readable()
        assert "Calendar Year" in readable
        assert "equals" in readable
        assert "2023" in readable


class TestFilter:
    """Test Filter construction and methods."""
    
    def test_dimension_filter(self):
        """Test creating dimension filter."""
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Calendar Year")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        dim_filter = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.EQUALS,
            values=["2023"]
        )
        
        filter_obj = Filter(filter_type=FilterType.DIMENSION, target=dim_filter)
        
        assert filter_obj.filter_type == FilterType.DIMENSION
        assert filter_obj.target == dim_filter
    
    def test_filter_to_dax(self):
        """Test filter DAX generation."""
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Calendar Year")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        dim_filter = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.EQUALS,
            values=["2023"]
        )
        
        filter_obj = Filter(filter_type=FilterType.DIMENSION, target=dim_filter)
        dax = filter_obj.to_dax()
        
        assert "Date[Calendar Year]" in dax
        assert "2023" in dax
    
    def test_filter_to_human_readable(self):
        """Test filter human-readable generation."""
        hierarchy = HierarchyReference(table="Date", name="Calendar")
        level = LevelReference(name="Calendar Year")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        dim_filter = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.EQUALS,
            values=["2023"]
        )
        
        filter_obj = Filter(filter_type=FilterType.DIMENSION, target=dim_filter)
        readable = filter_obj.to_human_readable()
        
        assert "Calendar Year" in readable
        assert "2023" in readable


class TestCalculation:
    """Test Calculation construction and methods."""
    
    def test_simple_calculation(self):
        """Test creating a simple calculation."""
        expression = BinaryOperation(
            left=MeasureReference(measure_name="Sales"),
            operator="/",
            right=MeasureReference(measure_name="Cost")
        )
        
        calculation = Calculation(
            name="Profit Margin",
            calculation_type=CalculationType.MEASURE,
            expression=expression
        )
        
        assert calculation.name == "Profit Margin"
        assert calculation.calculation_type == CalculationType.MEASURE
        assert calculation.expression == expression
        assert calculation.solve_order is None
    
    def test_calculation_with_solve_order(self):
        """Test creating calculation with solve order."""
        expression = Constant(value=100)
        
        calculation = Calculation(
            name="Test Calc",
            calculation_type=CalculationType.MEASURE,
            expression=expression,
            solve_order=10
        )
        
        assert calculation.solve_order == 10
    
    def test_calculation_to_dax_definition(self):
        """Test calculation DAX definition generation."""
        expression = MeasureReference(measure_name="Sales")
        
        calculation = Calculation(
            name="Total Sales",
            calculation_type=CalculationType.MEASURE,
            expression=expression
        )
        
        dax = calculation.to_dax_definition()
        assert "MEASURE" in dax
        assert "Total Sales" in dax
        assert "[Sales]" in dax
    
    def test_calculation_to_human_readable(self):
        """Test calculation human-readable generation."""
        expression = Constant(value=100)
        
        calculation = Calculation(
            name="Test Calc",
            calculation_type=CalculationType.MEASURE,
            expression=expression
        )
        
        readable = calculation.to_human_readable()
        assert "Calculate" in readable
        assert "measure" in readable
        assert "Test Calc" in readable
        assert "100" in readable
    
    def test_calculation_get_dependencies(self):
        """Test calculation dependency extraction."""
        expression = BinaryOperation(
            left=MeasureReference(measure_name="Sales"),
            operator="+",
            right=MeasureReference(measure_name="Returns")
        )
        
        calculation = Calculation(
            name="Net Sales",
            calculation_type=CalculationType.MEASURE,
            expression=expression
        )
        
        dependencies = calculation.get_dependencies()
        assert "Sales" in dependencies
        assert "Returns" in dependencies


class TestQueryMetadata:
    """Test QueryMetadata construction and methods."""
    
    def test_empty_metadata(self):
        """Test creating empty metadata."""
        metadata = QueryMetadata()
        
        assert metadata.created_at is None
        assert metadata.optimization_hints == []
        assert metadata.warnings == []
        assert metadata.errors == []
        assert not metadata.has_errors()
        assert not metadata.has_warnings()
    
    def test_metadata_with_values(self):
        """Test creating metadata with values."""
        now = datetime.now()
        metadata = QueryMetadata(
            created_at=now,
            source_mdx_hash="abc123",
            complexity_score=75
        )
        
        assert metadata.created_at == now
        assert metadata.source_mdx_hash == "abc123"
        assert metadata.complexity_score == 75
    
    def test_metadata_add_warning(self):
        """Test adding warnings to metadata."""
        metadata = QueryMetadata()
        metadata.add_warning("This is a warning")
        
        assert len(metadata.warnings) == 1
        assert metadata.warnings[0] == "This is a warning"
        assert metadata.has_warnings()
        assert not metadata.has_errors()
    
    def test_metadata_add_error(self):
        """Test adding errors to metadata."""
        metadata = QueryMetadata()
        metadata.add_error("This is an error")
        
        assert len(metadata.errors) == 1
        assert metadata.errors[0] == "This is an error"
        assert metadata.has_errors()
        assert not metadata.has_warnings()


class TestQuery:
    """Test Query construction and methods."""
    
    def test_empty_query(self):
        """Test creating an empty query."""
        cube = CubeReference(name="Test Cube")
        query = Query(cube=cube)
        
        assert query.cube == cube
        assert query.measures == []
        assert query.dimensions == []
        assert query.filters == []
        assert query.order_by == []
        assert query.limit is None
        assert query.calculations == []
        assert isinstance(query.metadata, QueryMetadata)
    
    def test_simple_query(self):
        """Test creating a simple query with measure."""
        cube = CubeReference(name="Adventure Works")
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        query = Query(cube=cube, measures=[measure])
        
        assert len(query.measures) == 1
        assert query.measures[0] == measure
    
    def test_query_with_dimension(self):
        """Test creating query with dimension."""
        cube = CubeReference(name="Adventure Works")
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        query = Query(cube=cube, measures=[measure], dimensions=[dimension])
        
        assert len(query.measures) == 1
        assert len(query.dimensions) == 1
        assert query.dimensions[0] == dimension
    
    def test_query_validation_empty(self):
        """Test query validation for empty query."""
        cube = CubeReference(name="Test Cube")
        query = Query(cube=cube)
        
        issues = query.validate_query()
        assert len(issues) > 0
        assert any("must have at least one measure or dimension" in issue for issue in issues)
    
    def test_query_validation_valid(self):
        """Test query validation for valid query."""
        cube = CubeReference(name="Adventure Works")
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        query = Query(cube=cube, measures=[measure])
        
        issues = query.validate_query()
        assert len(issues) == 0
    
    def test_query_get_dependencies(self):
        """Test query dependency extraction."""
        cube = CubeReference(name="Adventure Works")
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        
        hierarchy = HierarchyReference(table="Product", name="Product")
        level = LevelReference(name="Category")
        members = MemberSelection(selection_type=MemberSelectionType.ALL)
        dimension = Dimension(hierarchy=hierarchy, level=level, members=members)
        
        query = Query(cube=cube, measures=[measure], dimensions=[dimension])
        
        dependencies = query.get_all_dependencies()
        assert "measures" in dependencies
        assert "dimensions" in dependencies
        assert "calculations" in dependencies
        assert "Product.Category" in dependencies["dimensions"]