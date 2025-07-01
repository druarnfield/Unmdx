"""Unit tests for IR models."""


from unmdx.ir.models import (
    AggregationType,
    BinaryOperation,
    Calculation,
    CalculationType,
    ComparisonOperator,
    Constant,
    CubeReference,
    Dimension,
    DimensionFilter,
    Filter,
    FilterOperator,
    FilterType,
    HierarchyReference,
    LevelReference,
    Limit,
    Measure,
    MeasureFilter,
    MeasureReference,
    MemberSelection,
    MemberSelectionType,
    OrderBy,
    Query,
    QueryMetadata,
    SortDirection,
)


class TestCubeReference:
    """Test CubeReference class."""

    def test_creation(self):
        """Test basic creation."""
        cube = CubeReference(name="Test Cube")
        assert cube.name == "Test Cube"
        assert cube.database is None

    def test_with_database(self):
        """Test creation with database."""
        cube = CubeReference(name="Test Cube", database="Test DB")
        assert cube.name == "Test Cube"
        assert cube.database == "Test DB"

    def test_to_dax(self):
        """Test DAX generation."""
        cube = CubeReference(name="Test Cube")
        dax = cube.to_dax()
        assert "Test Cube" in dax
        assert dax.startswith("--")

    def test_to_human_readable(self):
        """Test human-readable generation."""
        cube = CubeReference(name="Test Cube")
        readable = cube.to_human_readable()
        assert "Test Cube" in readable
        assert "data model" in readable


