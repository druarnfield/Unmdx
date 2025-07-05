"""
UnMDX v2 - Simple MDX to DAX Converter

This is a recovery implementation focused on working functionality.
"""

__version__ = "2.0.0"

# Import main functionality
from .core.converter import mdx_to_dax

__all__ = ["mdx_to_dax"]