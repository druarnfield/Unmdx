"""Human-readable explanation generator from IR representation."""


from ..ir.models import AggregationType, Query


class HumanReadableGenerator:
    """Generates human-readable explanations from IR representation."""

    def generate(self, query: Query) -> str:
        """Generate human-readable explanation from IR Query object.

        Args:
            query: The IR Query to explain

        Returns:
            str: The human-readable explanation
        """
        parts = []

        # Main query explanation
        parts.append("This query will:")
        parts.append("")

        # What we're calculating
        if query.measures:
            measure_text = ", ".join(m.to_human_readable() for m in query.measures)
            parts.append(f"1. Calculate: {measure_text}")

        # How we're grouping
        if query.dimensions:
            dim_text = ", ".join(d.to_human_readable() for d in query.dimensions)
            parts.append(f"2. Grouped by: {dim_text}")

        # Filters
        if query.filters:
            parts.append("3. Where:")
            for filter_obj in query.filters:
                parts.append(f"   - {filter_obj.to_human_readable()}")

        # Calculations
        if query.calculations:
            parts.append("4. With these calculations:")
            for calc in query.calculations:
                parts.append(f"   - {calc.to_human_readable()}")

        # Sorting
        if query.order_by:
            order_text = ", ".join(o.to_human_readable() for o in query.order_by)
            parts.append(f"5. Sorted by: {order_text}")

        # Limits
        if query.limit:
            parts.append(f"6. {query.limit.to_human_readable()}")

        # SQL-like representation
        parts.append("")
        parts.append("SQL-like representation:")
        parts.append("```sql")
        parts.append(self._generate_sql_like(query))
        parts.append("```")

        return "\n".join(parts)

    def _generate_sql_like(self, query: Query) -> str:
        """Generate SQL-like syntax for easier understanding."""
        sql_parts = []

        # SELECT clause
        select_items = []

        # Add dimensions first
        for dim in query.dimensions:
            select_items.append(dim.level.name)

        # Add measures
        for measure in query.measures:
            alias = measure.alias or measure.name
            if measure.aggregation == AggregationType.CUSTOM:
                # For custom calculations, use the alias
                select_items.append(alias)
            else:
                select_items.append(
                    f"{measure.aggregation.value}({measure.name}) AS {alias}"
                )

        sql_parts.append(f"SELECT {', '.join(select_items)}")

        # FROM clause
        sql_parts.append(f"FROM {query.cube.name}")

        # WHERE clause
        if query.filters:
            where_conditions = []
            for filter_obj in query.filters:
                where_conditions.append(filter_obj.to_human_readable())
            sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")

        # GROUP BY clause
        if query.dimensions:
            group_by_items = [d.level.name for d in query.dimensions]
            sql_parts.append(f"GROUP BY {', '.join(group_by_items)}")

        # ORDER BY clause
        if query.order_by:
            order_items = [o.to_human_readable() for o in query.order_by]
            sql_parts.append(f"ORDER BY {', '.join(order_items)}")

        # LIMIT clause
        if query.limit:
            if query.limit.offset > 0:
                sql_parts.append(
                    f"LIMIT {query.limit.count} OFFSET {query.limit.offset}"
                )
            else:
                sql_parts.append(f"LIMIT {query.limit.count}")

        return "\n".join(sql_parts)
