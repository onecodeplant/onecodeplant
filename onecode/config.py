"""
Configuration management for OneCodePlant.

This module handles configuration settings, API keys, and environment variables
for the OneCodePlant CLI tool, including AI engine integration.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AIConfig:
    """Configuration for AI engine integration."""
    default_engine: str = "openai"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    google_api_key: Optional[str] = None
    google_model: str = "gemini-pro"
    max_tokens: int = 1000
    temperature: float = 0.1
    timeout: int = 30


@dataclass
class LogConfig:
    """Configuration for logging."""
    log_level: str = "INFO"
    log_dir: Path = Path.home() / ".onecode" / "logs"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class CLIConfig:
    """Configuration for CLI behavior."""
    default_dry_run: bool = False
    confirmation_timeout: int = 30
    auto_execute: bool = False
    safety_checks: bool = True


class Config:
    """
    Main configuration class for OneCodePlant.
    
    Manages loading and accessing configuration from environment variables,
    config files, and default values.
    """
    
    def __init__(self):
        """Initialize configuration with default values."""
        self.ai = AIConfig()
        self.logging = LogConfig()
        self.cli = CLIConfig()
        self._load_from_env()
        self._load_from_config_file()
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # AI configuration
        self.ai.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.ai.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.ai.google_api_key = os.getenv('GOOGLE_API_KEY')
        
        # Model overrides
        if model := os.getenv('ONECODE_AI_MODEL'):
            if 'gpt' in model.lower():
                self.ai.openai_model = model
                self.ai.default_engine = "openai"
            elif 'claude' in model.lower():
                self.ai.anthropic_model = model
                self.ai.default_engine = "anthropic"
            elif 'gemini' in model.lower():
                self.ai.google_model = model
                self.ai.default_engine = "google"
        
        # Engine preference
        if engine := os.getenv('ONECODE_AI_ENGINE'):
            self.ai.default_engine = engine.lower()
        
        # AI parameters
        if temp := os.getenv('ONECODE_AI_TEMPERATURE'):
            try:
                self.ai.temperature = float(temp)
            except ValueError:
                pass
        
        if tokens := os.getenv('ONECODE_AI_MAX_TOKENS'):
            try:
                self.ai.max_tokens = int(tokens)
            except ValueError:
                pass
        
        # CLI configuration
        self.cli.default_dry_run = os.getenv('ONECODE_DRY_RUN', '').lower() == 'true'
        self.cli.auto_execute = os.getenv('ONECODE_AUTO_EXECUTE', '').lower() == 'true'
        self.cli.safety_checks = os.getenv('ONECODE_SAFETY_CHECKS', 'true').lower() == 'true'
        
        # Logging configuration
        if log_level := os.getenv('ONECODE_LOG_LEVEL'):
            self.logging.log_level = log_level.upper()
        
        if log_dir := os.getenv('ONECODE_LOG_DIR'):
            self.logging.log_dir = Path(log_dir)
    
    def _load_from_config_file(self) -> None:
        """Load configuration from config file if it exists."""
        config_paths = [
            Path.home() / ".onecode" / "config.ini",
            Path.cwd() / ".onecode.ini",
            Path.cwd() / "onecode.ini"
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    import configparser
                    parser = configparser.ConfigParser()
                    parser.read(config_path)
                    
                    # Load AI settings
                    if 'ai' in parser:
                        ai_section = parser['ai']
                        self.ai.default_engine = ai_section.get('default_engine', self.ai.default_engine)
                        self.ai.openai_model = ai_section.get('openai_model', self.ai.openai_model)
                        self.ai.anthropic_model = ai_section.get('anthropic_model', self.ai.anthropic_model)
                        self.ai.google_model = ai_section.get('google_model', self.ai.google_model)
                        
                        if temp := ai_section.get('temperature'):
                            self.ai.temperature = float(temp)
                        if tokens := ai_section.get('max_tokens'):
                            self.ai.max_tokens = int(tokens)
                    
                    # Load CLI settings
                    if 'cli' in parser:
                        cli_section = parser['cli']
                        self.cli.auto_execute = cli_section.getboolean('auto_execute', self.cli.auto_execute)
                        self.cli.safety_checks = cli_section.getboolean('safety_checks', self.cli.safety_checks)
                    
                    break
                except Exception:
                    # Ignore config file errors and continue with env/defaults
                    continue
    
    def get_api_key(self, engine: str) -> Optional[str]:
        """
        Get API key for the specified engine.
        
        Args:
            engine: Engine name (openai, anthropic, google)
            
        Returns:
            API key if available, None otherwise
        """
        if engine == "openai":
            return self.ai.openai_api_key
        elif engine == "anthropic":
            return self.ai.anthropic_api_key
        elif engine == "google":
            return self.ai.google_api_key
        return None
    
    def get_model(self, engine: str) -> str:
        """
        Get model name for the specified engine.
        
        Args:
            engine: Engine name (openai, anthropic, google)
            
        Returns:
            Model name for the engine
        """
        if engine == "openai":
            return self.ai.openai_model
        elif engine == "anthropic":
            return self.ai.anthropic_model
        elif engine == "google":
            return self.ai.google_model
        return "gpt-4o"  # Default fallback
    
    def is_engine_available(self, engine: str) -> bool:
        """
        Check if an AI engine is available (has API key).
        
        Args:
            engine: Engine name to check
            
        Returns:
            True if engine is available, False otherwise
        """
        return self.get_api_key(engine) is not None
    
    def get_available_engines(self) -> list[str]:
        """
        Get list of available AI engines.
        
        Returns:
            List of engine names that have API keys configured
        """
        engines = []
        for engine in ["openai", "anthropic", "google"]:
            if self.is_engine_available(engine):
                engines.append(engine)
        return engines
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            'ai': {
                'default_engine': self.ai.default_engine,
                'openai_model': self.ai.openai_model,
                'anthropic_model': self.ai.anthropic_model,
                'google_model': self.ai.google_model,
                'max_tokens': self.ai.max_tokens,
                'temperature': self.ai.temperature,
                'timeout': self.ai.timeout,
                'available_engines': self.get_available_engines()
            },
            'cli': {
                'default_dry_run': self.cli.default_dry_run,
                'auto_execute': self.cli.auto_execute,
                'safety_checks': self.cli.safety_checks,
                'confirmation_timeout': self.cli.confirmation_timeout
            },
            'logging': {
                'log_level': self.logging.log_level,
                'log_dir': str(self.logging.log_dir),
                'max_log_size': self.logging.max_log_size
            }
        }


# Global configuration instance
config = Config()