class TestMeasure:
    """Test Measure class."""

    def test_basic_measure(self):
        """Test basic measure creation."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        assert measure.name == "Sales Amount"
        assert measure.aggregation == AggregationType.SUM
        assert measure.alias is None

    def test_measure_with_alias(self):
        """Test measure with alias."""
        measure = Measure(
            name="Sales Amount", aggregation=AggregationType.SUM, alias="Total Sales"
        )
        assert measure.alias == "Total Sales"

    def test_to_dax_without_alias(self):
        """Test DAX generation without alias."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        dax = measure.to_dax()
        assert "Sales Amount" in dax
        assert dax.count("Sales Amount") == 2  # Should appear twice

    def test_to_dax_with_alias(self):
        """Test DAX generation with alias."""
        measure = Measure(
            name="Sales Amount", aggregation=AggregationType.SUM, alias="Total Sales"
        )
        dax = measure.to_dax()
        assert "Total Sales" in dax
        assert "Sales Amount" in dax

    def test_to_human_readable(self):
        """Test human-readable generation."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        readable = measure.to_human_readable()
        assert "total" in readable.lower()
        assert "Sales Amount" in readable


class TestDimension:
    """Test Dimension class."""

    def test_basic_dimension(self):
        """Test basic dimension creation."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )
        assert dimension.hierarchy.name == "Product"
        assert dimension.level.name == "Category"
        assert dimension.members.is_all_members()

    def test_to_dax(self):
        """Test DAX generation."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )
        dax = dimension.to_dax()
        assert "Product[Category]" == dax

    def test_to_human_readable_all_members(self):
        """Test human-readable for all members."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )
        readable = dimension.to_human_readable()
        assert "each Category" == readable

    def test_to_human_readable_specific_members(self):
        """Test human-readable for specific members."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(
                selection_type=MemberSelectionType.SPECIFIC,
                specific_members=["Bikes", "Components"],
            ),
        )
        readable = dimension.to_human_readable()
        assert "specific Category values" == readable


class TestMemberSelection:
    """Test MemberSelection class."""

    def test_all_members(self):
        """Test all members selection."""
        selection = MemberSelection(selection_type=MemberSelectionType.ALL)
        assert selection.is_all_members()
        assert selection.to_human_readable() == "all values"

    def test_specific_members(self):
        """Test specific members selection."""
        selection = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=["Bikes", "Components"],
        )
        assert not selection.is_all_members()
        readable = selection.to_human_readable()
        assert "specific values" in readable
        assert "Bikes" in readable
        assert "Components" in readable

    def test_to_dax_specific_members(self):
        """Test DAX generation for specific members."""
        selection = MemberSelection(
            selection_type=MemberSelectionType.SPECIFIC,
            specific_members=["Bikes", "Components"],
        )
        dax = selection.to_dax()
        assert "IN" in dax
        assert "Bikes" in dax
        assert "Components" in dax


class TestExpressions:
    """Test expression classes."""

    def test_constant_numeric(self):
        """Test numeric constant."""
        const = Constant(100)
        assert const.to_dax() == "100"
        assert const.to_human_readable() == "100"

    def test_constant_string(self):
        """Test string constant."""
        const = Constant("Hello")
        assert const.to_dax() == '"Hello"'
        assert const.to_human_readable() == "Hello"

    def test_measure_reference(self):
        """Test measure reference."""
        ref = MeasureReference("Sales Amount")
        assert ref.to_dax() == "[Sales Amount]"
        assert ref.to_human_readable() == "Sales Amount"

    def test_binary_operation_addition(self):
        """Test binary addition operation."""
        left = MeasureReference("Sales")
        right = MeasureReference("Tax")
        op = BinaryOperation(left, "+", right)

        dax = op.to_dax()
        assert "([Sales] + [Tax])" == dax

        readable = op.to_human_readable()
        assert "Sales plus Tax" == readable

    def test_binary_operation_division(self):
        """Test binary division operation (uses DIVIDE)."""
        left = MeasureReference("Profit")
        right = MeasureReference("Sales")
        op = BinaryOperation(left, "/", right)

        dax = op.to_dax()
        assert dax.startswith("DIVIDE(")
        assert "[Profit]" in dax
        assert "[Sales]" in dax

        readable = op.to_human_readable()
        assert "Profit divided by Sales" == readable


class TestFilters:
    """Test filter classes."""

    def test_dimension_filter_equals(self):
        """Test dimension filter with equals operator."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Date", name="Date"),
            level=LevelReference(name="Year"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        filter_obj = DimensionFilter(
            dimension=dimension, operator=FilterOperator.EQUALS, values=["2023"]
        )

        dax = filter_obj.to_dax()
        assert 'Date[Year] = "2023"' == dax

        readable = filter_obj.to_human_readable()
        assert "Year equals 2023" == readable

    def test_dimension_filter_in(self):
        """Test dimension filter with IN operator."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        filter_obj = DimensionFilter(
            dimension=dimension,
            operator=FilterOperator.IN,
            values=["Bikes", "Components"],
        )

        dax = filter_obj.to_dax()
        assert "Product[Category] IN" in dax
        assert '"Bikes"' in dax
        assert '"Components"' in dax

        readable = filter_obj.to_human_readable()
        assert "Category is one of" in readable
        assert "Bikes" in readable
        assert "Components" in readable

    def test_measure_filter(self):
        """Test measure filter."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)

        filter_obj = MeasureFilter(
            measure=measure, operator=ComparisonOperator.GT, value=1000
        )

        dax = filter_obj.to_dax()
        assert "[Sales Amount] > 1000" == dax

        readable = filter_obj.to_human_readable()
        assert "Sales Amount is greater than 1000" == readable


class TestCalculation:
    """Test Calculation class."""

    def test_basic_calculation(self):
        """Test basic calculation."""
        expression = BinaryOperation(
            left=MeasureReference("Profit"),
            operator="/",
            right=MeasureReference("Sales"),
        )

        calc = Calculation(
            name="Profit Margin",
            calculation_type=CalculationType.MEASURE,
            expression=expression,
        )

        dax_def = calc.to_dax_definition()
        assert "MEASURE Profit Margin =" in dax_def
        assert "DIVIDE(" in dax_def

        readable = calc.to_human_readable()
        assert "Calculate Profit Margin as" in readable
        assert "divided by" in readable


class TestOrderBy:
    """Test OrderBy class."""

    def test_ascending_order(self):
        """Test ascending order."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)

        order = OrderBy(expression=measure, direction=SortDirection.ASC)

        dax = order.to_dax()
        assert 'Sales Amount", [Sales Amount]' in dax
        assert "DESC" not in dax

        readable = order.to_human_readable()
        assert "ascending" in readable

    def test_descending_order(self):
        """Test descending order."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)

        order = OrderBy(expression=measure, direction=SortDirection.DESC)

        dax = order.to_dax()
        assert "DESC" in dax

        readable = order.to_human_readable()
        assert "descending" in readable


class TestLimit:
    """Test Limit class."""

    def test_simple_limit(self):
        """Test simple limit."""
        limit = Limit(count=10)

        dax = limit.to_dax()
        assert "TOPN(10" in dax

        readable = limit.to_human_readable()
        assert "limit to 10 rows" == readable

    def test_limit_with_offset(self):
        """Test limit with offset."""
        limit = Limit(count=10, offset=5)

        dax = limit.to_dax()
        assert "TOPN(10" in dax
        assert "5" in dax

        readable = limit.to_human_readable()
        assert "limit to 10 rows starting from row 6" == readable


class TestQuery:
    """Test Query class."""

    def test_basic_query(self):
        """Test basic query creation."""
        cube = CubeReference(name="Test Cube")
        measure = Measure(name="Sales", aggregation=AggregationType.SUM)

        query = Query(cube=cube, measures=[measure], dimensions=[], filters=[])

        assert query.cube == cube
        assert len(query.measures) == 1
        assert len(query.dimensions) == 0
        assert len(query.filters) == 0
        assert isinstance(query.metadata, QueryMetadata)

    def test_query_with_all_components(self):
        """Test query with all components."""
        cube = CubeReference(name="Test Cube")
        measure = Measure(name="Sales", aggregation=AggregationType.SUM)
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        filter_obj = Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=dimension, operator=FilterOperator.EQUALS, values=["Bikes"]
            ),
        )

        order = OrderBy(expression=measure)
        limit = Limit(count=10)

        query = Query(
            cube=cube,
            measures=[measure],
            dimensions=[dimension],
            filters=[filter_obj],
            order_by=[order],
            limit=limit,
        )

        assert len(query.measures) == 1
        assert len(query.dimensions) == 1
        assert len(query.filters) == 1
        assert len(query.order_by) == 1
        assert query.limit is not None
