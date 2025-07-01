"""Unit tests for comment and hint extraction."""

import pytest
from lark import Tree, Token

from unmdx.transformer.comment_extractor import (
    CommentExtractor, CommentHint, HintType
)


class TestCommentExtractor:
    """Test comment extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = CommentExtractor()
    
    def test_extract_performance_hints(self):
        """Test extracting performance-related hints."""
        source_mdx = """
        /* Performance: This query is slow due to large dimension */
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        // Optimize: Consider adding filters
        """
        
        hints = self.extractor.extract_hints(Tree('query', []), source_mdx)
        
        performance_hints = [h for h in hints if h.hint_type == HintType.PERFORMANCE]
        assert len(performance_hints) >= 1
        
        perf_hint = performance_hints[0]
        assert "slow due to large dimension" in perf_hint.message
        assert perf_hint.severity in ["INFO", "WARNING", "ERROR"]
    
    def test_extract_caching_hints(self):
        """Test extracting caching-related hints."""
        source_mdx = """
        -- Cache: This result should be cached for 1 hour
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        /* Materialized view would improve performance */
        """
        
        hints = self.extractor.extract_hints(Tree('query', []), source_mdx)
        
        caching_hints = [h for h in hints if h.hint_type == HintType.CACHING]
        assert len(caching_hints) >= 1
        
        cache_hint = caching_hints[0]
        assert "cached for 1 hour" in cache_hint.message
    
    def test_extract_aggregation_hints(self):
        """Test extracting aggregation-related hints."""
        source_mdx = """
        /* Aggregation: Pre-aggregate at monthly level */
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        // Group by product category for better performance
        """
        
        hints = self.extractor.extract_hints(Tree('query', []), source_mdx)
        
        agg_hints = [h for h in hints if h.hint_type == HintType.AGGREGATION]
        assert len(agg_hints) >= 1
    
    def test_extract_filter_hints(self):
        """Test extracting filter-related hints."""
        source_mdx = """
        -- Filter: Push down date filters to improve performance
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        WHERE [Date].[Calendar Year].&[2023]
        """
        
        hints = self.extractor.extract_hints(Tree('query', []), source_mdx)
        
        filter_hints = [h for h in hints if h.hint_type == HintType.FILTER_PUSH_DOWN]
        assert len(filter_hints) >= 1
    
    def test_extract_custom_hints(self):
        """Test extracting custom/general hints."""
        source_mdx = """
        /* TODO: Optimize this query for production */
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        // FIXME: Handle null values properly
        -- NOTE: This query is used in the daily report
        """
        
        hints = self.extractor.extract_hints(Tree('query', []), source_mdx)
        
        custom_hints = [h for h in hints if h.hint_type == HintType.CUSTOM]
        assert len(custom_hints) >= 2  # TODO and FIXME should be captured
    
    def test_severity_detection(self):
        """Test severity level detection from comments."""
        test_cases = [
            ("ERROR: Critical issue with query", "ERROR"),
            ("WARNING: Performance may be slow", "WARNING"),
            ("This is just informational", "INFO"),
            ("CRITICAL: System failure", "ERROR"),
            ("Issue with data quality", "WARNING")
        ]
        
        for comment_text, expected_severity in test_cases:
            severity = self.extractor._determine_severity(comment_text)
            assert severity == expected_severity
    
    def test_extract_query_metadata(self):
        """Test extracting query metadata from comments."""
        source_mdx = """
        /*
         * Author: John Doe
         * Created: 2023-01-15
         * Purpose: Monthly sales analysis
         * Data Source: Adventure Works DW
         * Frequency: Daily
         */
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        """
        
        metadata = self.extractor.extract_query_metadata(Tree('query', []), source_mdx)
        
        assert metadata.get('author') == 'John Doe'
        assert metadata.get('created') == '2023-01-15'
        assert metadata.get('purpose') == 'Monthly sales analysis'
        assert metadata.get('data_source') == 'Adventure Works DW'
        assert metadata.get('frequency') == 'Daily'
    
    def test_extract_performance_warnings(self):
        """Test extracting performance warnings specifically."""
        source_mdx = """
        /* Performance: WARNING - This query scans entire fact table */
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        // Performance: ERROR - Memory usage exceeds limits
        """
        
        warnings = self.extractor.get_performance_warnings(Tree('query', []), source_mdx)
        
        assert len(warnings) >= 1
        assert any("scans entire fact table" in w for w in warnings)
    
    def test_extract_from_tree_comments(self):
        """Test extracting hints from parse tree comment nodes."""
        # Create tree with comment nodes
        comment1 = Tree('comment', [Token('COMMENT', '/* Performance: Slow query */')])
        comment2 = Tree('comment', [Token('COMMENT', '// Cache: Enable caching')])
        query_tree = Tree('query', [comment1, comment2])
        
        hints = self.extractor.extract_hints(query_tree)
        
        assert len(hints) >= 2
        hint_types = [h.hint_type for h in hints]
        assert HintType.PERFORMANCE in hint_types
        assert HintType.CACHING in hint_types
    
    def test_extract_comments_from_source(self):
        """Test extracting comments from source MDX text."""
        source_mdx = """
        /* Block comment line 1
           Block comment line 2 */
        SELECT [Sales Amount] ON COLUMNS
        -- Line comment
        FROM [Adventure Works]
        // Another line comment
        /* Single line block comment */
        """
        
        comments = self.extractor._extract_comments_from_source(source_mdx)
        
        assert len(comments) >= 4  # Should find multiple comments
        
        # Check line numbers are captured
        line_numbers = [line_num for line_num, _ in comments]
        assert 1 in line_numbers  # First block comment
    
    def test_multiline_block_comments(self):
        """Test handling multi-line block comments."""
        source_mdx = """
        /*
         * This is a multi-line
         * block comment with
         * performance hints: Optimize for speed
         */
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        """
        
        hints = self.extractor.extract_hints(Tree('query', []), source_mdx)
        
        # Should find the performance hint
        perf_hints = [h for h in hints if h.hint_type == HintType.PERFORMANCE]
        assert len(perf_hints) >= 1
        assert "Optimize for speed" in perf_hints[0].message
    
    def test_comment_deduplication(self):
        """Test deduplication of similar hints."""
        source_mdx = """
        /* Performance: This query is slow */
        SELECT [Sales Amount] ON COLUMNS
        FROM [Adventure Works]
        -- Performance: This query is slow
        """
        
        hints = self.extractor.extract_hints(Tree('query', []), source_mdx)
        
        # Should deduplicate identical hints
        perf_hints = [h for h in hints if h.hint_type == HintType.PERFORMANCE]
        unique_messages = set(h.message for h in perf_hints)
        assert len(unique_messages) == 1  # Should be deduplicated
    
    def test_important_keyword_detection(self):
        """Test detection of important keywords in comments."""
        important_comments = [
            "TODO: Fix this later",
            "FIXME: Broken functionality",
            "HACK: Temporary workaround",
            "BUG: Data quality issue",
            "IMPORTANT: Critical business logic"
        ]
        
        for comment in important_comments:
            is_important = self.extractor._is_important_comment(comment)
            assert is_important, f"Comment '{comment}' should be marked as important"
    
    def test_hint_pattern_matching(self):
        """Test hint pattern matching for different types."""
        test_cases = [
            ("Performance: Query is slow", HintType.PERFORMANCE),
            ("Cache this result", HintType.CACHING),
            ("Index needed on date column", HintType.INDEX),
            ("Aggregation should be pre-computed", HintType.AGGREGATION),
            ("Filter push down optimization", HintType.FILTER_PUSH_DOWN),
            ("Materialize this view", HintType.MATERIALIZATION),
            ("Parallel execution recommended", HintType.PARALLEL),
            ("Memory usage is high", HintType.MEMORY)
        ]
        
        for comment_text, expected_type in test_cases:
            hints = self.extractor._analyze_comment(comment_text)
            assert len(hints) >= 1
            assert hints[0].hint_type == expected_type
    
    def test_line_number_tracking(self):
        """Test that line numbers are properly tracked."""
        source_mdx = """Line 1
        -- Performance: Comment on line 2
        Line 3
        /* Cache: Comment on line 4 */
        Line 5"""
        
        hints = self.extractor.extract_hints(Tree('query', []), source_mdx)
        
        # Check that line numbers are captured
        for hint in hints:
            assert hint.line_number is not None
            assert hint.line_number > 0
    
    def test_context_extraction(self):
        """Test context extraction from comments."""
        long_comment = "Performance: This is a very long comment that should be truncated in the context field but the full message should be preserved"
        
        hints = self.extractor._analyze_comment(long_comment, line_number=5)
        
        assert len(hints) == 1
        hint = hints[0]
        assert hint.line_number == 5
        assert hint.context is not None
        assert len(hint.context) <= 53  # Should be truncated with "..."
        assert hint.message == "This is a very long comment that should be truncated in the context field but the full message should be preserved"


class TestCommentHint:
    """Test CommentHint data class."""
    
    def test_comment_hint_creation(self):
        """Test creating CommentHint."""
        hint = CommentHint(
            hint_type=HintType.PERFORMANCE,
            message="Query is slow",
            line_number=10,
            context="Performance: Query is slow",
            severity="WARNING"
        )
        
        assert hint.hint_type == HintType.PERFORMANCE
        assert hint.message == "Query is slow"
        assert hint.line_number == 10
        assert hint.context == "Performance: Query is slow"
        assert hint.severity == "WARNING"
    
    def test_comment_hint_string_representation(self):
        """Test string representation of CommentHint."""
        hint = CommentHint(
            hint_type=HintType.CACHING,
            message="Enable caching for better performance"
        )
        
        str_repr = str(hint)
        assert "CACHING" in str_repr
        assert "Enable caching for better performance" in str_repr
    
    def test_comment_hint_defaults(self):
        """Test default values for CommentHint."""
        hint = CommentHint(
            hint_type=HintType.CUSTOM,
            message="Test message"
        )
        
        assert hint.line_number is None
        assert hint.context is None
        assert hint.severity == "INFO"


class TestHintType:
    """Test HintType enumeration."""
    
    def test_hint_type_values(self):
        """Test that all hint types have expected values."""
        expected_types = [
            "PERFORMANCE", "CACHING", "INDEX", "AGGREGATION",
            "FILTER_PUSH_DOWN", "MATERIALIZATION", "PARALLEL",
            "MEMORY", "CUSTOM"
        ]
        
        for expected_type in expected_types:
            hint_type = HintType(expected_type)
            assert hint_type.value == expected_type
    
    def test_hint_type_enumeration(self):
        """Test hint type enumeration completeness."""
        all_types = list(HintType)
        assert len(all_types) >= 9  # Should have at least the expected types
        
        # Check that each type has a string value
        for hint_type in all_types:
            assert isinstance(hint_type.value, str)
            assert len(hint_type.value) > 0