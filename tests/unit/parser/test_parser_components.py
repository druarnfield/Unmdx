"""Unit tests for parser components."""

import pytest
from pathlib import Path
from lark import Tree

from unmdx.parser import (
    MDXParser, MDXParseError, MDXTreeAnalyzer, 
    TreeDebugger, MDXGrammarValidator
)


class TestMDXParser:
    """Test MDX parser core functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return MDXParser()
    
    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = MDXParser()
        assert parser is not None
        assert parser._parser is not None
        assert parser.grammar_path.exists()
    
    def test_parser_with_custom_grammar(self, tmp_path):
        """Test parser with custom grammar path."""
        # Create a minimal grammar file
        grammar_file = tmp_path / "test_grammar.lark"
        grammar_content = """
?start: query
query: "SELECT" "test"
%import common.WS
%ignore WS
"""
        grammar_file.write_text(grammar_content)
        
        parser = MDXParser(grammar_path=grammar_file)
        
        # This should parse successfully with our test grammar
        tree = parser.parse("SELECT test")
        assert isinstance(tree, Tree)
    
    def test_parser_debug_mode(self):
        """Test parser in debug mode."""
        parser = MDXParser(debug=True)
        assert parser.debug == True
    
    def test_parse_basic_query(self, parser):
        """Test parsing basic query."""
        query = "SELECT {[Measures].[Sales]} ON 0 FROM [Cube]"
        tree = parser.parse(query)
        
        assert isinstance(tree, Tree)
        assert tree.data == 'query'
    
    def test_parse_error_handling(self, parser):
        """Test error handling in parsing."""
        with pytest.raises(MDXParseError):
            parser.parse("INVALID QUERY SYNTAX")
    
    def test_parse_file_operations(self, parser, tmp_path):
        """Test file parsing operations."""
        mdx_file = tmp_path / "test.mdx"
        mdx_file.write_text("SELECT {[Measures].[Sales]} ON 0 FROM [Cube]")
        
        tree = parser.parse_file(mdx_file)
        assert isinstance(tree, Tree)
        
        # Test non-existent file
        with pytest.raises(MDXParseError):
            parser.parse_file(tmp_path / "missing.mdx")


class TestMDXTreeAnalyzer:
    """Test MDX tree analyzer functionality."""
    
    @pytest.fixture
    def sample_tree(self):
        """Create sample tree for testing."""
        parser = MDXParser()
        query = """WITH MEMBER [Measures].[Profit] AS [Measures].[Sales] - [Measures].[Cost]
                   SELECT {[Measures].[Sales], [Measures].[Profit]} ON COLUMNS,
                          {[Product].[Category].Members} ON ROWS
                   FROM [Adventure Works]
                   WHERE ([Date].[Year].&[2023])"""
        return parser.parse(query)
    
    def test_analyzer_initialization(self, sample_tree):
        """Test analyzer initialization."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        assert analyzer.tree == sample_tree
    
    def test_complete_analysis(self, sample_tree):
        """Test complete tree analysis."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        structure = analyzer.analyze()
        
        assert structure is not None
        assert hasattr(structure, 'measures')
        assert hasattr(structure, 'dimensions')
        assert hasattr(structure, 'filters')
        assert hasattr(structure, 'calculations')
        assert hasattr(structure, 'cube_name')
    
    def test_measure_extraction(self, sample_tree):
        """Test measure extraction."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        measures = analyzer.extract_measures()
        
        assert isinstance(measures, list)
        assert len(measures) > 0
    
    def test_dimension_extraction(self, sample_tree):
        """Test dimension extraction."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        dimensions = analyzer.extract_dimensions()
        
        assert isinstance(dimensions, list)
    
    def test_filter_extraction(self, sample_tree):
        """Test filter extraction."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        filters = analyzer.extract_filters()
        
        assert isinstance(filters, list)
    
    def test_calculation_extraction(self, sample_tree):
        """Test calculation extraction."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        calculations = analyzer.extract_calculations()
        
        assert isinstance(calculations, list)
    
    def test_cube_name_extraction(self, sample_tree):
        """Test cube name extraction."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        cube_name = analyzer.extract_cube_name()
        
        assert cube_name == "Adventure Works"
    
    def test_with_clause_detection(self, sample_tree):
        """Test WITH clause detection."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        has_with = analyzer.has_with_clause()
        
        assert has_with == True
    
    def test_nesting_calculation(self, sample_tree):
        """Test nesting depth calculation."""
        analyzer = MDXTreeAnalyzer(sample_tree)
        max_depth = analyzer.calculate_max_nesting()
        
        assert isinstance(max_depth, int)
        assert max_depth >= 0


class TestTreeDebugger:
    """Test tree debugger functionality."""
    
    @pytest.fixture
    def sample_tree(self):
        """Create sample tree for testing."""
        parser = MDXParser()
        return parser.parse("SELECT {[Measures].[Sales]} ON 0 FROM [Cube]")
    
    def test_debugger_initialization(self, sample_tree):
        """Test debugger initialization."""
        debugger = TreeDebugger(sample_tree)
        assert debugger.tree == sample_tree
    
    def test_detailed_print(self, sample_tree):
        """Test detailed tree printing."""
        debugger = TreeDebugger(sample_tree)
        output = debugger.print_detailed()
        
        assert isinstance(output, str)
        assert len(output) > 0
        assert "Tree(" in output
    
    def test_detailed_print_with_depth_limit(self, sample_tree):
        """Test detailed printing with depth limit."""
        debugger = TreeDebugger(sample_tree)
        output = debugger.print_detailed(max_depth=2)
        
        assert isinstance(output, str)
        assert len(output) > 0
    
    def test_issue_detection(self, sample_tree):
        """Test issue detection."""
        debugger = TreeDebugger(sample_tree)
        issues = debugger.find_issues()
        
        assert isinstance(issues, list)


class TestMDXGrammarValidator:
    """Test grammar validator functionality."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = MDXGrammarValidator()
        assert validator.grammar_path.exists()
    
    def test_grammar_validation(self):
        """Test grammar validation."""
        validator = MDXGrammarValidator()
        result = validator.validate()
        
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result
        assert 'suggestions' in result
        assert 'statistics' in result
    
    def test_sample_query_testing(self):
        """Test sample query testing."""
        validator = MDXGrammarValidator()
        
        sample_queries = [
            "SELECT {[Measures].[Sales]} ON 0 FROM [Cube]",
            "SELECT {[Measures].[Sales]} ON COLUMNS FROM [Cube]",
        ]
        
        result = validator.test_with_sample_queries(sample_queries)
        
        assert isinstance(result, dict)
        assert 'total_queries' in result
        assert 'successful_parses' in result
        assert 'failed_parses' in result
        assert result['total_queries'] == len(sample_queries)
    
    def test_invalid_grammar_path(self, tmp_path):
        """Test validator with invalid grammar path."""
        invalid_path = tmp_path / "missing_grammar.lark"
        
        with pytest.raises(Exception):
            validator = MDXGrammarValidator(grammar_path=invalid_path)
            validator.validate()


