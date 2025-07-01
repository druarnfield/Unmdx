"""Example of using the MDX Linter to clean up messy MDX queries."""

from lark import Tree, Token

from unmdx.linter import MDXLinter, LinterConfig, OptimizationLevel


def create_sample_messy_tree():
    """Create a sample MDX tree with common Necto patterns."""
    # Simulate a parsed MDX tree with redundant parentheses
    return Tree("query", [
        Tree("select_clause", [
            Tree("axis_specification", [
                Tree("parenthesized_expression", [
                    Tree("parenthesized_expression", [
                        Tree("bracketed_identifier", [Token("IDENTIFIER", "Measures.Sales")])
                    ])
                ]),
                Token("AXIS", "COLUMNS")
            ])
        ]),
        Tree("from_clause", [
            Tree("cube_specification", [
                Tree("bracketed_identifier", [Token("IDENTIFIER", "Sales Cube")])
            ])
        ])
    ])


def demonstrate_conservative_linting():
    """Demonstrate conservative linting approach."""
    print("=== Conservative Linting ===")
    
    # Create configuration
    config = LinterConfig(optimization_level=OptimizationLevel.CONSERVATIVE)
    linter = MDXLinter(config)
    
    # Get available rules
    print(f"Available rules: {', '.join(linter.get_available_rules())}")
    
    # Create sample tree
    messy_tree = create_sample_messy_tree()
    print(f"Original tree structure: {messy_tree.pretty()}")
    
    # Apply linting
    cleaned_tree, report = linter.lint(messy_tree, "SELECT (([Measures].[Sales])) ON COLUMNS FROM [Sales Cube]")
    
    print(f"Cleaned tree structure: {cleaned_tree.pretty()}")
    print(f"\\nLinting Report:")
    print(report.summary())
    
    return cleaned_tree, report


def demonstrate_moderate_linting():
    """Demonstrate moderate linting with more aggressive optimizations."""
    print("\\n=== Moderate Linting ===")
    
    # Create moderate configuration
    config = LinterConfig(
        optimization_level=OptimizationLevel.MODERATE,
        optimize_calculated_members=True,
        simplify_function_calls=True
    )
    linter = MDXLinter(config)
    
    print(f"Available rules: {', '.join(linter.get_available_rules())}")
    
    # Create sample tree with function calls
    function_tree = Tree("query", [
        Tree("function_call", [
            Token("IDENTIFIER", "IIF"),
            Tree("argument", [Tree("boolean_literal", [Token("BOOLEAN", "TRUE")])]),
            Tree("argument", [Tree("numeric_literal", [Token("NUMBER", "100")])]),
            Tree("argument", [Tree("numeric_literal", [Token("NUMBER", "100")])])  # Same value
        ])
    ])
    
    print(f"Original function tree: {function_tree.pretty()}")
    
    # Apply linting
    cleaned_tree, report = linter.lint(function_tree)
    
    print(f"Cleaned function tree: {cleaned_tree.pretty()}")
    print(f"\\nLinting Report:")
    print(report.summary())
    
    return cleaned_tree, report


def demonstrate_custom_configuration():
    """Demonstrate custom linter configuration."""
    print("\\n=== Custom Configuration ===")
    
    # Create custom configuration
    config = LinterConfig(
        optimization_level=OptimizationLevel.AGGRESSIVE,
        disabled_rules=["function_optimizer"],  # Disable specific rule
        max_crossjoin_depth=3,
        generate_optimization_report=True
    )
    linter = MDXLinter(config)
    
    print(f"Available rules (with function_optimizer disabled): {', '.join(linter.get_available_rules())}")
    print(f"Should apply moderate rules: {config.should_apply_moderate_rules()}")
    print(f"Should apply aggressive rules: {config.should_apply_aggressive_rules()}")
    
    # Test with sample tree
    tree = create_sample_messy_tree()
    cleaned_tree, report = linter.lint(tree)
    
    print(f"\\nCustom Linting Report:")
    print(report.summary())
    
    return cleaned_tree, report


def demonstrate_error_handling():
    """Demonstrate linter error handling capabilities."""
    print("\\n=== Error Handling ===")
    
    config = LinterConfig(
        optimization_level=OptimizationLevel.CONSERVATIVE,
        skip_on_validation_error=True,
        max_processing_time_ms=1000  # 1 second timeout
    )
    linter = MDXLinter(config)
    
    # Create potentially problematic tree
    problematic_tree = Tree("query", [
        Tree("invalid_node", ["bad_data"]),
        None  # Invalid child
    ])
    
    print("Processing potentially problematic tree...")
    
    try:
        cleaned_tree, report = linter.lint(problematic_tree)
        
        print("Linting completed without crashing!")
        print(f"Errors encountered: {len(report.errors)}")
        print(f"Warnings generated: {len(report.warnings)}")
        
        if report.errors:
            print("Errors:")
            for error in report.errors:
                print(f"  - {error}")
        
        if report.warnings:
            print("Warnings:")
            for warning in report.warnings:
                print(f"  - {warning}")
                
    except Exception as e:
        print(f"Exception occurred: {e}")
    
    return None, None


def main():
    """Main demonstration function."""
    print("MDX Linter Demonstration")
    print("=" * 50)
    
    try:
        # Demonstrate different linting approaches
        demonstrate_conservative_linting()
        demonstrate_moderate_linting()
        demonstrate_custom_configuration()
        demonstrate_error_handling()
        
        print("\\n=== Summary ===")
        print("The MDX Linter successfully:")
        print("- Removes redundant parentheses")
        print("- Optimizes function calls (in moderate+ mode)")
        print("- Provides comprehensive reporting")
        print("- Handles errors gracefully")
        print("- Supports custom configurations")
        
    except Exception as e:
        print(f"Demonstration failed: {e}")
        print("This may be due to missing dependencies or import issues.")


if __name__ == "__main__":
    main()