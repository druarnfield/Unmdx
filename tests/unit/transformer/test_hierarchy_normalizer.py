"""Unit tests for hierarchy normalization logic."""

import pytest
from lark import Tree, Token

from unmdx.transformer.hierarchy_normalizer import HierarchyNormalizer, HierarchyMapping
from unmdx.ir import MemberSelectionType


class TestHierarchyNormalizer:
    """Test hierarchy normalization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = HierarchyNormalizer()
    
    def test_normalize_simple_hierarchy(self):
        """Test normalizing a simple hierarchy reference."""
        # Create a simple hierarchy reference
        hierarchy_tree = Tree('hierarchy_reference', [Token('IDENTIFIER', 'Product')])
        member_tree = Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        query_tree = Tree('query', [hierarchy_tree, member_tree])
        
        mappings = self.normalizer.normalize_hierarchies(query_tree)
        
        assert 'Product' in mappings
        mapping = mappings['Product']
        assert isinstance(mapping, HierarchyMapping)
        assert mapping.table_name == 'Product'
        assert mapping.hierarchy_name == 'Product'
    
    def test_infer_hierarchy_from_member_patterns(self):
        """Test inferring hierarchy from member name patterns."""
        test_cases = [
            ('Date.Year.2023', 'Date'),
            ('Product.Category.Bikes', 'Product'),
            ('Customer.Region.USA', 'Customer'),
            ('Geography.Country.Canada', 'Geography'),
            ('Random.Member.Name', 'DefaultHierarchy')
        ]
        
        for member_name, expected_hierarchy in test_cases:
            member_tree = Tree('member_reference', [Token('IDENTIFIER', member_name)])
            hierarchy = self.normalizer._infer_hierarchy_from_member(member_tree)
            assert hierarchy == expected_hierarchy
    
    def test_detect_redundant_levels(self):
        """Test detection of redundant level specifications."""
        # Create hierarchy with multiple levels
        level1_tree = Tree('level_reference', [Token('IDENTIFIER', 'Category')])
        level2_tree = Tree('level_reference', [Token('IDENTIFIER', 'Subcategory')])
        level3_tree = Tree('level_reference', [Token('IDENTIFIER', 'Product')])
        
        hierarchy_tree = Tree('hierarchy_reference', [
            Token('IDENTIFIER', 'Product'),
            level1_tree, level2_tree, level3_tree
        ])
        
        member_tree = Tree('member_reference', [Token('IDENTIFIER', 'Mountain Bike')])
        query_tree = Tree('query', [hierarchy_tree, member_tree])
        
        mappings = self.normalizer.normalize_hierarchies(query_tree)
        
        # The deepest level should be detected
        product_mapping = mappings.get('Product')
        if product_mapping:
            deepest = self.normalizer.get_deepest_level('Product')
            assert deepest is not None
    
    def test_identify_ragged_hierarchies(self):
        """Test identification of ragged (uneven) hierarchies."""
        # Create mapping with different path lengths
        mapping = HierarchyMapping(
            table_name='Geography',
            hierarchy_name='Geography',
            levels=['Country', 'State', 'City'],
            level_ordinals={'Country': 1, 'State': 2, 'City': 3},
            deepest_level='City',
            member_paths={
                'USA.California.Los Angeles': ['Country', 'State', 'City'],
                'Canada.Ontario': ['Country', 'State'],  # Missing city level
                'Mexico': ['Country']  # Missing state and city levels
            }
        )
        
        self.normalizer._hierarchy_mappings['Geography'] = mapping
        self.normalizer._identify_ragged_hierarchies()
        
        assert mapping.is_ragged
    
    def test_get_normalized_dimension(self):
        """Test getting normalized dimension specifications."""
        # Set up a hierarchy mapping
        mapping = HierarchyMapping(
            table_name='Product',
            hierarchy_name='Product Categories',
            levels=['Category', 'Subcategory', 'Product'],
            level_ordinals={'Category': 1, 'Subcategory': 2, 'Product': 3},
            deepest_level='Product'
        )
        self.normalizer._hierarchy_mappings['Product'] = mapping
        
        # Test with specific members
        dimension = self.normalizer.get_normalized_dimension(
            'Product', 'Category', ['Bikes', 'Accessories']
        )
        
        assert dimension is not None
        assert dimension.hierarchy.table == 'Product'
        assert dimension.hierarchy.name == 'Product Categories'
        assert dimension.level.name == 'Product'  # Should use deepest level
        assert dimension.members.selection_type == MemberSelectionType.SPECIFIC
        assert dimension.members.specific_members == ['Bikes', 'Accessories']
    
    def test_get_normalized_dimension_all_members(self):
        """Test normalized dimension with all members."""
        # Set up mapping
        mapping = HierarchyMapping(
            table_name='Date',
            hierarchy_name='Calendar',
            levels=['Year', 'Quarter', 'Month'],
            level_ordinals={'Year': 1, 'Quarter': 2, 'Month': 3},
            deepest_level='Month'
        )
        self.normalizer._hierarchy_mappings['Date'] = mapping
        
        # Test with no specific members
        dimension = self.normalizer.get_normalized_dimension('Date', 'Year', [])
        
        assert dimension is not None
        assert dimension.members.selection_type == MemberSelectionType.ALL
    
    def test_collect_hierarchy_references(self):
        """Test collecting hierarchy references from parse tree."""
        # Create tree with multiple hierarchy references
        hier1_tree = Tree('hierarchy_reference', [Token('IDENTIFIER', 'Product')])
        hier2_tree = Tree('dimension_reference', [Token('IDENTIFIER', 'Date')])
        member_tree = Tree('member_reference', [Token('IDENTIFIER', 'Sales.Amount')])
        
        query_tree = Tree('query', [hier1_tree, hier2_tree, member_tree])
        
        hierarchy_refs = self.normalizer._collect_hierarchy_references(query_tree)
        
        # Should find references for Product and Date hierarchies
        assert len(hierarchy_refs) >= 1
    
    def test_analyze_member_usage(self):
        """Test analyzing member usage patterns."""
        # Create tree with member references
        member1_tree = Tree('member_reference', [Token('IDENTIFIER', 'Product.Category.Bikes')])
        member2_tree = Tree('member_reference', [Token('IDENTIFIER', 'Date.Year.2023')])
        member3_tree = Tree('member_reference', [Token('IDENTIFIER', 'Product.Category.Accessories')])
        
        query_tree = Tree('query', [member1_tree, member2_tree, member3_tree])
        
        member_usage = self.normalizer._analyze_member_usage(query_tree)
        
        # Should group members by hierarchy
        assert 'Product' in member_usage
        assert 'Date' in member_usage
        assert len(member_usage['Product']) == 2  # Bikes and Accessories
        assert len(member_usage['Date']) == 1    # 2023
    
    def test_infer_levels_from_members(self):
        """Test inferring levels from member names."""
        test_cases = [
            (['2023', '2024'], {'Year'}),
            (['Q1 2023', 'Q2 2023'], {'Quarter'}),
            (['January', 'February'], {'Month'}),
            (['Category A', 'Category B'], {'Category'}),
            (['Sub A', 'Sub B'], {'All'}),  # Default when no patterns match
            (['Year 2023', 'Quarter Q1', 'Month Jan'], {'Year', 'Quarter', 'Month'})
        ]
        
        for members, expected_levels in test_cases:
            levels = self.normalizer._infer_levels_from_members(members)
            assert levels == expected_levels
    
    def test_determine_deepest_level(self):
        """Test determining the deepest level in a hierarchy."""
        # Test with ordinals
        levels = ['Year', 'Quarter', 'Month']
        ordinals = {'Year': 1, 'Quarter': 2, 'Month': 3}
        deepest = self.normalizer._determine_deepest_level(levels, ordinals, [])
        assert deepest == 'Month'
        
        # Test without ordinals (using heuristics)
        levels = ['Category', 'Product']
        ordinals = {}
        deepest = self.normalizer._determine_deepest_level(levels, ordinals, [])
        assert deepest == 'Product'  # Product is deeper than Category
    
    def test_build_member_path(self):
        """Test building hierarchical paths for members."""
        levels = ['Country', 'State', 'City']
        path = self.normalizer._build_member_path('Los Angeles', levels)
        
        assert isinstance(path, list)
        assert 'Los Angeles' in path
        assert len(path) == len(levels) + 1  # Levels + member
    
    def test_extract_hierarchy_name(self):
        """Test extracting hierarchy names from nodes."""
        # Test with direct token
        hierarchy_tree = Tree('hierarchy_reference', [Token('IDENTIFIER', 'Product')])
        name = self.normalizer._extract_hierarchy_name(hierarchy_tree)
        assert name == 'Product'
        
        # Test with identifier tree
        id_tree = Tree('identifier', [Token('VALUE', 'Date')])
        hierarchy_tree = Tree('hierarchy_reference', [id_tree])
        name = self.normalizer._extract_hierarchy_name(hierarchy_tree)
        assert name == 'Date'
    
    def test_extract_member_name(self):
        """Test extracting member names from nodes."""
        # Test with direct token
        member_tree = Tree('member_reference', [Token('IDENTIFIER', 'Bikes')])
        name = self.normalizer._extract_member_name(member_tree)
        assert name == 'Bikes'
        
        # Test with identifier tree
        id_tree = Tree('identifier', [Token('VALUE', 'Accessories')])
        member_tree = Tree('member_reference', [id_tree])
        name = self.normalizer._extract_member_name(member_tree)
        assert name == 'Accessories'
    
    def test_is_redundant_level(self):
        """Test checking if a level specification is redundant."""
        # Set up mapping
        mapping = HierarchyMapping(
            table_name='Product',
            hierarchy_name='Product',
            levels=['Category', 'Subcategory', 'Product'],
            level_ordinals={'Category': 1, 'Subcategory': 2, 'Product': 3},
            deepest_level='Product'
        )
        self.normalizer._hierarchy_mappings['Product'] = mapping
        
        # Category and Subcategory should be redundant since Product is deepest
        assert self.normalizer.is_redundant_level('Product', 'Category')
        assert self.normalizer.is_redundant_level('Product', 'Subcategory')
        assert not self.normalizer.is_redundant_level('Product', 'Product')
        
        # Non-existent hierarchy should return False
        assert not self.normalizer.is_redundant_level('NonExistent', 'Level')


class TestHierarchyMapping:
    """Test HierarchyMapping data class."""
    
    def test_hierarchy_mapping_creation(self):
        """Test creating hierarchy mapping."""
        mapping = HierarchyMapping(
            table_name='Product',
            hierarchy_name='Product Categories',
            levels=['Category', 'Subcategory', 'Product'],
            level_ordinals={'Category': 1, 'Subcategory': 2, 'Product': 3},
            deepest_level='Product'
        )
        
        assert mapping.table_name == 'Product'
        assert mapping.hierarchy_name == 'Product Categories'
        assert len(mapping.levels) == 3
        assert mapping.deepest_level == 'Product'
        assert not mapping.is_ragged  # Default value
        assert mapping.member_paths == {}  # Default value
    
    def test_hierarchy_mapping_with_member_paths(self):
        """Test hierarchy mapping with member paths."""
        member_paths = {
            'Bikes': ['Category', 'Bikes'],
            'Mountain Bikes': ['Category', 'Subcategory', 'Mountain Bikes']
        }
        
        mapping = HierarchyMapping(
            table_name='Product',
            hierarchy_name='Product',
            levels=['Category', 'Subcategory', 'Product'],
            level_ordinals={},
            deepest_level='Product',
            member_paths=member_paths
        )
        
        assert mapping.member_paths == member_paths
    
    def test_hierarchy_mapping_ragged_detection(self):
        """Test ragged hierarchy detection."""
        mapping = HierarchyMapping(
            table_name='Geography',
            hierarchy_name='Geography',
            levels=['Country', 'State', 'City'],
            level_ordinals={},
            deepest_level='City',
            is_ragged=True
        )
        
        assert mapping.is_ragged