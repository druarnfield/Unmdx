"""Unit tests for human-readable explanation generator."""

import pytest

from unmdx.explainer.generator import HumanReadableGenerator
from unmdx.ir.models import (
    AggregationType,
    Calculation,
    CalculationType,
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
    MeasureReference,
    MemberSelection,
    MemberSelectionType,
    OrderBy,
    Query,
    QueryMetadata,
    SortDirection,
)


class TestHumanReadableGenerator:
    """Test human-readable explanation generation."""

    @pytest.fixture
    def generator(self):
        """Create explanation generator instance."""
        return HumanReadableGenerator()

    def test_simple_measure_query(self, generator):
        """Test explanation for simple measure query."""
        query = Query(
            cube=CubeReference(name="Sales Data"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        assert "This query will:" in explanation
        assert "Calculate: total Sales Amount" in explanation
        assert "SQL-like representation:" in explanation
        assert "SELECT" in explanation
        assert "FROM Sales Data" in explanation

    def test_dimensional_query(self, generator):
        """Test explanation for dimensional query."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        query = Query(
            cube=CubeReference(name="Sales Data"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[dimension],
            filters=[],
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        assert "Calculate: total Sales Amount" in explanation
        assert "Grouped by: each Category" in explanation
        assert "GROUP BY Category" in explanation

    def test_query_with_filters(self, generator):
        """Test explanation for query with filters."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Date", name="Date"),
            level=LevelReference(name="Year"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        filter_obj = Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=dimension, operator=FilterOperator.EQUALS, values=["2023"]
            ),
        )

        query = Query(
            cube=CubeReference(name="Sales Data"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[filter_obj],
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        assert "Where:" in explanation
        assert "Year equals 2023" in explanation
        assert "WHERE Year equals 2023" in explanation

    def test_query_with_calculations(self, generator):
        """Test explanation for query with calculations."""
        calc = Calculation(
            name="Profit Margin",
            calculation_type=CalculationType.MEASURE,
            expression=MeasureReference("Profit"),
        )

        query = Query(
            cube=CubeReference(name="Sales Data"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM),
                Measure(name="Profit Margin", aggregation=AggregationType.CUSTOM),
            ],
            dimensions=[],
            filters=[],
            calculations=[calc],
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        assert "With these calculations:" in explanation
        assert "Calculate Profit Margin as" in explanation

    def test_query_with_sorting(self, generator):
        """Test explanation for query with sorting."""
        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        order = OrderBy(expression=measure, direction=SortDirection.DESC)

        query = Query(
            cube=CubeReference(name="Sales Data"),
            measures=[measure],
            dimensions=[],
            filters=[],
            order_by=[order],
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        assert "Sorted by:" in explanation
        assert "descending" in explanation
        assert "ORDER BY" in explanation

    def test_query_with_limit(self, generator):
        """Test explanation for query with limit."""
        query = Query(
            cube=CubeReference(name="Sales Data"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[],
            limit=Limit(count=10),
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        assert "limit to 10 rows" in explanation
        assert "LIMIT 10" in explanation

    def test_complex_query(self, generator):
        """Test explanation for complex query with all components."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        filter_obj = Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=dimension,
                operator=FilterOperator.IN,
                values=["Bikes", "Components"],
            ),
        )

        measure = Measure(name="Sales Amount", aggregation=AggregationType.SUM)
        order = OrderBy(expression=measure, direction=SortDirection.DESC)

        query = Query(
            cube=CubeReference(name="Adventure Works"),
            measures=[measure],
            dimensions=[dimension],
            filters=[filter_obj],
            order_by=[order],
            limit=Limit(count=5),
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        # Check all components are mentioned
        assert "Calculate: total Sales Amount" in explanation
        assert "Grouped by: each Category" in explanation
        assert "Where:" in explanation
        assert "Category is one of (Bikes, Components)" in explanation
        assert "Sorted by:" in explanation
        assert "descending" in explanation
        assert "limit to 5 rows" in explanation

        # Check SQL structure
        sql_part = explanation[
            explanation.find("```sql") : explanation.find(
                "```", explanation.find("```sql") + 1
            )
        ]
        assert "SELECT Category" in sql_part
        assert "FROM Adventure Works" in sql_part
        assert "WHERE" in sql_part
        assert "GROUP BY Category" in sql_part
        assert "ORDER BY" in sql_part
        assert "LIMIT 5" in sql_part

    def test_multiple_measures_explanation(self, generator):
        """Test explanation for multiple measures."""
        query = Query(
            cube=CubeReference(name="Sales Data"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM),
                Measure(name="Order Count", aggregation=AggregationType.COUNT),
                Measure(name="Average Order", aggregation=AggregationType.AVG),
            ],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        assert "total Sales Amount" in explanation
        assert "count of Order Count" in explanation
        assert "average Average Order" in explanation

    def test_multiple_filters_explanation(self, generator):
        """Test explanation for multiple filters."""
        dim1 = Dimension(
            hierarchy=HierarchyReference(table="Date", name="Date"),
            level=LevelReference(name="Year"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        dim2 = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        filter1 = Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=dim1, operator=FilterOperator.EQUALS, values=["2023"]
            ),
        )

        filter2 = Filter(
            filter_type=FilterType.DIMENSION,
            target=DimensionFilter(
                dimension=dim2,
                operator=FilterOperator.IN,
                values=["Bikes", "Components"],
            ),
        )

        query = Query(
            cube=CubeReference(name="Sales Data"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[filter1, filter2],
            metadata=QueryMetadata(),
        )

        explanation = generator.generate(query)

        assert "Where:" in explanation
        assert "Year equals 2023" in explanation
        assert "Category is one of (Bikes, Components)" in explanation
        assert (
            "WHERE Year equals 2023 AND Category is one of (Bikes, Components)"
            in explanation
        )


class TestSQLLikeGeneration:
    """Test SQL-like syntax generation specifically."""

    @pytest.fixture
    def generator(self):
        """Create explanation generator instance."""
        return HumanReadableGenerator()

    def test_basic_sql_structure(self, generator):
        """Test basic SQL structure generation."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        sql = generator._generate_sql_like(query)
        lines = sql.strip().split("\n")

        assert lines[0].startswith("SELECT")
        assert any(line.startswith("FROM") for line in lines)
        assert "SUM(Sales) AS Sales" in sql

    def test_sql_with_dimensions(self, generator):
        """Test SQL generation with dimensions."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales", aggregation=AggregationType.SUM)],
            dimensions=[dimension],
            filters=[],
            metadata=QueryMetadata(),
        )

        sql = generator._generate_sql_like(query)

        assert "SELECT Category, SUM(Sales) AS Sales" in sql
        assert "GROUP BY Category" in sql

    def test_sql_with_custom_aggregation(self, generator):
        """Test SQL generation with custom aggregation."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[
                Measure(
                    name="Profit Margin",
                    aggregation=AggregationType.CUSTOM,
                    alias="Margin %",
                )
            ],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        sql = generator._generate_sql_like(query)

        # Custom measures should use alias directly
        assert "SELECT Margin %" in sql
        assert "SUM(" not in sql

    def test_sql_with_limit_and_offset(self, generator):
        """Test SQL generation with limit and offset."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[],
            limit=Limit(count=10, offset=5),
            metadata=QueryMetadata(),
        )

        sql = generator._generate_sql_like(query)

        assert "LIMIT 10 OFFSET 5" in sql
