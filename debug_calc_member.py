#!/usr/bin/env python3
"""Debug script for calculated member parsing."""

from unmdx.parser.mdx_parser import MDXParser
from unmdx.transformer.mdx_transformer import MDXTransformer
from lark import Tree, Token

def debug_calculated_member():
    """Debug calculated member parsing."""
    
    # Test both with and without spaces around operator
    mdx_no_spaces = """WITH MEMBER[Measures].[Average Price]AS[Measures].[Sales Amount]/[Measures].[Order Quantity]
SELECT{[Measures].[Sales Amount],[Measures].[Order Quantity],[Measures].[Average Price]}ON 0
FROM[Adventure Works]"""
    
    mdx_with_spaces = """WITH MEMBER [Measures].[Average Price] AS [Measures].[Sales Amount] / [Measures].[Order Quantity]
SELECT {[Measures].[Sales Amount], [Measures].[Order Quantity], [Measures].[Average Price]} ON 0
FROM [Adventure Works]"""
    
    for mdx_name, mdx in [("No Spaces", mdx_no_spaces), ("With Spaces", mdx_with_spaces)]:
        print(f"=== DEBUG: Calculated Member Parsing ({mdx_name}) ===")
        print(f"MDX Query:\n{mdx}\n")
        
        # Parse the MDX
        parser = MDXParser()
        try:
            parse_result = parser.parse(mdx)
            parse_tree = parse_result.parse_tree if hasattr(parse_result, 'parse_tree') else parse_result
            print("✅ Parsing successful")
            print()
        except Exception as e:
            print(f"❌ Parsing failed: {e}")
            continue
        
        def find_nodes(tree, node_type):
            """Find all nodes of a specific type."""
            nodes = []
            if isinstance(tree, Tree):
                if tree.data == node_type:
                    nodes.append(tree)
                for child in tree.children:
                    if isinstance(child, Tree):
                        nodes.extend(find_nodes(child, node_type))
            return nodes
        
        # Look for WITH clause
        with_nodes = find_nodes(parse_tree, "with_clause")
        print(f"Found {len(with_nodes)} WITH clauses")
        
        if with_nodes:
            with_node = with_nodes[0]
            print(f"WITH clause: {with_node}")
            print()
            
            # Look for member_definition nodes
            member_defs = find_nodes(with_node, "member_definition")
            print(f"Found {len(member_defs)} member definitions")
            
            for i, member_def in enumerate(member_defs):
                print(f"\nMember definition {i+1}:")
                print(f"  Full node: {member_def}")
                
                # Look for calculation_expression directly (based on debug output)
                calc_exprs = find_nodes(member_def, "calculation_expression")
                print(f"  Calculation expressions: {len(calc_exprs)}")
                for ce in calc_exprs:
                    print(f"    {ce}")
                    
                    # Look at the children of calculation_expression
                    print(f"    Children: {len(ce.children)}")
                    for j, child in enumerate(ce.children):
                        print(f"      Child {j}: {type(child).__name__} - {child}")
                        
                        if isinstance(child, Tree) and child.data == "arithmetic_op":
                            print(f"        Arithmetic operator children: {len(child.children)}")
                            for k, op_child in enumerate(child.children):
                                print(f"          {k}: {type(op_child).__name__} - {op_child}")
                            
                            # If no children, let's check if this is a parsing issue
                            if len(child.children) == 0:
                                print(f"        ⚠️  Empty arithmetic_op node! This might be a parsing issue.")
                                
                        # Also check for direct Token children that might be operators
                        if isinstance(child, Token):
                            print(f"        Direct token: {child.type} = '{child.value}'")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    debug_calculated_member()