class TestParseErrorTypes:
    """Test different types of parse errors."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return MDXParser()
    
    def test_mdx_parse_error_creation(self):
        """Test MDXParseError creation."""
        error = MDXParseError(
            "Test error",
            line=10,
            column=5,
            context="test context",
            original_error=ValueError("original")
        )
        
        assert error.message == "Test error"
        assert error.line == 10
        assert error.column == 5
        assert error.context == "test context"
        assert isinstance(error.original_error, ValueError)
    
    def test_syntax_error_handling(self, parser):
        """Test syntax error handling."""
        with pytest.raises(MDXParseError) as exc_info:
            parser.parse("SELECT invalid syntax")
        
        error = exc_info.value
        assert isinstance(error, MDXParseError)
    
    def test_unexpected_token_handling(self, parser):
        """Test unexpected token handling."""
        with pytest.raises(MDXParseError):
            parser.parse("SELECT {[Measures].[Sales]} ON INVALID FROM [Cube]")
    
    def test_empty_input_handling(self, parser):
        """Test empty input handling."""
        with pytest.raises(MDXParseError) as exc_info:
            parser.parse("")
        
        assert "Empty or whitespace-only query" in str(exc_info.value)


class TestParserWarnings:
    """Test parser warning generation."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return MDXParser()
    
    def test_deep_nesting_warning(self, parser):
        """Test deep nesting warning."""
        # Create deeply nested query
        nested_query = "SELECT " + "{" * 10 + "[Measures].[Sales]" + "}" * 10 + " ON 0 FROM [Cube]"
        
        result = parser.validate_syntax(nested_query)
        
        # Should parse successfully but have warnings
        assert result['valid'] == True
        assert len(result['warnings']) > 0
    
    def test_redundant_construct_detection(self, parser):
        """Test redundant construct detection."""
        # Query with redundant parentheses and nesting
        redundant_query = """SELECT {{{[Measures].[Sales]}}} ON 0,
                            CROSSJOIN(([Product].[Category].Members), ([Date].[Year].Members)) ON 1
                            FROM [Cube]"""
        
        result = parser.validate_syntax(redundant_query)
        
        # Should be valid but may have warnings about redundancy
        assert result['valid'] == True
    
    def test_empty_set_detection(self, parser):
        """Test empty set detection."""
        # Query with empty sets
        empty_set_query = "SELECT {{}, {[Measures].[Sales]}, {}} ON 0 FROM [Cube]"
        
        result = parser.validate_syntax(empty_set_query)
        
        # Should be valid but may have warnings about empty sets
        assert result['valid'] == True