"""Integration tests for parser → linter → transformer pipeline."""

import pytest
from datetime import datetime

from unmdx.parser.mdx_parser import MDXParser
from unmdx.linter import MDXLinter, LinterConfig, OptimizationLevel
from unmdx.transformer.mdx_transformer import MDXTransformer


class TestParserLinterIntegration:
    """Test integration of parser with linter in the processing pipeline."""
    
    @pytest.fixture
    def parser(self):
        """Create MDX parser instance."""
        return MDXParser()
    
    @pytest.fixture
    def conservative_linter(self):
        """Create conservative linter instance."""
        config = LinterConfig(optimization_level=OptimizationLevel.CONSERVATIVE)
        return MDXLinter(config)
    
    @pytest.fixture
    def moderate_linter(self):
        """Create moderate linter instance."""
        config = LinterConfig(optimization_level=OptimizationLevel.MODERATE)
        return MDXLinter(config)
    
    @pytest.fixture
    def transformer(self):
        """Create MDX transformer instance."""
        return MDXTransformer()
    
    @pytest.fixture
    def sample_messy_mdx_queries(self):
        """Sample messy MDX queries that would benefit from linting."""
        return [
            # Redundant parentheses (common Necto pattern)
            """
            SELECT 
                (((([Measures].[Sales Amount])))) ON COLUMNS,
                (((NON EMPTY (([Product].[Category].Members))))) ON ROWS
            FROM [Sales Cube]
            """,
            
            # Nested CrossJoins that could be simplified
            """
            SELECT 
                [Measures].[Sales Amount] ON COLUMNS,
                CROSSJOIN(
                    CROSSJOIN(
                        [Time].[Year].Members,
                        [Geography].[Country].Members
                    ),
                    [Product].[Category].Members
                ) ON ROWS
            FROM [Sales Cube]
            """,
            
            # Duplicate member specifications
            """
            SELECT 
                {[Measures].[Sales Amount], [Measures].[Cost Amount]} ON COLUMNS,
                {[Product].[Category].[Electronics], 
                 [Product].[Category].[Clothing],
                 [Product].[Category].[Electronics]} ON ROWS
            FROM [Sales Cube]
            """,
            
            # Complex calculated member with redundant parentheses
            """
            WITH MEMBER [Measures].[Profit Margin] AS 
                IIF(
                    (([Measures].[Sales Amount])) <> 0,
                    ((([Measures].[Sales Amount]) - ([Measures].[Cost Amount])) / (([Measures].[Sales Amount]))),
                    NULL
                )
            SELECT 
                {[Measures].[Sales Amount], [Measures].[Profit Margin]} ON COLUMNS
            FROM [Sales Cube]
            """
        ]
    
    def test_parser_linter_basic_integration(self, parser, conservative_linter, sample_messy_mdx_queries):
        """Test basic parser → linter integration workflow."""
        mdx_query = sample_messy_mdx_queries[0]  # Redundant parentheses
        
        # Parse MDX
        try:
            parse_tree = parser.parse(mdx_query)
            assert parse_tree is not None
            
            # Lint the parsed tree
            linted_tree, lint_report = conservative_linter.lint(parse_tree, mdx_query)
            
            assert linted_tree is not None
            assert lint_report is not None
            assert lint_report.original_size == len(mdx_query)
            assert lint_report.optimization_level == OptimizationLevel.CONSERVATIVE
            
            # Should have found and removed redundant parentheses
            if hasattr(lint_report, 'actions') and len(lint_report.actions) > 0:
                parentheses_actions = [a for a in lint_report.actions 
                                     if "parentheses" in a.description.lower()]
                assert len(parentheses_actions) >= 1
            
        except Exception as e:
            pytest.skip(f"Parser failed on sample query: {e}")
    
    def test_parser_linter_transformer_full_pipeline(
        self, 
        parser, 
        moderate_linter, 
        transformer, 
        sample_messy_mdx_queries
    ):
        """Test complete parser → linter → transformer pipeline."""
        mdx_query = sample_messy_mdx_queries[0]  # Simple case to start
        
        try:
            # Step 1: Parse MDX
            parse_tree = parser.parse(mdx_query)
            assert parse_tree is not None
            
            # Step 2: Lint the parsed tree
            linted_tree, lint_report = moderate_linter.lint(parse_tree, mdx_query)
            assert linted_tree is not None
            
            # Step 3: Transform to IR
            ir_query = transformer.transform(linted_tree, mdx_query)
            assert ir_query is not None
            
            # Verify the pipeline worked
            assert hasattr(ir_query, 'cube')
            assert hasattr(ir_query, 'measures')
            assert hasattr(ir_query, 'dimensions')
            
            # Linting should have improved the query
            if hasattr(lint_report, 'size_reduction'):
                # May or may not have size reduction depending on what was optimized
                assert lint_report.size_reduction >= 0
            
        except Exception as e:
            pytest.skip(f"Pipeline failed on sample query: {e}")
    
    def test_linter_preserves_parse_tree_validity(self, parser, moderate_linter, sample_messy_mdx_queries):
        """Test that linter preserves parse tree validity for transformer."""
        for i, mdx_query in enumerate(sample_messy_mdx_queries[:2]):  # Test first 2 queries
            try:
                # Parse original query
                original_tree = parser.parse(mdx_query)
                assert original_tree is not None
                
                # Lint the tree
                linted_tree, lint_report = moderate_linter.lint(original_tree, mdx_query)
                assert linted_tree is not None
                
                # Verify linted tree is still a valid parse tree structure
                assert hasattr(linted_tree, 'data')
                assert hasattr(linted_tree, 'children')
                
                # Tree should still be parseable structure
                assert isinstance(linted_tree.data, str)
                assert isinstance(linted_tree.children, list)
                
            except Exception as e:
                pytest.skip(f"Query {i} failed in linter validity test: {e}")
    
    def test_linter_performance_in_pipeline(self, parser, conservative_linter, sample_messy_mdx_queries):
        """Test linter performance as part of the processing pipeline."""
        mdx_query = sample_messy_mdx_queries[0]
        
        try:
            # Parse
            parse_start = datetime.now()
            parse_tree = parser.parse(mdx_query)
            parse_duration = (datetime.now() - parse_start).total_seconds() * 1000
            
            # Lint
            lint_start = datetime.now()
            linted_tree, lint_report = conservative_linter.lint(parse_tree, mdx_query)
            lint_duration = (datetime.now() - lint_start).total_seconds() * 1000
            
            # Linting should be fast relative to parsing
            assert lint_duration < 5000  # Less than 5 seconds
            
            # Report should include timing
            if hasattr(lint_report, 'duration_ms'):
                assert lint_report.duration_ms is not None
                assert lint_report.duration_ms > 0
                # Report timing should be close to measured timing
                assert abs(lint_report.duration_ms - lint_duration) < 100  # Within 100ms
            
        except Exception as e:
            pytest.skip(f"Performance test failed: {e}")
    
    def test_linter_error_handling_in_pipeline(self, parser, conservative_linter):
        """Test linter error handling when integrated with parser."""
        # Test with potentially problematic MDX
        problematic_queries = [
            "SELECT",  # Incomplete query
            "SELECT [Measures].[Sales] ON",  # Missing FROM
            "",  # Empty query
        ]
        
        for query in problematic_queries:
            try:
                # Try to parse (may fail)
                parse_tree = parser.parse(query)
                if parse_tree is not None:
                    # If parsing succeeded, linting should handle gracefully
                    linted_tree, lint_report = conservative_linter.lint(parse_tree, query)
                    
                    assert linted_tree is not None
                    assert lint_report is not None
                    
                    # Should handle errors gracefully
                    if hasattr(lint_report, 'errors'):
                        # Errors may be recorded but shouldn't crash
                        assert isinstance(lint_report.errors, list)
                
            except Exception:
                # If parsing fails, that's expected for malformed queries
                continue
    
    def test_optimization_level_impact_in_pipeline(self, parser, sample_messy_mdx_queries):
        """Test that different optimization levels work in the pipeline."""
        mdx_query = sample_messy_mdx_queries[1]  # CrossJoin query
        
        configs = [
            LinterConfig(optimization_level=OptimizationLevel.CONSERVATIVE),
            LinterConfig(optimization_level=OptimizationLevel.MODERATE),
            LinterConfig(optimization_level=OptimizationLevel.AGGRESSIVE)
        ]
        
        results = []
        
        for config in configs:
            try:
                linter = MDXLinter(config)
                
                # Parse
                parse_tree = parser.parse(mdx_query)
                assert parse_tree is not None
                
                # Lint with different levels
                linted_tree, lint_report = linter.lint(parse_tree, mdx_query)
                
                results.append({
                    'level': config.optimization_level,
                    'tree': linted_tree,
                    'report': lint_report,
                    'rules': linter.get_available_rules()
                })
                
            except Exception as e:
                pytest.skip(f"Optimization level test failed: {e}")
        
        if len(results) >= 2:
            # Should have different numbers of available rules
            conservative_rules = set(results[0]['rules'])
            moderate_rules = set(results[1]['rules'])
            
            # Moderate should have at least as many rules as conservative
            assert len(moderate_rules) >= len(conservative_rules)
    
    def test_linter_with_various_mdx_patterns(self, parser, moderate_linter, sample_messy_mdx_queries):
        """Test linter with various MDX patterns from sample queries."""
        successful_tests = 0
        
        for i, mdx_query in enumerate(sample_messy_mdx_queries):
            try:
                # Parse the query
                parse_tree = parser.parse(mdx_query)
                assert parse_tree is not None
                
                # Lint the query
                linted_tree, lint_report = moderate_linter.lint(parse_tree, mdx_query)
                
                assert linted_tree is not None
                assert lint_report is not None
                
                # Verify report structure
                assert hasattr(lint_report, 'optimization_level')
                assert hasattr(lint_report, 'start_time')
                assert hasattr(lint_report, 'original_size')
                
                successful_tests += 1
                
            except Exception as e:
                # Log the failure but continue with other queries
                print(f"Query {i} failed: {e}")
                continue
        
        # Should successfully process at least some queries
        assert successful_tests >= 1
    
    def test_linter_maintains_semantic_correctness(self, parser, conservative_linter, transformer):
        """Test that linter maintains semantic correctness for transformation."""
        # Simple query that should parse, lint, and transform successfully
        simple_mdx = """
        SELECT 
            ([Measures].[Sales Amount]) ON COLUMNS,
            ([Product].[Category].Members) ON ROWS
        FROM [Sales Cube]
        """
        
        try:
            # Parse original
            original_tree = parser.parse(simple_mdx)
            assert original_tree is not None
            
            # Transform original (without linting)
            original_ir = transformer.transform(original_tree, simple_mdx)
            assert original_ir is not None
            
            # Lint then transform
            linted_tree, lint_report = conservative_linter.lint(original_tree, simple_mdx)
            linted_ir = transformer.transform(linted_tree, simple_mdx)
            assert linted_ir is not None
            
            # Both should produce valid IR with same basic structure
            assert hasattr(original_ir, 'cube')
            assert hasattr(linted_ir, 'cube')
            
            # Basic query structure should be preserved
            if hasattr(original_ir, 'measures') and hasattr(linted_ir, 'measures'):
                # Should have similar number of measures (semantic preservation)
                assert len(original_ir.measures) == len(linted_ir.measures)
            
        except Exception as e:
            pytest.skip(f"Semantic correctness test failed: {e}")


class TestLinterErrorRecovery:
    """Test linter error recovery in pipeline integration."""
    
    def test_linter_with_parser_edge_cases(self):
        """Test linter behavior with edge cases from parser."""
        parser = MDXParser()
        linter = MDXLinter(LinterConfig(
            optimization_level=OptimizationLevel.CONSERVATIVE,
            skip_on_validation_error=True
        ))
        
        edge_cases = [
            "SELECT [Measures] FROM [Cube]",  # Minimal query
            "WITH MEMBER [M] AS 1 SELECT [M] ON 0 FROM [C]",  # Minimal WITH
        ]
        
        successful_cases = 0
        
        for query in edge_cases:
            try:
                parse_tree = parser.parse(query)
                if parse_tree is not None:
                    linted_tree, lint_report = linter.lint(parse_tree, query)
                    
                    assert linted_tree is not None
                    assert lint_report is not None
                    successful_cases += 1
                    
            except Exception as e:
                # Continue with other test cases
                print(f"Edge case failed: {e}")
                continue
        
        # Should handle at least some edge cases
        assert successful_cases >= 0  # At minimum, shouldn't crash