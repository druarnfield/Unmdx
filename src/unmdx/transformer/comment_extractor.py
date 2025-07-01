"""Comment and hint extraction for MDX transformations."""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Set, Tuple
from enum import Enum

from lark import Tree, Token

from ..utils.logging import get_logger

logger = get_logger(__name__)


class HintType(Enum):
    """Types of optimization hints found in comments."""
    PERFORMANCE = "PERFORMANCE"
    CACHING = "CACHING"
    INDEX = "INDEX"
    AGGREGATION = "AGGREGATION"
    FILTER_PUSH_DOWN = "FILTER_PUSH_DOWN"
    MATERIALIZATION = "MATERIALIZATION"
    PARALLEL = "PARALLEL"
    MEMORY = "MEMORY"
    CUSTOM = "CUSTOM"


@dataclass
class CommentHint:
    """A hint extracted from comments."""
    hint_type: HintType
    message: str
    line_number: Optional[int] = None
    context: Optional[str] = None
    severity: str = "INFO"  # INFO, WARNING, ERROR
    
    def __str__(self) -> str:
        return f"{self.hint_type.value}: {self.message}"


class CommentExtractor:
    """
    Extracts optimization hints and metadata from MDX comments.
    
    This component analyzes MDX queries to find:
    - Performance hints in comments
    - Optimization suggestions
    - User annotations about query intent
    - Metadata about data sources and expectations
    - Error handling instructions
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Patterns for detecting different types of hints
        self._hint_patterns = {
            HintType.PERFORMANCE: [
                r'(?i)perf(?:ormance)?[:\s]+(.+)',
                r'(?i)slow[:\s]+(.+)',
                r'(?i)optimize[:\s]+(.+)',
                r'(?i)speed[:\s]+(.+)',
            ],
            HintType.CACHING: [
                r'(?i)cache[:\s]+(.+)',
                r'(?i)cached?[:\s]+(.+)',
                r'(?i)materialize[:\s]+(.+)',
            ],
            HintType.INDEX: [
                r'(?i)index[:\s]+(.+)',
                r'(?i)indexed?[:\s]+(.+)',
            ],
            HintType.AGGREGATION: [
                r'(?i)agg(?:regat(?:e|ion))?[:\s]+(.+)',
                r'(?i)sum(?:mariz(?:e|ation))?[:\s]+(.+)',
                r'(?i)group[:\s]+(.+)',
            ],
            HintType.FILTER_PUSH_DOWN: [
                r'(?i)filter[:\s]+(.+)',
                r'(?i)where[:\s]+(.+)',
                r'(?i)push[:\s]+(.+)',
            ],
            HintType.MATERIALIZATION: [
                r'(?i)materialize[:\s]+(.+)',
                r'(?i)precompute[:\s]+(.+)',
                r'(?i)precalc(?:ulate)?[:\s]+(.+)',
            ],
            HintType.PARALLEL: [
                r'(?i)parallel[:\s]+(.+)',
                r'(?i)concurrent[:\s]+(.+)',
                r'(?i)thread[:\s]+(.+)',
            ],
            HintType.MEMORY: [
                r'(?i)memory[:\s]+(.+)',
                r'(?i)mem[:\s]+(.+)',
                r'(?i)ram[:\s]+(.+)',
            ],
        }
        
        # Keywords that indicate important comments
        self._important_keywords = {
            'todo', 'fixme', 'hack', 'bug', 'issue', 'problem',
            'note', 'important', 'warning', 'error', 'critical',
            'optimize', 'performance', 'slow', 'fast', 'cache'
        }
    
    def extract_hints(self, tree: Tree, source_mdx: Optional[str] = None) -> List[CommentHint]:
        """
        Extract all hints from comments in the parse tree and source.
        
        Args:
            tree: The MDX parse tree
            source_mdx: Original MDX source code
            
        Returns:
            List of extracted hints
        """
        hints = []
        
        # Extract hints from parse tree comments
        tree_hints = self._extract_from_tree(tree)
        hints.extend(tree_hints)
        
        # Extract hints from source text
        if source_mdx:
            source_hints = self._extract_from_source(source_mdx)
            hints.extend(source_hints)
        
        # Deduplicate hints
        hints = self._deduplicate_hints(hints)
        
        self.logger.info(f"Extracted {len(hints)} hints from comments")
        return hints
    
    def extract_query_metadata(self, tree: Tree, source_mdx: Optional[str] = None) -> Dict[str, str]:
        """
        Extract metadata about the query from comments.
        
        Returns:
            Dictionary with metadata like author, purpose, data sources, etc.
        """
        metadata = {}
        
        # Extract metadata from comments
        comments = self._collect_all_comments(tree, source_mdx)
        
        for comment in comments:
            # Look for metadata patterns
            metadata.update(self._extract_metadata_from_comment(comment))
        
        return metadata
    
    def get_performance_warnings(self, tree: Tree, source_mdx: Optional[str] = None) -> List[str]:
        """
        Extract performance-related warnings from comments.
        
        Returns:
            List of performance warning messages
        """
        hints = self.extract_hints(tree, source_mdx)
        
        warnings = []
        for hint in hints:
            if hint.hint_type == HintType.PERFORMANCE and hint.severity in ["WARNING", "ERROR"]:
                warnings.append(hint.message)
        
        return warnings
    
    def _extract_from_tree(self, tree: Tree) -> List[CommentHint]:
        """Extract hints from comments found in the parse tree."""
        hints = []
        
        # Recursively find comment nodes
        comment_nodes = self._find_comment_nodes(tree)
        
        for comment_node in comment_nodes:
            comment_text = self._extract_comment_text(comment_node)
            if comment_text:
                comment_hints = self._analyze_comment(comment_text)
                hints.extend(comment_hints)
        
        return hints
    
    def _extract_from_source(self, source_mdx: str) -> List[CommentHint]:
        """Extract hints from comments in the source MDX text."""
        hints = []
        
        # Find all comments in the source
        comments = self._extract_comments_from_source(source_mdx)
        
        for line_num, comment_text in comments:
            comment_hints = self._analyze_comment(comment_text, line_num)
            hints.extend(comment_hints)
        
        return hints
    
    def _find_comment_nodes(self, tree: Tree) -> List[Tree]:
        """Find all comment nodes in the parse tree."""
        comment_nodes = []
        
        if isinstance(tree, Tree):
            if tree.data == "comment":
                comment_nodes.append(tree)
            
            for child in tree.children:
                if isinstance(child, Tree):
                    comment_nodes.extend(self._find_comment_nodes(child))
        
        return comment_nodes
    
    def _extract_comment_text(self, comment_node: Tree) -> Optional[str]:
        """Extract text content from a comment node."""
        for child in comment_node.children:
            if isinstance(child, Token):
                text = str(child)
                # Remove comment markers
                text = re.sub(r'^/\*|\*/$|^//|^--', '', text).strip()
                return text
        
        return None
    
    def _extract_comments_from_source(self, source_mdx: str) -> List[Tuple[int, str]]:
        """Extract all comments from source MDX with line numbers."""
        comments = []
        lines = source_mdx.split('\n')
        
        in_block_comment = False
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Handle block comments /* ... */
            if '/*' in line and '*/' in line:
                # Single line block comment
                match = re.search(r'/\*(.*?)\*/', line)
                if match:
                    comments.append((line_num, match.group(1).strip()))
            elif '/*' in line:
                # Start of multi-line block comment
                in_block_comment = True
                comment_start = line[line.find('/*') + 2:]
                if comment_start.strip():
                    comments.append((line_num, comment_start.strip()))
            elif '*/' in line and in_block_comment:
                # End of multi-line block comment
                in_block_comment = False
                comment_end = line[:line.find('*/')]
                if comment_end.strip():
                    comments.append((line_num, comment_end.strip()))
            elif in_block_comment:
                # Middle of multi-line block comment
                clean_line = re.sub(r'^\s*\*\s?', '', line)
                if clean_line:
                    comments.append((line_num, clean_line))
            
            # Handle line comments // or --
            elif line.startswith('//') or line.startswith('--'):
                comment_text = re.sub(r'^(//|--)\s*', '', line)
                if comment_text:
                    comments.append((line_num, comment_text))
        
        return comments
    
    def _analyze_comment(self, comment_text: str, line_number: Optional[int] = None) -> List[CommentHint]:
        """Analyze a comment and extract hints."""
        hints = []
        
        # Check against all hint patterns
        for hint_type, patterns in self._hint_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, comment_text)
                if match:
                    message = match.group(1).strip()
                    severity = self._determine_severity(comment_text)
                    
                    hint = CommentHint(
                        hint_type=hint_type,
                        message=message,
                        line_number=line_number,
                        context=comment_text[:50] + "..." if len(comment_text) > 50 else comment_text,
                        severity=severity
                    )
                    hints.append(hint)
        
        # Check for custom/general hints
        if not hints and self._is_important_comment(comment_text):
            hint = CommentHint(
                hint_type=HintType.CUSTOM,
                message=comment_text,
                line_number=line_number,
                severity=self._determine_severity(comment_text)
            )
            hints.append(hint)
        
        return hints
    
    def _determine_severity(self, comment_text: str) -> str:
        """Determine severity level from comment text."""
        text_lower = comment_text.lower()
        
        if any(word in text_lower for word in ['error', 'critical', 'urgent', 'broken']):
            return "ERROR"
        elif any(word in text_lower for word in ['warning', 'warn', 'issue', 'problem', 'slow']):
            return "WARNING"
        else:
            return "INFO"
    
    def _is_important_comment(self, comment_text: str) -> bool:
        """Check if a comment contains important keywords."""
        text_lower = comment_text.lower()
        return any(keyword in text_lower for keyword in self._important_keywords)
    
    def _collect_all_comments(self, tree: Tree, source_mdx: Optional[str] = None) -> List[str]:
        """Collect all comment text from tree and source."""
        comments = []
        
        # From tree
        comment_nodes = self._find_comment_nodes(tree)
        for node in comment_nodes:
            text = self._extract_comment_text(node)
            if text:
                comments.append(text)
        
        # From source
        if source_mdx:
            source_comments = self._extract_comments_from_source(source_mdx)
            comments.extend([comment for _, comment in source_comments])
        
        return comments
    
    def _extract_metadata_from_comment(self, comment_text: str) -> Dict[str, str]:
        """Extract metadata from a single comment."""
        metadata = {}
        
        # Common metadata patterns
        metadata_patterns = {
            'author': r'(?i)author[:\s]+(.+)',
            'created': r'(?i)created[:\s]+(.+)',
            'modified': r'(?i)(?:modified|updated)[:\s]+(.+)',
            'version': r'(?i)version[:\s]+(.+)',
            'purpose': r'(?i)purpose[:\s]+(.+)',
            'description': r'(?i)(?:description|desc)[:\s]+(.+)',
            'data_source': r'(?i)(?:data[_\s]?source|source)[:\s]+(.+)',
            'frequency': r'(?i)frequency[:\s]+(.+)',
            'owner': r'(?i)owner[:\s]+(.+)',
            'contact': r'(?i)contact[:\s]+(.+)',
        }
        
        for key, pattern in metadata_patterns.items():
            match = re.search(pattern, comment_text)
            if match:
                metadata[key] = match.group(1).strip()
        
        return metadata
    
    def _deduplicate_hints(self, hints: List[CommentHint]) -> List[CommentHint]:
        """Remove duplicate hints."""
        seen = set()
        unique_hints = []
        
        for hint in hints:
            # Create a key for deduplication
            key = (hint.hint_type, hint.message.lower().strip())
            if key not in seen:
                seen.add(key)
                unique_hints.append(hint)
        
        return unique_hints