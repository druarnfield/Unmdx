"""Convert IR expressions to DAX syntax."""

from typing import Any, Dict, List, Optional

from ..ir.expressions import (
    Expression, Constant, MeasureReference, MemberReference,
    BinaryOperation, FunctionCall, IifExpression, CaseExpression,
    UnaryOperation
)
from ..ir.enums import FunctionType
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ExpressionConverter:
    """Converts IR Expression objects to DAX syntax."""
    
    def __init__(self):
        """Initialize the expression converter."""
        self.logger = get_logger(__name__)
        
        # Map binary operators to DAX equivalents
        self.binary_operator_map = {
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "DIVIDE",  # Use DIVIDE for safety
            "^": "^",
            "&": "&",  # String concatenation
            "=": "=",
            "<>": "<>",
            ">": ">",
            "<": "<",
            ">=": ">=",
            "<=": "<=",
            "AND": "&&",
            "OR": "||",
        }
        
        # Map function types to DAX functions
        self.function_map = {
            FunctionType.SUM: "SUM",
            FunctionType.AVG: "AVERAGE",
            FunctionType.COUNT: "COUNT",
            FunctionType.DISTINCT_COUNT: "DISTINCTCOUNT",
            FunctionType.MIN: "MIN",
            FunctionType.MAX: "MAX",
            FunctionType.ABS: "ABS",
            FunctionType.ROUND: "ROUND",
            FunctionType.FLOOR: "FLOOR",
            FunctionType.CEILING: "CEILING",
            FunctionType.MEMBERS: "VALUES",  # MDX MEMBERS -> DAX VALUES
            FunctionType.CHILDREN: "VALUES",  # Simplified mapping
            FunctionType.IIF: "IF",
            FunctionType.CASE: "SWITCH",
        }
    
    def convert(self, expression: Expression) -> str:
        """
        Convert an Expression to DAX syntax.
        
        Args:
            expression: The IR expression to convert
            
        Returns:
            DAX expression string
            
        Raises:
            ValueError: If expression type is not supported
        """
        if isinstance(expression, Constant):
            return self._convert_constant(expression)
        elif isinstance(expression, MeasureReference):
            return self._convert_measure_reference(expression)
        elif isinstance(expression, MemberReference):
            return self._convert_member_reference(expression)
        elif isinstance(expression, BinaryOperation):
            return self._convert_binary_operation(expression)
        elif isinstance(expression, FunctionCall):
            return self._convert_function_call(expression)
        elif isinstance(expression, IifExpression):
            return self._convert_iif(expression)
        elif isinstance(expression, CaseExpression):
            return self._convert_case(expression)
        elif isinstance(expression, UnaryOperation):
            return self._convert_unary_operation(expression)
        else:
            raise ValueError(f"Unsupported expression type: {type(expression).__name__}")
    
    def _convert_constant(self, constant: Constant) -> str:
        """Convert a constant value to DAX."""
        # Use the existing to_dax method from the IR
        return constant.to_dax()
    
    def _convert_measure_reference(self, measure_ref: MeasureReference) -> str:
        """Convert a measure reference to DAX."""
        # Use the existing to_dax method from the IR
        return measure_ref.to_dax()
    
    def _convert_member_reference(self, member_ref: MemberReference) -> str:
        """Convert a member reference to DAX."""
        # Use the existing to_dax method from the IR
        return member_ref.to_dax()
    
    def _convert_binary_operation(self, binary_op: BinaryOperation) -> str:
        """Convert a binary operation to DAX."""
        # Use the existing to_dax method from the IR
        return binary_op.to_dax()
    
    def _convert_function_call(self, func_call: FunctionCall) -> str:
        """Convert a function call to DAX."""
        # Use the existing to_dax method from the IR, but add some custom handling for special cases
        base_dax = func_call.to_dax()
        
        # For certain function types, we might want to do additional processing
        func_type = func_call.function_type
        
        if func_type == FunctionType.CROSSJOIN:
            # CrossJoin in expressions (rare) - add a comment
            return f"-- CROSSJOIN expression: {base_dax}"
        elif func_type == FunctionType.MEMBERS:
            # MDX MEMBERS might map to DAX VALUES
            return base_dax.replace("MEMBERS", "VALUES")
        else:
            return base_dax
    
    def _convert_iif(self, iif_expr: IifExpression) -> str:
        """Convert an IIF expression to DAX."""
        # Use the existing to_dax method from the IR
        return iif_expr.to_dax()
    
    def _convert_case(self, case_expr: CaseExpression) -> str:
        """Convert a CASE expression to DAX."""
        # Use the existing to_dax method from CaseExpression
        return case_expr.to_dax()
    
    def _convert_unary_operation(self, unary_op: UnaryOperation) -> str:
        """Convert a unary operation to DAX."""
        # Use the existing to_dax method from the IR
        return unary_op.to_dax()
    
    def validate_expression(self, expression: Expression) -> List[str]:
        """
        Validate an expression for DAX compatibility.
        
        Args:
            expression: The expression to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        try:
            # Try to convert - this will catch unsupported types
            self.convert(expression)
        except Exception as e:
            issues.append(f"Expression conversion error: {str(e)}")
        
        # Check for specific DAX limitations
        if isinstance(expression, BinaryOperation):
            # Check for problematic operators
            if expression.operator == "%":
                issues.append("Modulo operator (%) not directly supported in DAX - use MOD function")
        
        elif isinstance(expression, FunctionCall):
            # Check for unsupported functions
            if expression.function_type == FunctionType.MATH:
                # Generic math functions need validation
                func_name = expression.function_name.upper()
                unsupported = ["STDDEV", "VARIANCE", "MEDIAN"]
                if func_name in unsupported:
                    issues.append(f"Function {func_name} may require special handling in DAX")
        
        return issues