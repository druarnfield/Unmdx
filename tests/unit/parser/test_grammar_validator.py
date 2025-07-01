"""Unit tests for grammar validator."""

import pytest
from pathlib import Path

from unmdx.parser.grammar_validator import (
    MDXGrammarValidator, 
    GrammarValidationError,
    get_sample_mdx_queries
)


class TestMDXGrammarValidator:
    """Test MDX grammar validator."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return MDXGrammarValidator()
    
    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator.grammar_path.exists()
        assert validator.grammar_text == ""
        assert validator.rules == {}
        assert validator.terminals == {}
    
    def test_validate_grammar(self, validator):
        """Test complete grammar validation."""
        result = validator.validate()
        
        assert isinstance(result, dict)
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result
        assert 'suggestions' in result
        assert 'statistics' in result
        
        # Grammar should be valid
        assert result['valid'] == True
        assert len(result['errors']) == 0
    
    def test_grammar_statistics(self, validator):
        """Test grammar statistics calculation."""
        result = validator.validate()
        stats = result['statistics']
        
        assert 'total_rules' in stats
        assert 'terminal_rules' in stats
        assert 'non_terminal_rules' in stats
        assert 'grammar_size_bytes' in stats
        assert 'grammar_lines' in stats
        assert 'documentation_coverage' in stats
        assert 'complexity_score' in stats
        
        # Verify reasonable values
        assert stats['total_rules'] > 0
        assert stats['grammar_size_bytes'] > 0
        assert stats['grammar_lines'] > 0
        assert 0 <= stats['documentation_coverage'] <= 1
        assert stats['complexity_score'] > 0
    
    def test_sample_query_testing(self, validator):
        """Test sample query testing."""
        sample_queries = get_sample_mdx_queries()
        result = validator.test_with_sample_queries(sample_queries)
        
        assert isinstance(result, dict)
        assert 'total_queries' in result
        assert 'successful_parses' in result
        assert 'failed_parses' in result
        assert 'parse_errors' in result
        assert 'success_rate' in result
        
        assert result['total_queries'] == len(sample_queries)
        assert result['successful_parses'] + result['failed_parses'] == result['total_queries']
        assert 0 <= result['success_rate'] <= 100
    
    def test_custom_grammar_path(self, tmp_path):
        """Test validator with custom grammar path."""
        # Create a simple test grammar
        grammar_file = tmp_path / "test_grammar.lark"
        grammar_content = """
// Test grammar
?start: query
query: "SELECT" identifier "FROM" identifier
identifier: CNAME
CNAME: /[a-zA-Z_][a-zA-Z0-9_]*/
%import common.WS
%ignore WS
"""
        grammar_file.write_text(grammar_content)
        
        validator = MDXGrammarValidator(grammar_path=grammar_file)
        result = validator.validate()
        
        assert result['valid'] == True
    
    def test_invalid_grammar_file(self, tmp_path):
        """Test validator with invalid grammar file."""
        invalid_path = tmp_path / "missing.lark"
        
        with pytest.raises(GrammarValidationError):
            validator = MDXGrammarValidator(grammar_path=invalid_path)
            validator.validate()
    
    def test_malformed_grammar(self, tmp_path):
        """Test validator with malformed grammar."""
        grammar_file = tmp_path / "bad_grammar.lark"
        grammar_content = "INVALID GRAMMAR SYNTAX :::: ERROR"
        grammar_file.write_text(grammar_content)
        
        validator = MDXGrammarValidator(grammar_path=grammar_file)
        result = validator.validate()
        
        assert result['valid'] == False
        assert len(result['errors']) > 0


class TestGrammarAnalysis:
    """Test grammar analysis features."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return MDXGrammarValidator()
    
    def test_rule_completeness_check(self, validator):
        """Test rule completeness checking."""
        result = validator.validate()
        
        # Should have essential rules
        if result['warnings']:
            for warning in result['warnings']:
                if "Missing essential rules" in warning:
                    pytest.fail(f"Missing essential rules: {warning}")
    
    def test_undefined_reference_detection(self, tmp_path):
        """Test undefined reference detection."""
        grammar_file = tmp_path / "incomplete_grammar.lark"
        grammar_content = """
?start: query
query: undefined_rule
identifier: CNAME
CNAME: /[a-zA-Z_][a-zA-Z0-9_]*/
%import common.WS
%ignore WS
"""
        grammar_file.write_text(grammar_content)
        
        validator = MDXGrammarValidator(grammar_path=grammar_file)
        result = validator.validate()
        
        # Should detect undefined references
        undefined_warning = any("undefined" in w.lower() for w in result['warnings'])
        assert undefined_warning
    
    def test_unused_rule_detection(self, tmp_path):
        """Test unused rule detection."""
        grammar_file = tmp_path / "unused_rules_grammar.lark"
        grammar_content = """
?start: query
query: "SELECT" identifier "FROM" identifier
identifier: CNAME
unused_rule: "UNUSED"
another_unused: "ALSO_UNUSED"
CNAME: /[a-zA-Z_][a-zA-Z0-9_]*/
%import common.WS
%ignore WS
"""
        grammar_file.write_text(grammar_content)
        
        validator = MDXGrammarValidator(grammar_path=grammar_file)
        result = validator.validate()
        
        # Should detect unused rules
        unused_warning = any("unused" in w.lower() for w in result['warnings'])
        assert unused_warning
    
    def test_left_recursion_detection(self, tmp_path):
        """Test left recursion detection."""
        grammar_file = tmp_path / "left_recursive_grammar.lark"
        grammar_content = """
?start: expr
expr: expr "+" term
    | term
term: NUMBER
NUMBER: /[0-9]+/
%import common.WS
%ignore WS
"""
        grammar_file.write_text(grammar_content)
        
        validator = MDXGrammarValidator(grammar_path=grammar_file)
        result = validator.validate()
        
        # Should detect left recursion
        recursion_warning = any("recursive" in w.lower() for w in result['warnings'])
        assert recursion_warning


