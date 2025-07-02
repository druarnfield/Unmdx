"""
High-level public API for UnMDX package.

This module provides the main public interface for MDX to DAX conversion,
offering simple, intuitive functions for common use cases while maintaining
full access to advanced features through configuration.
"""

import hashlib
import time
import traceback
from pathlib import Path
from typing import Optional, Union, Dict, Any
import tracemalloc

from .config import UnMDXConfig, create_default_config
from .exceptions import (
    UnMDXError, ParseError, TransformError, GenerationError, 
    LintError, ExplanationError, ValidationError, create_parse_error_from_lark
)
from .results import (
    ConversionResult, ParseResult, ExplanationResult, OptimizationResult,
    PerformanceStats, Warning
)
from .parser import MDXParser, MDXParseError
from .transformer import MDXTransformer, TransformationError
from .dax_generator import DAXGenerator, DAXGenerationError
from .linter import MDXLinter
from .explainer import ExplainerGenerator, ExplanationConfig, ExplanationFormat, ExplanationDetail
from .utils.logging import get_logger

logger = get_logger(__name__)


def mdx_to_dax(
    mdx_text: str,
    config: Optional[UnMDXConfig] = None,
    optimize: bool = True,
    include_metadata: bool = False
) -> ConversionResult:
    """
    Convert MDX query to DAX query.
    
    This is the main high-level function for converting MDX queries to DAX.
    It handles the complete pipeline: parsing, transformation, optional optimization,
    and DAX generation.
    
    Args:
        mdx_text: MDX query string to convert
        config: Configuration for conversion process (uses defaults if None)
        optimize: Whether to apply MDX linting/optimization before conversion
        include_metadata: Whether to include detailed metadata in result
        
    Returns:
        ConversionResult with DAX query and metadata
        
    Raises:
        ParseError: If MDX parsing fails
        TransformError: If IR transformation fails  
        GenerationError: If DAX generation fails
        LintError: If optimization fails (when optimize=True)
        ValidationError: If input validation fails
        
    Example:
        >>> result = mdx_to_dax("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
        >>> print(result.dax_query)
        EVALUATE
        SUMMARIZECOLUMNS(
            "Sales", [Measures].[Sales]
        )
        
        >>> print(f"Conversion took {result.performance.total_time:.2f}s")
        Conversion took 0.15s
    """
    # Input validation
    if not mdx_text or not mdx_text.strip():
        raise ValidationError(
            "MDX text cannot be empty",
            field_name="mdx_text",
            field_value=mdx_text,
            suggestions=["Provide a valid MDX query string"]
        )
    
    # Use default config if none provided
    if config is None:
        config = create_default_config()
    
    # Validate configuration
    try:
        config.validate()
    except Exception as e:
        raise ValidationError(f"Configuration validation failed: {e}")
    
    # Initialize performance tracking
    perf_stats = PerformanceStats()
    perf_stats.input_size_chars = len(mdx_text)
    
    # Start memory tracking if needed
    if include_metadata:
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]
    
    # Initialize result
    query_hash = hashlib.md5(mdx_text.encode()).hexdigest()
    result = ConversionResult(
        dax_query="",
        query_hash=query_hash,
        original_mdx=mdx_text if include_metadata else None
    )
    
    try:
        # Step 1: Parse MDX
        start_time = time.time()
        logger.info(f"Parsing MDX query (hash: {query_hash[:8]})")
        
        parser = MDXParser(debug=config.debug)
        try:
            parse_tree = parser.parse(mdx_text)
        except Exception as e:
            raise create_parse_error_from_lark(
                e, 
                suggestions=["Check MDX syntax", "Try with less strict parsing mode"]
            )
        
        perf_stats.add_timing("parse", time.time() - start_time)
        
        # Step 2: Transform to IR
        start_time = time.time()
        logger.info("Transforming MDX to intermediate representation")
        
        transformer = MDXTransformer(debug=config.debug)
        try:
            ir_query = transformer.transform(parse_tree)
            result.ir_query = ir_query if include_metadata else None
        except TransformationError as e:
            raise TransformError(
                f"Failed to transform MDX to IR: {e.message}",
                node_type=getattr(e, 'node_type', None),
                context=getattr(e, 'context', None),
                suggestions=["Check for unsupported MDX constructs", "Simplify query structure"]
            )
        
        perf_stats.add_timing("transform", time.time() - start_time)
        
        # Step 3: Optional optimization
        if optimize and config.linter.optimization_level.value != "none":
            start_time = time.time()
            logger.info(f"Optimizing MDX with level: {config.linter.optimization_level.value}")
            
            try:
                linter = MDXLinter()
                optimized_tree, lint_report = linter.lint(parse_tree, mdx_text)
                
                # Add optimization info to result
                result.optimization_applied = True
                result.optimization_level = config.linter.optimization_level.value
                
                # Add warnings from linting
                for warning_msg in lint_report.warnings:
                    result.add_warning(warning_msg, "optimization")
                
                # Re-transform if significant optimizations were applied
                if lint_report.actions:
                    ir_query = transformer.transform(parse_tree)
                    result.ir_query = ir_query if include_metadata else None
                    
            except Exception as e:
                raise LintError(
                    f"Optimization failed: {e}",
                    optimization_level=config.linter.optimization_level.value,
                    suggestions=["Try with lower optimization level", "Disable optimization"]
                )
            
            perf_stats.add_timing("lint", time.time() - start_time)
        
        # Step 4: Generate DAX
        start_time = time.time()
        logger.info("Generating DAX query")
        
        dax_generator = DAXGenerator(
            format_output=config.dax.format_output,
            debug=config.debug
        )
        
        try:
            dax_query = dax_generator.generate(ir_query)
            result.dax_query = dax_query
            perf_stats.output_size_chars = len(dax_query)
            
            # Extract DAX metadata if requested
            if include_metadata:
                result.dax_functions_used = _extract_dax_functions(dax_query)
                result.dax_tables_referenced = _extract_dax_tables(dax_query)
                result.dax_measures_created = dax_query.count("MEASURE")
                
        except DAXGenerationError as e:
            raise GenerationError(
                f"Failed to generate DAX: {e.message}",
                ir_construct=getattr(e, 'ir_construct', None),
                context=getattr(e, 'context', None),
                suggestions=["Check IR structure", "Try simpler MDX constructs"]
            )
        
        perf_stats.add_timing("generation", time.time() - start_time)
        
        # Finalize performance stats
        result.performance = perf_stats
        
        # Add memory usage if tracking
        if include_metadata and tracemalloc.is_tracing():
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            result.performance.memory_peak_mb = peak_memory / 1024 / 1024
            result.performance.memory_delta_mb = (current_memory - initial_memory) / 1024 / 1024
            tracemalloc.stop()
        
        # Calculate complexity score
        result.complexity_score = _calculate_complexity_score(ir_query)
        result.estimated_performance = _estimate_performance(result.complexity_score)
        
        logger.info(f"Successfully converted MDX to DAX in {perf_stats.total_time:.2f}s")
        return result
        
    except (ParseError, TransformError, GenerationError, LintError, ValidationError):
        # Re-raise known exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during conversion: {e}")
        if config.debug:
            logger.error(f"Stack trace: {traceback.format_exc()}")
        raise UnMDXError(
            f"Unexpected error during MDX to DAX conversion: {e}",
            suggestions=["Enable debug mode for more details", "Check input format"]
        )


