"""
Unified configuration system for UnMDX package.

This module provides a comprehensive configuration system that allows users
to control all aspects of MDX processing, from parsing to DAX generation
to explanation formatting.
"""

import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from .exceptions import ConfigurationError, ValidationError


class OptimizationLevel(Enum):
    """Optimization levels for MDX linting."""
    
    NONE = "none"                   # No optimization
    CONSERVATIVE = "conservative"   # Safe optimizations only
    MODERATE = "moderate"          # Balanced optimization
    AGGRESSIVE = "aggressive"      # Maximum optimization


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


@dataclass
class ParserConfig:
    """Configuration for MDX parsing."""
    
    # Basic parsing options
    strict_mode: bool = False
    allow_unknown_functions: bool = True
    validate_member_references: bool = False
    
    # Error handling
    continue_on_parse_errors: bool = False
    max_parse_errors: int = 10
    
    # Performance options
    parse_timeout_seconds: Optional[int] = None
    max_input_size_chars: Optional[int] = None
    
    # Debug options
    generate_parse_tree: bool = False
    save_debug_info: bool = False


@dataclass
class LinterConfig:
    """Configuration for MDX linting and optimization."""
    
    # Optimization level
    optimization_level: OptimizationLevel = OptimizationLevel.CONSERVATIVE
    
    # Basic rule settings
    remove_redundant_parentheses: bool = True
    optimize_crossjoins: bool = True
    remove_duplicates: bool = True
    normalize_member_references: bool = True
    
    # Advanced rule settings (auto-enabled based on optimization level)
    optimize_calculated_members: bool = False
    simplify_function_calls: bool = False
    inline_simple_expressions: bool = False
    
    # CrossJoin optimization
    max_crossjoin_depth: int = 3
    convert_crossjoins_to_tuples: bool = True
    
    # Safety settings
    validate_before_optimizing: bool = True
    validate_after_optimizing: bool = True
    skip_on_validation_error: bool = True
    preserve_original_structure: bool = False
    
    # Performance settings
    max_processing_time_ms: int = 5000
    
    # Custom rules
    custom_rules: List[str] = field(default_factory=list)
    disabled_rules: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Apply optimization level defaults."""
        if self.optimization_level == OptimizationLevel.MODERATE:
            self.optimize_calculated_members = True
            self.simplify_function_calls = True
        elif self.optimization_level == OptimizationLevel.AGGRESSIVE:
            self.optimize_calculated_members = True
            self.simplify_function_calls = True
            self.inline_simple_expressions = True
            self.max_crossjoin_depth = 5


@dataclass
class DAXConfig:
    """Configuration for DAX generation."""
    
    # Output formatting
    format_output: bool = True
    indent_size: int = 4
    line_width: int = 100
    
    # DAX style preferences
    use_summarizecolumns: bool = True
    prefer_table_functions: bool = True
    generate_measure_definitions: bool = False
    
    # Naming conventions
    escape_reserved_words: bool = True
    quote_table_names: bool = True
    use_friendly_names: bool = True
    
    # Advanced options
    optimize_dax_expressions: bool = True
    include_performance_hints: bool = False
    generate_comments: bool = True
    
    # Compatibility settings
    target_dax_version: str = "latest"  # latest, 2.0, 1.0
    power_bi_compatibility: bool = True
    ssas_compatibility: bool = False


@dataclass
class ExplanationConfig:
    """Configuration for explanation generation."""
    
    # Format and detail
    format: ExplanationFormat = ExplanationFormat.SQL
    detail: ExplanationDetail = ExplanationDetail.STANDARD
    
    # Content options
    include_sql_representation: bool = True
    include_dax_comparison: bool = False
    include_metadata: bool = False
    include_performance_notes: bool = False
    
    # Natural language options
    use_technical_terms: bool = True
    explain_mdx_concepts: bool = False
    include_best_practices: bool = False
    
    # Output formatting
    max_line_length: int = 80
    use_markdown_formatting: bool = False
    include_examples: bool = False


@dataclass
class UnMDXConfig:
    """
    Unified configuration for all UnMDX operations.
    
    This is the main configuration class that combines settings for all
    stages of MDX processing: parsing, linting, DAX generation, and explanation.
    """
    
    # Component configurations
    parser: ParserConfig = field(default_factory=ParserConfig)
    linter: LinterConfig = field(default_factory=LinterConfig)
    dax: DAXConfig = field(default_factory=DAXConfig)
    explanation: ExplanationConfig = field(default_factory=ExplanationConfig)
    
    # Global settings
    debug: bool = False
    verbose: bool = False
    
    # Performance settings
    enable_caching: bool = True
    cache_size_mb: int = 100
    parallel_processing: bool = False
    max_workers: int = 4
    
    # Output settings
    output_encoding: str = "utf-8"
    preserve_whitespace: bool = False
    
    # Error handling
    fail_fast: bool = False
    collect_all_errors: bool = True
    max_warnings: int = 50
    
    def validate(self) -> None:
        """
        Validate the configuration for consistency and correctness.
        
        Raises:
            ConfigurationError: If configuration is invalid
            ValidationError: If validation constraints are violated
        """
        errors = []
        
        # Validate optimization level consistency
        if (self.linter.optimization_level == OptimizationLevel.NONE and 
            any([self.linter.remove_redundant_parentheses,
                 self.linter.optimize_crossjoins,
                 self.linter.remove_duplicates])):
            errors.append("Linting rules enabled but optimization level is NONE")
        
        # Validate DAX configuration
        if self.dax.indent_size < 0 or self.dax.indent_size > 10:
            errors.append(f"Invalid DAX indent size: {self.dax.indent_size}")
        
        if self.dax.line_width < 40 or self.dax.line_width > 200:
            errors.append(f"Invalid DAX line width: {self.dax.line_width}")
        
        # Validate performance settings
        if self.cache_size_mb < 0 or self.cache_size_mb > 1000:
            errors.append(f"Invalid cache size: {self.cache_size_mb}MB")
        
        if self.max_workers < 1 or self.max_workers > 16:
            errors.append(f"Invalid max workers: {self.max_workers}")
        
        # Validate parser settings
        if (self.parser.max_input_size_chars is not None and 
            self.parser.max_input_size_chars < 1000):
            errors.append("Max input size too small (minimum 1000 characters)")
        
        if errors:
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(errors)}",
                suggestions=["Check configuration values and constraints"]
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary representation.
        
        Returns:
            Dictionary with all configuration values
        """
        result = {}
        
        # Component configs
        result["parser"] = {
            "strict_mode": self.parser.strict_mode,
            "allow_unknown_functions": self.parser.allow_unknown_functions,
            "validate_member_references": self.parser.validate_member_references,
            "continue_on_parse_errors": self.parser.continue_on_parse_errors,
            "max_parse_errors": self.parser.max_parse_errors,
            "parse_timeout_seconds": self.parser.parse_timeout_seconds,
            "max_input_size_chars": self.parser.max_input_size_chars,
            "generate_parse_tree": self.parser.generate_parse_tree,
            "save_debug_info": self.parser.save_debug_info
        }
        
        result["linter"] = {
            "optimization_level": self.linter.optimization_level.value,
            "remove_redundant_parentheses": self.linter.remove_redundant_parentheses,
            "optimize_crossjoins": self.linter.optimize_crossjoins,
            "remove_duplicates": self.linter.remove_duplicates,
            "normalize_member_references": self.linter.normalize_member_references,
            "optimize_calculated_members": self.linter.optimize_calculated_members,
            "simplify_function_calls": self.linter.simplify_function_calls,
            "max_crossjoin_depth": self.linter.max_crossjoin_depth,
            "custom_rules": self.linter.custom_rules,
            "disabled_rules": self.linter.disabled_rules
        }
        
        result["dax"] = {
            "format_output": self.dax.format_output,
            "indent_size": self.dax.indent_size,
            "line_width": self.dax.line_width,
            "use_summarizecolumns": self.dax.use_summarizecolumns,
            "prefer_table_functions": self.dax.prefer_table_functions,
            "escape_reserved_words": self.dax.escape_reserved_words,
            "target_dax_version": self.dax.target_dax_version
        }
        
        result["explanation"] = {
            "format": self.explanation.format.value,
            "detail": self.explanation.detail.value,
            "include_sql_representation": self.explanation.include_sql_representation,
            "include_dax_comparison": self.explanation.include_dax_comparison,
            "include_metadata": self.explanation.include_metadata,
            "use_technical_terms": self.explanation.use_technical_terms
        }
        
        # Global settings
        result["global"] = {
            "debug": self.debug,
            "verbose": self.verbose,
            "enable_caching": self.enable_caching,
            "parallel_processing": self.parallel_processing,
            "fail_fast": self.fail_fast
        }
        
        return result
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "UnMDXConfig":
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            UnMDXConfig instance
            
        Raises:
            ConfigurationError: If dictionary structure is invalid
        """
        try:
            config = cls()
            
            # Parser config
            if "parser" in config_dict:
                parser_dict = config_dict["parser"]
                for key, value in parser_dict.items():
                    if hasattr(config.parser, key):
                        setattr(config.parser, key, value)
            
            # Linter config
            if "linter" in config_dict:
                linter_dict = config_dict["linter"]
                for key, value in linter_dict.items():
                    if key == "optimization_level":
                        config.linter.optimization_level = OptimizationLevel(value)
                    elif hasattr(config.linter, key):
                        setattr(config.linter, key, value)
            
            # DAX config
            if "dax" in config_dict:
                dax_dict = config_dict["dax"]
                for key, value in dax_dict.items():
                    if hasattr(config.dax, key):
                        setattr(config.dax, key, value)
            
            # Explanation config
            if "explanation" in config_dict:
                exp_dict = config_dict["explanation"]
                for key, value in exp_dict.items():
                    if key == "format":
                        config.explanation.format = ExplanationFormat(value)
                    elif key == "detail":
                        config.explanation.detail = ExplanationDetail(value)
                    elif hasattr(config.explanation, key):
                        setattr(config.explanation, key, value)
            
            # Global settings
            if "global" in config_dict:
                global_dict = config_dict["global"]
                for key, value in global_dict.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            
            return config
            
        except (KeyError, ValueError, TypeError) as e:
            raise ConfigurationError(
                f"Invalid configuration dictionary: {e}",
                suggestions=["Check configuration format and valid values"]
            )


# Factory functions for common configurations

def create_default_config() -> UnMDXConfig:
    """
    Create default configuration.
    
    Returns:
        UnMDXConfig with sensible defaults for most use cases
    """
    return UnMDXConfig()


def create_fast_config() -> UnMDXConfig:
    """
    Create configuration optimized for speed.
    
    Returns:
        UnMDXConfig optimized for fast processing
    """
    config = UnMDXConfig()
    
    # Disable expensive operations
    config.linter.optimization_level = OptimizationLevel.NONE
    config.parser.validate_member_references = False
    config.dax.format_output = False
    config.dax.generate_comments = False
    config.explanation.detail = ExplanationDetail.MINIMAL
    
    # Enable performance features
    config.enable_caching = True
    config.parallel_processing = True
    
    return config


def create_comprehensive_config() -> UnMDXConfig:
    """
    Create configuration for comprehensive processing.
    
    Returns:
        UnMDXConfig with all features enabled for thorough analysis
    """
    config = UnMDXConfig()
    
    # Enable all optimizations
    config.linter.optimization_level = OptimizationLevel.AGGRESSIVE
    
    # Enable comprehensive parsing
    config.parser.strict_mode = True
    config.parser.validate_member_references = True
    config.parser.generate_parse_tree = True
    
    # Enable all DAX features
    config.dax.generate_measure_definitions = True
    config.dax.include_performance_hints = True
    config.dax.generate_comments = True
    
    # Enable detailed explanations
    config.explanation.detail = ExplanationDetail.DETAILED
    config.explanation.include_dax_comparison = True
    config.explanation.include_metadata = True
    config.explanation.include_performance_notes = True
    config.explanation.include_best_practices = True
    
    return config


def load_config_from_file(file_path: Union[str, Path]) -> UnMDXConfig:
    """
    Load configuration from JSON file.
    
    Args:
        file_path: Path to JSON configuration file
        
    Returns:
        UnMDXConfig loaded from file
        
    Raises:
        ConfigurationError: If file cannot be read or parsed
    """
    path = Path(file_path)
    
    if not path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {path}",
            suggestions=["Check file path and permissions"]
        )
    
    try:
        with path.open("r", encoding="utf-8") as f:
            config_dict = json.load(f)
        
        return UnMDXConfig.from_dict(config_dict)
        
    except (json.JSONDecodeError, OSError) as e:
        raise ConfigurationError(
            f"Failed to load configuration from {path}: {e}",
            suggestions=["Check file format and content"]
        )


def load_config_from_env() -> UnMDXConfig:
    """
    Load configuration from environment variables.
    
    Environment variables should be prefixed with UNMDX_ and use
    the format UNMDX_SECTION_SETTING (e.g., UNMDX_LINTER_OPTIMIZATION_LEVEL).
    
    Returns:
        UnMDXConfig with settings from environment variables
    """
    config = create_default_config()
    
    # Map environment variables to config settings
    env_mappings = {
        "UNMDX_DEBUG": ("debug", bool),
        "UNMDX_VERBOSE": ("verbose", bool),
        "UNMDX_PARSER_STRICT_MODE": ("parser.strict_mode", bool),
        "UNMDX_LINTER_OPTIMIZATION_LEVEL": ("linter.optimization_level", OptimizationLevel),
        "UNMDX_DAX_FORMAT_OUTPUT": ("dax.format_output", bool),
        "UNMDX_EXPLANATION_FORMAT": ("explanation.format", ExplanationFormat),
        "UNMDX_EXPLANATION_DETAIL": ("explanation.detail", ExplanationDetail),
    }
    
    for env_var, (config_path, value_type) in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                # Convert value to appropriate type
                if value_type == bool:
                    value = env_value.lower() in ("true", "1", "yes", "on")
                elif issubclass(value_type, Enum):
                    value = value_type(env_value.lower())
                else:
                    value = value_type(env_value)
                
                # Set value in config using dot notation
                obj = config
                parts = config_path.split(".")
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
                
            except (ValueError, AttributeError) as e:
                raise ConfigurationError(
                    f"Invalid environment variable {env_var}={env_value}: {e}",
                    suggestions=[f"Check valid values for {config_path}"]
                )
    
    return config