"""
UnMDX - MDX to DAX Converter

A comprehensive Python package that converts MDX queries (particularly messy output 
from Necto SSAS cubes) into clean, optimized DAX queries with human-readable explanations.
Provides both high-level API functions for common use cases and low-level components
for advanced customization.
"""

__version__ = "0.1.0"
__author__ = "Dru Arnfield"

# High-level public API functions (recommended for most users)
from .api import mdx_to_dax, parse_mdx, optimize_mdx, explain_mdx

# Configuration and results
from .config import (
    UnMDXConfig, ParserConfig, LinterConfig, DAXConfig, ExplanationConfig,
    OptimizationLevel, ExplanationFormat, ExplanationDetail,
    create_default_config, create_fast_config, create_comprehensive_config,
    load_config_from_file, load_config_from_env
)
from .results import (
    ConversionResult, ParseResult, ExplanationResult, OptimizationResult,
    PerformanceStats, Warning
)

# Exception hierarchy
from .exceptions import (
    UnMDXError, ParseError, TransformError, GenerationError, 
    LintError, ExplanationError, ConfigurationError, ValidationError
)

# Low-level components (for advanced users)
from .parser import MDXParser
from .transformer import MDXTransformer
from .dax_generator import DAXGenerator
from .linter import MDXLinter
from .explainer import ExplainerGenerator

# Legacy imports (deprecated - use high-level API instead)
from .explainer import explain_mdx as legacy_explain_mdx, explain_file

# Public API - high-level functions for common use cases
__all__ = [
    # Main API functions
    "mdx_to_dax",
    "parse_mdx", 
    "optimize_mdx",
    "explain_mdx",
    
    # Configuration classes
    "UnMDXConfig",
    "ParserConfig",
    "LinterConfig", 
    "DAXConfig",
    "ExplanationConfig",
    
    # Configuration enums
    "OptimizationLevel",
    "ExplanationFormat",
    "ExplanationDetail",
    
    # Configuration factory functions
    "create_default_config",
    "create_fast_config",
    "create_comprehensive_config",
    "load_config_from_file",
    "load_config_from_env",
    
    # Result classes
    "ConversionResult",
    "ParseResult",
    "ExplanationResult", 
    "OptimizationResult",
    "PerformanceStats",
    "Warning",
    
    # Exception classes
    "UnMDXError",
    "ParseError",
    "TransformError",
    "GenerationError",
    "LintError", 
    "ExplanationError",
    "ConfigurationError",
    "ValidationError",
    
    # Low-level components (advanced use)
    "MDXParser",
    "MDXTransformer",
    "DAXGenerator", 
    "MDXLinter",
    "ExplainerGenerator",
    
    # Legacy functions (deprecated)
    "legacy_explain_mdx",
    "explain_file",
]

# Package metadata
__title__ = "UnMDX"
__description__ = "MDX to DAX converter with human-readable explanations"
__url__ = "https://github.com/druarnfield/unmdx"
__license__ = "MIT"