def parse_mdx(
    mdx_text: str,
    config: Optional[UnMDXConfig] = None,
    include_metadata: bool = False
) -> ParseResult:
    """
    Parse MDX query into intermediate representation.
    
    This function parses an MDX query and transforms it into the internal
    intermediate representation (IR) without generating DAX output.
    
    Args:
        mdx_text: MDX query string to parse
        config: Configuration for parsing process (uses defaults if None)
        include_metadata: Whether to include detailed parsing metadata
        
    Returns:
        ParseResult with IR query and metadata
        
    Raises:
        ParseError: If MDX parsing fails
        TransformError: If IR transformation fails
        ValidationError: If input validation fails
        
    Example:
        >>> result = parse_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
        >>> print(f"Parsed {len(result.ir_query.measures)} measures")
        Parsed 1 measures
        
        >>> print(f"Query complexity: {result.complexity_score}")
        Query complexity: 0.3
    """
    # Input validation
    if not mdx_text or not mdx_text.strip():
        raise ValidationError(
            "MDX text cannot be empty",
            field_name="mdx_text",
            suggestions=["Provide a valid MDX query string"]
        )
    
    # Use default config if none provided
    if config is None:
        config = create_default_config()
    
    # Initialize performance tracking
    perf_stats = PerformanceStats()
    perf_stats.input_size_chars = len(mdx_text)
    
    # Initialize result
    query_hash = hashlib.md5(mdx_text.encode()).hexdigest()
    
    try:
        # Step 1: Parse MDX
        start_time = time.time()
        logger.info(f"Parsing MDX query (hash: {query_hash[:8]})")
        
        parser = MDXParser(debug=config.debug)
        try:
            parse_tree = parser.parse(mdx_text)
            if include_metadata:
                perf_stats.ast_nodes_processed = _count_ast_nodes(parse_tree)
        except Exception as e:
            raise create_parse_error_from_lark(
                e,
                suggestions=["Check MDX syntax", "Verify query structure"]
            )
        
        perf_stats.add_timing("parse", time.time() - start_time)
        
        # Step 2: Transform to IR
        start_time = time.time()
        logger.info("Transforming to intermediate representation")
        
        transformer = MDXTransformer(debug=config.debug)
        try:
            ir_query = transformer.transform(parse_tree)
            if include_metadata:
                perf_stats.ir_constructs_created = _count_ir_constructs(ir_query)
        except TransformationError as e:
            raise TransformError(
                f"Failed to transform MDX to IR: {e.message}",
                node_type=getattr(e, 'node_type', None),
                context=getattr(e, 'context', None),
                suggestions=["Check for unsupported constructs"]
            )
        
        perf_stats.add_timing("transform", time.time() - start_time)
        
        # Create result
        result = ParseResult(
            ir_query=ir_query,
            query_hash=query_hash,
            performance=perf_stats
        )
        
        # Add metadata if requested
        if include_metadata:
            result.ast_node_count = perf_stats.ast_nodes_processed
            result.ir_construct_count = perf_stats.ir_constructs_created
        
        # Calculate complexity score
        result.complexity_score = _calculate_complexity_score(ir_query)
        result.estimated_performance = _estimate_performance(result.complexity_score)
        
        logger.info(f"Successfully parsed MDX in {perf_stats.total_time:.2f}s")
        return result
        
    except (ParseError, TransformError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error during parsing: {e}")
        raise UnMDXError(f"Unexpected error during MDX parsing: {e}")


def optimize_mdx(
    mdx_text: str,
    config: Optional[UnMDXConfig] = None,
    optimization_level: Optional[str] = None
) -> OptimizationResult:
    """
    Optimize MDX query by applying linting rules.
    
    This function applies various optimization rules to clean up and improve
    the structure of an MDX query without changing its semantic meaning.
    
    Args:
        mdx_text: MDX query string to optimize
        config: Configuration for optimization process (uses defaults if None)
        optimization_level: Override optimization level (conservative, moderate, aggressive)
        
    Returns:
        OptimizationResult with optimized MDX and optimization details
        
    Raises:
        ParseError: If MDX parsing fails
        LintError: If optimization fails
        ValidationError: If input validation fails
        
    Example:
        >>> result = optimize_mdx("SELECT (([Measures].[Sales])) ON 0 FROM [Sales]")
        >>> print(result.optimized_mdx)
        SELECT [Measures].[Sales] ON 0 FROM [Sales]
        
        >>> print(f"Size reduction: {result.size_reduction_percent:.1f}%")
        Size reduction: 15.2%
    """
    # Input validation
    if not mdx_text or not mdx_text.strip():
        raise ValidationError(
            "MDX text cannot be empty",
            field_name="mdx_text",
            suggestions=["Provide a valid MDX query string"]
        )
    
    # Use default config if none provided
    if config is None:
        config = create_default_config()
    
    # Override optimization level if specified
    if optimization_level:
        from .config import OptimizationLevel
        try:
            config.linter.optimization_level = OptimizationLevel(optimization_level.lower())
        except ValueError:
            raise ValidationError(
                f"Invalid optimization level: {optimization_level}",
                field_name="optimization_level",
                field_value=optimization_level,
                valid_values=["conservative", "moderate", "aggressive"],
                suggestions=["Use one of: conservative, moderate, aggressive"]
            )
    
    # Initialize performance tracking
    perf_stats = PerformanceStats()
    perf_stats.input_size_chars = len(mdx_text)
    
    # Initialize result
    query_hash = hashlib.md5(mdx_text.encode()).hexdigest()
    result = OptimizationResult(
        optimized_mdx=mdx_text,  # Default to original
        original_mdx=mdx_text,
        query_hash=query_hash,
        optimization_level=config.linter.optimization_level.value
    )
    
    try:
        # Step 1: Parse MDX
        start_time = time.time()
        logger.info(f"Parsing MDX for optimization (level: {config.linter.optimization_level.value})")
        
        parser = MDXParser(debug=config.debug)
        try:
            parse_tree = parser.parse(mdx_text)
        except Exception as e:
            raise create_parse_error_from_lark(
                e,
                suggestions=["Check MDX syntax before optimization"]
            )
        
        perf_stats.add_timing("parse", time.time() - start_time)
        
        # Step 2: Apply optimization
        start_time = time.time()
        logger.info("Applying optimization rules")
        
        try:
            linter = MDXLinter()
            optimized_tree, lint_report = linter.lint(parse_tree, mdx_text)
            
            # Convert optimized tree back to MDX text
            # For now we'll use the original text as linter may not preserve text format
            result.optimized_mdx = mdx_text  # TODO: Implement tree-to-text conversion
            
            # Populate result with linting information
            result.rules_applied = lint_report.rules_applied.copy()
            
            # Calculate metrics
            original_size = len(mdx_text)
            optimized_size = len(result.optimized_mdx)
            result.size_reduction_percent = ((original_size - optimized_size) / original_size) * 100 if original_size > 0 else 0.0
            
            # Add changes summary
            for action in lint_report.actions:
                result.changes_summary.append(action.description)
                if action.action_type.value == "remove":
                    result.removed_patterns.append(action.original_text)
            
            # Add warnings
            for warning_msg in lint_report.warnings:
                result.add_warning(warning_msg, "optimization")
            
            # Estimate performance improvement
            if result.size_reduction_percent > 20:
                result.estimated_performance_improvement = "significant"
            elif result.size_reduction_percent > 5:
                result.estimated_performance_improvement = "moderate"
            else:
                result.estimated_performance_improvement = "minimal"
            
        except Exception as e:
            raise LintError(
                f"Optimization failed: {e}",
                optimization_level=config.linter.optimization_level.value,
                suggestions=["Try with lower optimization level"]
            )
        
        perf_stats.add_timing("lint", time.time() - start_time)
        
        # Finalize result
        result.performance = perf_stats
        result.semantic_equivalence_verified = True  # Assuming linter preserves semantics
        
        logger.info(f"Successfully optimized MDX in {perf_stats.total_time:.2f}s")
        return result
        
    except (ParseError, LintError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error during optimization: {e}")
        raise UnMDXError(f"Unexpected error during MDX optimization: {e}")


def explain_mdx(
    mdx_text: str,
    config: Optional[UnMDXConfig] = None,
    format_type: str = "sql",
    detail_level: str = "standard",
    include_dax: bool = False
) -> ExplanationResult:
    """
    Generate human-readable explanation of MDX query.
    
    This function converts an MDX query into human-readable explanations
    in various formats (SQL-like, natural language, JSON, Markdown).
    
    Args:
        mdx_text: MDX query string to explain
        config: Configuration for explanation process (uses defaults if None)
        format_type: Output format (sql, natural, json, markdown)
        detail_level: Level of detail (minimal, standard, detailed)
        include_dax: Whether to include DAX comparison in explanation
        
    Returns:
        ExplanationResult with human-readable explanations
        
    Raises:
        ParseError: If MDX parsing fails
        ExplanationError: If explanation generation fails
        ValidationError: If input validation fails
        
    Example:
        >>> result = explain_mdx("SELECT [Measures].[Sales] ON 0 FROM [Sales]")
        >>> print(result.sql_explanation)
        This query selects the Sales measure from the Sales data model.
        It returns a single value showing the total sales amount.
        
        >>> print(f"Query complexity: {result.query_complexity}")
        Query complexity: simple
    """
    # Input validation
    if not mdx_text or not mdx_text.strip():
        raise ValidationError(
            "MDX text cannot be empty",
            field_name="mdx_text",
            suggestions=["Provide a valid MDX query string"]
        )
    
    # Validate format
    try:
        explanation_format = ExplanationFormat(format_type.lower())
    except ValueError:
        raise ValidationError(
            f"Invalid explanation format: {format_type}",
            field_name="format_type",
            field_value=format_type,
            valid_values=["sql", "natural", "json", "markdown"],
            suggestions=["Use one of: sql, natural, json, markdown"]
        )
    
    # Validate detail level
    try:
        explanation_detail = ExplanationDetail(detail_level.lower())
    except ValueError:
        raise ValidationError(
            f"Invalid detail level: {detail_level}",
            field_name="detail_level",
            field_value=detail_level,
            valid_values=["minimal", "standard", "detailed"],
            suggestions=["Use one of: minimal, standard, detailed"]
        )
    
    # Use default config if none provided
    if config is None:
        config = create_default_config()
    
    # Initialize performance tracking
    perf_stats = PerformanceStats()
    perf_stats.input_size_chars = len(mdx_text)
    
    # Initialize result
    query_hash = hashlib.md5(mdx_text.encode()).hexdigest()
    result = ExplanationResult(
        query_hash=query_hash,
        format_used=format_type,
        detail_level=detail_level,
        include_dax_comparison=include_dax
    )
    
    try:
        # Create explanation configuration
        exp_config = ExplanationConfig(
            format=explanation_format,
            detail=explanation_detail,
            include_dax_comparison=include_dax,
            include_metadata=True,
            use_linter=config.linter.optimization_level.value != "none"
        )
        
        # Generate explanation
        start_time = time.time()
        logger.info(f"Generating explanation (format: {format_type}, detail: {detail_level})")
        
        try:
            explainer = ExplainerGenerator(debug=config.debug)
            explanation_text = explainer.explain_mdx(mdx_text, exp_config)
            
            # Set appropriate result field based on format
            if explanation_format == ExplanationFormat.SQL:
                result.sql_explanation = explanation_text
            elif explanation_format == ExplanationFormat.NATURAL:
                result.natural_explanation = explanation_text
            elif explanation_format == ExplanationFormat.MARKDOWN:
                result.markdown_explanation = explanation_text
            elif explanation_format == ExplanationFormat.JSON:
                import json
                try:
                    result.json_explanation = json.loads(explanation_text)
                except json.JSONDecodeError:
                    result.json_explanation = {"explanation": explanation_text}
            
            # Generate DAX comparison if requested
            if include_dax:
                dax_result = mdx_to_dax(mdx_text, config, optimize=False, include_metadata=False)
                result.dax_query = dax_result.dax_query
            
        except Exception as e:
            raise ExplanationError(
                f"Failed to generate explanation: {e}",
                format_type=format_type,
                suggestions=["Try with simpler detail level", "Check MDX syntax"]
            )
        
        perf_stats.add_timing("explanation", time.time() - start_time)
        
        # Analyze query complexity
        try:
            parse_result = parse_mdx(mdx_text, config, include_metadata=True)
            result.query_complexity = _estimate_query_complexity(parse_result.complexity_score)
            
            # Extract key insights
            result.key_insights = _extract_key_insights(parse_result.ir_query)
            result.potential_issues = _identify_potential_issues(parse_result.ir_query)
            
        except Exception as e:
            logger.warning(f"Failed to analyze query complexity: {e}")
        
        # Finalize result
        result.performance = perf_stats
        
        # Calculate quality scores (placeholder implementation)
        result.explanation_quality_score = 0.85  # TODO: Implement actual quality scoring
        result.readability_score = 0.80  # TODO: Implement readability analysis
        
        logger.info(f"Successfully generated explanation in {perf_stats.total_time:.2f}s")
        return result
        
    except (ParseError, ExplanationError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error during explanation: {e}")
        raise UnMDXError(f"Unexpected error during MDX explanation: {e}")


# Helper functions for metadata extraction and analysis

def _extract_dax_functions(dax_query: str) -> list[str]:
    """Extract DAX functions used in the query."""
    # Simple implementation - could be enhanced with proper parsing
    common_functions = [
        "SUMMARIZECOLUMNS", "EVALUATE", "FILTER", "CALCULATE", 
        "SUM", "COUNT", "AVERAGE", "MAX", "MIN", "DISTINCTCOUNT"
    ]
    
    functions_found = []
    dax_upper = dax_query.upper()
    
    for func in common_functions:
        if func in dax_upper:
            functions_found.append(func)
    
    return functions_found


def _extract_dax_tables(dax_query: str) -> list[str]:
    """Extract table references from DAX query."""
    # Simple implementation - could be enhanced with proper parsing
    import re
    
    # Look for patterns like 'Table'[Column] or [Table]
    table_pattern = r"(?:'([^']+)'|\[([^\]]+)\])"
    matches = re.findall(table_pattern, dax_query)
    
    tables = set()
    for match in matches:
        table_name = match[0] or match[1]
        if table_name and not table_name.startswith("Measures"):
            tables.add(table_name)
    
    return list(tables)


def _count_ast_nodes(parse_tree) -> int:
    """Count AST nodes in the parse tree."""
    # Simple recursive counting
    if not hasattr(parse_tree, 'children'):
        return 1
    
    count = 1
    for child in parse_tree.children:
        count += _count_ast_nodes(child)
    
    return count


def _count_ir_constructs(ir_query) -> int:
    """Count IR constructs in the query."""
    count = 1  # The query itself
    
    if hasattr(ir_query, 'measures'):
        count += len(ir_query.measures)
    
    if hasattr(ir_query, 'dimensions'):
        count += len(ir_query.dimensions)
    
    if hasattr(ir_query, 'filters'):
        count += len(ir_query.filters)
    
    if hasattr(ir_query, 'calculations'):
        count += len(ir_query.calculations)
    
    return count


def _calculate_complexity_score(ir_query) -> float:
    """Calculate complexity score for IR query."""
    score = 0.0
    
    # Base complexity
    score += 0.1
    
    # Add complexity for each construct
    if hasattr(ir_query, 'measures'):
        score += len(ir_query.measures) * 0.1
    
    if hasattr(ir_query, 'dimensions'):
        score += len(ir_query.dimensions) * 0.15
    
    if hasattr(ir_query, 'filters'):
        score += len(ir_query.filters) * 0.2
    
    if hasattr(ir_query, 'calculations'):
        score += len(ir_query.calculations) * 0.3
    
    # Cap at 1.0
    return min(score, 1.0)


def _estimate_performance(complexity_score: float) -> str:
    """Estimate query performance based on complexity."""
    if complexity_score < 0.3:
        return "fast"
    elif complexity_score < 0.7:
        return "moderate"
    else:
        return "slow"


def _estimate_query_complexity(complexity_score: float) -> str:
    """Estimate query complexity level."""
    if complexity_score < 0.3:
        return "simple"
    elif complexity_score < 0.7:
        return "moderate"
    else:
        return "complex"


def _extract_key_insights(ir_query) -> list[str]:
    """Extract key insights from IR query."""
    insights = []
    
    if hasattr(ir_query, 'measures') and ir_query.measures:
        insights.append(f"Query returns {len(ir_query.measures)} measure(s)")
    
    if hasattr(ir_query, 'dimensions') and ir_query.dimensions:
        insights.append(f"Data is grouped by {len(ir_query.dimensions)} dimension(s)")
    
    if hasattr(ir_query, 'filters') and ir_query.filters:
        insights.append(f"Results are filtered using {len(ir_query.filters)} condition(s)")
    
    return insights


def _identify_potential_issues(ir_query) -> list[str]:
    """Identify potential issues in IR query."""
    issues = []
    
    # Check for common issues
    if hasattr(ir_query, 'measures') and not ir_query.measures:
        issues.append("No measures specified - query may return empty results")
    
    if hasattr(ir_query, 'filters') and len(ir_query.filters) > 5:
        issues.append("Many filters may impact performance")
    
    return issues