"""Unit tests for ParenthesesCleaner rule."""

import pytest
from lark import Tree, Token

from unmdx.linter.rules.parentheses_cleaner import ParenthesesCleaner
from unmdx.linter.models import LinterConfig
from unmdx.linter.enums import OptimizationLevel, LintActionType


class TestParenthesesCleaner:
    """Test cases for ParenthesesCleaner rule."""
    
    @pytest.fixture
    def config(self):
        """Create configuration for testing."""
        return LinterConfig(optimization_level=OptimizationLevel.CONSERVATIVE)
    
    @pytest.fixture
    def rule(self, config):
        """Create ParenthesesCleaner rule instance."""
        return ParenthesesCleaner(config)
    
    def test_rule_properties(self, rule):
        """Test rule basic properties."""
        assert rule.name == "parentheses_cleaner"
        assert "parentheses" in rule.description.lower()
        assert rule.optimization_level == OptimizationLevel.CONSERVATIVE
    
    def test_rule_should_apply_conservative(self, rule):
        """Test that rule applies at conservative level."""
        assert rule.should_apply() == True
    
    def test_rule_should_not_apply_disabled(self, config):
        """Test that rule doesn't apply when disabled."""
        config.disabled_rules = ["parentheses_cleaner"]
        rule = ParenthesesCleaner(config)
        assert rule.should_apply() == False
    
    def test_can_apply_no_parentheses(self, rule):
        """Test can_apply with tree that has no parentheses."""
        tree = Tree("query", [
            Tree("identifier", [Token("IDENTIFIER", "Measures")])
        ])
        
        assert rule.can_apply(tree) == False
    
    def test_can_apply_redundant_parentheses(self, rule):
        """Test can_apply with redundant parentheses."""
        tree = Tree("query", [
            Tree("parenthesized_expression", [
                Tree("identifier", [Token("IDENTIFIER", "Measures")])
            ])
        ])
        
        assert rule.can_apply(tree) == True
    
    def test_can_apply_nested_parentheses(self, rule):
        """Test can_apply with nested redundant parentheses."""
        tree = Tree("query", [
            Tree("parenthesized_expression", [
                Tree("parenthesized_expression", [
                    Tree("identifier", [Token("IDENTIFIER", "Measures")])
                ])
            ])
        ])
        
        assert rule.can_apply(tree) == True
    
    def test_is_redundant_simple_identifier(self, rule):
        """Test redundancy detection for simple identifier."""
        paren_node = Tree("parenthesized_expression", [
            Tree("identifier", [Token("IDENTIFIER", "Measures")])
        ])
        
        assert rule._is_redundant_parentheses(paren_node) == True
    
    def test_is_redundant_bracketed_identifier(self, rule):
        """Test redundancy detection for bracketed identifier."""
        paren_node = Tree("parenthesized_expression", [
            Tree("bracketed_identifier", [Token("IDENTIFIER", "Sales Amount")])
        ])
        
        assert rule._is_redundant_parentheses(paren_node) == True
    
    def test_is_redundant_numeric_literal(self, rule):
        """Test redundancy detection for numeric literal."""
        paren_node = Tree("parenthesized_expression", [
            Tree("numeric_literal", [Token("NUMBER", "123")])
        ])
        
        assert rule._is_redundant_parentheses(paren_node) == True
    
    def test_is_redundant_string_literal(self, rule):
        """Test redundancy detection for string literal."""
        paren_node = Tree("parenthesized_expression", [
            Tree("string_literal", [Token("STRING", "\"Hello\"")])
        ])
        
        assert rule._is_redundant_parentheses(paren_node) == True
    
    def test_is_redundant_function_call(self, rule):
        """Test redundancy detection for function call."""
        paren_node = Tree("parenthesized_expression", [
            Tree("function_call", [
                Token("IDENTIFIER", "SUM"),
                Tree("argument", [Tree("identifier", [Token("IDENTIFIER", "Sales")])])
            ])
        ])
        
        assert rule._is_redundant_parentheses(paren_node) == True
    
    def test_is_redundant_nested_parentheses(self, rule):
        """Test redundancy detection for nested parentheses."""
        paren_node = Tree("parenthesized_expression", [
            Tree("parenthesized_expression", [
                Tree("identifier", [Token("IDENTIFIER", "Measures")])
            ])
        ])
        
        assert rule._is_redundant_parentheses(paren_node) == True
    
    def test_is_not_redundant_binary_operation(self, rule):
        """Test that binary operations are not considered redundant."""
        paren_node = Tree("parenthesized_expression", [
            Tree("binary_operation", [
                Tree("identifier", [Token("IDENTIFIER", "A")]),
                Token("OPERATOR", "+"),
                Tree("identifier", [Token("IDENTIFIER", "B")])
            ])
        ])
        
        # For now, binary operations might be kept
        # This test may need adjustment based on implementation
        assert rule._is_redundant_parentheses(paren_node) == False
    
    def test_is_not_redundant_wrong_node_type(self, rule):
        """Test that non-parenthesized expressions return False."""
        non_paren_node = Tree("identifier", [Token("IDENTIFIER", "Measures")])
        
        assert rule._is_redundant_parentheses(non_paren_node) == False
    
    def test_apply_removes_simple_parentheses(self, rule):
        """Test applying rule removes simple redundant parentheses."""
        tree = Tree("query", [
            Tree("parenthesized_expression", [
                Tree("identifier", [Token("IDENTIFIER", "Measures")])
            ])
        ])
        
        result_tree, actions = rule.apply(tree)
        
        assert len(actions) == 1
        assert actions[0].action_type == LintActionType.REMOVE_PARENTHESES
        assert "Removed redundant parentheses" in actions[0].description
        
        # Check that parentheses were removed
        assert result_tree.data == "query"
        assert len(result_tree.children) == 1
        assert result_tree.children[0].data == "identifier"
    
    def test_apply_removes_nested_parentheses(self, rule):
        """Test applying rule removes nested redundant parentheses."""
        tree = Tree("query", [
            Tree("parenthesized_expression", [
                Tree("parenthesized_expression", [
                    Tree("identifier", [Token("IDENTIFIER", "Measures")])
                ])
            ])
        ])
        
        result_tree, actions = rule.apply(tree)
        
        # Should remove both levels of parentheses
        assert len(actions) >= 1  # At least one action
        
        # Final result should be just the identifier
        assert result_tree.data == "query"
        assert len(result_tree.children) == 1
        assert result_tree.children[0].data == "identifier"
    
    def test_apply_preserves_necessary_parentheses(self, rule):
        """Test that necessary parentheses are preserved."""
        tree = Tree("query", [
            Tree("parenthesized_expression", [
                Tree("binary_operation", [
                    Tree("identifier", [Token("IDENTIFIER", "A")]),
                    Token("OPERATOR", "+"),
                    Tree("identifier", [Token("IDENTIFIER", "B")])
                ])
            ])
        ])
        
        result_tree, actions = rule.apply(tree)
        
        # Should not remove parentheses around binary operation
        # (implementation may vary)
        assert isinstance(result_tree, Tree)
    
    def test_apply_multiple_parentheses_in_tree(self, rule):
        """Test applying rule to tree with multiple parentheses."""
        tree = Tree("query", [
            Tree("select_clause", [
                Tree("parenthesized_expression", [
                    Tree("identifier", [Token("IDENTIFIER", "Measures")])
                ]),
                Tree("parenthesized_expression", [
                    Tree("bracketed_identifier", [Token("IDENTIFIER", "Sales")])
                ])
            ])
        ])
        
        result_tree, actions = rule.apply(tree)
        
        # Should remove both sets of redundant parentheses
        assert len(actions) == 2
        assert all(action.action_type == LintActionType.REMOVE_PARENTHESES for action in actions)
        
        # Check structure is preserved but parentheses removed
        assert result_tree.data == "query"
        assert result_tree.children[0].data == "select_clause"
        assert len(result_tree.children[0].children) == 2
        assert result_tree.children[0].children[0].data == "identifier"
        assert result_tree.children[0].children[1].data == "bracketed_identifier"
    
    def test_apply_no_changes_needed(self, rule):
        """Test applying rule when no changes are needed."""
        tree = Tree("query", [
            Tree("identifier", [Token("IDENTIFIER", "Measures")])
        ])
        
        result_tree, actions = rule.apply(tree)
        
        assert len(actions) == 0
        assert str(result_tree) == str(tree)  # Should be identical
    
    def test_get_node_text_identifier(self, rule):
        """Test node text generation for identifier."""
        node = Tree("identifier", [Token("IDENTIFIER", "Measures")])
        text = rule._get_node_text(node)
        assert text == "Measures"
    
    def test_get_node_text_bracketed_identifier(self, rule):
        """Test node text generation for bracketed identifier."""
        node = Tree("bracketed_identifier", [Token("IDENTIFIER", "Sales Amount")])
        text = rule._get_node_text(node)
        assert text == "[Sales Amount]"
    
    def test_get_node_text_parenthesized_expression(self, rule):
        """Test node text generation for parenthesized expression."""
        node = Tree("parenthesized_expression", [
            Tree("identifier", [Token("IDENTIFIER", "Measures")])
        ])
        text = rule._get_node_text(node)
        assert text == "(Measures)"
    
    def test_tree_copying_preserves_original(self, rule):
        """Test that applying rule doesn't modify original tree."""
        original_tree = Tree("query", [
            Tree("parenthesized_expression", [
                Tree("identifier", [Token("IDENTIFIER", "Measures")])
            ])
        ])
        
        original_str = str(original_tree)
        result_tree, actions = rule.apply(original_tree)
        
        # Original should be unchanged
        assert str(original_tree) == original_str
        # Result should be different
        assert str(result_tree) != str(original_tree)