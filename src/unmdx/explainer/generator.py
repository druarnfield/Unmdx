"""Explainer generator for converting MDX queries to human-readable explanations."""

import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..ir.models import Query
from ..parser.mdx_parser import MDXParser, MDXParseError
from ..transformer.mdx_transformer import MDXTransformer, TransformationError
from ..linter.mdx_linter import MDXLinter
from ..linter.models import LinterConfig
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ExplanationFormat(Enum):
    """Available explanation formats."""
    
    SQL = "sql"              # SQL-like syntax with natural language
    NATURAL = "natural"      # Pure natural language
    JSON = "json"           # Structured JSON output
    MARKDOWN = "markdown"   # Markdown formatted


class ExplanationDetail(Enum):
    """Level of detail in explanations."""
    
    MINIMAL = "minimal"     # Basic query structure only
    STANDARD = "standard"   # Default level with key details
    DETAILED = "detailed"   # Comprehensive explanation with all elements


class ExplanationConfig:
    """Configuration for explanation generation."""
    
    def __init__(
        self,
        format: ExplanationFormat = ExplanationFormat.SQL,
        detail: ExplanationDetail = ExplanationDetail.STANDARD,
        include_sql_representation: bool = True,
        include_dax_comparison: bool = False,
        include_metadata: bool = False,
        use_linter: bool = True,
        linter_config: Optional[LinterConfig] = None
    ):
        self.format = format
        self.detail = detail
        self.include_sql_representation = include_sql_representation
        self.include_dax_comparison = include_dax_comparison
        self.include_metadata = include_metadata
        self.use_linter = use_linter
        self.linter_config = linter_config or LinterConfig()


