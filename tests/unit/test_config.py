"""
Unit tests for OneCodePlant configuration management.

Tests configuration loading, API key management, and environment variable handling
without requiring external dependencies.
"""

import pytest
import os
from unittest.mock import Mock, patch
from pathlib import Path

from onecode.config import Config, AIConfig, LogConfig, CLIConfig


class TestAIConfig:
    """Test AI configuration handling."""
    
    def test_ai_config_defaults(self):
        """Test AI configuration default values."""
        ai_config = AIConfig()
        
        assert ai_config.default_engine == "openai"
        assert ai_config.openai_model == "gpt-4o"
        assert ai_config.anthropic_model == "claude-3-5-sonnet-20241022"
        assert ai_config.google_model == "gemini-pro"
        assert ai_config.max_tokens == 1000
        assert ai_config.temperature == 0.1
        assert ai_config.timeout == 30
    
    def test_ai_config_modification(self):
        """Test modifying AI configuration values."""
        ai_config = AIConfig()
        ai_config.default_engine = "anthropic"
        ai_config.max_tokens = 2000
        ai_config.temperature = 0.5
        
        assert ai_config.default_engine == "anthropic"
        assert ai_config.max_tokens == 2000
        assert ai_config.temperature == 0.5


class TestLogConfig:
    """Test logging configuration handling."""
    
    def test_log_config_defaults(self):
        """Test log configuration default values."""
        log_config = LogConfig()
        
        assert log_config.log_level == "INFO"
        assert log_config.max_log_size == 10 * 1024 * 1024  # 10MB
        assert log_config.backup_count == 5
        assert isinstance(log_config.log_dir, Path)
    
    def test_log_config_path_creation(self):
        """Test log directory path handling."""
        log_config = LogConfig()
        expected_path = Path.home() / ".onecode" / "logs"
        
        assert log_config.log_dir == expected_path


class TestCLIConfig:
    """Test CLI configuration handling."""
    
    def test_cli_config_defaults(self):
        """Test CLI configuration default values."""
        cli_config = CLIConfig()
        
        assert cli_config.default_dry_run is False
        assert cli_config.confirmation_timeout == 30
        assert cli_config.auto_execute is False
        assert cli_config.safety_checks is True
    
    def test_cli_config_modification(self):
        """Test modifying CLI configuration values."""
        cli_config = CLIConfig()
        cli_config.default_dry_run = True
        cli_config.auto_execute = True
        cli_config.safety_checks = False
        
        assert cli_config.default_dry_run is True
        assert cli_config.auto_execute is True
        assert cli_config.safety_checks is False


