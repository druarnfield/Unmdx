"""Hierarchy normalization logic for MDX transformations."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

from lark import Tree

from ..ir import HierarchyReference, LevelReference, Dimension, MemberSelection, MemberSelectionType
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class HierarchyMapping:
    """Mapping information for a hierarchy."""
    table_name: str
    hierarchy_name: str
    levels: List[str]
    level_ordinals: Dict[str, int]
    deepest_level: str
    is_ragged: bool = False
    member_paths: Dict[str, List[str]] = None  # member -> path from root
    
    def __post_init__(self):
        if self.member_paths is None:
            self.member_paths = {}


class HierarchyNormalizer:
    """
    Normalizes hierarchy references and detects redundant levels.
    
    This component analyzes MDX parse trees to:
    - Identify all hierarchies being used
    - Detect redundant level specifications
    - Extract the deepest meaningful level
    - Handle ragged hierarchies
    - Map members to their proper hierarchical positions
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Caches for hierarchy analysis
        self._hierarchy_mappings: Dict[str, HierarchyMapping] = {}
        self._member_hierarchy_map: Dict[str, str] = {}  # member -> hierarchy
        self._level_member_map: Dict[str, Set[str]] = defaultdict(set)  # level -> members
        
    def normalize_hierarchies(self, tree: Tree) -> Dict[str, HierarchyMapping]:
        """
        Analyze the parse tree and normalize all hierarchy references.
        
        Args:
            tree: The MDX parse tree
            
        Returns:
            Dictionary mapping hierarchy names to their normalized mappings
        """
        self.logger.debug("Starting hierarchy normalization")
        
        # Clear caches
        self._hierarchy_mappings.clear()
        self._member_hierarchy_map.clear()
        self._level_member_map.clear()
        
        # Step 1: Collect all hierarchy references
        hierarchy_refs = self._collect_hierarchy_references(tree)
        
        # Step 2: Analyze member usage patterns
        member_usage = self._analyze_member_usage(tree)
        
        # Step 3: Build hierarchy mappings
        for hierarchy_name, refs in hierarchy_refs.items():
            mapping = self._build_hierarchy_mapping(hierarchy_name, refs, member_usage)
            self._hierarchy_mappings[hierarchy_name] = mapping
        
        # Step 4: Detect redundant levels
        self._detect_redundant_levels()
        
        # Step 5: Identify ragged hierarchies
        self._identify_ragged_hierarchies()
        
        self.logger.info(f"Normalized {len(self._hierarchy_mappings)} hierarchies")
        return self._hierarchy_mappings.copy()
    
    def get_deepest_level(self, hierarchy_name: str) -> Optional[str]:
        """Get the deepest level being used in a hierarchy."""
        mapping = self._hierarchy_mappings.get(hierarchy_name)
        return mapping.deepest_level if mapping else None
    
    def is_redundant_level(self, hierarchy_name: str, level_name: str) -> bool:
        """Check if a level specification is redundant."""
        mapping = self._hierarchy_mappings.get(hierarchy_name)
        if not mapping:
            return False
        
        # A level is redundant if it's not the deepest level being used
        return level_name != mapping.deepest_level
    
    def get_normalized_dimension(self, hierarchy_name: str, level_name: str, 
                                members: List[str]) -> Optional[Dimension]:
        """
        Get a normalized dimension specification.
        
        Args:
            hierarchy_name: Name of the hierarchy
            level_name: Name of the level
            members: List of members being referenced
            
        Returns:
            Normalized Dimension object
        """
        mapping = self._hierarchy_mappings.get(hierarchy_name)
        if not mapping:
            self.logger.warning(f"No mapping found for hierarchy {hierarchy_name}")
            return None
        
        # Use the deepest level if the specified level is redundant
        normalized_level = mapping.deepest_level
        
        # Create hierarchy and level references
        hierarchy_ref = HierarchyReference(
            table=mapping.table_name,
            name=mapping.hierarchy_name
        )
        
        level_ref = LevelReference(
            name=normalized_level,
            ordinal=mapping.level_ordinals.get(normalized_level)
        )
        
        # Determine member selection type
        if not members:
            member_selection = MemberSelection(
                selection_type=MemberSelectionType.ALL
            )
        else:
            member_selection = MemberSelection(
                selection_type=MemberSelectionType.SPECIFIC,
                specific_members=members
            )
        
        return Dimension(
            hierarchy=hierarchy_ref,
            level=level_ref,
            members=member_selection
        )
    
    def _collect_hierarchy_references(self, tree: Tree) -> Dict[str, List[Tree]]:
        """Collect all hierarchy references from the parse tree."""
        hierarchy_refs = defaultdict(list)
        
        # Look for various hierarchy reference patterns
        self._collect_hierarchy_refs_recursive(tree, hierarchy_refs)
        
        return dict(hierarchy_refs)
    
    def _collect_hierarchy_refs_recursive(self, node: Tree, hierarchy_refs: Dict[str, List[Tree]]):
        """Recursively collect hierarchy references."""
        if not isinstance(node, Tree):
            return
        
        # Check for hierarchy-related nodes
        if node.data in ["hierarchy_reference", "dimension_reference", "level_reference"]:
            hierarchy_name = self._extract_hierarchy_name(node)
            if hierarchy_name:
                hierarchy_refs[hierarchy_name].append(node)
        
        # Check for member references that imply hierarchies
        elif node.data == "member_reference":
            hierarchy_name = self._infer_hierarchy_from_member(node)
            if hierarchy_name:
                hierarchy_refs[hierarchy_name].append(node)
        
        # Recurse into children
        for child in node.children:
            if isinstance(child, Tree):
                self._collect_hierarchy_refs_recursive(child, hierarchy_refs)
    
    def _analyze_member_usage(self, tree: Tree) -> Dict[str, List[str]]:
        """Analyze which members are being used from each hierarchy."""
        member_usage = defaultdict(list)
        
        self._analyze_member_usage_recursive(tree, member_usage)
        
        return dict(member_usage)
    
    def _analyze_member_usage_recursive(self, node: Tree, member_usage: Dict[str, List[str]]):
        """Recursively analyze member usage."""
        if not isinstance(node, Tree):
            return
        
        if node.data == "member_reference":
            member_name = self._extract_member_name(node)
            hierarchy_name = self._infer_hierarchy_from_member(node)
            
            if member_name and hierarchy_name:
                member_usage[hierarchy_name].append(member_name)
                self._member_hierarchy_map[member_name] = hierarchy_name
        
        # Recurse into children
        for child in node.children:
            if isinstance(child, Tree):
                self._analyze_member_usage_recursive(child, member_usage)
    
    def _build_hierarchy_mapping(self, hierarchy_name: str, refs: List[Tree], 
                                member_usage: Dict[str, List[str]]) -> HierarchyMapping:
        """Build a hierarchy mapping from collected references."""
        
        # Extract table name (use hierarchy name as default)
        table_name = self._extract_table_name(hierarchy_name, refs)
        
        # Extract levels mentioned in references
        levels = set()
        level_ordinals = {}
        
        for ref in refs:
            level_info = self._extract_level_info(ref)
            if level_info:
                level_name, ordinal = level_info
                levels.add(level_name)
                if ordinal is not None:
                    level_ordinals[level_name] = ordinal
        
        # If no explicit levels found, infer from member usage
        if not levels and hierarchy_name in member_usage:
            levels = self._infer_levels_from_members(member_usage[hierarchy_name])
        
        levels_list = sorted(levels)
        
        # Determine deepest level
        deepest_level = self._determine_deepest_level(levels_list, level_ordinals, member_usage.get(hierarchy_name, []))
        
        # Build member paths
        member_paths = {}
        if hierarchy_name in member_usage:
            for member in member_usage[hierarchy_name]:
                path = self._build_member_path(member, levels_list)
                member_paths[member] = path
        
        return HierarchyMapping(
            table_name=table_name,
            hierarchy_name=hierarchy_name,
            levels=levels_list,
            level_ordinals=level_ordinals,
            deepest_level=deepest_level,
            member_paths=member_paths
        )
    
    def _detect_redundant_levels(self):
        """Detect redundant level specifications across all hierarchies."""
        for hierarchy_name, mapping in self._hierarchy_mappings.items():
            # Mark levels as redundant if they're not the deepest level being used
            for level in mapping.levels:
                if level != mapping.deepest_level:
                    self.logger.debug(f"Level {level} in {hierarchy_name} is redundant")
    
    def _identify_ragged_hierarchies(self):
        """Identify hierarchies that have ragged (uneven) structures."""
        for hierarchy_name, mapping in self._hierarchy_mappings.items():
            # Check if member paths have different lengths
            path_lengths = [len(path) for path in mapping.member_paths.values()]
            if len(set(path_lengths)) > 1:
                mapping.is_ragged = True
                self.logger.info(f"Hierarchy {hierarchy_name} is ragged")
    
    def _extract_hierarchy_name(self, node: Tree) -> Optional[str]:
        """Extract hierarchy name from a node."""
        # Look for hierarchy identifier
        for child in node.children:
            if hasattr(child, 'value'):
                return str(child.value)
            elif isinstance(child, Tree) and child.data == "identifier":
                return self._extract_identifier_value(child)
        
        return None
    
    def _infer_hierarchy_from_member(self, member_node: Tree) -> Optional[str]:
        """Infer hierarchy name from a member reference."""
        # This is a simplified implementation
        # In practice, would need more sophisticated logic to map members to hierarchies
        
        member_name = self._extract_member_name(member_node)
        if not member_name:
            return None
        
        # Simple heuristics based on member name patterns
        if any(keyword in member_name.upper() for keyword in ["DATE", "TIME", "CALENDAR"]):
            return "Date"
        elif any(keyword in member_name.upper() for keyword in ["PRODUCT", "ITEM"]):
            return "Product"
        elif any(keyword in member_name.upper() for keyword in ["CUSTOMER", "CLIENT"]):
            return "Customer"
        elif any(keyword in member_name.upper() for keyword in ["GEO", "LOCATION", "REGION"]):
            return "Geography"
        
        # Default fallback
        return "DefaultHierarchy"
    
    def _extract_member_name(self, member_node: Tree) -> Optional[str]:
        """Extract member name from a member reference node."""
        for child in member_node.children:
            if hasattr(child, 'value'):
                return str(child.value)
            elif isinstance(child, Tree) and child.data == "identifier":
                return self._extract_identifier_value(child)
        
        return None
    
    def _extract_table_name(self, hierarchy_name: str, refs: List[Tree]) -> str:
        """Extract table name from hierarchy references."""
        # Look for qualified names that might contain table information
        for ref in refs:
            table_name = self._extract_table_from_reference(ref)
            if table_name:
                return table_name
        
        # Default to hierarchy name
        return hierarchy_name
    
    def _extract_table_from_reference(self, ref: Tree) -> Optional[str]:
        """Extract table name from a specific reference."""
        # This would need more sophisticated parsing of qualified names
        return None
    
    def _extract_level_info(self, ref: Tree) -> Optional[Tuple[str, Optional[int]]]:
        """Extract level name and ordinal from a reference."""
        # Look for level specifications
        level_name = None
        ordinal = None
        
        # This is a placeholder implementation
        # Would need to parse actual level references from the tree
        
        return (level_name, ordinal) if level_name else None
    
    def _infer_levels_from_members(self, members: List[str]) -> Set[str]:
        """Infer possible levels from member names."""
        levels = set()
        
        # Simple heuristics based on member name patterns
        for member in members:
            member_upper = member.upper()
            level_found = False
            
            # Check for year patterns
            if any(keyword in member_upper for keyword in ["YEAR", "YTD"]) or member.isdigit() and len(member) == 4:
                levels.add("Year")
                level_found = True
            
            # Check for quarter patterns  
            if any(keyword in member_upper for keyword in ["QUARTER", "QTD", "Q1", "Q2", "Q3", "Q4"]):
                levels.add("Quarter")
                level_found = True
                
            # Check for month patterns
            if any(keyword in member_upper for keyword in ["MONTH", "MTD", "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]):
                levels.add("Month")
                level_found = True
                
            # Check for category patterns
            if any(keyword in member_upper for keyword in ["CATEGORY"]):
                levels.add("Category")
                level_found = True
                
            # Check for subcategory patterns
            if any(keyword in member_upper for keyword in ["SUBCATEGORY", "SUB"]):
                levels.add("Subcategory")
                level_found = True
            
            # If no specific pattern found, add default
            if not level_found:
                levels.add("All")
        
        return levels
    
    def _determine_deepest_level(self, levels: List[str], level_ordinals: Dict[str, int], 
                                members: List[str]) -> str:
        """Determine the deepest level being used."""
        if not levels:
            return "All"
        
        # If we have ordinals, use the highest one
        if level_ordinals:
            max_ordinal = max(level_ordinals.values())
            for level, ordinal in level_ordinals.items():
                if ordinal == max_ordinal:
                    return level
        
        # Otherwise, use heuristics based on level names
        level_depth_map = {
            "All": 0,
            "Year": 1,
            "Quarter": 2,
            "Month": 3,
            "Day": 4,
            "Category": 1,
            "Subcategory": 2,
            "Product": 3
        }
        
        deepest_level = levels[0]
        max_depth = level_depth_map.get(deepest_level, 0)
        
        for level in levels:
            depth = level_depth_map.get(level, 0)
            if depth > max_depth:
                max_depth = depth
                deepest_level = level
        
        return deepest_level
    
    def _build_member_path(self, member: str, levels: List[str]) -> List[str]:
        """Build hierarchical path for a member."""
        # This is a simplified implementation
        # In practice, would need to understand the actual hierarchy structure
        
        # Return a simple path with the member at the deepest level
        return levels + [member] if levels else [member]
    
    def _extract_identifier_value(self, node: Tree) -> str:
        """Extract identifier value from a node."""
        if node.children:
            return str(node.children[0])
        return str(node)