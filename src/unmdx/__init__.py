"""
UnMDX - MDX to DAX Converter

A comprehensive Python CLI tool that converts MDX queries (particularly messy output 
from Necto SSAS cubes) into clean, optimized DAX queries with human-readable explanations.
"""

__version__ = "0.1.0"
__author__ = "Dru Arnfield"

# Convenience imports for common functionality
from .explainer import explain_mdx, explain_file, ExplainerGenerator
from .parser import MDXParser
from .transformer import MDXTransformer
from .dax_generator import DAXGenerator
from .linter import MDXLinter

__all__ = [
    "explain_mdx",
    "explain_file", 
    "ExplainerGenerator",
    "MDXParser",
    "MDXTransformer", 
    "DAXGenerator",
    "MDXLinter",
]
