"""Intermediate Representation (IR) models for MDX to DAX conversion."""

from dataclasses import dataclass, field
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


class FilterType(Enum):
    """Types of filters."""

    DIMENSION = "DIMENSION"
    MEASURE = "MEASURE"


class FilterOperator(Enum):
    """Filter operators for dimension filters."""

    EQUALS = "EQUALS"
    IN = "IN"
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"


class ComparisonOperator(Enum):
    """Comparison operators for measure filters."""

    EQ = "="
    NEQ = "<>"
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="


class MemberSelectionType(Enum):
    """Types of member selection."""

    ALL = "ALL"
    SPECIFIC = "SPECIFIC"
    CHILDREN = "CHILDREN"
    DESCENDANTS = "DESCENDANTS"
    RANGE = "RANGE"


class CalculationType(Enum):
    """Types of calculations."""

    MEASURE = "MEASURE"
    MEMBER = "MEMBER"


class SortDirection(Enum):
    """Sort directions."""

    ASC = "ASC"
    DESC = "DESC"


@dataclass
class CubeReference:
    """Reference to the data source."""

    name: str
    database: str | None = None

    def to_dax(self) -> str:
        """Generate DAX representation."""
        return f"-- Using model: {self.name}"

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        return f"the {self.name} data model"


@dataclass
class HierarchyReference:
    """Reference to a dimension hierarchy."""

    table: str
    name: str

    def to_dax(self) -> str:
        """Generate DAX representation."""
        return self.table

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        return self.name


@dataclass
class LevelReference:
    """Reference to a level within a hierarchy."""

    name: str

    def to_dax(self) -> str:
        """Generate DAX representation."""
        return self.name

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        return self.name


@dataclass
class MemberSelection:
    """How members are selected from a dimension."""

    selection_type: MemberSelectionType
    specific_members: list[str] | None = None

    def is_all_members(self) -> bool:
        """Check if this selects all members."""
        return self.selection_type == MemberSelectionType.ALL

    def to_dax(self) -> str:
        """Generate DAX representation."""
        if (
            self.selection_type == MemberSelectionType.SPECIFIC
            and self.specific_members
        ):
            values_list = ", ".join(f'"{v}"' for v in self.specific_members)
            return f"IN {{{values_list}}}"
        return ""

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        if self.selection_type == MemberSelectionType.ALL:
            return "all values"
        elif (
            self.selection_type == MemberSelectionType.SPECIFIC
            and self.specific_members
        ):
            return f"specific values: {', '.join(self.specific_members)}"
        return "unknown selection"


@dataclass
class Expression:
    """Base class for expressions."""

    def to_dax(self) -> str:
        """Generate DAX representation."""
        raise NotImplementedError("Subclasses must implement to_dax()")

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        raise NotImplementedError("Subclasses must implement to_human_readable()")


@dataclass
class BinaryOperation(Expression):
    """Binary operations like +, -, *, /."""

    left: Expression
    operator: str
    right: Expression

    def to_dax(self) -> str:
        """Generate DAX representation."""
        if self.operator == "/":
            return f"DIVIDE({self.left.to_dax()}, {self.right.to_dax()})"
        return f"({self.left.to_dax()} {self.operator} {self.right.to_dax()})"

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        op_text = {"+": "plus", "-": "minus", "*": "times", "/": "divided by"}
        return f"{self.left.to_human_readable()} {op_text.get(self.operator, self.operator)} {self.right.to_human_readable()}"


@dataclass
class MeasureReference(Expression):
    """Reference to a measure."""

    measure_name: str

    def to_dax(self) -> str:
        """Generate DAX representation."""
        return f"[{self.measure_name}]"

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        return self.measure_name


@dataclass
class Constant(Expression):
    """Constant value."""

    value: float | int | str

    def to_dax(self) -> str:
        """Generate DAX representation."""
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        return str(self.value)


@dataclass
class Measure:
    """A measure to be calculated."""

    name: str
    aggregation: AggregationType
    expression: Expression | None = None
    alias: str | None = None
    format_string: str | None = None

    def to_dax(self) -> str:
        """Generate DAX representation."""
        if self.alias:
            return f'"{self.alias}", [{self.name}]'
        return f'"{self.name}", [{self.name}]'

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        agg_text = {
            AggregationType.SUM: "total",
            AggregationType.AVG: "average",
            AggregationType.COUNT: "count of",
            AggregationType.MIN: "minimum",
            AggregationType.MAX: "maximum",
        }
        return f"{agg_text.get(self.aggregation, '')} {self.name}"


