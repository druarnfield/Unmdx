"""Grammar validation utilities for MDX parser."""

from pathlib import Path
import re

from lark import Lark
from lark.exceptions import GrammarError, LarkError

from ..utils.logging import get_logger

logger = get_logger(__name__)


class GrammarValidationError(Exception):
    """Exception raised when grammar validation fails."""
    pass


class MDXGrammarValidator:
    """
    Validates MDX grammar files and provides analysis tools.
    
    Checks for common grammar issues, validates rule completeness,
    and provides suggestions for improvements.
    """

    def __init__(self, grammar_path: Path | None = None):
        """
        Initialize grammar validator.
        
        Args:
            grammar_path: Path to grammar file. If None, uses default.
        """
        if grammar_path is None:
            grammar_path = Path(__file__).parent / "mdx_grammar.lark"

        self.grammar_path = grammar_path
        self.grammar_text = ""
        self.rules = {}
        self.terminals = {}

    def validate(self) -> dict[str, any]:
        """
        Perform complete grammar validation.
        
        Returns:
            Dictionary with validation results including:
            - valid: bool - Whether grammar is valid
            - errors: List of error messages
            - warnings: List of warning messages
            - suggestions: List of improvement suggestions
            - statistics: Grammar statistics
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "statistics": {}
        }

        try:
            # Load and parse grammar
            self._load_grammar()
            self._parse_grammar_structure()

            # Validate syntax
            syntax_errors = self._validate_syntax()
            result["errors"].extend(syntax_errors)

            # Check rule completeness
            completeness_warnings = self._check_rule_completeness()
            result["warnings"].extend(completeness_warnings)

            # Check for ambiguities
            ambiguity_warnings = self._check_ambiguities()
            result["warnings"].extend(ambiguity_warnings)

            # Generate improvement suggestions
            suggestions = self._generate_suggestions()
            result["suggestions"].extend(suggestions)

            # Calculate statistics
            result["statistics"] = self._calculate_statistics()

            # Grammar is valid if no errors
            result["valid"] = len(result["errors"]) == 0

            logger.info(f"Grammar validation complete. Valid: {result['valid']}")

        except GrammarValidationError:
            # Re-raise grammar validation errors
            raise
        except Exception as e:
            result["errors"].append(f"Validation failed: {str(e)}")
            logger.error(f"Grammar validation error: {e}")

        return result

    def test_with_sample_queries(self, sample_queries: list[str]) -> dict[str, any]:
        """
        Test grammar with sample MDX queries.
        
        Args:
            sample_queries: List of MDX query strings to test
            
        Returns:
            Dictionary with test results
        """
        results = {
            "total_queries": len(sample_queries),
            "successful_parses": 0,
            "failed_parses": 0,
            "parse_errors": [],
            "performance_stats": {}
        }

        try:
            # Load grammar if not already loaded
            if not self.grammar_text:
                self._load_grammar()
                
            # Create parser
            parser = Lark(
                self.grammar_text,
                parser="earley",
                ambiguity="resolve"
            )

            # Test each query
            for i, query in enumerate(sample_queries):
                try:
                    tree = parser.parse(query)
                    results["successful_parses"] += 1
                    logger.debug(f"Successfully parsed query {i+1}")

                except Exception as e:
                    results["failed_parses"] += 1
                    error_info = {
                        "query_index": i + 1,
                        "query_preview": query[:100] + "..." if len(query) > 100 else query,
                        "error": str(e)
                    }
                    results["parse_errors"].append(error_info)
                    logger.warning(f"Failed to parse query {i+1}: {e}")

            # Calculate success rate
            success_rate = (results["successful_parses"] / results["total_queries"]) * 100
            results["success_rate"] = success_rate

            logger.info(f"Grammar test complete. Success rate: {success_rate:.1f}%")

        except Exception as e:
            results["parse_errors"].append({
                "error": f"Failed to create parser: {str(e)}"
            })
            results["success_rate"] = 0.0
            logger.error(f"Grammar test setup failed: {e}")

        return results

    def _load_grammar(self) -> None:
        """Load grammar file content."""
        try:
            with open(self.grammar_path, encoding="utf-8") as f:
                self.grammar_text = f.read()

            logger.debug(f"Loaded grammar from {self.grammar_path}")

        except FileNotFoundError:
            raise GrammarValidationError(f"Grammar file not found: {self.grammar_path}")
        except Exception as e:
            raise GrammarValidationError(f"Failed to load grammar: {e}")

    def _parse_grammar_structure(self) -> None:
        """Parse grammar structure to extract rules and terminals."""
        lines = self.grammar_text.split("\n")

        current_rule = None
        current_content = []

        for line in lines:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("//") or line.startswith("#"):
                continue

            # Check for rule definition
            if ":" in line and not line.startswith("|"):
                # Save previous rule
                if current_rule:
                    self.rules[current_rule] = "\n".join(current_content)

                # Start new rule
                parts = line.split(":", 1)
                current_rule = parts[0].strip()
                current_content = [parts[1].strip() if len(parts) > 1 else ""]

            elif line.startswith("|") and current_rule:
                # Continuation of current rule
                current_content.append(line)

            elif current_rule:
                # Part of current rule
                current_content.append(line)

        # Save last rule
        if current_rule:
            self.rules[current_rule] = "\n".join(current_content)

        # Extract terminals (uppercase rules)
        for rule_name in self.rules:
            if rule_name.isupper():
                self.terminals[rule_name] = self.rules[rule_name]

        logger.debug(f"Parsed {len(self.rules)} rules, {len(self.terminals)} terminals")

    def _validate_syntax(self) -> list[str]:
        """Validate grammar syntax using Lark."""
        errors = []

        try:
            # Try to create parser - this will catch syntax errors
            Lark(self.grammar_text)
            logger.debug("Grammar syntax validation passed")

        except GrammarError as e:
            errors.append(f"Grammar syntax error: {str(e)}")

        except LarkError as e:
            errors.append(f"Lark grammar error: {str(e)}")

        except Exception as e:
            errors.append(f"Unexpected grammar validation error: {str(e)}")

        return errors

    def _check_rule_completeness(self) -> list[str]:
        """Check for missing or incomplete rules."""
        warnings = []

        # Essential MDX rules that should be present
        essential_rules = {
            "query", "select_statement", "axis_specification",
            "set_expression", "member_expression", "cube_specification",
            "with_clause", "where_clause"
        }

        missing_rules = essential_rules - set(self.rules.keys())
        if missing_rules:
            warnings.append(f"Missing essential rules: {', '.join(missing_rules)}")

        # Check for referenced but undefined rules
        undefined_refs = self._find_undefined_references()
        if undefined_refs:
            warnings.append(f"Referenced but undefined rules: {', '.join(undefined_refs)}")

        # Check for unused rules
        unused_rules = self._find_unused_rules()
        if unused_rules:
            warnings.append(f"Unused rules (may be unnecessary): {', '.join(unused_rules)}")

        return warnings

    def _check_ambiguities(self) -> list[str]:
        """Check for potential grammar ambiguities."""
        warnings = []

        # Check for left recursion (which can cause issues)
        left_recursive = self._find_left_recursive_rules()
        if left_recursive:
            warnings.append(f"Left recursive rules found: {', '.join(left_recursive)}")

        # Check for overly permissive rules
        permissive_rules = self._find_overly_permissive_rules()
        if permissive_rules:
            warnings.append(f"Overly permissive rules: {', '.join(permissive_rules)}")

        return warnings

    def _generate_suggestions(self) -> list[str]:
        """Generate improvement suggestions."""
        suggestions = []

        # Suggest adding error recovery rules
        if "error_recovery" not in self.rules:
            suggestions.append("Consider adding error recovery rules for better error handling")

        # Suggest performance optimizations
        if len(self.rules) > 100:
            suggestions.append("Large grammar detected. Consider splitting into modules")

        # Suggest documentation
        doc_coverage = self._calculate_documentation_coverage()
        if doc_coverage < 0.5:
            suggestions.append("Consider adding more comments to document grammar rules")

        return suggestions

    def _calculate_statistics(self) -> dict[str, any]:
        """Calculate grammar statistics."""
        stats = {
            "total_rules": len(self.rules),
            "terminal_rules": len(self.terminals),
            "non_terminal_rules": len(self.rules) - len(self.terminals),
            "grammar_size_bytes": len(self.grammar_text.encode("utf-8")),
            "grammar_lines": len(self.grammar_text.split("\n")),
            "documentation_coverage": self._calculate_documentation_coverage(),
            "complexity_score": self._calculate_complexity_score()
        }

        return stats

    def _find_undefined_references(self) -> set[str]:
        """Find rules that are referenced but not defined."""
        referenced = set()
        defined = set(self.rules.keys())

        # Extract rule references from rule bodies
        for rule_name, rule_body in self.rules.items():
            # Simple pattern matching for rule references
            # This is a simplified version - could be more sophisticated
            words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", rule_body)
            for word in words:
                if word.islower() and word not in ["import", "common", "ignore"]:
                    referenced.add(word)

        return referenced - defined

    def _find_unused_rules(self) -> set[str]:
        """Find rules that are defined but never used."""
        used = set()
        defined = set(self.rules.keys())

        # Rules used in other rule bodies
        for rule_name, rule_body in self.rules.items():
            words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", rule_body)
            for word in words:
                if word in defined:
                    used.add(word)

        # Start rule is always used
        if "start" in defined:
            used.add("start")
        if "query" in defined:
            used.add("query")

        return defined - used

    def _find_left_recursive_rules(self) -> list[str]:
        """Find left recursive rules."""
        left_recursive = []

        for rule_name, rule_body in self.rules.items():
            # Check if rule starts with itself
            lines = rule_body.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("|"):
                    line = line[1:].strip()

                # Check if line starts with the rule name
                if line.startswith(rule_name + " "):
                    left_recursive.append(rule_name)
                    break

        return left_recursive

    def _find_overly_permissive_rules(self) -> list[str]:
        """Find rules that might be too permissive."""
        permissive = []

        for rule_name, rule_body in self.rules.items():
            # Rules with many alternatives might be too permissive
            alternatives = rule_body.count("|") + 1
            if alternatives > 10:
                permissive.append(f"{rule_name} ({alternatives} alternatives)")

        return permissive

    def _calculate_documentation_coverage(self) -> float:
        """Calculate percentage of grammar that is documented."""
        total_lines = len(self.grammar_text.split("\n"))
        comment_lines = len([line for line in self.grammar_text.split("\n")
                            if line.strip().startswith("//") or line.strip().startswith("#")])

        return comment_lines / total_lines if total_lines > 0 else 0.0

    def _calculate_complexity_score(self) -> int:
        """Calculate a complexity score for the grammar."""
        score = 0

        # Base score from number of rules
        score += len(self.rules)

        # Add complexity for alternatives
        for rule_body in self.rules.values():
            score += rule_body.count("|") * 2

        # Add complexity for nesting
        for rule_body in self.rules.values():
            score += rule_body.count("(") + rule_body.count("[")

        return score


def get_sample_mdx_queries() -> list[str]:
    """Get sample MDX queries for testing grammar."""
    return [
        # Basic queries
        "SELECT {[Measures].[Sales]} ON 0 FROM [Cube]",

        # With dimensions
        """SELECT {[Measures].[Sales]} ON COLUMNS,
           {[Product].[Category].Members} ON ROWS
           FROM [Adventure Works]""",

        # With WHERE clause
        """SELECT {[Measures].[Sales]} ON 0,
           {[Product].[Category].Members} ON 1
           FROM [Adventure Works]
           WHERE ([Date].[Year].&[2023])""",

        # With calculated member
        """WITH MEMBER [Measures].[Profit] AS [Measures].[Sales] - [Measures].[Cost]
           SELECT {[Measures].[Sales], [Measures].[Profit]} ON 0
           FROM [Adventure Works]""",

        # Complex with CrossJoin
        """SELECT {[Measures].[Sales]} ON 0,
           CROSSJOIN([Product].[Category].Members, [Date].[Year].Members) ON 1
           FROM [Adventure Works]""",

        # Poorly formatted (like Necto output)
        """SELECT{{{[Measures].[Sales Amount]},{[Measures].[Order Quantity]}}}ON 0,
           NON EMPTY{[Product].[Category].Members}ON 1
           FROM[Adventure Works]WHERE([Date].[Year].&[2023])""",
    ]
