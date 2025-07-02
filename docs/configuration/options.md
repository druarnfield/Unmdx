# UnMDX Configuration Guide

UnMDX provides a comprehensive configuration system that allows you to customize every aspect of MDX processing, from parsing to optimization to output formatting. This guide covers all available configuration options.

## Configuration Overview

UnMDX uses a hierarchical configuration system with four main sections:

1. **Parser Configuration** - Controls MDX parsing behavior
2. **Linter Configuration** - Controls optimization and cleanup rules
3. **DAX Configuration** - Controls DAX output formatting
4. **Explanation Configuration** - Controls human-readable output

## Using Configuration

### Python API

```python
from unmdx import mdx_to_dax, create_default_config

# Create and customize configuration
config = create_default_config()
config.linter.optimization_level = "aggressive"
config.dax.indent_size = 2

# Use configuration
result = mdx_to_dax(mdx_query, config=config)
```

### Configuration Files

UnMDX supports JSON and YAML configuration files:

```python
from unmdx import load_config_from_file

config = load_config_from_file("config.json")
```

### Environment Variables

Configuration can also be loaded from environment variables:

```python
from unmdx import load_config_from_env

config = load_config_from_env()
```

## Parser Configuration

Controls how MDX queries are parsed.

### Basic Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `strict_mode` | bool | False | Enforce strict MDX syntax rules |
| `allow_unknown_functions` | bool | True | Allow functions not in MDX spec |
| `validate_member_references` | bool | False | Validate all member references exist |

### Error Handling

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `continue_on_parse_errors` | bool | False | Continue parsing after errors |
| `max_parse_errors` | int | 10 | Maximum errors before stopping |

### Performance Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `parse_timeout_seconds` | int? | None | Timeout for parsing operation |
| `max_input_size_chars` | int? | None | Maximum input size in characters |

### Debug Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `generate_parse_tree` | bool | False | Generate visual parse tree |
| `save_debug_info` | bool | False | Save debugging information |

### Example

```python
config = create_default_config()
config.parser.strict_mode = True
config.parser.max_parse_errors = 5
config.parser.parse_timeout_seconds = 30
```

## Linter Configuration

Controls MDX optimization and cleanup.

### Optimization Levels

The `optimization_level` setting controls the aggressiveness of optimizations:

| Level | Description | Use Case |
|-------|-------------|----------|
| `none` | No optimization | When exact MDX preservation is needed |
| `conservative` | Safe optimizations only | Default, suitable for most cases |
| `moderate` | Balanced optimization | Good for clean Necto output |
| `aggressive` | Maximum optimization | May restructure queries significantly |

### Basic Rules

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `remove_redundant_parentheses` | bool | True | Remove unnecessary parentheses |
| `optimize_crossjoins` | bool | True | Simplify CrossJoin patterns |
| `remove_duplicates` | bool | True | Remove duplicate members |
| `normalize_member_references` | bool | True | Standardize member syntax |

### Advanced Rules

These are automatically enabled based on optimization level:

| Option | Type | Auto-enabled at | Description |
|--------|------|----------------|-------------|
| `optimize_calculated_members` | bool | moderate | Optimize MEMBER definitions |
| `simplify_function_calls` | bool | moderate | Simplify verbose functions |
| `inline_simple_expressions` | bool | aggressive | Inline simple calculations |

### CrossJoin Optimization

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_crossjoin_depth` | int | 3 | Maximum nesting depth to optimize |
| `convert_crossjoins_to_tuples` | bool | True | Convert to tuple syntax |

### Safety Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `validate_before_optimizing` | bool | True | Validate MDX before optimization |
| `validate_after_optimizing` | bool | True | Validate result after optimization |
| `skip_on_validation_error` | bool | True | Skip optimization if validation fails |
| `preserve_original_structure` | bool | False | Maintain original query structure |

### Performance

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_processing_time_ms` | int | 5000 | Maximum processing time |

### Custom Rules

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `custom_rules` | list | [] | List of custom rule names to apply |
| `disabled_rules` | list | [] | List of rules to disable |

### Example

```python
config = create_default_config()
config.linter.optimization_level = "moderate"
config.linter.max_crossjoin_depth = 5
config.linter.disabled_rules = ["normalize_member_references"]
```

## DAX Configuration

Controls DAX output generation and formatting.

### Output Formatting

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `format_output` | bool | True | Format DAX with indentation |
| `indent_size` | int | 4 | Number of spaces for indentation |
| `line_width` | int | 100 | Maximum line width before wrapping |

### DAX Style Preferences

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `use_summarizecolumns` | bool | True | Use SUMMARIZECOLUMNS function |
| `prefer_table_functions` | bool | True | Prefer table functions over scalar |
| `generate_measure_definitions` | bool | False | Generate MEASURE definitions |

### Naming Conventions

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `escape_reserved_words` | bool | True | Escape DAX reserved words |
| `quote_table_names` | bool | True | Quote table names with spaces |
| `use_friendly_names` | bool | True | Generate readable column names |

### Advanced Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `optimize_dax_expressions` | bool | True | Optimize generated DAX |
| `include_performance_hints` | bool | False | Add performance comments |
| `generate_comments` | bool | True | Include helpful comments |

### Compatibility Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `target_dax_version` | str | "latest" | Target DAX version |
| `power_bi_compatibility` | bool | True | Ensure Power BI compatibility |
| `ssas_compatibility` | bool | False | Ensure SSAS compatibility |

### Example

