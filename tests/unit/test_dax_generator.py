"""Unit tests for DAX generator."""

import pytest

from unmdx.dax_generator.generator import DaxGenerator
from unmdx.ir.models import (
    AggregationType,
    CubeReference,
    Dimension,
    DimensionFilter,
    Filter,
    FilterOperator,
    FilterType,
    HierarchyReference,
    LevelReference,
    Measure,
    MemberSelection,
    MemberSelectionType,
    Query,
    QueryMetadata,
)


class TestDaxGenerator:
    """Test DAX query generation."""

    @pytest.fixture
    def generator(self):
        """Create DAX generator instance."""
        return DaxGenerator()

    def test_simple_measure_query(self, generator):
        """Test generating DAX for simple measure query."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        dax = generator.generate(query)

        assert "EVALUATE" in dax
        assert "ROW(" in dax
        assert "Sales Amount" in dax
        assert "[Sales Amount]" in dax

    def test_dimensional_query(self, generator):
        """Test generating DAX for dimensional query."""
        dimension = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[dimension],
            filters=[],
            metadata=QueryMetadata(),
        )

        dax = generator.generate(query)

        assert "EVALUATE" in dax
        assert "SUMMARIZECOLUMNS(" in dax
        assert "Product[Category]" in dax
        assert "Sales Amount" in dax

    def test_query_with_filters(self, generator):
        """Test generating DAX for query with filters."""
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

        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[dimension],
            filters=[filter_obj],
            metadata=QueryMetadata(),
        )

        dax = generator.generate(query)

        assert "SUMMARIZECOLUMNS(" in dax
        assert "FILTER(ALL(Product)" in dax
        assert 'Product[Category] = "Bikes"' in dax

    def test_multiple_measures(self, generator):
        """Test generating DAX for multiple measures."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[
                Measure(name="Sales Amount", aggregation=AggregationType.SUM),
                Measure(name="Order Count", aggregation=AggregationType.COUNT),
            ],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        dax = generator.generate(query)

        assert "Sales Amount" in dax
        assert "Order Count" in dax
        assert dax.count('"') >= 4  # At least 4 quotes for 2 measures

    def test_multiple_dimensions(self, generator):
        """Test generating DAX for multiple dimensions."""
        dim1 = Dimension(
            hierarchy=HierarchyReference(table="Product", name="Product"),
            level=LevelReference(name="Category"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        dim2 = Dimension(
            hierarchy=HierarchyReference(table="Date", name="Date"),
            level=LevelReference(name="Year"),
            members=MemberSelection(selection_type=MemberSelectionType.ALL),
        )

        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[dim1, dim2],
            filters=[],
            metadata=QueryMetadata(),
        )

        dax = generator.generate(query)

        assert "Product[Category]" in dax
        assert "Date[Year]" in dax
        assert "SUMMARIZECOLUMNS(" in dax

    def test_measure_with_alias(self, generator):
        """Test generating DAX for measure with alias."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[
                Measure(
                    name="Sales Amount",
                    aggregation=AggregationType.SUM,
                    alias="Total Sales",
                )
            ],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        dax = generator.generate(query)

        assert "Total Sales" in dax
        assert "[Sales Amount]" in dax

    def test_empty_query(self, generator):
        """Test generating DAX for query with no measures."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        dax = generator.generate(query)

        assert "EVALUATE" in dax
        assert "ROW(" in dax
        assert "BLANK()" in dax

    def test_dax_structure(self, generator):
        """Test overall DAX structure."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales Amount", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        dax = generator.generate(query)
        lines = dax.strip().split("\n")

        # Should start with EVALUATE
        assert lines[0].strip() == "EVALUATE"

        # Should have proper structure
        assert any("ROW(" in line for line in lines)


class TestSummarizeColumnsGeneration:
    """Test SUMMARIZECOLUMNS generation specifically."""

    @pytest.fixture
    def generator(self):
        """Create DAX generator instance."""
        return DaxGenerator()

    def test_summarizecolumns_basic(self, generator):
        """Test basic SUMMARIZECOLUMNS generation."""
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

        result = generator._generate_summarizecolumns(query)

        assert result.startswith("SUMMARIZECOLUMNS(")
        assert result.endswith(")")
        assert "Product[Category]" in result
        assert "Sales" in result

    def test_summarizecolumns_with_filter(self, generator):
        """Test SUMMARIZECOLUMNS with filters."""
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

        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales", aggregation=AggregationType.SUM)],
            dimensions=[dimension],
            filters=[filter_obj],
            metadata=QueryMetadata(),
        )

        result = generator._generate_summarizecolumns(query)

        assert "FILTER(ALL(Product)" in result
        assert 'Product[Category] = "Bikes"' in result


class TestMeasureTableGeneration:
    """Test simple measure table generation."""

    @pytest.fixture
    def generator(self):
        """Create DAX generator instance."""
        return DaxGenerator()

    def test_single_measure_table(self, generator):
        """Test single measure table generation."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[Measure(name="Sales", aggregation=AggregationType.SUM)],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        result = generator._generate_measure_table(query)

        assert result.startswith("ROW(")
        assert result.endswith(")")
        assert "Sales" in result
        assert "[Sales]" in result

    def test_multiple_measures_table(self, generator):
        """Test multiple measures table generation."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[
                Measure(name="Sales", aggregation=AggregationType.SUM),
                Measure(
                    name="Profit", aggregation=AggregationType.SUM, alias="Total Profit"
                ),
            ],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        result = generator._generate_measure_table(query)

        assert result.startswith("ROW(")
        assert "Sales" in result
        assert "Total Profit" in result
        assert "[Profit]" in result

    def test_empty_measures_table(self, generator):
        """Test empty measures table generation."""
        query = Query(
            cube=CubeReference(name="Test Cube"),
            measures=[],
            dimensions=[],
            filters=[],
            metadata=QueryMetadata(),
        )

        result = generator._generate_measure_table(query)

        assert result == 'ROW("Result", BLANK())'
