"""
Example demonstrating DAX generation from IR.

This example shows how to use the DAX generator to convert
Intermediate Representation (IR) queries into DAX code.
"""

from unmdx.dax_generator import DAXGenerator, DAXGenerationOptions
from unmdx.ir.models import (
    Query, Measure, Dimension, CubeReference, 
    HierarchyReference, LevelReference, MemberSelection
)
from unmdx.ir.enums import AggregationType, MemberSelectionType
from unmdx.ir.expressions import MeasureReference, BinaryOperation


def main():
    """Run DAX generation examples."""
    
    print("=== UnMDX DAX Generator Examples ===\n")
    
    # Create DAX generator with custom options
    options = DAXGenerationOptions(
        use_summarizecolumns=True,
        optimize_filters=True,
        include_comments=True,
        format_output=True
    )
    generator = DAXGenerator(options)
    
    # Example 1: Simple measure query
    print("Example 1: Simple Measure Query")
    print("-" * 40)
    
    cube = CubeReference(name="Adventure Works")
    measure = Measure(
        name="Sales Amount",
        aggregation=AggregationType.SUM,
        expression=MeasureReference(measure_name="Sales Amount")
    )
    
    simple_query = Query(
        cube=cube,
        measures=[measure]
    )
    
    dax1 = generator.generate(simple_query)
    print(dax1)
    print()
    
    # Example 2: Dimensional query
    print("Example 2: Dimensional Query")
    print("-" * 40)
    
    # Create dimension
    hierarchy = HierarchyReference(table="Product", name="Category")
    level = LevelReference(name="Category")
    members = MemberSelection(selection_type=MemberSelectionType.ALL)
    
    dimension = Dimension(
        hierarchy=hierarchy,
        level=level,
        members=members
    )
    
    dimensional_query = Query(
        cube=cube,
        measures=[measure],
        dimensions=[dimension]
    )
    
    dax2 = generator.generate(dimensional_query)
    print(dax2)
    print()
    
    # Example 3: Multiple measures
    print("Example 3: Multiple Measures")
    print("-" * 40)
    
    measure2 = Measure(
        name="Order Quantity",
        aggregation=AggregationType.SUM,
        expression=MeasureReference(measure_name="Order Quantity")
    )
    
    multi_measure_query = Query(
        cube=cube,
        measures=[measure, measure2],
        dimensions=[dimension]
    )
    
    dax3 = generator.generate(multi_measure_query)
    print(dax3)
    print()
    
    # Example 4: Calculated measure
    print("Example 4: Calculated Measure")
    print("-" * 40)
    
    # Create calculated measure: Profit = Sales - Cost
    sales_ref = MeasureReference(measure_name="Sales Amount")
    cost_ref = MeasureReference(measure_name="Total Cost")
    
    profit_expr = BinaryOperation(
        left=sales_ref,
        operator="-",
        right=cost_ref
    )
    
    profit_measure = Measure(
        name="Profit",
        aggregation=AggregationType.CUSTOM,
        expression=profit_expr
    )
    
    # Note: For calculated measures, we'd need to add them to the calculations list
    # This is simplified for the example
    
    calculated_query = Query(
        cube=cube,
        measures=[measure, profit_measure],
        dimensions=[dimension]
    )
    
    dax4 = generator.generate(calculated_query)
    print(dax4)
    print()
    
    print("=== DAX Generation Complete ===")


if __name__ == "__main__":
    main()