```python
config = create_default_config()
config.dax.indent_size = 2
config.dax.line_width = 80
config.dax.include_performance_hints = True
```

## Explanation Configuration

Controls human-readable output generation.

### Format and Detail

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `format` | enum | SQL | Output format (sql, natural, json, markdown) |
| `detail` | enum | STANDARD | Detail level (minimal, standard, detailed) |

### Content Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `include_sql_representation` | bool | True | Include SQL-like syntax |
| `include_dax_comparison` | bool | False | Include DAX equivalent |
| `include_metadata` | bool | False | Include query metadata |
| `include_performance_notes` | bool | False | Include performance tips |

### Natural Language Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `use_technical_terms` | bool | True | Use technical terminology |
| `explain_mdx_concepts` | bool | False | Explain MDX concepts |
| `include_best_practices` | bool | False | Include best practice tips |

### Output Formatting

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_line_length` | int | 80 | Maximum line length |
| `use_markdown_formatting` | bool | False | Use markdown syntax |
| `include_examples` | bool | False | Include usage examples |

### Example

```python
config = create_default_config()
config.explanation.format = "markdown"
config.explanation.detail = "detailed"
config.explanation.include_dax_comparison = True
```

## Global Settings

Settings that affect all components.

### Debug and Verbosity

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `debug` | bool | False | Enable debug mode |
| `verbose` | bool | False | Enable verbose output |

### Performance Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_caching` | bool | True | Enable result caching |
| `cache_size_mb` | int | 100 | Maximum cache size |
| `parallel_processing` | bool | False | Enable parallel processing |
| `max_workers` | int | 4 | Maximum parallel workers |

### Output Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_encoding` | str | "utf-8" | Output file encoding |
| `preserve_whitespace` | bool | False | Preserve original whitespace |

### Error Handling

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `fail_fast` | bool | False | Stop on first error |
| `collect_all_errors` | bool | True | Collect all errors before reporting |
| `max_warnings` | int | 50 | Maximum warnings to collect |

## Factory Functions

UnMDX provides convenient factory functions for common configurations:

### create_default_config()

Creates a balanced configuration suitable for most use cases.

```python
config = create_default_config()
```

### create_fast_config()

Optimized for speed, disables expensive operations.

```python
config = create_fast_config()
# Characteristics:
# - optimization_level = "none"
# - validate_* = False
# - enable_caching = False
# - generate_comments = False
```

### create_comprehensive_config()

Maximum detail and validation, suitable for debugging.

```python
config = create_comprehensive_config()
# Characteristics:
# - optimization_level = "aggressive"
# - All validation enabled
# - detailed explanations
# - include all metadata
```

## Configuration File Examples

### JSON Configuration

```json
{
  "parser": {
    "strict_mode": false,
    "allow_unknown_functions": true
  },
  "linter": {
    "optimization_level": "moderate",
    "max_crossjoin_depth": 5
  },
  "dax": {
    "indent_size": 2,
    "line_width": 100,
    "include_performance_hints": true
  },
  "explanation": {
    "format": "markdown",
    "detail": "detailed",
    "include_dax_comparison": true
  },
  "global": {
    "debug": false,
    "enable_caching": true
  }
}
```

### YAML Configuration

```yaml
parser:
  strict_mode: false
  allow_unknown_functions: true

linter:
  optimization_level: moderate
  max_crossjoin_depth: 5

dax:
  indent_size: 2
  line_width: 100
  include_performance_hints: true

explanation:
  format: markdown
  detail: detailed
  include_dax_comparison: true

global:
  debug: false
  enable_caching: true
```

## Environment Variables

Configuration can be set via environment variables using the pattern:
`UNMDX_<SECTION>_<OPTION>`

Examples:
```bash
export UNMDX_LINTER_OPTIMIZATION_LEVEL=aggressive
export UNMDX_DAX_INDENT_SIZE=2
export UNMDX_GLOBAL_DEBUG=true
```

## Configuration Validation

UnMDX validates configuration to ensure consistency:

```python
config = create_default_config()
config.dax.indent_size = -1  # Invalid!

try:
    config.validate()
except ConfigurationError as e:
    print(f"Invalid configuration: {e}")
```

## Best Practices

1. **Start with defaults**: Use `create_default_config()` and modify as needed
2. **Use appropriate optimization levels**: Conservative for production, aggressive for development
3. **Enable caching**: For repeated conversions of similar queries
4. **Validate configurations**: Call `validate()` before using custom configurations
5. **Use configuration files**: For reproducible results across teams

## Common Configuration Patterns

### For Necto MDX Cleanup

```python
config = create_default_config()
config.linter.optimization_level = "aggressive"
config.linter.max_crossjoin_depth = 7
config.dax.generate_comments = True
```

### For Learning/Documentation

```python
config = create_default_config()
config.explanation.format = "markdown"
config.explanation.detail = "detailed"
config.explanation.include_dax_comparison = True
config.explanation.explain_mdx_concepts = True
```

### For Production Pipelines

```python
config = create_fast_config()
config.global.fail_fast = True
config.global.max_warnings = 10
config.parser.validate_member_references = True
```

### For Debugging

```python
config = create_comprehensive_config()
config.parser.generate_parse_tree = True
config.parser.save_debug_info = True
config.global.debug = True
```

## Troubleshooting

If you encounter configuration issues:

1. Use `config.validate()` to check for errors
2. Enable debug mode: `config.global.debug = True`
3. Check the [Troubleshooting Guide](../troubleshooting/common-issues.md)
4. Use factory functions as a starting point