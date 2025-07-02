# UnMDX Troubleshooting Guide

This guide helps resolve common issues when using UnMDX for MDX to DAX conversion.

## Common Issues

### Installation Issues

#### Issue: `unmdx` command not found
```bash
unmdx: command not found
```

**Solution**: Ensure UnMDX is properly installed:
```bash
# Using pip
pip install unmdx

# Using uv (for development)
uv sync
uv run unmdx --help
```

#### Issue: Import errors when using Python API
```python
ImportError: No module named 'unmdx'
```

**Solution**: 
1. Install UnMDX: `pip install unmdx`
2. Or add to Python path for development:
   ```python
   import sys
   sys.path.insert(0, 'path/to/unmdx/src')
   ```

### Parsing Issues

#### Issue: MDX parsing fails with "Unexpected Characters"
```
lark.exceptions.UnexpectedCharacters: No terminal matches '(' in the current parser context
```

**Causes**:
- MDX grammar doesn't support all syntax variations
- Parentheses around measures may not be supported
- Complex calculated members might not parse

**Solutions**:
1. Simplify the MDX query
2. Remove redundant parentheses
3. Check [supported MDX syntax](../mdx_spec.md)

**Example**:
```mdx
# ❌ Not supported
SELECT (([Measures].[Sales])) ON 0 FROM [Sales]

# ✅ Supported  
SELECT [Measures].[Sales] ON 0 FROM [Sales]
```

#### Issue: "Empty MDX text" validation error
```
ValidationError: MDX text cannot be empty
```

**Solution**: Ensure your MDX file contains valid content:
```bash
# Check file contents
cat your_file.mdx

# Ensure file is not empty and contains MDX
```

### Conversion Issues

#### Issue: Generated DAX is `EVALUATE ROW ( "Value" , BLANK ( ) )`
This indicates the IR transformation isn't extracting all elements properly.

**Possible causes**:
- Complex MDX structures not fully supported
- Missing measures or dimensions in transformation
- WITH clauses or calculated members not processed

**Solutions**:
1. Use simpler MDX queries
2. Break complex queries into parts
3. Check logs with `--verbose` flag

#### Issue: Optimization fails
```
LintError: Optimization failed
```

**Solution**: Disable optimization or use lower level:
```bash
# Disable optimization
unmdx convert query.mdx --optimization-level none

# Use conservative optimization
unmdx convert query.mdx --optimization-level conservative
```

### Configuration Issues

#### Issue: Invalid optimization level
```
Error: Invalid optimization level 'high'. Valid options: none, conservative, moderate, aggressive
```

**Solution**: Use valid optimization levels:
```bash
unmdx convert query.mdx --optimization-level moderate
```

#### Issue: Configuration validation failed
```
ConfigurationError: Configuration validation failed
```

**Solution**: Check configuration values:
```python
config = create_default_config()
config.validate()  # This will show specific errors
```

### Performance Issues

#### Issue: Conversion takes too long
**Solutions**:
1. Use faster configuration:
   ```python
   config = create_fast_config()
   ```

2. Disable expensive operations:
   ```bash
   unmdx convert query.mdx --optimization-level none
   ```

3. Break large queries into smaller parts

#### Issue: High memory usage
**Solutions**:
1. Reduce input size
2. Disable caching:
   ```python
   config = create_default_config()
   config.enable_caching = False
   ```

### Output Issues

#### Issue: Explanation is too brief or generic
```
Explanation: This query from the Adventure Works data model.
```

**Solutions**:
1. Use detailed explanation level:
   ```bash
   unmdx explain query.mdx --detail detailed
   ```

2. Try different formats:
   ```bash
   unmdx explain query.mdx --format markdown --detail detailed
   ```

#### Issue: DAX output not formatted
**Solution**: Ensure formatting is enabled:
```python
config = create_default_config()
config.dax.format_output = True
```

## Environment-Specific Issues

### Windows Issues

#### Issue: Path separators in file paths
**Solution**: Use forward slashes or raw strings:
```python
# ✅ Good
file_path = "C:/path/to/query.mdx"
file_path = r"C:\path\to\query.mdx"

# ❌ Problematic
file_path = "C:\path\to\query.mdx"
```

### Docker Issues

#### Issue: File not found in container
**Solution**: Ensure proper volume mounting:
```bash
docker run -v /host/path:/container/path unmdx:latest convert /container/path/query.mdx
```

## Debug Mode

Enable debug mode for detailed troubleshooting:

### CLI Debug Mode
```bash
unmdx convert query.mdx --verbose
```

### Python API Debug Mode
```python
config = create_default_config()
config.debug = True
config.verbose = True
```

## Getting Detailed Error Information

### Check Logs
UnMDX provides detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Examine Parse Tree
For parsing issues, generate parse tree:
```python
config = create_default_config()
config.parser.generate_parse_tree = True
config.parser.save_debug_info = True
```

### Performance Analysis
Enable performance tracking:
```python
result = mdx_to_dax(mdx_query, include_metadata=True)
print(f"Parse time: {result.performance.timings['parse']:.3f}s")
print(f"Transform time: {result.performance.timings['transform']:.3f}s")
print(f"Generation time: {result.performance.timings['generation']:.3f}s")
```

## FAQ

### Q: Which MDX features are supported?
**A**: UnMDX supports core MDX constructs like SELECT, FROM, WHERE, basic functions, and member references. Complex calculated members and some advanced functions may not be fully supported. Check the [MDX specification](../mdx_spec.md) for details.

### Q: Can I customize the DAX output format?
**A**: Yes, through configuration:
```python
config = create_default_config()
config.dax.indent_size = 2
config.dax.line_width = 120
config.dax.use_summarizecolumns = True
```

### Q: How do I report a bug?
**A**: 
1. Enable debug mode and capture full error output
2. Create a minimal test case
3. Report on [GitHub Issues](https://github.com/druarnfield/unmdx/issues)

### Q: Is my MDX syntax supported?
**A**: Test with a simple example first:
```bash
echo "SELECT [Measures].[Sales] ON 0 FROM [Sales]" | unmdx convert -
```

### Q: How do I improve explanation quality?
**A**: 
1. Use detailed level: `--detail detailed`
2. Include DAX comparison: `--include-dax`
3. Use markdown format for better structure

### Q: Can I use UnMDX in production?
**A**: UnMDX is currently in alpha stage. Test thoroughly and consider:
- Enabling conservative optimization only
- Validating output against expected results
- Using error handling in your integration

## Contact Support

- **Documentation**: [User Guide](../user-guide/)
- **API Reference**: [API Documentation](../api/)
- **Issues**: [GitHub Issues](https://github.com/druarnfield/unmdx/issues)
- **Discussions**: [GitHub Discussions](https://github.com/druarnfield/unmdx/discussions)

## Performance Benchmarks

Expected performance on typical hardware:

| Query Size | Parse Time | Transform Time | Generate Time |
|------------|------------|----------------|---------------|
| Simple (1-5 lines) | < 50ms | < 10ms | < 10ms |
| Medium (10-50 lines) | < 200ms | < 50ms | < 50ms |
| Large (100+ lines) | < 1s | < 200ms | < 200ms |

If your performance differs significantly, consider:
- Using `create_fast_config()`
- Disabling optimization
- Breaking large queries into parts