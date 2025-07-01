"""Data models for the MDX linter."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

from .enums import LintActionType, OptimizationLevel


@dataclass
class LintAction:
    """Represents a single linting action performed."""
    
    action_type: LintActionType
    description: str
    node_type: str
    original_text: str
    optimized_text: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    def __str__(self) -> str:
        """Return human-readable description of the action."""
        location = ""
        if self.line_number is not None:
            location = f" at line {self.line_number}"
            if self.column_number is not None:
                location += f", column {self.column_number}"
        
        return f"{self.action_type.value}: {self.description}{location}"


@dataclass 
class LintReport:
    """Report of all linting actions performed on an MDX query."""
    
    optimization_level: OptimizationLevel
    start_time: datetime
    end_time: Optional[datetime] = None
    actions: List[LintAction] = None
    rules_applied: List[str] = None
    original_size: int = 0
    optimized_size: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        """Initialize lists if not provided."""
        if self.actions is None:
            self.actions = []
        if self.rules_applied is None:
            self.rules_applied = []
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    @property
    def duration_ms(self) -> Optional[float]:
        """Calculate linting duration in milliseconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    @property
    def size_reduction(self) -> float:
        """Calculate size reduction percentage."""
        if self.original_size == 0:
            return 0.0
        return ((self.original_size - self.optimized_size) / self.original_size) * 100
    
    @property
    def action_summary(self) -> Dict[LintActionType, int]:
        """Get summary of actions by type."""
        summary = {}
        for action in self.actions:
            action_type = action.action_type
            summary[action_type] = summary.get(action_type, 0) + 1
        return summary
    
    def add_action(self, action: LintAction) -> None:
        """Add a linting action to the report."""
        self.actions.append(action)
    
    def add_rule(self, rule_name: str) -> None:
        """Add a rule name to the applied rules list."""
        if rule_name not in self.rules_applied:
            self.rules_applied.append(rule_name)
    
    def add_error(self, error: str) -> None:
        """Add an error to the report."""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the report."""
        self.warnings.append(warning)
    
    def finish(self) -> None:
        """Mark the linting process as finished."""
        self.end_time = datetime.now()
    
    def summary(self) -> str:
        """Generate a summary string of the linting results."""
        lines = []
        
        # Header
        lines.append("=== MDX Linting Report ===")
        lines.append(f"Optimization Level: {self.optimization_level.value}")
        
        if self.duration_ms is not None:
            lines.append(f"Duration: {self.duration_ms:.2f}ms")
        
        # Size changes
        lines.append(f"Original Size: {self.original_size:,} characters")
        lines.append(f"Optimized Size: {self.optimized_size:,} characters")
        lines.append(f"Size Reduction: {self.size_reduction:.1f}%")
        
        # Actions summary
        if self.actions:
            lines.append(f"\nActions Performed: {len(self.actions)}")
            action_summary = self.action_summary
            for action_type, count in action_summary.items():
                lines.append(f"  - {action_type.value}: {count}")
        else:
            lines.append("\nNo optimizations performed")
        
        # Rules applied
        if self.rules_applied:
            lines.append(f"\nRules Applied: {', '.join(self.rules_applied)}")
        
        # Errors and warnings
        if self.errors:
            lines.append(f"\nErrors: {len(self.errors)}")
            for error in self.errors:
                lines.append(f"  - {error}")
        
        if self.warnings:
            lines.append(f"\nWarnings: {len(self.warnings)}")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        return "\n".join(lines)


@dataclass
class LinterConfig:
    """Configuration for MDX linter behavior."""
    
    # Optimization level
    optimization_level: OptimizationLevel = OptimizationLevel.CONSERVATIVE
    
    # Rule-specific settings
    remove_redundant_parentheses: bool = True
    optimize_crossjoins: bool = True
    remove_duplicates: bool = True
    normalize_member_references: bool = True
    optimize_calculated_members: bool = False  # Only in moderate+
    simplify_function_calls: bool = False  # Only in moderate+
    
    # Advanced settings
    max_crossjoin_depth: int = 3  # Convert nested CrossJoins to tuples
    preserve_original_structure: bool = False  # Keep original for comparison
    generate_optimization_report: bool = True
    
    # Safety settings
    validate_before_optimizing: bool = True
    validate_after_optimizing: bool = True
    skip_on_validation_error: bool = True
    
    # Performance settings
    max_processing_time_ms: int = 5000  # 5 seconds max
    
    # Custom rules and disabled rules
    custom_rules: List[str] = None
    disabled_rules: List[str] = None
    
    def __post_init__(self):
        """Initialize lists and apply optimization level defaults."""
        if self.custom_rules is None:
            self.custom_rules = []
        if self.disabled_rules is None:
            self.disabled_rules = []
        
        # Apply optimization level defaults
        if self.optimization_level == OptimizationLevel.MODERATE:
            self.optimize_calculated_members = True
            self.simplify_function_calls = True
        elif self.optimization_level == OptimizationLevel.AGGRESSIVE:
            self.optimize_calculated_members = True
            self.simplify_function_calls = True
            self.max_crossjoin_depth = 5
    
    def is_rule_enabled(self, rule_name: str) -> bool:
        """Check if a specific rule is enabled."""
        return rule_name not in self.disabled_rules
    
    def should_apply_moderate_rules(self) -> bool:
        """Check if moderate-level rules should be applied."""
        return self.optimization_level in [OptimizationLevel.MODERATE, OptimizationLevel.AGGRESSIVE]
    
    def should_apply_aggressive_rules(self) -> bool:
        """Check if aggressive-level rules should be applied."""
        return self.optimization_level == OptimizationLevel.AGGRESSIVE