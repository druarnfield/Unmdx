"""Expression classes for Intermediate Representation."""

from abc import ABC, abstractmethod
from typing import Any, List, Union
from pydantic import BaseModel, Field

from .enums import ExpressionType, FunctionType


class Expression(BaseModel, ABC):
    """Base class for all expressions."""
    
    expression_type: ExpressionType
    
    @abstractmethod
    def to_dax(self) -> str:
        """Convert expression to DAX syntax."""
        pass
    
    @abstractmethod
    def to_human_readable(self) -> str:
        """Convert expression to human-readable text."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get list of measure/member names this expression depends on."""
        pass


class Constant(Expression):
    """Constant value expression."""
    
    expression_type: ExpressionType = Field(default=ExpressionType.CONSTANT, frozen=True)
    value: Union[float, int, str, bool]
    
    def to_dax(self) -> str:
        """Convert constant to DAX syntax."""
        if isinstance(self.value, str):
            return f'"{self.value}"'
        elif isinstance(self.value, bool):
            return "TRUE" if self.value else "FALSE"
        else:
            return str(self.value)
    
    def to_human_readable(self) -> str:
        """Convert constant to human-readable text."""
        return str(self.value)
    
    def get_dependencies(self) -> List[str]:
        """Constants have no dependencies."""
        return []


class MeasureReference(Expression):
    """Reference to a measure."""
    
    expression_type: ExpressionType = Field(default=ExpressionType.MEASURE_REFERENCE, frozen=True)
    measure_name: str
    
    def to_dax(self) -> str:
        """Convert measure reference to DAX syntax."""
        return f"[{self.measure_name}]"
    
    def to_human_readable(self) -> str:
        """Convert measure reference to human-readable text."""
        return self.measure_name
    
    def get_dependencies(self) -> List[str]:
        """Return the measure name as dependency."""
        return [self.measure_name]


class MemberReference(Expression):
    """Reference to a dimension member."""
    
    expression_type: ExpressionType = Field(default=ExpressionType.MEMBER_REFERENCE, frozen=True)
    dimension: str
    hierarchy: str
    member: str
    
    def to_dax(self) -> str:
        """Convert member reference to DAX syntax."""
        # In DAX, member references are typically used in filters
        return f"{self.dimension}[{self.member}]"
    
    def to_human_readable(self) -> str:
        """Convert member reference to human-readable text."""
        return f"{self.member} in {self.dimension}"
    
    def get_dependencies(self) -> List[str]:
        """Return the dimension as dependency."""
        return [f"{self.dimension}.{self.member}"]


class BinaryOperation(Expression):
    """Binary operation expression (e.g., +, -, *, /)."""
    
    expression_type: ExpressionType = Field(default=ExpressionType.BINARY_OPERATION, frozen=True)
    left: Expression
    operator: str
    right: Expression
    
    def to_dax(self) -> str:
        """Convert binary operation to DAX syntax."""
        # Handle division specially for safety
        if self.operator == "/":
            return f"DIVIDE({self.left.to_dax()}, {self.right.to_dax()})"
        elif self.operator in ["+", "-", "*"]:
            return f"({self.left.to_dax()} {self.operator} {self.right.to_dax()})"
        elif self.operator == "&":
            # String concatenation
            return f"CONCATENATE({self.left.to_dax()}, {self.right.to_dax()})"
        else:
            # Default case
            return f"({self.left.to_dax()} {self.operator} {self.right.to_dax()})"
    
    def to_human_readable(self) -> str:
        """Convert binary operation to human-readable text."""
        op_text = {
            "+": "plus",
            "-": "minus",
            "*": "times",
            "/": "divided by",
            "&": "concatenated with",
            "=": "equals",
            "<>": "not equal to",
            ">": "greater than",
            "<": "less than",
            ">=": "greater than or equal to",
            "<=": "less than or equal to"
        }
        operator_text = op_text.get(self.operator, self.operator)
        return f"{self.left.to_human_readable()} {operator_text} {self.right.to_human_readable()}"
    
    def get_dependencies(self) -> List[str]:
        """Get dependencies from both operands."""
        return self.left.get_dependencies() + self.right.get_dependencies()


class UnaryOperation(Expression):
    """Unary operation expression (e.g., -, NOT)."""
    
    expression_type: ExpressionType = Field(default=ExpressionType.UNARY_OPERATION, frozen=True)
    operator: str
    operand: Expression
    
    def to_dax(self) -> str:
        """Convert unary operation to DAX syntax."""
        if self.operator == "-":
            return f"-({self.operand.to_dax()})"
        elif self.operator.upper() == "NOT":
            return f"NOT({self.operand.to_dax()})"
        else:
            return f"{self.operator}({self.operand.to_dax()})"
    
    def to_human_readable(self) -> str:
        """Convert unary operation to human-readable text."""
        op_text = {
            "-": "negative",
            "NOT": "not",
            "+": "positive"
        }
        operator_text = op_text.get(self.operator.upper(), self.operator)
        return f"{operator_text} {self.operand.to_human_readable()}"
    
    def get_dependencies(self) -> List[str]:
        """Get dependencies from operand."""
        return self.operand.get_dependencies()


