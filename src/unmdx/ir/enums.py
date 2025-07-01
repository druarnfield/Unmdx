"""Enums for Intermediate Representation."""

from enum import Enum


class AggregationType(Enum):
    """Types of aggregation for measures."""
    SUM = "SUM"
    AVG = "AVERAGE"
    COUNT = "COUNT"
    DISTINCT_COUNT = "DISTINCTCOUNT"
    MIN = "MIN"
    MAX = "MAX"
    CUSTOM = "CUSTOM"


class MemberSelectionType(Enum):
    """How members are selected from a dimension."""
    ALL = "ALL"              # All members at this level
    SPECIFIC = "SPECIFIC"    # Listed members
    CHILDREN = "CHILDREN"    # Children of a member
    DESCENDANTS = "DESCENDANTS"
    RANGE = "RANGE"         # Member range


class FilterType(Enum):
    """Types of filters."""
    DIMENSION = "DIMENSION"
    MEASURE = "MEASURE"
    NON_EMPTY = "NON_EMPTY"


class FilterOperator(Enum):
    """Operators for dimension filters."""
    EQUALS = "="
    NOT_EQUALS = "<>"
    IN = "IN"
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="


class ComparisonOperator(Enum):
    """Operators for measure comparisons."""
    EQ = "="
    NEQ = "<>"
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="


class CalculationType(Enum):
    """Types of calculations."""
    MEASURE = "MEASURE"
    MEMBER = "MEMBER"
    SET = "SET"


class SortDirection(Enum):
    """Sort direction."""
    ASC = "ASC"
    DESC = "DESC"


class ExpressionType(Enum):
    """Types of expressions."""
    BINARY_OPERATION = "BINARY_OPERATION"
    UNARY_OPERATION = "UNARY_OPERATION"
    MEASURE_REFERENCE = "MEASURE_REFERENCE"
    MEMBER_REFERENCE = "MEMBER_REFERENCE"
    CONSTANT = "CONSTANT"
    FUNCTION_CALL = "FUNCTION_CALL"
    CASE_EXPRESSION = "CASE_EXPRESSION"
    IIF_EXPRESSION = "IIF_EXPRESSION"


class FunctionType(Enum):
    """Types of MDX functions."""
    # Set functions
    CROSSJOIN = "CROSSJOIN"
    FILTER = "FILTER"
    DESCENDANTS = "DESCENDANTS"
    ANCESTORS = "ANCESTORS"
    MEMBERS = "MEMBERS"
    CHILDREN = "CHILDREN"
    UNION = "UNION"
    INTERSECT = "INTERSECT"
    EXCEPT = "EXCEPT"
    NONEMPTY = "NONEMPTY"
    
    # Aggregation functions
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    MIN = "MIN"
    MAX = "MAX"
    
    # Math functions
    MATH = "MATH"
    
    # Aggregate functions
    AGGREGATE = "AGGREGATE"
    
    # Navigation functions
    PARENT = "PARENT"
    LEAD = "LEAD"
    LAG = "LAG"
    
    # String functions
    CONCATENATE = "CONCATENATE"
    FORMAT = "FORMAT"
    
    # Logical functions
    IIF = "IIF"
    CASE = "CASE"
    
    # Time intelligence
    PARALLELPERIOD = "PARALLELPERIOD"
    PERIODSTODATE = "PERIODSTODATE"
    YTD = "YTD"
    QTD = "QTD"
    TIME = "TIME"
    PREVIOUSMONTH = "PREVIOUSMONTH"
    
    # Statistical functions
    STATISTICAL = "STATISTICAL"
    CORRELATION = "CORRELATION"
    
    # Lookup functions
    LOOKUP = "LOOKUP"
    RELATED = "RELATED"
    MTD = "MTD"
    
    # Math functions
    DIVIDE = "DIVIDE"
    ROUND = "ROUND"
    ABS = "ABS"