class TestSampleQueries:
    """Test sample query generation and testing."""
    
    def test_sample_query_generation(self):
        """Test sample query generation."""
        queries = get_sample_mdx_queries()
        
        assert isinstance(queries, list)
        assert len(queries) > 0
        
        # All queries should be strings
        for query in queries:
            assert isinstance(query, str)
            assert len(query.strip()) > 0
    
    def test_sample_query_variety(self):
        """Test variety in sample queries."""
        queries = get_sample_mdx_queries()
        
        # Should have different types of queries
        has_basic = any("SELECT" in q and "WHERE" not in q for q in queries)
        has_with_where = any("WHERE" in q for q in queries)
        has_calculated = any("WITH MEMBER" in q for q in queries)
        has_crossjoin = any("CROSSJOIN" in q for q in queries)
        
        assert has_basic, "Should have basic SELECT queries"
        assert has_with_where, "Should have queries with WHERE clause"
        assert has_calculated, "Should have queries with calculated members"
        assert has_crossjoin, "Should have queries with CrossJoin"
    
    def test_sample_queries_parse_with_real_grammar(self):
        """Test sample queries parse with real grammar."""
        from unmdx.parser import MDXParser
        
        parser = MDXParser()
        queries = get_sample_mdx_queries()
        
        parse_count = 0
        for query in queries:
            try:
                tree = parser.parse(query)
                parse_count += 1
            except Exception as e:
                # Some sample queries might intentionally be malformed
                pass
        
        # Most sample queries should parse successfully
        success_rate = parse_count / len(queries)
        assert success_rate >= 0.8, f"Sample query success rate too low: {success_rate:.2f}"


class TestValidatorHelpers:
    """Test validator helper methods."""
    
    @pytest.fixture
    def validator(self):
        """Create validator with loaded grammar."""
        validator = MDXGrammarValidator()
        validator._load_grammar()
        validator._parse_grammar_structure()
        return validator
    
    def test_grammar_loading(self, validator):
        """Test grammar loading."""
        assert len(validator.grammar_text) > 0
        assert "query" in validator.grammar_text.lower()
        assert "select" in validator.grammar_text.lower()
    
    def test_grammar_structure_parsing(self, validator):
        """Test grammar structure parsing."""
        assert len(validator.rules) > 0
        assert len(validator.terminals) > 0
        
        # Should have key rules
        rule_names = set(validator.rules.keys())
        assert 'query' in rule_names or '?query' in rule_names
    
    def test_documentation_coverage_calculation(self, validator):
        """Test documentation coverage calculation."""
        coverage = validator._calculate_documentation_coverage()
        
        assert isinstance(coverage, float)
        assert 0 <= coverage <= 1
    
    def test_complexity_score_calculation(self, validator):
        """Test complexity score calculation."""
        score = validator._calculate_complexity_score()
        
        assert isinstance(score, int)
        assert score > 0


class TestValidatorErrorHandling:
    """Test validator error handling."""
    
    def test_missing_grammar_file(self, tmp_path):
        """Test handling of missing grammar file."""
        missing_path = tmp_path / "missing.lark"
        
        with pytest.raises(GrammarValidationError) as exc_info:
            validator = MDXGrammarValidator(grammar_path=missing_path)
            validator.validate()
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_invalid_grammar_syntax(self, tmp_path):
        """Test handling of invalid grammar syntax."""
        grammar_file = tmp_path / "invalid.lark"
        grammar_file.write_text("COMPLETELY INVALID SYNTAX !!!")
        
        validator = MDXGrammarValidator(grammar_path=grammar_file)
        result = validator.validate()
        
        assert result['valid'] == False
        assert len(result['errors']) > 0
    
    def test_parser_creation_failure(self, tmp_path):
        """Test handling of parser creation failure."""
        grammar_file = tmp_path / "problematic.lark"
        # Grammar that loads but fails during parser creation
        grammar_content = """
?start: expr
expr: expr expr  // Ambiguous rule that might cause issues
"""
        grammar_file.write_text(grammar_content)
        
        validator = MDXGrammarValidator(grammar_path=grammar_file)
        queries = ["test query"]
        result = validator.test_with_sample_queries(queries)
        
        # Should handle parser creation gracefully
        assert 'parse_errors' in result
    
    def test_empty_grammar_file(self, tmp_path):
        """Test handling of empty grammar file."""
        grammar_file = tmp_path / "empty.lark"
        grammar_file.write_text("")
        
        validator = MDXGrammarValidator(grammar_path=grammar_file)
        result = validator.validate()
        
        assert result['valid'] == False
        assert len(result['errors']) > 0