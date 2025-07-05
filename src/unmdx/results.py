"""
Result classes for UnMDX API operations.

This module defines result classes that encapsulate the outputs from various
UnMDX operations, providing structured access to results, metadata, warnings,
and performance statistics.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

from .ir.models import Query as IRQuery


@dataclass
class PerformanceStats:
    """
    Performance statistics for UnMDX operations.
    
    Tracks timing information and resource usage for various stages
    of the MDX processing pipeline.
    """
    
    # Timing information (in seconds)
    total_time: float = 0.0
    parse_time: Optional[float] = None
    transform_time: Optional[float] = None
    lint_time: Optional[float] = None
    generation_time: Optional[float] = None
    explanation_time: Optional[float] = None
    
    # Resource usage
    memory_peak_mb: Optional[float] = None
    memory_delta_mb: Optional[float] = None
    
    # Processing statistics
    input_size_chars: Optional[int] = None
    output_size_chars: Optional[int] = None
    ast_nodes_processed: Optional[int] = None
    ir_constructs_created: Optional[int] = None
    
    def add_timing(self, stage: str, duration: float) -> None:
        """
        Add timing information for a processing stage.
        
        Args:
            stage: Name of the processing stage
            duration: Duration in seconds
        """
        setattr(self, f"{stage}_time", duration)
        self.total_time += duration
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance statistics.
        
        Returns:
            Dictionary with key performance metrics
        """
        return {
            "total_time_ms": round(self.total_time * 1000, 2),
            "parse_time_ms": round(self.parse_time * 1000, 2) if self.parse_time else None,
            "transform_time_ms": round(self.transform_time * 1000, 2) if self.transform_time else None,
            "generation_time_ms": round(self.generation_time * 1000, 2) if self.generation_time else None,
            "memory_peak_mb": self.memory_peak_mb,
            "input_size_chars": self.input_size_chars,
            "output_size_chars": self.output_size_chars
        }


@dataclass
class Warning:
    """
    Represents a warning generated during processing.
    
    Warnings indicate non-fatal issues that the user should be aware of,
    such as deprecated syntax, suboptimal patterns, or potential issues.
    """
    
    message: str
    category: str
    severity: str = "warning"  # warning, info, deprecation
    location: Optional[Dict[str, Any]] = None  # line, column, context
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the warning."""
        location_str = ""
        if self.location and self.location.get("line"):
            location_str = f" (line {self.location['line']})"
        
        result = f"{self.severity.title()}: {self.message}{location_str}"
        if self.suggestion:
            result += f" Suggestion: {self.suggestion}"
        return result


@dataclass
class ParseResult:
    """
    Result of MDX parsing operation.
    
    Contains the intermediate representation (IR) generated from parsing
    an MDX query, along with metadata and performance information.
    """
    
    # Primary result
    ir_query: IRQuery
    
    # Metadata
    query_hash: str
    parsed_at: datetime = field(default_factory=datetime.now)
    parser_version: str = "1.0.0"
    
    # Quality metrics
    warnings: List[Warning] = field(default_factory=list)
    complexity_score: Optional[float] = None
    estimated_performance: Optional[str] = None  # fast, moderate, slow
    
    # Performance statistics
    performance: PerformanceStats = field(default_factory=PerformanceStats)
    
    # Raw parsing information
    parse_tree: Optional[Any] = None  # Parse tree from Lark parser
    ast_node_count: Optional[int] = None
    ir_construct_count: Optional[int] = None
    
    def add_warning(self, message: str, category: str = "general", **kwargs) -> None:
        """
        Add a warning to the result.
        
        Args:
            message: Warning message
            category: Warning category
            **kwargs: Additional warning properties
        """
        warning = Warning(message=message, category=category, **kwargs)
        self.warnings.append(warning)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_warning_summary(self) -> Dict[str, int]:
        """
        Get summary of warnings by category.
        
        Returns:
            Dictionary mapping warning categories to counts
        """
        summary = {}
        for warning in self.warnings:
            summary[warning.category] = summary.get(warning.category, 0) + 1
        return summary


@dataclass
class ConversionResult:
    """
    Result of MDX to DAX conversion operation.
    
    Contains the generated DAX query along with metadata, warnings,
    and performance information from the complete conversion pipeline.
    """
    
    # Primary result
    dax_query: str
    
    # Intermediate representation (optional)
    ir_query: Optional[IRQuery] = None
    
    # Metadata
    query_hash: str = ""
    converted_at: datetime = field(default_factory=datetime.now)
    converter_version: str = "1.0.0"
    
    # Processing information
    original_mdx: Optional[str] = None
    optimization_applied: bool = False
    optimization_level: Optional[str] = None
    
    # Quality metrics
    warnings: List[Warning] = field(default_factory=list)
    complexity_score: Optional[float] = None
    estimated_performance: Optional[str] = None
    semantic_equivalence_score: Optional[float] = None
    
    # Performance statistics
    performance: PerformanceStats = field(default_factory=PerformanceStats)
    
    # Generated DAX properties
    dax_functions_used: List[str] = field(default_factory=list)
    dax_tables_referenced: List[str] = field(default_factory=list)
    dax_measures_created: int = 0
    
    def add_warning(self, message: str, category: str = "general", **kwargs) -> None:
        """Add a warning to the result."""
        warning = Warning(message=message, category=category, **kwargs)
        self.warnings.append(warning)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get comprehensive metadata about the conversion.
        
        Returns:
            Dictionary with conversion metadata
        """
        return {
            "query_hash": self.query_hash,
            "converted_at": self.converted_at.isoformat(),
            "converter_version": self.converter_version,
            "optimization_applied": self.optimization_applied,
            "optimization_level": self.optimization_level,
            "complexity_score": self.complexity_score,
            "estimated_performance": self.estimated_performance,
            "semantic_equivalence_score": self.semantic_equivalence_score,
            "dax_functions_used": self.dax_functions_used,
            "dax_tables_referenced": self.dax_tables_referenced,
            "dax_measures_created": self.dax_measures_created,
            "warning_count": len(self.warnings),
            "performance": self.performance.get_summary()
        }


