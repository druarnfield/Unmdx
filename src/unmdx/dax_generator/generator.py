"""DAX query generator from IR representation."""


from ..ir.models import Query


class DaxGenerator:
    """Generates DAX queries from IR representation."""

    def generate(self, query: Query) -> str:
        """Generate DAX from IR Query object.

        Args:
            query: The IR Query to convert to DAX

        Returns:
            str: The generated DAX query
        """
        parts = []

        # Add DEFINE section if there are calculations
        if query.calculations:
            parts.append("DEFINE")
            for calc in query.calculations:
                parts.append(f"    {calc.to_dax_definition()}")
            parts.append("")

        # Main query
        parts.append("EVALUATE")

        # Determine the main table function
        if query.dimensions:
            # Use SUMMARIZECOLUMNS for dimensional queries
            parts.append(self._generate_summarizecolumns(query))
        else:
            # Simple measure query
            parts.append(self._generate_measure_table(query))

        # Add ORDER BY if needed
        if query.order_by:
            order_parts = [o.to_dax() for o in query.order_by]
            parts.append(f"ORDER BY {', '.join(order_parts)}")

        return "\n".join(parts)

    def _generate_summarizecolumns(self, query: Query) -> str:
        """Generate SUMMARIZECOLUMNS function."""
        args = []

        # Group by columns (dimensions)
        for dim in query.dimensions:
            args.append(f"    {dim.to_dax()}")

        # Filters
        for filter_obj in query.filters:
            if hasattr(filter_obj.target, "dimension"):
                # Dimension filter
                dim_filter = filter_obj.target
                table = dim_filter.dimension.hierarchy.table
                filter_condition = dim_filter.to_dax()
                args.append(f"    FILTER(ALL({table}), {filter_condition})")

        # Measures
        for measure in query.measures:
            args.append(f"    {measure.to_dax()}")

        args_str = ",\n".join(args)
        return f"SUMMARIZECOLUMNS(\n{args_str}\n)"

    def _generate_measure_table(self, query: Query) -> str:
        """Generate a simple measure table for queries without dimensions."""
        if not query.measures:
            return 'ROW("Result", BLANK())'

        # Create a ROW with each measure
        measure_pairs = []
        for measure in query.measures:
            alias = measure.alias or measure.name
            measure_pairs.append(f'"{alias}", [{measure.name}]')

        return f"ROW({', '.join(measure_pairs)})"
