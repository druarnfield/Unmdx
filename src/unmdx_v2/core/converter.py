"""
Main converter interface for UnMDX v2.

This is the primary API that orchestrates the parser and DAX generator
to provide a simple, working MDX-to-DAX conversion.
"""

import logging
from typing import Dict, Any

from .parser import parse_mdx, MDXParseError
from .dax_generator import generate_dax, DAXGenerationError

logger = logging.getLogger(__name__)


class UnMDXError(Exception):
    """Base exception for UnMDX v2 errors."""
    pass


class ConversionError(UnMDXError):
    """Error during MDX to DAX conversion."""
    pass


def mdx_to_dax(mdx_query: str, debug: bool = False) -> str:
    """
    Convert MDX query to DAX query.
    
    This is the main function that orchestrates parsing and DAX generation
    to convert an MDX query into equivalent DAX.
    
    Args:
        mdx_query: MDX query string to convert
        debug: Enable debug logging
        
    Returns:
        DAX query string
        
    Raises:
        ConversionError: If conversion fails at any stage
        
    Example:
        >>> dax = mdx_to_dax("SELECT {[Measures].[Sales]} ON 0 FROM [Sales]")
        >>> print(dax)
        EVALUATE
        { [Sales] }
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    
    if not mdx_query or not mdx_query.strip():
        raise ConversionError("MDX query cannot be empty")
    
    try:
        logger.debug(f"Starting conversion of MDX: {mdx_query[:100]}...")
        
        # Step 1: Parse MDX
        logger.debug("Parsing MDX query...")
        parsed_mdx = parse_mdx(mdx_query)
        logger.debug(f"Parse result: {parsed_mdx}")
        
        # Step 2: Generate DAX
        logger.debug("Generating DAX query...")
        dax_query = generate_dax(parsed_mdx)
        logger.debug(f"Generated DAX: {dax_query}")
        
        logger.debug("Conversion completed successfully")
        return dax_query
        
    except MDXParseError as e:
        raise ConversionError(f"Failed to parse MDX: {e}") from e
    except DAXGenerationError as e:
        raise ConversionError(f"Failed to generate DAX: {e}") from e
    except Exception as e:
        raise ConversionError(f"Unexpected error during conversion: {e}") from e


def validate_dax(dax_query: str) -> bool:
    """
    Basic validation of generated DAX query.
    
    Args:
        dax_query: DAX query to validate
        
    Returns:
        True if basic validation passes
    """
    if not dax_query or not dax_query.strip():
        return False
    
    # Basic structural checks
    dax_upper = dax_query.upper()
    
    # Must start with EVALUATE
    if not dax_upper.startswith("EVALUATE"):
        return False
    
    # Should have proper structure
    if "EVALUATE\n{" in dax_query:
        # Simple measure query - should have closing brace
        return "}" in dax_query
    elif "SUMMARIZECOLUMNS" in dax_upper:
        # Dimension query - should have proper parentheses
        return dax_query.count("(") == dax_query.count(")")
    
    return True


def get_conversion_info(mdx_query: str) -> Dict[str, Any]:
    """
    Get detailed information about MDX query and conversion.
    
    Args:
        mdx_query: MDX query to analyze
        
    Returns:
        Dictionary with conversion information
    """
    try:
        parsed_mdx = parse_mdx(mdx_query)
        dax_query = generate_dax(parsed_mdx)
        
        return {
            "mdx_query": mdx_query,
            "parsed_structure": parsed_mdx,
            "dax_query": dax_query,
            "is_valid": validate_dax(dax_query),
            "measures_count": len(parsed_mdx["measures"]),
            "dimensions_count": len(parsed_mdx["dimensions"]),
            "cube": parsed_mdx["cube"],
            "query_type": "measure_only" if not parsed_mdx["dimensions"] else "dimensional"
        }
    except Exception as e:
        return {
            "mdx_query": mdx_query,
            "error": str(e),
            "is_valid": False
        }