@dataclass 
class ExplanationResult:
    """
    Result of MDX explanation operation.
    
    Contains human-readable explanations in various formats along with
    metadata about the explanation generation process.
    """
    
    # Primary results (different formats)
    sql_explanation: Optional[str] = None
    natural_explanation: Optional[str] = None
    json_explanation: Optional[Dict[str, Any]] = None
    markdown_explanation: Optional[str] = None
    
    # Optional DAX comparison
    dax_query: Optional[str] = None
    
    # Metadata
    query_hash: str = ""
    explained_at: datetime = field(default_factory=datetime.now)
    explainer_version: str = "1.0.0"
    
    # Configuration used
    format_used: str = "sql"
    detail_level: str = "standard"
    include_dax_comparison: bool = False
    include_metadata: bool = False
    
    # Quality metrics
    warnings: List[Warning] = field(default_factory=list)
    explanation_quality_score: Optional[float] = None
    readability_score: Optional[float] = None
    
    # Performance statistics
    performance: PerformanceStats = field(default_factory=PerformanceStats)
    
    # Analysis results
    query_complexity: Optional[str] = None  # simple, moderate, complex
    key_insights: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    
    def add_warning(self, message: str, category: str = "general", **kwargs) -> None:
        """Add a warning to the result."""
        warning = Warning(message=message, category=category, **kwargs)
        self.warnings.append(warning)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_explanation(self, format_type: str = "auto") -> Optional[str]:
        """
        Get explanation in the specified format.
        
        Args:
            format_type: Format type (sql, natural, markdown, auto)
            
        Returns:
            Explanation text or None if format not available
        """
        if format_type == "auto":
            format_type = self.format_used
            
        format_map = {
            "sql": self.sql_explanation,
            "natural": self.natural_explanation,
            "markdown": self.markdown_explanation,
            "json": str(self.json_explanation) if self.json_explanation else None
        }
        
        return format_map.get(format_type)
    
    def get_available_formats(self) -> List[str]:
        """
        Get list of available explanation formats.
        
        Returns:
            List of format names that have content
        """
        available = []
        if self.sql_explanation:
            available.append("sql")
        if self.natural_explanation:
            available.append("natural")
        if self.json_explanation:
            available.append("json")
        if self.markdown_explanation:
            available.append("markdown")
        return available
    
    @property
    def explanation(self) -> Optional[str]:
        """
        Get explanation in the primary format used.
        
        Returns:
            Explanation text in the format that was used for generation
        """
        return self.get_explanation("auto")


@dataclass
class OptimizationResult:
    """
    Result of MDX optimization operation.
    
    Contains the optimized MDX query along with information about
    the optimizations applied and their impact.
    """
    
    # Primary result
    optimized_mdx: str
    
    # Optimization details
    original_mdx: str
    optimization_level: str = "moderate"
    rules_applied: List[str] = field(default_factory=list)
    
    # Metadata
    query_hash: str = ""
    optimized_at: datetime = field(default_factory=datetime.now)
    optimizer_version: str = "1.0.0"
    
    # Impact metrics
    size_reduction_percent: Optional[float] = None
    complexity_reduction_score: Optional[float] = None
    estimated_performance_improvement: Optional[str] = None
    
    # Quality metrics
    warnings: List[Warning] = field(default_factory=list)
    semantic_equivalence_verified: bool = False
    
    # Performance statistics
    performance: PerformanceStats = field(default_factory=PerformanceStats)
    
    # Detailed changes
    changes_summary: List[str] = field(default_factory=list)
    removed_patterns: List[str] = field(default_factory=list)
    
    def add_warning(self, message: str, category: str = "general", **kwargs) -> None:
        """Add a warning to the result."""
        warning = Warning(message=message, category=category, **kwargs)
        self.warnings.append(warning)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of optimization results.
        
        Returns:
            Dictionary with optimization metrics and changes
        """
        return {
            "optimization_level": self.optimization_level,
            "rules_applied": self.rules_applied,
            "size_reduction_percent": self.size_reduction_percent,
            "complexity_reduction_score": self.complexity_reduction_score,
            "estimated_performance_improvement": self.estimated_performance_improvement,
            "semantic_equivalence_verified": self.semantic_equivalence_verified,
            "changes_count": len(self.changes_summary),
            "warning_count": len(self.warnings),
            "performance": self.performance.get_summary()
        }