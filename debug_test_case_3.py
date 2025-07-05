#!/usr/bin/env python3
"""Debug script for Test Case 3 dimension extraction issue."""

from unmdx.parser.mdx_parser import MDXParser
from unmdx.transformer.mdx_transformer import MDXTransformer
from unmdx.config import create_default_config

def debug_test_case_3():
    """Debug Test Case 3 to see why dimensions aren't being extracted."""
    
    mdx = """SELECT {{{[Measures].[Sales Amount]}, {[Measures].[Order Quantity]}}} ON 0,
{[Date].[Calendar Year].Members} ON 1
FROM [Adventure Works]"""
    
    print("=== DEBUG: Test Case 3 ===")
    print(f"MDX Query:\n{mdx}\n")
    
    # Step 1: Parse the MDX
    print("Step 1: Parsing MDX...")
    parser = MDXParser()
    try:
        parse_result = parser.parse(mdx)
        print("✅ Parsing successful")
        parse_tree = parse_result.parse_tree if hasattr(parse_result, 'parse_tree') else parse_result
        print(f"Parse tree: {parse_tree}")
        print()
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return
    
    # Step 2: Transform to IR 
    print("Step 2: Transforming to IR...")
    transformer = MDXTransformer(debug=True)
    try:
        query = transformer.transform(parse_tree, mdx)
        print("✅ Transformation successful")
        print(f"Query cube: {query.cube}")
        print(f"Number of measures: {len(query.measures)}")
        print(f"Number of dimensions: {len(query.dimensions)}")
        print()
        
        # Show measures
        print("Measures found:")
        for i, measure in enumerate(query.measures):
            print(f"  {i+1}. {measure.name}")
        print()
        
        # Show dimensions (this is our issue)
        print("Dimensions found:")
        if query.dimensions:
            for i, dimension in enumerate(query.dimensions):
                print(f"  {i+1}. Hierarchy: {dimension.hierarchy.name}")
                print(f"      Level: {dimension.level.name if dimension.level else 'None'}")
                print(f"      Members: {dimension.members}")
        else:
            print("  ❌ NO DIMENSIONS FOUND - This is the bug!")
        print()
        
    except Exception as e:
        print(f"❌ Transformation failed: {e}")
        return
    
    # Step 3: Let's manually inspect the parse tree for axis 1
    print("Step 3: Manual parse tree inspection...")
    print("Looking for axis_specification nodes...")
    
    def find_nodes(tree, node_type):
        """Find all nodes of a specific type."""
        from lark import Tree
        nodes = []
        if isinstance(tree, Tree):
            if tree.data == node_type:
                nodes.append(tree)
            for child in tree.children:
                if isinstance(child, Tree):
                    nodes.extend(find_nodes(child, node_type))
        return nodes
    
    axis_specs = find_nodes(parse_tree, "axis_specification")
    print(f"Found {len(axis_specs)} axis specifications:")
    
    for i, axis_spec in enumerate(axis_specs):
        print(f"\nAxis {i}:")
        print(f"  Raw node: {axis_spec}")
        
        # Check what axis this is
        axis_id = None
        from lark import Token
        for child in axis_spec.children:
            if isinstance(child, Token):
                token_str = str(child).upper()
                if "COLUMNS" in token_str or token_str == "0":
                    axis_id = 0
                elif "ROWS" in token_str or token_str == "1":
                    axis_id = 1
        
        # Also check for axis_number_short nodes
        axis_number_nodes = find_nodes(axis_spec, "axis_number_short")
        if axis_number_nodes:
            for num_node in axis_number_nodes:
                for child in num_node.children:
                    if isinstance(child, Token) and child.type == "NUMBER":
                        axis_id = int(str(child))
                        break
                    
        print(f"  Axis ID: {axis_id}")
        
        # Look for member expressions in this axis
        member_exprs = find_nodes(axis_spec, "member_expression")
        print(f"  Member expressions found: {len(member_exprs)}")
        
        for j, member_expr in enumerate(member_exprs):
            print(f"    Member {j+1}: {member_expr}")
            
            # Try to extract hierarchy name
            hierarchy_nodes = find_nodes(member_expr, "hierarchy_expression")
            print(f"      Hierarchy expressions: {len(hierarchy_nodes)}")
            for h_node in hierarchy_nodes:
                print(f"        Hierarchy: {h_node}")
                bracketed_ids = find_nodes(h_node, "bracketed_identifier")
                for b_id in bracketed_ids:
                    print(f"          Hierarchy name: {b_id.children[0]}")
                
            # Try to extract level name
            level_nodes = find_nodes(member_expr, "level_expression")
            print(f"      Level expressions: {len(level_nodes)}")
            for l_node in level_nodes:
                print(f"        Level: {l_node}")
                bracketed_ids = find_nodes(l_node, "bracketed_identifier")
                for b_id in bracketed_ids:
                    print(f"          Level name: {b_id.children[0]}")
                    
            # Check for members identifier
            identifiers = find_nodes(member_expr, "identifier")
            print(f"      Identifiers: {len(identifiers)}")
            for ident in identifiers:
                print(f"        Identifier: {ident.children[0]}")
                
            # Check if this is a measure
            is_measure = False
            for h_node in hierarchy_nodes:
                bracketed_ids = find_nodes(h_node, "bracketed_identifier")
                for b_id in bracketed_ids:
                    if str(b_id.children[0]).lower() == "measures":
                        is_measure = True
                        break
                        
            print(f"      Is measure: {is_measure}")
            
            # If this is axis 1 and not a measure, this should be extracted as a dimension
            if axis_id == 1 and not is_measure:
                print(f"      ⚠️  This should be extracted as a dimension!")

if __name__ == "__main__":
    debug_test_case_3()