"""Serialization and deserialization for IR objects."""

import json
from typing import Any, Dict, Union
from pathlib import Path

from .models import Query
from .expressions import Expression


class IRSerializer:
    """Serializer for IR objects to JSON."""
    
    @staticmethod
    def serialize_query(query: Query) -> str:
        """Serialize a Query object to JSON string."""
        return query.model_dump_json(indent=2)
    
    @staticmethod
    def serialize_query_to_dict(query: Query) -> Dict[str, Any]:
        """Serialize a Query object to dictionary."""
        return query.model_dump()
    
    @staticmethod
    def save_query_to_file(query: Query, file_path: Union[str, Path]) -> None:
        """Save a Query object to JSON file."""
        file_path = Path(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(IRSerializer.serialize_query(query))
    
    @staticmethod
    def serialize_expression(expression: Expression) -> str:
        """Serialize an Expression object to JSON string."""
        return expression.model_dump_json(indent=2)
    
    @staticmethod
    def serialize_expression_to_dict(expression: Expression) -> Dict[str, Any]:
        """Serialize an Expression object to dictionary."""
        return expression.model_dump()


class IRDeserializer:
    """Deserializer for IR objects from JSON."""
    
    @staticmethod
    def deserialize_query(json_str: str) -> Query:
        """Deserialize a Query object from JSON string."""
        data = json.loads(json_str)
        return Query.model_validate(data)
    
    @staticmethod
    def deserialize_query_from_dict(data: Dict[str, Any]) -> Query:
        """Deserialize a Query object from dictionary."""
        return Query.model_validate(data)
    
    @staticmethod
    def load_query_from_file(file_path: Union[str, Path]) -> Query:
        """Load a Query object from JSON file."""
        file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            json_str = f.read()
        return IRDeserializer.deserialize_query(json_str)
    
    @staticmethod
    def deserialize_expression(json_str: str, expression_type: type) -> Expression:
        """Deserialize an Expression object from JSON string."""
        data = json.loads(json_str)
        return expression_type.model_validate(data)
    
    @staticmethod
    def deserialize_expression_from_dict(data: Dict[str, Any], expression_type: type) -> Expression:
        """Deserialize an Expression object from dictionary."""
        return expression_type.model_validate(data)


class IRValidator:
    """Validator for IR objects."""
    
    @staticmethod
    def validate_query(query: Query) -> Dict[str, Any]:
        """
        Validate a Query object and return validation results.
        
        Returns:
            Dictionary with validation results:
            - valid: bool - Whether the query is valid
            - errors: List[str] - List of error messages
            - warnings: List[str] - List of warning messages
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Use the query's built-in validation
            issues = query.validate_query()
            if issues:
                result['errors'].extend(issues)
                result['valid'] = False
            
            # Additional validation checks
            warnings = IRValidator._check_query_warnings(query)
            result['warnings'].extend(warnings)
            
        except Exception as e:
            result['errors'].append(f"Validation error: {str(e)}")
            result['valid'] = False
        
        return result
    
    @staticmethod
    def _check_query_warnings(query: Query) -> list[str]:
        """Check for potential issues that are warnings, not errors."""
        warnings = []
        
        # Check for complex calculations
        if len(query.calculations) > 5:
            warnings.append("Query has many calculations which may impact performance")
        
        # Check for many dimensions
        if len(query.dimensions) > 10:
            warnings.append("Query has many dimensions which may result in large result set")
        
        # Check for no filters on large dimensions
        if len(query.dimensions) > 3 and not query.filters:
            warnings.append("Query with many dimensions has no filters - result set may be very large")
        
        # Check for measure filters without dimensions
        measure_filters = [f for f in query.filters if f.filter_type.value == 'MEASURE']
        if measure_filters and not query.dimensions:
            warnings.append("Measure filters without grouping dimensions may not work as expected")
        
        # Check for circular dependencies (more sophisticated check)
        calc_names = {calc.name for calc in query.calculations}
        for calc in query.calculations:
            deps = calc.get_dependencies()
            circular_deps = calc_names.intersection(set(deps))
            if circular_deps:
                warnings.append(f"Calculation '{calc.name}' may have circular dependencies: {', '.join(circular_deps)}")
        
        return warnings


class IRComparator:
    """Utility for comparing IR objects."""
    
    @staticmethod
    def queries_equivalent(query1: Query, query2: Query) -> bool:
        """
        Check if two queries are semantically equivalent.
        
        This does a deep comparison of the query structure, ignoring
        metadata and other non-semantic differences.
        """
        # Create copies without metadata for comparison
        q1_dict = query1.model_dump(exclude={'metadata'})
        q2_dict = query2.model_dump(exclude={'metadata'})
        
        return q1_dict == q2_dict
    
    @staticmethod
    def query_differences(query1: Query, query2: Query) -> Dict[str, Any]:
        """
        Find differences between two queries.
        
        Returns:
            Dictionary describing the differences between the queries.
        """
        differences = {
            'cube': None,
            'measures': [],
            'dimensions': [],
            'filters': [],
            'calculations': [],
            'order_by': [],
            'limit': None
        }
        
        # Compare cubes
        if query1.cube != query2.cube:
            differences['cube'] = {
                'query1': query1.cube.model_dump(),
                'query2': query2.cube.model_dump()
            }
        
        # Compare measures
        q1_measures = {m.name: m for m in query1.measures}
        q2_measures = {m.name: m for m in query2.measures}
        
        for name in set(q1_measures.keys()) | set(q2_measures.keys()):
            if name not in q1_measures:
                differences['measures'].append({'type': 'added', 'measure': q2_measures[name].model_dump()})
            elif name not in q2_measures:
                differences['measures'].append({'type': 'removed', 'measure': q1_measures[name].model_dump()})
            elif q1_measures[name] != q2_measures[name]:
                differences['measures'].append({
                    'type': 'modified',
                    'name': name,
                    'query1': q1_measures[name].model_dump(),
                    'query2': q2_measures[name].model_dump()
                })
        
        # Similar comparisons for other components...
        # (Implementation would continue for dimensions, filters, etc.)
        
        return differences


class IROptimizer:
    """Optimizer for IR objects."""
    
    @staticmethod
    def optimize_query(query: Query) -> Query:
        """
        Optimize a query by applying various optimization techniques.
        
        Returns:
            Optimized copy of the query.
        """
        # Create a copy to avoid modifying the original
        import copy
        optimized = copy.deepcopy(query)
        
        # Apply optimizations
        optimized = IROptimizer._remove_redundant_filters(optimized)
        optimized = IROptimizer._merge_compatible_dimensions(optimized)
        optimized = IROptimizer._optimize_calculations(optimized)
        
        # Add optimization metadata
        optimized.metadata.optimization_hints.append("Query optimized by IROptimizer")
        
        return optimized
    
    @staticmethod
    def _remove_redundant_filters(query: Query) -> Query:
        """Remove redundant filters from the query."""
        # Simple implementation - remove duplicate filters
        seen_filters = set()
        unique_filters = []
        
        for filter_obj in query.filters:
            filter_key = (filter_obj.filter_type, str(filter_obj.target))
            if filter_key not in seen_filters:
                seen_filters.add(filter_key)
                unique_filters.append(filter_obj)
        
        query.filters = unique_filters
        return query
    
    @staticmethod
    def _merge_compatible_dimensions(query: Query) -> Query:
        """Merge compatible dimensions where possible."""
        # This is a placeholder - would implement logic to merge
        # dimensions from the same hierarchy at compatible levels
        return query
    
    @staticmethod
    def _optimize_calculations(query: Query) -> Query:
        """Optimize calculation expressions."""
        for calc in query.calculations:
            # Simple optimization - could expand this
            calc.expression = IROptimizer._optimize_expression(calc.expression)
        
        return query
    
    @staticmethod
    def _optimize_expression(expression: Expression) -> Expression:
        """Optimize an expression tree."""
        # Placeholder for expression optimization
        # Could implement things like constant folding, algebraic simplification, etc.
        return expression