@dataclass
class Dimension:
    """A dimension for grouping."""

    hierarchy: HierarchyReference
    level: LevelReference
    members: MemberSelection

    def to_dax(self) -> str:
        """Generate DAX representation."""
        return f"{self.hierarchy.table}[{self.level.name}]"

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        if self.members.is_all_members():
            return f"each {self.level.name}"
        else:
            return f"specific {self.level.name} values"


@dataclass
class DimensionFilter:
    """Filter on dimension members."""

    dimension: Dimension
    operator: FilterOperator
    values: list[str]

    def to_dax(self) -> str:
        """Generate DAX representation."""
        table = self.dimension.hierarchy.table
        column = self.dimension.level.name
        if self.operator == FilterOperator.IN:
            values_list = ", ".join(f'"{v}"' for v in self.values)
            return f"{table}[{column}] IN {{{values_list}}}"
        elif self.operator == FilterOperator.EQUALS:
            return f'{table}[{column}] = "{self.values[0]}"'
        return ""

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        if self.operator == FilterOperator.IN:
            return f"{self.dimension.level.name} is one of ({', '.join(self.values)})"
        elif self.operator == FilterOperator.EQUALS:
            return f"{self.dimension.level.name} equals {self.values[0]}"
        return "unknown filter"


@dataclass
class MeasureFilter:
    """Filter on measure values."""

    measure: Measure
    operator: ComparisonOperator
    value: float | int

    def to_dax(self) -> str:
        """Generate DAX representation."""
        return f"[{self.measure.name}] {self.operator.value} {self.value}"

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        op_text = {
            ComparisonOperator.GT: "greater than",
            ComparisonOperator.LT: "less than",
            ComparisonOperator.GTE: "at least",
            ComparisonOperator.LTE: "at most",
            ComparisonOperator.EQ: "equals",
            ComparisonOperator.NEQ: "not equal to",
        }
        return f"{self.measure.name} is {op_text[self.operator]} {self.value}"


@dataclass
class Filter:
    """A filter condition."""

    filter_type: FilterType
    target: DimensionFilter | MeasureFilter

    def to_dax(self) -> str:
        """Generate DAX representation."""
        return self.target.to_dax()

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        return self.target.to_human_readable()


@dataclass
class Calculation:
    """A calculated measure or member."""

    name: str
    calculation_type: CalculationType
    expression: Expression
    solve_order: int | None = None

    def to_dax_definition(self) -> str:
        """Generate DAX definition."""
        return f"MEASURE {self.name} = {self.expression.to_dax()}"

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        return f"Calculate {self.name} as {self.expression.to_human_readable()}"


@dataclass
class OrderBy:
    """Ordering specification."""

    expression: Measure | Dimension
    direction: SortDirection = SortDirection.ASC

    def to_dax(self) -> str:
        """Generate DAX representation."""
        expr_dax = self.expression.to_dax()
        if self.direction == SortDirection.DESC:
            return f"{expr_dax} DESC"
        return expr_dax

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        direction_text = (
            "descending" if self.direction == SortDirection.DESC else "ascending"
        )
        return f"{self.expression.to_human_readable()} {direction_text}"


@dataclass
class Limit:
    """Limit specification."""

    count: int
    offset: int = 0

    def to_dax(self) -> str:
        """Generate DAX representation."""
        if self.offset > 0:
            return f"TOPN({self.count}, ..., ..., {self.offset})"
        return f"TOPN({self.count}, ...)"

    def to_human_readable(self) -> str:
        """Generate human-readable representation."""
        if self.offset > 0:
            return f"limit to {self.count} rows starting from row {self.offset + 1}"
        return f"limit to {self.count} rows"


@dataclass
class QueryMetadata:
    """Metadata for optimization and processing."""

    complexity_score: float = 0.0
    estimated_rows: int | None = None
    source_mdx: str | None = None
    parsing_warnings: list[str] = field(default_factory=list)
    optimization_notes: list[str] = field(default_factory=list)


@dataclass
class Query:
    """Root node representing a complete query."""

    cube: CubeReference
    measures: list[Measure]
    dimensions: list[Dimension]
    filters: list[Filter]
    order_by: list[OrderBy] = field(default_factory=list)
    limit: Limit | None = None
    calculations: list[Calculation] = field(default_factory=list)
    metadata: QueryMetadata = field(default_factory=QueryMetadata)

    def to_dax(self) -> str:
        """Generate DAX representation."""
        from ..dax_generator.generator import DaxGenerator

        generator = DaxGenerator()
        return generator.generate(self)

    def to_human_readable(self) -> str:
        """Generate human-readable explanation."""
        from ..explainer.generator import HumanReadableGenerator

        generator = HumanReadableGenerator()
        return generator.generate(self)