class FunctionCall(Expression):
    """Function call expression."""
    
    expression_type: ExpressionType = Field(default=ExpressionType.FUNCTION_CALL, frozen=True)
    function_type: FunctionType
    arguments: List[Expression] = Field(default_factory=list)
    
    def to_dax(self) -> str:
        """Convert function call to DAX syntax."""
        args_dax = [arg.to_dax() for arg in self.arguments]
        
        # Special handling for specific functions
        if self.function_type == FunctionType.DIVIDE and len(args_dax) == 2:
            return f"DIVIDE({args_dax[0]}, {args_dax[1]})"
        elif self.function_type == FunctionType.IIF and len(args_dax) == 3:
            return f"IF({args_dax[0]}, {args_dax[1]}, {args_dax[2]})"
        elif self.function_type == FunctionType.CONCATENATE:
            return f"CONCATENATE({', '.join(args_dax)})"
        elif self.function_type in [FunctionType.SUM, FunctionType.AVG, FunctionType.COUNT, 
                                   FunctionType.MIN, FunctionType.MAX]:
            # Aggregation functions in DAX context
            if len(args_dax) == 1:
                return f"{self.function_type.value}({args_dax[0]})"
            else:
                return f"{self.function_type.value}X({args_dax[0]}, {args_dax[1]})"
        else:
            # Default function call
            return f"{self.function_type.value}({', '.join(args_dax)})"
    
    def to_human_readable(self) -> str:
        """Convert function call to human-readable text."""
        args_readable = [arg.to_human_readable() for arg in self.arguments]
        
        # Special handling for common functions
        if self.function_type == FunctionType.DIVIDE and len(args_readable) == 2:
            return f"{args_readable[0]} divided by {args_readable[1]}"
        elif self.function_type == FunctionType.IIF and len(args_readable) == 3:
            return f"if {args_readable[0]} then {args_readable[1]} else {args_readable[2]}"
        elif self.function_type == FunctionType.SUM:
            return f"sum of {', '.join(args_readable)}"
        elif self.function_type == FunctionType.AVG:
            return f"average of {', '.join(args_readable)}"
        elif self.function_type == FunctionType.COUNT:
            return f"count of {', '.join(args_readable)}"
        elif self.function_type == FunctionType.MIN:
            return f"minimum of {', '.join(args_readable)}"
        elif self.function_type == FunctionType.MAX:
            return f"maximum of {', '.join(args_readable)}"
        else:
            # Default function description
            function_name = self.function_type.value.lower()
            return f"{function_name}({', '.join(args_readable)})"
    
    def get_dependencies(self) -> List[str]:
        """Get dependencies from all arguments."""
        dependencies = []
        for arg in self.arguments:
            dependencies.extend(arg.get_dependencies())
        return dependencies


class CaseExpression(Expression):
    """CASE expression with when/then/else clauses."""
    
    expression_type: ExpressionType = Field(default=ExpressionType.CASE_EXPRESSION, frozen=True)
    when_conditions: List[tuple[Expression, Expression]]  # (condition, result) pairs
    else_value: Expression | None = None
    
    def to_dax(self) -> str:
        """Convert CASE expression to DAX SWITCH syntax."""
        if not self.when_conditions:
            return self.else_value.to_dax() if self.else_value else "BLANK()"
        
        # Build nested IF statements
        result = self.else_value.to_dax() if self.else_value else "BLANK()"
        
        # Build from the end backwards
        for condition, value in reversed(self.when_conditions):
            result = f"IF({condition.to_dax()}, {value.to_dax()}, {result})"
        
        return result
    
    def to_human_readable(self) -> str:
        """Convert CASE expression to human-readable text."""
        parts = ["case when"]
        
        for i, (condition, value) in enumerate(self.when_conditions):
            if i > 0:
                parts.append("when")
            parts.append(f"{condition.to_human_readable()} then {value.to_human_readable()}")
        
        if self.else_value:
            parts.append(f"else {self.else_value.to_human_readable()}")
        
        return " ".join(parts)
    
    def get_dependencies(self) -> List[str]:
        """Get dependencies from all conditions and values."""
        dependencies = []
        for condition, value in self.when_conditions:
            dependencies.extend(condition.get_dependencies())
            dependencies.extend(value.get_dependencies())
        if self.else_value:
            dependencies.extend(self.else_value.get_dependencies())
        return dependencies


class IifExpression(Expression):
    """IIF (Immediate If) expression."""
    
    expression_type: ExpressionType = Field(default=ExpressionType.IIF_EXPRESSION, frozen=True)
    condition: Expression
    true_value: Expression
    false_value: Expression
    
    def to_dax(self) -> str:
        """Convert IIF expression to DAX IF syntax."""
        return f"IF({self.condition.to_dax()}, {self.true_value.to_dax()}, {self.false_value.to_dax()})"
    
    def to_human_readable(self) -> str:
        """Convert IIF expression to human-readable text."""
        return f"if {self.condition.to_human_readable()} then {self.true_value.to_human_readable()} else {self.false_value.to_human_readable()}"
    
    def get_dependencies(self) -> List[str]:
        """Get dependencies from condition and both values."""
        dependencies = []
        dependencies.extend(self.condition.get_dependencies())
        dependencies.extend(self.true_value.get_dependencies())
        dependencies.extend(self.false_value.get_dependencies())
        return dependencies