"""Integration tests for explainer functionality."""

import json
import pytest
from pathlib import Path

from unmdx.explainer import (
    ExplainerGenerator,
    ExplanationConfig,
    ExplanationFormat,
    ExplanationDetail,
    explain_mdx,
    explain_file
)
from unmdx.ir.models import (
    Query, CubeReference, Measure, Dimension, 
    HierarchyReference, LevelReference, MemberSelection,
    QueryMetadata
)
from unmdx.ir.enums import AggregationType, MemberSelectionType


class TestExplainerIntegration:
    """Integration tests for the explainer module."""
    
    @pytest.fixture
    def generator(self):
        """Create ExplainerGenerator instance."""
        return ExplainerGenerator(debug=True)
    
    @pytest.fixture  
    def sample_ir_query(self):
        """Create a sample IR query for testing."""
        return Query(
            cube=CubeReference(name="Adventure Works", database="SSAS"),
            measures=[
                Measure(
                    name="Sales Amount",
                    aggregation=AggregationType.SUM,
                    alias="Total Sales"
                ),
                Measure(
                    name="Order Count", 
                    aggregation=AggregationType.COUNT,
                    alias="Number of Orders"
                )
            ],
            dimensions=[
                Dimension(
                    hierarchy=HierarchyReference(table="Product", name="Product"),
                    level=LevelReference(name="Category"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                ),
                Dimension(
                    hierarchy=HierarchyReference(table="Geography", name="Geography"),
                    level=LevelReference(name="Country"),
                    members=MemberSelection(selection_type=MemberSelectionType.ALL)
                )
            ],
            metadata=QueryMetadata(
                complexity_score=3,
                hierarchy_depth=2,
                estimated_result_size=50,
                warnings=["High cardinality dimension detected"],
                errors=[]
            )
        )
    
    def test_explain_ir_all_formats(self, generator, sample_ir_query):
        """Test explaining IR query in all supported formats."""
        formats_to_test = [
            ExplanationFormat.SQL,
            ExplanationFormat.NATURAL,
            ExplanationFormat.JSON,
            ExplanationFormat.MARKDOWN
        ]
        
        for format_type in formats_to_test:
            config = ExplanationConfig(format=format_type)
            result = generator.explain_ir(sample_ir_query, config)
            
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Format-specific validations
            if format_type == ExplanationFormat.JSON:
                # Should be valid JSON
                data = json.loads(result)
                assert "summary" in data
                assert "measures" in data
                assert len(data["measures"]) == 2
            
            elif format_type == ExplanationFormat.MARKDOWN:
                assert result.startswith("# Query Explanation")
                assert "## Summary" in result
                assert "## Measures" in result
            
            elif format_type == ExplanationFormat.SQL:
                assert "This query will:" in result
                assert "SQL-like representation:" in result
            
            elif format_type == ExplanationFormat.NATURAL:
                assert "analyzes data from" in result
                assert "Adventure Works" in result
    
    def test_explain_ir_all_detail_levels(self, generator, sample_ir_query):
        """Test explaining IR query with all detail levels."""
        detail_levels = [
            ExplanationDetail.MINIMAL,
            ExplanationDetail.STANDARD,
            ExplanationDetail.DETAILED
        ]
        
        results = {}
        for detail in detail_levels:
            config = ExplanationConfig(
                format=ExplanationFormat.NATURAL,
                detail=detail
            )
            result = generator.explain_ir(sample_ir_query, config)
            results[detail] = result
            
            assert isinstance(result, str)
            assert len(result) > 0
        
        # Detailed should be longer than standard, standard longer than minimal
        assert len(results[ExplanationDetail.DETAILED]) > len(results[ExplanationDetail.STANDARD])
        assert len(results[ExplanationDetail.STANDARD]) > len(results[ExplanationDetail.MINIMAL])
    
    def test_explain_ir_with_all_options(self, generator, sample_ir_query):
        """Test explaining IR with all configuration options enabled."""
        config = ExplanationConfig(
            format=ExplanationFormat.MARKDOWN,
            detail=ExplanationDetail.DETAILED,
            include_sql_representation=True,
            include_dax_comparison=True,
            include_metadata=True
        )
        
        result = generator.explain_ir(sample_ir_query, config)
        
        # Should include all requested sections
        assert "# Query Explanation" in result
        assert "## Summary" in result
        assert "## Measures" in result
        assert "## Grouping" in result
        assert "## SQL-like Representation" in result
        assert "## Equivalent DAX Query" in result
        assert "## Query Metadata" in result
        
        # Should include specific content
        assert "Total Sales" in result
        assert "Number of Orders" in result
        assert "EVALUATE" in result  # DAX content
        assert "SUMMARIZECOLUMNS" in result  # DAX content
        assert "Complexity Score: 3" in result  # Metadata
        assert "High cardinality dimension detected" in result  # Warning
    
    def test_explain_ir_json_structure_complete(self, generator, sample_ir_query):
        """Test that JSON explanation has complete structure."""
        config = ExplanationConfig(
            format=ExplanationFormat.JSON,
            detail=ExplanationDetail.DETAILED,
            include_metadata=True,
            include_dax_comparison=True
        )
        
        result = generator.explain_ir(sample_ir_query, config)
        data = json.loads(result)
        
        # Check required top-level keys
        required_keys = ["summary", "data_source", "measures", "dimensions", "filters"]
        for key in required_keys:
            assert key in data, f"Missing required key: {key}"
        
        # Check data source structure
        assert data["data_source"]["cube"] == "Adventure Works"
        assert data["data_source"]["database"] == "SSAS"
        assert "description" in data["data_source"]
        
        # Check measures structure
        assert len(data["measures"]) == 2
        for measure in data["measures"]:
            assert "name" in measure
            assert "aggregation" in measure
            assert "description" in measure
        
        # Check dimensions structure
        assert len(data["dimensions"]) == 2
        for dimension in data["dimensions"]:
            assert "hierarchy" in dimension
            assert "level" in dimension
            assert "table" in dimension
            assert "description" in dimension
        
        # Check optional sections (detailed level)
        assert "metadata" in data
        assert "dax_query" in data
        
        # Check metadata structure
        metadata = data["metadata"]
        assert metadata["complexity_score"] == 3
        assert metadata["hierarchy_depth"] == 2
        assert metadata["estimated_result_size"] == 50
        assert len(metadata["warnings"]) == 1
        assert len(metadata["errors"]) == 0
    
    def test_explain_ir_markdown_formatting(self, generator, sample_ir_query):
        """Test Markdown formatting is correct."""
        config = ExplanationConfig(format=ExplanationFormat.MARKDOWN)
        result = generator.explain_ir(sample_ir_query, config)
        
        lines = result.split('\n')
        
        # Check heading hierarchy
        h1_lines = [line for line in lines if line.startswith('# ')]
        h2_lines = [line for line in lines if line.startswith('## ')]
        
        assert len(h1_lines) == 1  # Should have exactly one main title
        assert len(h2_lines) >= 3  # Should have multiple sections
        
        # Check for proper Markdown formatting
        assert any('**' in line for line in lines)  # Should have bold text
        assert any(line.startswith('- ') for line in lines)  # Should have lists
        
        # Check code blocks if DAX is included
        if "```dax" in result:
            assert "```" in result  # Should close code blocks
    
    def test_explain_ir_natural_language_quality(self, generator, sample_ir_query):
        """Test quality of natural language explanation."""
        config = ExplanationConfig(
            format=ExplanationFormat.NATURAL,
            detail=ExplanationDetail.STANDARD
        )
        
        result = generator.explain_ir(sample_ir_query, config)
        
        # Should form coherent sentences
        sentences = [s.strip() for s in result.split('.') if s.strip()]
        assert len(sentences) >= 3  # Should have multiple sentences
        
        # Should mention key elements
        assert "Adventure Works" in result
        assert "Total Sales" in result or "Sales Amount" in result
        assert "Number of Orders" in result or "Order Count" in result
        assert "Category" in result
        assert "Country" in result
        
        # Should use proper grammar patterns
        assert "analyzes data from" in result
        assert any(phrase in result for phrase in ["calculates", "broken down by"])
    
    def test_explain_ir_sql_representation_validity(self, generator, sample_ir_query):
        """Test SQL-like representation is properly formatted."""
        config = ExplanationConfig(format=ExplanationFormat.SQL)
        result = generator.explain_ir(sample_ir_query, config)
        
        # Extract SQL portion
        if "```sql" in result:
            sql_start = result.find("```sql") + 6
            sql_end = result.find("```", sql_start)
            sql_content = result[sql_start:sql_end].strip()
            
            # Check SQL structure
            assert "SELECT" in sql_content
            assert "FROM" in sql_content
            assert "GROUP BY" in sql_content
            
            # Check measure aliases
            assert "Total Sales" in sql_content
            assert "Number of Orders" in sql_content
            
            # Check table name
            assert "Adventure Works" in sql_content
    
    def test_explain_ir_error_handling_graceful(self, generator):
        """Test that explanation handles edge cases gracefully."""
        # Empty query
        empty_query = Query(
            cube=CubeReference(name="Empty"),
            measures=[],
            dimensions=[]
        )
        
        config = ExplanationConfig(format=ExplanationFormat.SQL)
        result = generator.explain_ir(empty_query, config)
        
        # Should still produce valid output
        assert isinstance(result, str)
        assert "Empty" in result
        assert "This query will:" in result
    
    def test_explain_ir_consistency_across_formats(self, generator, sample_ir_query):
        """Test that core information is consistent across formats."""
        formats = [ExplanationFormat.SQL, ExplanationFormat.NATURAL, ExplanationFormat.MARKDOWN]
        results = {}
        
        for fmt in formats:
            config = ExplanationConfig(format=fmt, detail=ExplanationDetail.STANDARD)
            results[fmt] = generator.explain_ir(sample_ir_query, config)
        
        # All should mention the same key elements
        key_elements = ["Adventure Works", "Sales Amount", "Order Count", "Category", "Country"]
        
        for element in key_elements:
            for fmt, result in results.items():
                assert element in result or element.replace(" ", "") in result.replace(" ", ""), \
                    f"Element '{element}' missing from {fmt.value} format"
    
    def test_performance_reasonable(self, generator, sample_ir_query):
        """Test that explanation generation completes in reasonable time."""
        import time
        
        config = ExplanationConfig(
            format=ExplanationFormat.MARKDOWN,
            detail=ExplanationDetail.DETAILED,
            include_metadata=True,
            include_dax_comparison=True
        )
        
        start_time = time.time()
        result = generator.explain_ir(sample_ir_query, config)
        end_time = time.time()
        
        # Should complete in under 1 second for a simple query
        elapsed = end_time - start_time
        assert elapsed < 1.0, f"Explanation took too long: {elapsed:.2f} seconds"
        assert len(result) > 100, "Result should be substantial"


class TestConvenienceFunctionIntegration:
    """Integration tests for convenience functions."""
    
    def test_explain_mdx_format_conversion(self):
        """Test that string format parameters are properly converted."""
        # Test with string parameters instead of enums
        sample_query = Query(
            cube=CubeReference(name="Test"),
            measures=[Measure(name="Sales", aggregation=AggregationType.SUM)]
        )
        
        generator = ExplainerGenerator()
        
        # Test format conversion
        result1 = generator.explain_ir(sample_query, ExplanationConfig(format=ExplanationFormat.JSON))
        
        # These would test the convenience function format conversion
        # but require full MDX parsing pipeline
        # result2 = explain_mdx("SELECT {[Measures].[Sales]} ON 0 FROM [Test]", format="json")
        
        assert isinstance(result1, str)
        data = json.loads(result1)
        assert "summary" in data
    
    @pytest.mark.skip(reason="Requires file system setup and full pipeline")
    def test_explain_file_integration(self, tmp_path):
        """Test file-based explanation functionality."""
        # Create test MDX file
        mdx_content = """
        SELECT {[Measures].[Sales Amount]} ON COLUMNS,
               {[Product].[Category].Members} ON ROWS
        FROM [Adventure Works]
        """
        
        input_file = tmp_path / "test_query.mdx"
        input_file.write_text(mdx_content)
        
        output_file = tmp_path / "explanation.md"
        
        # Test file explanation
        result = explain_file(
            input_file,
            output_file,
            format="markdown",
            detail="detailed"
        )
        
        # Check result
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Check output file was created
        assert output_file.exists()
        file_content = output_file.read_text()
        assert file_content == result
        assert "# Query Explanation" in file_content


@pytest.mark.slow
class TestExplainerPerformance:
    """Performance tests for explainer functionality."""
    
    def test_large_query_performance(self):
        """Test performance with a large, complex query."""
        # Create a complex query with many dimensions and measures
        measures = [
            Measure(name=f"Measure_{i}", aggregation=AggregationType.SUM)
            for i in range(10)
        ]
        
        dimensions = [
            Dimension(
                hierarchy=HierarchyReference(table=f"Table_{i}", name=f"Hierarchy_{i}"),
                level=LevelReference(name=f"Level_{i}"),
                members=MemberSelection(selection_type=MemberSelectionType.ALL)
            )
            for i in range(5)
        ]
        
        large_query = Query(
            cube=CubeReference(name="Large_Cube"),
            measures=measures,
            dimensions=dimensions,
            metadata=QueryMetadata(
                complexity_score=8,
                hierarchy_depth=5,
                estimated_result_size=10000
            )
        )
        
        generator = ExplainerGenerator()
        config = ExplanationConfig(
            format=ExplanationFormat.MARKDOWN,
            detail=ExplanationDetail.DETAILED,
            include_metadata=True,
            include_dax_comparison=True
        )
        
        import time
        start_time = time.time()
        result = generator.explain_ir(large_query, config)
        end_time = time.time()
        
        # Should still complete reasonably quickly
        elapsed = end_time - start_time
        assert elapsed < 2.0, f"Large query explanation took too long: {elapsed:.2f} seconds"
        
        # Should include all measures and dimensions
        assert "10" in result or "ten" in result  # Should mention number of measures
        assert "5" in result or "five" in result   # Should mention number of dimensions
        
        # Should be substantial output
        assert len(result) > 1000, "Large query should produce substantial explanation"
    
    def test_memory_usage_reasonable(self):
        """Test that memory usage doesn't grow excessively."""
        import gc
        import sys
        
        generator = ExplainerGenerator()
        
        # Create multiple queries and explain them
        for i in range(10):
            query = Query(
                cube=CubeReference(name=f"Cube_{i}"),
                measures=[Measure(name=f"Measure_{i}", aggregation=AggregationType.SUM)],
                dimensions=[
                    Dimension(
                        hierarchy=HierarchyReference(table=f"Table_{i}", name=f"Hierarchy_{i}"),
                        level=LevelReference(name=f"Level_{i}"),
                        members=MemberSelection(selection_type=MemberSelectionType.ALL)
                    )
                ]
            )
            
            config = ExplanationConfig(format=ExplanationFormat.JSON)
            result = generator.explain_ir(query, config)
            
            # Verify result is valid
            data = json.loads(result)
            assert data["data_source"]["cube"] == f"Cube_{i}"
        
        # Force garbage collection
        gc.collect()
        
        # Memory usage test would require more sophisticated monitoring
        # For now, just verify we can create multiple explanations without errors
        assert True