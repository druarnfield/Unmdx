"""MDX to IR Transformer module."""

from .mdx_transformer import MDXTransformer, TransformationError, TransformationWarning
from .hierarchy_normalizer import HierarchyNormalizer, HierarchyMapping
from .set_flattener import SetFlattener, SetOperationType
from .comment_extractor import CommentExtractor, CommentHint

__all__ = [
    "MDXTransformer",
    "TransformationError", 
    "TransformationWarning",
    "HierarchyNormalizer",
    "HierarchyMapping",
    "SetFlattener",
    "SetOperationType",
    "CommentExtractor",
    "CommentHint"
]