"""DAX query formatting utilities."""

from typing import List, Optional
import re


class DAXFormatter:
    """Formats DAX queries for readability and consistency."""
    
    def __init__(self, indent_size: int = 4):
        """
        Initialize the formatter.
        
        Args:
            indent_size: Number of spaces per indent level
        """
        self.indent_size = indent_size
        self.indent_char = " " * indent_size
        
        # Keywords that should be on their own line
        self.line_keywords = {
            "DEFINE", "EVALUATE", "ORDER BY", "VAR", "RETURN",
            "CALCULATE", "CALCULATETABLE", "FILTER", "ALL",
            "SUMMARIZE", "SUMMARIZECOLUMNS", "ADDCOLUMNS",
            "SELECTCOLUMNS", "GROUPBY"
        }
        
        # Keywords that increase indent on next line
        self.indent_keywords = {
            "DEFINE", "EVALUATE", "CALCULATE", "CALCULATETABLE",
            "FILTER", "SUMMARIZE", "SUMMARIZECOLUMNS", "ADDCOLUMNS",
            "SELECTCOLUMNS", "GROUPBY", "VAR"
        }
    
    def format(self, dax_query: str) -> str:
        """
        Format a DAX query for readability.
        
        Args:
            dax_query: The DAX query to format
            
        Returns:
            Formatted DAX query
        """
        # Remove extra whitespace
        dax_query = re.sub(r'\s+', ' ', dax_query.strip())
        
        # Split into logical lines
        lines = self._split_into_lines(dax_query)
        
        # Apply indentation
        formatted_lines = self._apply_indentation(lines)
        
        # Join and clean up
        result = '\n'.join(formatted_lines)
        
        # Final cleanup
        result = self._final_cleanup(result)
        
        return result
    
    def _split_into_lines(self, dax_query: str) -> List[str]:
        """Split DAX query into logical lines."""
        lines = []
        current_line = []
        
        # Simple tokenization
        tokens = self._tokenize(dax_query)
        
        for i, token in enumerate(tokens):
            # Check if this token should start a new line
            if self._should_start_new_line(token, tokens, i):
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = []
            
            current_line.append(token)
            
            # Check if this token should end the line
            if self._should_end_line(token, tokens, i):
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = []
        
        # Add remaining tokens
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _tokenize(self, dax_query: str) -> List[str]:
        """Simple tokenization of DAX query."""
        # Pattern to match:
        # - Quoted strings (with escaped quotes)
        # - Square bracket identifiers
        # - Numbers
        # - Operators
        # - Keywords/identifiers
        # - Parentheses and commas
        pattern = r'"(?:[^"]|"")*"|\'(?:[^\']|\'\')*\'|\[[^\]]+\]|[\d.]+|[<>=!]+|[\w]+|[(),]'
        
        tokens = re.findall(pattern, dax_query)
        return tokens
    
    def _should_start_new_line(self, token: str, tokens: List[str], index: int) -> bool:
        """Check if token should start a new line."""
        token_upper = token.upper()
        
        # Main keywords start new lines
        if token_upper in self.line_keywords:
            return True
        
        # Comma in certain contexts (like measure definitions)
        if index > 0 and token == "," and self._in_measure_list(tokens, index):
            return False  # Keep measures on same line if short
        
        return False
    
    def _should_end_line(self, token: str, tokens: List[str], index: int) -> bool:
        """Check if token should end the current line."""
        # Look ahead for certain patterns
        if index + 1 < len(tokens):
            next_token = tokens[index + 1].upper()
            if next_token in self.line_keywords:
                return True
        
        return False
    
    def _in_measure_list(self, tokens: List[str], index: int) -> bool:
        """Check if we're in a measure list context."""
        # Simple heuristic - look for pattern like "measure_name", [measure]
        if index >= 2:
            if tokens[index - 2].startswith('"') and tokens[index - 1] == ",":
                return True
        return False
    
    def _apply_indentation(self, lines: List[str]) -> List[str]:
        """Apply proper indentation to lines."""
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for indent decrease
            first_token = self._get_first_token(line_stripped).upper()
            if first_token in ["ORDER BY", "RETURN"]:
                indent_level = max(0, indent_level - 1)
            elif line_stripped.startswith(")"):
                indent_level = max(0, indent_level - 1)
            
            # Apply current indentation
            formatted_line = self.indent_char * indent_level + line_stripped
            formatted_lines.append(formatted_line)
            
            # Check for indent increase
            if any(keyword in line_stripped.upper() for keyword in self.indent_keywords):
                # Don't increase indent if line ends with closing paren
                if not line_stripped.rstrip().endswith(")"):
                    indent_level += 1
            
            # Handle parentheses
            open_parens = line_stripped.count("(") - line_stripped.count(")")
            if open_parens > 0:
                indent_level += 1
            elif open_parens < 0:
                indent_level = max(0, indent_level + open_parens)
        
        return formatted_lines
    
    def _get_first_token(self, line: str) -> str:
        """Get the first token from a line."""
        tokens = self._tokenize(line)
        return tokens[0] if tokens else ""
    
    def _final_cleanup(self, dax_query: str) -> str:
        """Final cleanup pass on the formatted query."""
        # Remove trailing whitespace
        lines = [line.rstrip() for line in dax_query.split('\n')]
        
        # Remove empty lines at start/end
        while lines and not lines[0]:
            lines.pop(0)
        while lines and not lines[-1]:
            lines.pop()
        
        # Ensure single blank line between major sections
        result_lines = []
        prev_was_major = False
        
        for line in lines:
            is_major = any(line.strip().upper().startswith(kw) for kw in ["DEFINE", "EVALUATE"])
            
            if is_major and prev_was_major and result_lines:
                # Ensure blank line between major sections
                if result_lines[-1].strip():
                    result_lines.append("")
            
            result_lines.append(line)
            prev_was_major = is_major
        
        return '\n'.join(result_lines)
    
    def format_identifier(self, identifier: str) -> str:
        """
        Format a DAX identifier (table/column name).
        
        Args:
            identifier: The identifier to format
            
        Returns:
            Properly escaped identifier
        """
        # Check if already bracketed
        if identifier.startswith('[') and identifier.endswith(']'):
            return identifier
        
        # Check if brackets are needed
        needs_brackets = (
            ' ' in identifier or
            '-' in identifier or
            not identifier.replace('_', '').isalnum() or
            identifier[0].isdigit() or
            identifier.upper() in self._get_dax_keywords()
        )
        
        if needs_brackets:
            # Escape any existing brackets
            escaped = identifier.replace(']', ']]')
            return f"[{escaped}]"
        
        return identifier
    
    def _get_dax_keywords(self) -> set:
        """Get set of DAX reserved keywords."""
        return {
            "ALL", "ALLEXCEPT", "ALLNOBLANKROW", "ALLSELECTED",
            "CALCULATE", "CALCULATETABLE", "CALENDAR", "CALENDARAUTO",
            "COUNT", "COUNTA", "COUNTAX", "COUNTBLANK", "COUNTROWS",
            "COUNTX", "DATE", "DATEDIFF", "DATEVALUE", "DAY",
            "DISTINCT", "DISTINCTCOUNT", "DIVIDE", "EARLIER",
            "EARLIEST", "FILTER", "FILTERS", "HASONEFILTER",
            "HASONEVALUE", "IF", "ISBLANK", "ISERROR", "ISFILTERED",
            "MAX", "MAXA", "MAXX", "MIN", "MINA", "MINX",
            "MONTH", "NOT", "OR", "RELATED", "RELATEDTABLE",
            "SELECTEDVALUE", "SUM", "SUMA", "SUMMARIZE",
            "SUMMARIZECOLUMNS", "SUMX", "SWITCH", "TIME",
            "TODAY", "TREATAS", "TRUE", "FALSE", "VALUES",
            "VAR", "RETURN", "YEAR"
        }
    
    def escape_string(self, value: str) -> str:
        """
        Escape a string value for DAX.
        
        Args:
            value: The string to escape
            
        Returns:
            Properly escaped string with quotes
        """
        # Escape quotes by doubling them
        escaped = value.replace('"', '""')
        return f'"{escaped}"'