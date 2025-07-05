#!/usr/bin/env python3
"""
Debug calculated member expression parsing
"""

from unmdx.parser import MDXParser

def debug_expression_parsing():
    """Debug how expressions are parsed"""
    
    parser = MDXParser()
    
    test_expressions = [
        "WITH MEMBER[Measures].[Test]AS[A]/[B] SELECT {[Test]} ON 0 FROM [Cube]",
        "WITH MEMBER[Measures].[Test]AS[A]+[B] SELECT {[Test]} ON 0 FROM [Cube]",
        "WITH MEMBER[Measures].[Test]AS[A]-[B] SELECT {[Test]} ON 0 FROM [Cube]", 
        "WITH MEMBER[Measures].[Test]AS[A]*[B] SELECT {[Test]} ON 0 FROM [Cube]",
    ]
    
    for i, mdx in enumerate(test_expressions, 1):
        print(f"\n=== Test {i}: {mdx.split('AS')[1].split(' SELECT')[0]} ===")
        try:
            tree = parser.parse(mdx)
            if tree:
                # Find with clause
                def find_nodes(node, target_data):
                    """Find all nodes with specific data"""
                    results = []
                    if hasattr(node, 'data') and node.data == target_data:
                        results.append(node)
                    if hasattr(node, 'children'):
                        for child in node.children:
                            results.extend(find_nodes(child, target_data))
                    return results
                
                def print_tree(node, indent=0):
                    """Print tree structure"""
                    prefix = "  " * indent
                    if hasattr(node, 'data'):
                        print(f"{prefix}{node.data}")
                        if hasattr(node, 'children'):
                            for child in node.children:
                                print_tree(child, indent + 1)
                    else:
                        print(f"{prefix}TOKEN: {repr(node)}")
                
                with_nodes = find_nodes(tree, "with_clause")
                if with_nodes:
                    print("WITH clause structure:")
                    print_tree(with_nodes[0])
                    
                    # Find calculation expressions
                    calc_exprs = find_nodes(with_nodes[0], "calculation_expression")
                    print(f"\nFound {len(calc_exprs)} calculation expressions")
                    
                    for j, calc_expr in enumerate(calc_exprs):
                        print(f"\nCalculation expression {j+1}:")
                        print_tree(calc_expr)
                        
                        # Find arithmetic operators
                        arith_ops = find_nodes(calc_expr, "arithmetic_op")
                        print(f"Arithmetic operators found: {len(arith_ops)}")
                        for k, op in enumerate(arith_ops):
                            print(f"  Operator {k+1}:")
                            print_tree(op, 2)
                
        except Exception as e:
            print(f"❌ Parse failed: {e}")

if __name__ == "__main__":
    debug_expression_parsing()