class ExplainerGenerator:
    """Main class for generating human-readable explanations from MDX queries."""
    
    def __init__(self, debug: bool = False):
        """
        Initialize the explainer generator.
        
        Args:
            debug: Enable debug logging
        """
        self.debug = debug
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.parser = MDXParser()
        self.transformer = MDXTransformer(debug=debug)
        self.linter = MDXLinter()
    
    def explain_mdx(
        self,
        mdx_query: str,
        config: Optional[ExplanationConfig] = None
    ) -> str:
        """
        Generate human-readable explanation from MDX query string.
        
        Args:
            mdx_query: The MDX query to explain
            config: Explanation configuration
            
        Returns:
            Formatted explanation string
            
        Raises:
            MDXParseError: If MDX parsing fails
            TransformationError: If IR transformation fails
        """
        config = config or ExplanationConfig()
        
        self.logger.info(f"Explaining MDX query (format: {config.format.value})")
        
        try:
            # Step 1: Parse MDX
            self.logger.debug("Parsing MDX query")
            tree = self.parser.parse(mdx_query)
            
            # Step 2: Optional linting
            if config.use_linter:
                self.logger.debug("Applying MDX linter")
                tree, lint_report = self.linter.lint(tree, mdx_query)
            
            # Step 3: Transform to IR
            self.logger.debug("Transforming to IR")
            query = self.transformer.transform(tree, mdx_query)
            
            # Step 4: Generate explanation
            self.logger.debug(f"Generating explanation in {config.format.value} format")
            return self._generate_explanation(query, config)
            
        except MDXParseError as e:
            self.logger.error(f"MDX parsing failed: {e}")
            raise
        except TransformationError as e:
            self.logger.error(f"IR transformation failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during explanation: {e}")
            raise
    
    def explain_file(
        self,
        input_path: Path,
        config: Optional[ExplanationConfig] = None,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate explanation from MDX file.
        
        Args:
            input_path: Path to MDX file
            config: Explanation configuration
            output_path: Optional path to write explanation to file
            
        Returns:
            Formatted explanation string
        """
        config = config or ExplanationConfig()
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Read MDX from file
        mdx_query = input_path.read_text(encoding="utf-8")
        
        # Generate explanation
        explanation = self.explain_mdx(mdx_query, config)
        
        # Write to output file if specified
        if output_path:
            output_path.write_text(explanation, encoding="utf-8")
            self.logger.info(f"Explanation written to: {output_path}")
        
        return explanation
    
    def explain_ir(
        self,
        query: Query,
        config: Optional[ExplanationConfig] = None
    ) -> str:
        """
        Generate explanation from IR Query object.
        
        Args:
            query: IR Query object
            config: Explanation configuration
            
        Returns:
            Formatted explanation string
        """
        config = config or ExplanationConfig()
        return self._generate_explanation(query, config)
    
    def _generate_explanation(self, query: Query, config: ExplanationConfig) -> str:
        """
        Generate explanation based on format and configuration.
        
        Args:
            query: IR Query object
            config: Explanation configuration
            
        Returns:
            Formatted explanation string
        """
        if config.format == ExplanationFormat.SQL:
            return self._generate_sql_explanation(query, config)
        elif config.format == ExplanationFormat.NATURAL:
            return self._generate_natural_explanation(query, config)
        elif config.format == ExplanationFormat.JSON:
            return self._generate_json_explanation(query, config)
        elif config.format == ExplanationFormat.MARKDOWN:
            return self._generate_markdown_explanation(query, config)
        else:
            raise ValueError(f"Unsupported explanation format: {config.format}")
    
    def _generate_sql_explanation(self, query: Query, config: ExplanationConfig) -> str:
        """Generate SQL-like explanation with natural language."""
        parts = []
        
        # Use the existing to_human_readable method from the Query class
        base_explanation = query.to_human_readable()
        parts.append(base_explanation)
        
        # Add DAX comparison if requested
        if config.include_dax_comparison:
            parts.append("")
            parts.append("Equivalent DAX query:")
            parts.append("```dax")
            parts.append(query.to_dax())
            parts.append("```")
        
        # Add metadata if requested
        if config.include_metadata and config.detail == ExplanationDetail.DETAILED:
            parts.extend(self._generate_metadata_section(query))
        
        return "\n".join(parts)
    
    def _generate_natural_explanation(self, query: Query, config: ExplanationConfig) -> str:
        """Generate pure natural language explanation."""
        parts = []
        
        # Start with query summary
        parts.append(self._generate_query_summary(query))
        parts.append("")
        
        # Detail level determines what to include
        if config.detail in [ExplanationDetail.STANDARD, ExplanationDetail.DETAILED]:
            # Data source
            parts.append(f"The query analyzes data from {query.cube.to_human_readable()}.")
            parts.append("")
            
            # Measures
            if query.measures:
                measure_descriptions = []
                for measure in query.measures:
                    measure_descriptions.append(measure.to_human_readable())
                
                if len(measure_descriptions) == 1:
                    parts.append(f"It calculates the {measure_descriptions[0]}.")
                else:
                    parts.append(f"It calculates these metrics: {', '.join(measure_descriptions)}.")
                parts.append("")
            
            # Dimensions
            if query.dimensions:
                dim_descriptions = []
                for dim in query.dimensions:
                    dim_descriptions.append(dim.to_human_readable())
                
                if len(dim_descriptions) == 1:
                    parts.append(f"Results are broken down by {dim_descriptions[0]}.")
                else:
                    parts.append(f"Results are broken down by: {', '.join(dim_descriptions)}.")
                parts.append("")
            
            # Filters
            if query.filters:
                parts.append("The data is filtered to include only records where:")
                for filter_obj in query.filters:
                    parts.append(f"  • {filter_obj.to_human_readable()}")
                parts.append("")
            
            # Calculations
            if query.calculations and config.detail == ExplanationDetail.DETAILED:
                parts.append("The query includes these custom calculations:")
                for calc in query.calculations:
                    parts.append(f"  • {calc.to_human_readable()}")
                parts.append("")
            
            # Sorting and limits
            if query.order_by:
                order_descriptions = [o.to_human_readable() for o in query.order_by]
                parts.append(f"Results are sorted by: {', '.join(order_descriptions)}.")
                parts.append("")
            
            if query.limit:
                parts.append(f"{query.limit.to_human_readable()}.")
                parts.append("")
        
        # Add metadata for detailed explanations
        if config.include_metadata and config.detail == ExplanationDetail.DETAILED:
            parts.extend(self._generate_metadata_section(query))
        
        return "\n".join(parts).strip()
    
    def _generate_json_explanation(self, query: Query, config: ExplanationConfig) -> str:
        """Generate structured JSON explanation."""
        explanation = {
            "summary": self._generate_query_summary(query),
            "data_source": {
                "cube": query.cube.name,
                "database": query.cube.database,
                "description": query.cube.to_human_readable()
            },
            "measures": [
                {
                    "name": m.name,
                    "alias": m.alias,
                    "aggregation": m.aggregation.value if m.aggregation else None,
                    "description": m.to_human_readable()
                }
                for m in query.measures
            ],
            "dimensions": [
                {
                    "hierarchy": d.hierarchy.name,
                    "level": d.level.name,
                    "table": d.hierarchy.table,
                    "description": d.to_human_readable()
                }
                for d in query.dimensions
            ],
            "filters": [
                {
                    "type": f.filter_type.value,
                    "description": f.to_human_readable()
                }
                for f in query.filters
            ]
        }
        
        # Add optional sections based on detail level
        if config.detail == ExplanationDetail.DETAILED:
            if query.calculations:
                explanation["calculations"] = [
                    {
                        "name": c.name,
                        "type": c.calculation_type.value,
                        "description": c.to_human_readable()
                    }
                    for c in query.calculations
                ]
            
            if query.order_by:
                explanation["sorting"] = [
                    {
                        "description": o.to_human_readable()
                    }
                    for o in query.order_by
                ]
            
            if query.limit:
                explanation["limit"] = {
                    "count": query.limit.count,
                    "description": query.limit.to_human_readable()
                }
        
        # Add metadata if requested
        if config.include_metadata:
            explanation["metadata"] = {
                "complexity_score": query.metadata.complexity_score,
                "hierarchy_depth": query.metadata.hierarchy_depth,
                "estimated_result_size": query.metadata.estimated_result_size,
                "warnings": query.metadata.warnings,
                "errors": query.metadata.errors
            }
        
        # Add DAX if requested
        if config.include_dax_comparison:
            explanation["dax_query"] = query.to_dax()
        
        return json.dumps(explanation, indent=2)
    
    def _generate_markdown_explanation(self, query: Query, config: ExplanationConfig) -> str:
        """Generate Markdown-formatted explanation."""
        parts = []
        
        # Title
        parts.append("# Query Explanation")
        parts.append("")
        
        # Summary
        parts.append("## Summary")
        parts.append(self._generate_query_summary(query))
        parts.append("")
        
        # Data Source
        parts.append("## Data Source")
        parts.append(f"- **Cube**: {query.cube.name}")
        if query.cube.database:
            parts.append(f"- **Database**: {query.cube.database}")
        parts.append("")
        
        # Measures
        if query.measures:
            parts.append("## Measures")
            for measure in query.measures:
                alias = f" (as {measure.alias})" if measure.alias else ""
                agg = f" - {measure.aggregation.value}" if measure.aggregation else ""
                parts.append(f"- **{measure.name}**{alias}{agg}")
                if config.detail == ExplanationDetail.DETAILED:
                    parts.append(f"  - {measure.to_human_readable()}")
            parts.append("")
        
        # Dimensions
        if query.dimensions:
            parts.append("## Grouping")
            for dim in query.dimensions:
                parts.append(f"- **{dim.level.name}** from {dim.hierarchy.name} hierarchy")
                if config.detail == ExplanationDetail.DETAILED:
                    parts.append(f"  - {dim.to_human_readable()}")
            parts.append("")
        
        # Filters
        if query.filters:
            parts.append("## Filters")
            for filter_obj in query.filters:
                parts.append(f"- {filter_obj.to_human_readable()}")
            parts.append("")
        
        # Calculations
        if query.calculations and config.detail in [ExplanationDetail.STANDARD, ExplanationDetail.DETAILED]:
            parts.append("## Calculations")
            for calc in query.calculations:
                parts.append(f"- **{calc.name}**: {calc.to_human_readable()}")
            parts.append("")
        
        # Sorting
        if query.order_by:
            parts.append("## Sorting")
            for order in query.order_by:
                parts.append(f"- {order.to_human_readable()}")
            parts.append("")
        
        # Limit
        if query.limit:
            parts.append("## Limit")
            parts.append(f"- {query.limit.to_human_readable()}")
            parts.append("")
        
        # SQL representation
        if config.include_sql_representation:
            # Extract SQL from the base human-readable output
            base_explanation = query.to_human_readable()
            if "SQL-like representation:" in base_explanation:
                sql_part = base_explanation.split("SQL-like representation:")[1].strip()
                parts.append("## SQL-like Representation")
                parts.append(sql_part)
                parts.append("")
        
        # DAX comparison
        if config.include_dax_comparison:
            parts.append("## Equivalent DAX Query")
            parts.append("```dax")
            parts.append(query.to_dax())
            parts.append("```")
            parts.append("")
        
        # Metadata
        if config.include_metadata and config.detail == ExplanationDetail.DETAILED:
            parts.extend(self._generate_metadata_section_markdown(query))
        
        return "\n".join(parts).strip()
    
    def _generate_query_summary(self, query: Query) -> str:
        """Generate a concise summary of the query."""
        summary_parts = []
        
        # What we're calculating
        if query.measures:
            if len(query.measures) == 1:
                summary_parts.append(f"calculates {query.measures[0].to_human_readable()}")
            else:
                summary_parts.append(f"calculates {len(query.measures)} metrics")
        
        # How we're grouping
        if query.dimensions:
            if len(query.dimensions) == 1:
                summary_parts.append(f"grouped by {query.dimensions[0].to_human_readable()}")
            else:
                summary_parts.append(f"grouped by {len(query.dimensions)} dimensions")
        
        # Data source
        summary_parts.append(f"from {query.cube.to_human_readable()}")
        
        # Filters
        if query.filters:
            if len(query.filters) == 1:
                summary_parts.append("with 1 filter")
            else:
                summary_parts.append(f"with {len(query.filters)} filters")
        
        base = "This query " + ", ".join(summary_parts) + "."
        
        # Add calculations note
        if query.calculations:
            if len(query.calculations) == 1:
                base += " It includes 1 custom calculation."
            else:
                base += f" It includes {len(query.calculations)} custom calculations."
        
        return base
    
    def _generate_metadata_section(self, query: Query) -> List[str]:
        """Generate metadata section for text-based explanations."""
        parts = []
        metadata = query.metadata
        
        parts.append("")
        parts.append("Query Metadata:")
        
        if metadata.complexity_score is not None:
            parts.append(f"  • Complexity Score: {metadata.complexity_score}")
        
        if metadata.hierarchy_depth is not None:
            parts.append(f"  • Hierarchy Depth: {metadata.hierarchy_depth}")
        
        if metadata.estimated_result_size is not None:
            parts.append(f"  • Estimated Result Size: {metadata.estimated_result_size} rows")
        
        if metadata.warnings:
            parts.append(f"  • Warnings: {len(metadata.warnings)}")
            for warning in metadata.warnings:
                parts.append(f"    - {warning}")
        
        if metadata.errors:
            parts.append(f"  • Errors: {len(metadata.errors)}")
            for error in metadata.errors:
                parts.append(f"    - {error}")
        
        return parts
    
    def _generate_metadata_section_markdown(self, query: Query) -> List[str]:
        """Generate metadata section for Markdown explanations."""
        parts = []
        metadata = query.metadata
        
        parts.append("## Query Metadata")
        
        if metadata.complexity_score is not None:
            parts.append(f"- **Complexity Score**: {metadata.complexity_score}")
        
        if metadata.hierarchy_depth is not None:
            parts.append(f"- **Hierarchy Depth**: {metadata.hierarchy_depth}")
        
        if metadata.estimated_result_size is not None:
            parts.append(f"- **Estimated Result Size**: {metadata.estimated_result_size} rows")
        
        if metadata.warnings:
            parts.append(f"- **Warnings**: {len(metadata.warnings)}")
            for warning in metadata.warnings:
                parts.append(f"  - {warning}")
        
        if metadata.errors:
            parts.append(f"- **Errors**: {len(metadata.errors)}")
            for error in metadata.errors:
                parts.append(f"  - {error}")
        
        parts.append("")
        
        return parts


# Convenience functions for direct usage
def explain_mdx(
    mdx_query: str,
    format: Union[str, ExplanationFormat] = ExplanationFormat.SQL,
    detail: Union[str, ExplanationDetail] = ExplanationDetail.STANDARD,
    **kwargs
) -> str:
    """
    Convenience function to explain an MDX query.
    
    Args:
        mdx_query: The MDX query to explain
        format: Explanation format ('sql', 'natural', 'json', 'markdown')
        detail: Detail level ('minimal', 'standard', 'detailed')
        **kwargs: Additional configuration options
        
    Returns:
        Formatted explanation string
    """
    # Convert string formats to enums
    if isinstance(format, str):
        format = ExplanationFormat(format.lower())
    if isinstance(detail, str):
        detail = ExplanationDetail(detail.lower())
    
    config = ExplanationConfig(format=format, detail=detail, **kwargs)
    generator = ExplainerGenerator()
    return generator.explain_mdx(mdx_query, config)


def explain_file(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    format: Union[str, ExplanationFormat] = ExplanationFormat.SQL,
    **kwargs
) -> str:
    """
    Convenience function to explain an MDX file.
    
    Args:
        input_path: Path to MDX file
        output_path: Optional path to write explanation
        format: Explanation format
        **kwargs: Additional configuration options
        
    Returns:
        Formatted explanation string
    """
    if isinstance(format, str):
        format = ExplanationFormat(format.lower())
    
    config = ExplanationConfig(format=format, **kwargs)
    generator = ExplainerGenerator()
    
    return generator.explain_file(
        Path(input_path),
        config,
        Path(output_path) if output_path else None
    )