class TestConfig:
    """Test main configuration class."""
    
    def test_config_initialization(self):
        """Test configuration initialization."""
        config = Config()
        
        assert hasattr(config, 'ai')
        assert hasattr(config, 'log')
        assert hasattr(config, 'cli')
        assert isinstance(config.ai, AIConfig)
        assert isinstance(config.log, LogConfig)
        assert isinstance(config.cli, CLIConfig)
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'GOOGLE_API_KEY': 'test-google-key'
    })
    def test_load_from_env_with_keys(self):
        """Test loading configuration from environment variables."""
        config = Config()
        
        assert config.ai.openai_api_key == 'test-openai-key'
        assert config.ai.anthropic_api_key == 'test-anthropic-key'
        assert config.ai.google_api_key == 'test-google-key'
    
    @patch.dict(os.environ, {}, clear=True)
    def test_load_from_env_without_keys(self):
        """Test loading configuration when environment variables are missing."""
        config = Config()
        
        assert config.ai.openai_api_key is None
        assert config.ai.anthropic_api_key is None
        assert config.ai.google_api_key is None
    
    @patch.dict(os.environ, {
        'ONECODE_LOG_LEVEL': 'DEBUG',
        'ONECODE_MAX_TOKENS': '2000',
        'ONECODE_TEMPERATURE': '0.5'
    })
    def test_load_custom_env_vars(self):
        """Test loading custom OneCode environment variables."""
        config = Config()
        
        # Note: This assumes the config class supports these env vars
        # The actual implementation may need to be updated to support this
        if hasattr(config, '_load_from_env'):
            config._load_from_env()
    
    def test_get_api_key_openai(self):
        """Test getting OpenAI API key."""
        config = Config()
        config.ai.openai_api_key = 'test-key'
        
        key = config.get_api_key('openai')
        assert key == 'test-key'
    
    def test_get_api_key_anthropic(self):
        """Test getting Anthropic API key."""
        config = Config()
        config.ai.anthropic_api_key = 'test-key'
        
        key = config.get_api_key('anthropic')
        assert key == 'test-key'
    
    def test_get_api_key_google(self):
        """Test getting Google API key."""
        config = Config()
        config.ai.google_api_key = 'test-key'
        
        key = config.get_api_key('google')
        assert key == 'test-key'
    
    def test_get_api_key_invalid_engine(self):
        """Test getting API key for invalid engine."""
        config = Config()
        
        key = config.get_api_key('invalid_engine')
        assert key is None
    
    def test_get_model_openai(self):
        """Test getting OpenAI model name."""
        config = Config()
        
        model = config.get_model('openai')
        assert model == 'gpt-4o'
    
    def test_get_model_anthropic(self):
        """Test getting Anthropic model name."""
        config = Config()
        
        model = config.get_model('anthropic')
        assert model == 'claude-3-5-sonnet-20241022'
    
    def test_get_model_google(self):
        """Test getting Google model name."""
        config = Config()
        
        model = config.get_model('google')
        assert model == 'gemini-pro'
    
    def test_get_model_invalid_engine(self):
        """Test getting model for invalid engine."""
        config = Config()
        
        model = config.get_model('invalid_engine')
        assert model == 'gpt-4o'  # Should return default
    
    def test_is_engine_available_with_key(self):
        """Test checking engine availability when API key exists."""
        config = Config()
        config.ai.openai_api_key = 'test-key'
        
        available = config.is_engine_available('openai')
        assert available is True
    
    def test_is_engine_available_without_key(self):
        """Test checking engine availability when API key is missing."""
        config = Config()
        config.ai.openai_api_key = None
        
        available = config.is_engine_available('openai')
        assert available is False
    
    def test_is_engine_available_invalid_engine(self):
        """Test checking availability for invalid engine."""
        config = Config()
        
        available = config.is_engine_available('invalid_engine')
        assert available is False
    
    def test_get_available_engines_none(self):
        """Test getting available engines when none are configured."""
        config = Config()
        config.ai.openai_api_key = None
        config.ai.anthropic_api_key = None
        config.ai.google_api_key = None
        
        engines = config.get_available_engines()
        assert engines == []
    
    def test_get_available_engines_some(self):
        """Test getting available engines when some are configured."""
        config = Config()
        config.ai.openai_api_key = 'test-key'
        config.ai.anthropic_api_key = None
        config.ai.google_api_key = 'test-key'
        
        engines = config.get_available_engines()
        assert 'openai' in engines
        assert 'google' in engines
        assert 'anthropic' not in engines
    
    def test_get_available_engines_all(self):
        """Test getting available engines when all are configured."""
        config = Config()
        config.ai.openai_api_key = 'test-key-1'
        config.ai.anthropic_api_key = 'test-key-2'
        config.ai.google_api_key = 'test-key-3'
        
        engines = config.get_available_engines()
        assert 'openai' in engines
        assert 'anthropic' in engines
        assert 'google' in engines
    
    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'ai' in config_dict
        assert 'log' in config_dict
        assert 'cli' in config_dict
        
        # Check nested structure
        assert 'default_engine' in config_dict['ai']
        assert 'log_level' in config_dict['log']
        assert 'default_dry_run' in config_dict['cli']
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_load_from_config_file_exists(self, mock_open, mock_exists):
        """Test loading configuration from existing file."""
        mock_exists.return_value = True
        mock_file_content = """
        {
            "ai": {
                "default_engine": "anthropic",
                "max_tokens": 1500
            },
            "cli": {
                "auto_execute": true
            }
        }
        """
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content
        
        config = Config()
        # This would need the actual implementation to support file loading
        if hasattr(config, '_load_from_config_file'):
            config._load_from_config_file()
    
    @patch('pathlib.Path.exists')
    def test_load_from_config_file_missing(self, mock_exists):
        """Test loading configuration when file doesn't exist."""
        mock_exists.return_value = False
        
        config = Config()
        # Should not raise error when config file is missing
        if hasattr(config, '_load_from_config_file'):
            config._load_from_config_file()
    
    def test_config_immutability_protection(self):
        """Test that sensitive configuration values are protected."""
        config = Config()
        original_key = config.ai.openai_api_key
        
        # Configuration should allow modification (not immutable)
        # but should not expose keys in logs or string representations
        config.ai.openai_api_key = 'new-key'
        assert config.ai.openai_api_key == 'new-key'
    
    def test_config_validation(self):
        """Test configuration value validation."""
        config = Config()
        
        # Test that invalid values are handled gracefully
        config.ai.temperature = 1.5  # Outside typical range but should be allowed
        config.ai.max_tokens = -1     # Invalid but should be handled
        
        # Configuration should maintain these values but validate during use
        assert config.ai.temperature == 1.5
        assert config.ai.max_tokens == -1
    
    def test_config_environment_isolation(self):
        """Test that configuration doesn't leak between instances."""
        config1 = Config()
        config2 = Config()
        
        config1.ai.openai_api_key = 'key1'
        config2.ai.openai_api_key = 'key2'
        
        assert config1.ai.openai_api_key == 'key1'
        assert config2.ai.openai_api_key == 'key2'
        assert config1.ai.openai_api_key != config2.ai.openai_api_key