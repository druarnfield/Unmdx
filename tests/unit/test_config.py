"""
Unit tests for the configuration system.

Tests the unified configuration classes and factory functions.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from unmdx.config import (
    UnMDXConfig, ParserConfig, LinterConfig, DAXConfig, ExplanationConfig,
    OptimizationLevel, ExplanationFormat, ExplanationDetail,
    create_default_config, create_fast_config, create_comprehensive_config,
    load_config_from_file, load_config_from_env
)
from unmdx.exceptions import ConfigurationError


class TestUnMDXConfig:
    """Test the main UnMDXConfig class."""
    
    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = UnMDXConfig()
        
        # Verify default values
        assert isinstance(config.parser, ParserConfig)
        assert isinstance(config.linter, LinterConfig)
        assert isinstance(config.dax, DAXConfig)
        assert isinstance(config.explanation, ExplanationConfig)
        
        assert config.debug == False
        assert config.verbose == False
        assert config.enable_caching == True
        assert config.cache_size_mb == 100
        assert config.parallel_processing == False
        assert config.max_workers == 4
    
    def test_validation_success(self):
        """Test successful configuration validation."""
        config = UnMDXConfig()
        
        # Should not raise any exception
        config.validate()
    
    def test_validation_invalid_cache_size(self):
        """Test validation failure for invalid cache size."""
        config = UnMDXConfig()
        config.cache_size_mb = -10
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "Invalid cache size" in str(exc_info.value)
    
    def test_validation_invalid_max_workers(self):
        """Test validation failure for invalid max workers."""
        config = UnMDXConfig()
        config.max_workers = 0
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "Invalid max workers" in str(exc_info.value)
    
    def test_validation_invalid_dax_indent_size(self):
        """Test validation failure for invalid DAX indent size."""
        config = UnMDXConfig()
        config.dax.indent_size = -1
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "Invalid DAX indent size" in str(exc_info.value)
    
    def test_validation_optimization_level_consistency(self):
        """Test validation of optimization level consistency."""
        config = UnMDXConfig()
        config.linter.optimization_level = OptimizationLevel.NONE
        # Keep some rules enabled - this should trigger validation error
        config.linter.remove_redundant_parentheses = True
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "optimization level is NONE" in str(exc_info.value)
    
    def test_to_dict_conversion(self):
        """Test conversion of config to dictionary."""
        config = UnMDXConfig()
        config.debug = True
        config.dax.format_output = False
        config.explanation.format = ExplanationFormat.JSON
        
        config_dict = config.to_dict()
        
        # Verify structure and values
        assert "parser" in config_dict
        assert "linter" in config_dict
        assert "dax" in config_dict
        assert "explanation" in config_dict
        assert "global" in config_dict
        
        assert config_dict["global"]["debug"] == True
        assert config_dict["dax"]["format_output"] == False
        assert config_dict["explanation"]["format"] == "json"
        assert config_dict["linter"]["optimization_level"] == "conservative"
    
    def test_from_dict_creation(self):
        """Test creation of config from dictionary."""
        config_dict = {
            "parser": {
                "strict_mode": True,
                "max_parse_errors": 5
            },
            "linter": {
                "optimization_level": "aggressive",
                "remove_redundant_parentheses": False
            },
            "dax": {
                "format_output": False,
                "indent_size": 2
            },
            "explanation": {
                "format": "markdown",
                "detail": "detailed"
            },
            "global": {
                "debug": True,
                "verbose": True
            }
        }
        
        config = UnMDXConfig.from_dict(config_dict)
        
        # Verify values were set correctly
        assert config.parser.strict_mode == True
        assert config.parser.max_parse_errors == 5
        assert config.linter.optimization_level == OptimizationLevel.AGGRESSIVE
        assert config.linter.remove_redundant_parentheses == False
        assert config.dax.format_output == False
        assert config.dax.indent_size == 2
        assert config.explanation.format == ExplanationFormat.MARKDOWN
        assert config.explanation.detail == ExplanationDetail.DETAILED
        assert config.debug == True
        assert config.verbose == True
    
    def test_from_dict_invalid_enum_value(self):
        """Test handling of invalid enum values in dictionary."""
        config_dict = {
            "linter": {
                "optimization_level": "invalid_level"
            }
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            UnMDXConfig.from_dict(config_dict)
        
        assert "Invalid configuration dictionary" in str(exc_info.value)
    
    def test_from_dict_partial_config(self):
        """Test creation from partial configuration dictionary."""
        config_dict = {
            "dax": {
                "format_output": False
            }
        }
        
        config = UnMDXConfig.from_dict(config_dict)
        
        # Verify only specified values changed, others remain default
        assert config.dax.format_output == False
        assert config.dax.indent_size == 4  # Default value
        assert config.parser.strict_mode == False  # Default value


class TestLinterConfig:
    """Test the LinterConfig class."""
    
    def test_default_initialization(self):
        """Test default linter configuration."""
        config = LinterConfig()
        
        assert config.optimization_level == OptimizationLevel.CONSERVATIVE
        assert config.remove_redundant_parentheses == True
        assert config.optimize_crossjoins == True
        assert config.remove_duplicates == True
        assert config.optimize_calculated_members == False
        assert config.simplify_function_calls == False
        assert config.max_crossjoin_depth == 3
    
    def test_moderate_optimization_level(self):
        """Test moderate optimization level defaults."""
        config = LinterConfig(optimization_level=OptimizationLevel.MODERATE)
        
        # Should enable additional rules
        assert config.optimize_calculated_members == True
        assert config.simplify_function_calls == True
    
    def test_aggressive_optimization_level(self):
        """Test aggressive optimization level defaults."""
        config = LinterConfig(optimization_level=OptimizationLevel.AGGRESSIVE)
        
        # Should enable all rules and increase limits
        assert config.optimize_calculated_members == True
        assert config.simplify_function_calls == True
        assert config.inline_simple_expressions == True
        assert config.max_crossjoin_depth == 5


class TestFactoryFunctions:
    """Test configuration factory functions."""
    
    def test_create_default_config(self):
        """Test default configuration factory."""
        config = create_default_config()
        
        assert isinstance(config, UnMDXConfig)
        assert config.linter.optimization_level == OptimizationLevel.CONSERVATIVE
        assert config.dax.format_output == True
        assert config.explanation.format == ExplanationFormat.SQL
    
    def test_create_fast_config(self):
        """Test fast configuration factory."""
        config = create_fast_config()
        
        assert isinstance(config, UnMDXConfig)
        assert config.linter.optimization_level == OptimizationLevel.NONE
        assert config.dax.format_output == False
        assert config.dax.generate_comments == False
        assert config.explanation.detail == ExplanationDetail.MINIMAL
        assert config.enable_caching == True
        assert config.parallel_processing == True
    
    def test_create_comprehensive_config(self):
        """Test comprehensive configuration factory."""
        config = create_comprehensive_config()
        
        assert isinstance(config, UnMDXConfig)
        assert config.linter.optimization_level == OptimizationLevel.AGGRESSIVE
        assert config.parser.strict_mode == True
        assert config.parser.validate_member_references == True
        assert config.dax.generate_measure_definitions == True
        assert config.dax.include_performance_hints == True
        assert config.explanation.detail == ExplanationDetail.DETAILED
        assert config.explanation.include_dax_comparison == True
        assert config.explanation.include_metadata == True


class TestConfigFileLoading:
    """Test configuration loading from files."""
    
    def test_load_config_from_valid_file(self):
        """Test loading configuration from valid JSON file."""
        config_data = {
            "parser": {
                "strict_mode": True
            },
            "dax": {
                "format_output": False,
                "indent_size": 2
            },
            "global": {
                "debug": True
            }
        }
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = load_config_from_file(temp_path)
            
            assert config.parser.strict_mode == True
            assert config.dax.format_output == False
            assert config.dax.indent_size == 2
            assert config.debug == True
            
        finally:
            os.unlink(temp_path)
    
    def test_load_config_from_nonexistent_file(self):
        """Test error handling for nonexistent config file."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config_from_file("/nonexistent/path/config.json")
        
        assert "Configuration file not found" in str(exc_info.value)
    
    def test_load_config_from_invalid_json(self):
        """Test error handling for invalid JSON file."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json")
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_file(temp_path)
            
            assert "Failed to load configuration" in str(exc_info.value)
            
        finally:
            os.unlink(temp_path)


class TestEnvironmentVariables:
    """Test configuration loading from environment variables."""
    
    def test_load_config_from_env_basic(self):
        """Test loading basic configuration from environment variables."""
        env_vars = {
            "UNMDX_DEBUG": "true",
            "UNMDX_VERBOSE": "false",
            "UNMDX_PARSER_STRICT_MODE": "1",
            "UNMDX_LINTER_OPTIMIZATION_LEVEL": "aggressive",
            "UNMDX_DAX_FORMAT_OUTPUT": "no",
            "UNMDX_EXPLANATION_FORMAT": "markdown",
            "UNMDX_EXPLANATION_DETAIL": "detailed"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = load_config_from_env()
            
            assert config.debug == True
            assert config.verbose == False
            assert config.parser.strict_mode == True
            assert config.linter.optimization_level == OptimizationLevel.AGGRESSIVE
            assert config.dax.format_output == False
            assert config.explanation.format == ExplanationFormat.MARKDOWN
            assert config.explanation.detail == ExplanationDetail.DETAILED
    
    def test_load_config_from_env_boolean_variations(self):
        """Test various boolean value formats in environment variables."""
        test_cases = [
            ("true", True),
            ("True", True), 
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
            ("anything_else", False)
        ]
        
        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"UNMDX_DEBUG": env_value}, clear=False):
                config = load_config_from_env()
                assert config.debug == expected, f"Failed for env_value: {env_value}"
    
    def test_load_config_from_env_invalid_enum(self):
        """Test error handling for invalid enum values in environment."""
        with patch.dict(os.environ, {"UNMDX_LINTER_OPTIMIZATION_LEVEL": "invalid"}, clear=False):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config_from_env()
            
            assert "Invalid environment variable" in str(exc_info.value)
    
    def test_load_config_from_env_no_variables(self):
        """Test loading from environment with no UnMDX variables set."""
        # Clear any existing UnMDX environment variables
        env_to_clear = {k: None for k in os.environ.keys() if k.startswith("UNMDX_")}
        
        with patch.dict(os.environ, env_to_clear, clear=False):
            config = load_config_from_env()
            
            # Should return default configuration
            assert config.debug == False
            assert config.linter.optimization_level == OptimizationLevel.CONSERVATIVE
            assert config.explanation.format == ExplanationFormat.SQL


class TestEnumClasses:
    """Test enum classes used in configuration."""
    
    def test_optimization_level_enum(self):
        """Test OptimizationLevel enum values."""
        assert OptimizationLevel.NONE.value == "none"
        assert OptimizationLevel.CONSERVATIVE.value == "conservative" 
        assert OptimizationLevel.MODERATE.value == "moderate"
        assert OptimizationLevel.AGGRESSIVE.value == "aggressive"
    
    def test_explanation_format_enum(self):
        """Test ExplanationFormat enum values."""
        assert ExplanationFormat.SQL.value == "sql"
        assert ExplanationFormat.NATURAL.value == "natural"
        assert ExplanationFormat.JSON.value == "json"
        assert ExplanationFormat.MARKDOWN.value == "markdown"
    
    def test_explanation_detail_enum(self):
        """Test ExplanationDetail enum values."""
        assert ExplanationDetail.MINIMAL.value == "minimal"
        assert ExplanationDetail.STANDARD.value == "standard"
        assert ExplanationDetail.DETAILED.value == "detailed"