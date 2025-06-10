# Developer Guide - OneCodePlant

This guide provides comprehensive information for developers working on OneCodePlant, including architecture details, development patterns, and advanced features.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Plugin System](#plugin-system)
- [Middleware Components](#middleware-components)
- [AI Integration](#ai-integration)
- [Testing Strategies](#testing-strategies)
- [Performance Considerations](#performance-considerations)
- [Security Guidelines](#security-guidelines)
- [Deployment and Packaging](#deployment-and-packaging)

## Architecture Overview

### Core Components

OneCodePlant follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │  AI Processing  │    │ Plugin System   │
│                 │    │                 │    │                 │
│ • Click Commands│    │ • NLP Engine    │    │ • Dynamic Load  │
│ • Argument Parse│    │ • Model Bridge  │    │ • Registration  │
│ • Help System   │    │ • Safety Check  │    │ • Lifecycle     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └─────────────┬─────────────────┬─────────────────┘
                       │                 │
                ┌─────────────────┐    ┌─────────────────┐
                │  Core Engine    │    │  Middleware     │
                │                 │    │                 │
                │ • Command Route │    │ • Logging       │
                │ • State Mgmt    │    │ • Validation    │
                │ • Config Mgmt   │    │ • Error Handle  │
                └─────────────────┘    └─────────────────┘
```

### Key Design Principles

1. **Plugin-First**: Core functionality is extensible through plugins
2. **Safety by Default**: Dry-run mode and validation prevent accidental operations
3. **Async-Ready**: Architecture supports future async operations
4. **Configuration Driven**: Behavior controlled through config files and environment
5. **Test-Friendly**: All components are mockable and testable

## Plugin System

### Plugin Architecture

```python
# onecode/plugins/base_plugin.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BasePlugin(ABC):
    """Base class for all OneCodePlant plugins."""
    
    def __init__(self):
        self._name: str = ""
        self._version: str = "1.0.0"
        self._description: str = ""
        self._dependencies: list = []
        self._config: Dict[str, Any] = {}
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
    
    @abstractmethod
    def get_commands(self) -> Dict[str, Any]:
        """Return dictionary of commands provided by this plugin."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            "name": self._name,
            "version": self._version,
            "description": self._description,
            "dependencies": self._dependencies
        }
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the plugin with provided settings."""
        self._config.update(config)
    
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
```

### Creating Custom Plugins

#### 1. Basic Plugin Structure

```python
# my_custom_plugin/plugin.py
from onecode.plugins.base_plugin import BasePlugin
from typing import Dict, Any
import click

class NavigationPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self._name = "navigation_plugin"
        self._version = "1.0.0"
        self._description = "Advanced navigation commands for ROS 2"
        self._dependencies = ["ros2", "nav2"]
    
    def initialize(self) -> bool:
        """Initialize navigation plugin."""
        # Check for required dependencies
        try:
            import nav2_msgs
            return True
        except ImportError:
            return False
    
    def get_commands(self) -> Dict[str, Any]:
        """Return navigation-specific commands."""
        return {
            'navigate': self.navigate_to_goal,
            'map': self.mapping_commands,
            'localize': self.localization_commands
        }
    
    @click.command()
    @click.option('--x', type=float, required=True, help='X coordinate')
    @click.option('--y', type=float, required=True, help='Y coordinate')
    @click.option('--frame', default='map', help='Reference frame')
    def navigate_to_goal(self, x: float, y: float, frame: str):
        """Navigate robot to specified goal coordinates."""
        goal_msg = self._create_navigation_goal(x, y, frame)
        return self._send_navigation_goal(goal_msg)
    
    def _create_navigation_goal(self, x: float, y: float, frame: str):
        """Create navigation goal message."""
        # Implementation details
        pass
    
    def _send_navigation_goal(self, goal):
        """Send goal to navigation stack."""
        # Implementation details
        pass

# Plugin entry point
def get_plugin():
    return NavigationPlugin()
```

#### 2. Plugin Configuration

```python
# my_custom_plugin/config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class NavigationConfig:
    default_planner: str = "NavfnPlanner"
    timeout: int = 30
    use_recovery: bool = True
    max_retries: int = 3
    
class NavigationPlugin(BasePlugin):
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure navigation plugin."""
        super().configure(config)
        nav_config = config.get('navigation', {})
        self.nav_config = NavigationConfig(**nav_config)
```

#### 3. Plugin Installation

```bash
# Install from local directory
onecode plugin install ./my_custom_plugin

# Install from GitHub
onecode plugin install user/navigation-plugin

# Install from PyPI
onecode plugin install onecode-navigation-plugin
```

### Plugin Manager Implementation

```python
# onecode/plugins/manager.py
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Optional

class PluginManager:
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_paths: List[Path] = []
        self._registry_file = Path.home() / ".onecode" / "plugin_registry.json"
    
    def discover_plugins(self) -> None:
        """Discover and load all available plugins."""
        # Load from standard locations
        plugin_dirs = [
            Path(__file__).parent / "builtin",
            Path.home() / ".onecode" / "plugins",
            Path.cwd() / "plugins"
        ]
        
        for plugin_dir in plugin_dirs:
            if plugin_dir.exists():
                self._load_plugins_from_directory(plugin_dir)
    
    def _load_plugins_from_directory(self, directory: Path) -> None:
        """Load plugins from a specific directory."""
        for plugin_path in directory.iterdir():
            if plugin_path.is_dir() and (plugin_path / "plugin.py").exists():
                self._load_plugin(plugin_path)
    
    def _load_plugin(self, plugin_path: Path) -> Optional[BasePlugin]:
        """Load a single plugin from path."""
        try:
            spec = importlib.util.spec_from_file_location(
                "plugin", plugin_path / "plugin.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, 'get_plugin'):
                plugin = module.get_plugin()
                if plugin.initialize():
                    self._plugins[plugin._name] = plugin
                    return plugin
        except Exception as e:
            print(f"Failed to load plugin from {plugin_path}: {e}")
        
        return None
```

## Middleware Components

### Logging Middleware

```python
# onecode/middleware/logging.py
import logging
import functools
from typing import Callable, Any

def log_command_execution(func: Callable) -> Callable:
    """Decorator to log command execution details."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('onecode_cli')
        logger.info(f"Executing command: {func.__name__}")
        logger.debug(f"Args: {args}, Kwargs: {kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"Command {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Command {func.__name__} failed: {str(e)}")
            raise
    
    return wrapper
```

### Validation Middleware

```python
# onecode/middleware/validation.py
from typing import Any, Dict, List
from dataclasses import dataclass

@dataclass
class ValidationRule:
    field: str
    validator: Callable[[Any], bool]
    error_message: str

class CommandValidator:
    def __init__(self):
        self._rules: Dict[str, List[ValidationRule]] = {}
    
    def add_rule(self, command: str, rule: ValidationRule):
        """Add validation rule for specific command."""
        if command not in self._rules:
            self._rules[command] = []
        self._rules[command].append(rule)
    
    def validate_command(self, command: str, params: Dict[str, Any]) -> List[str]:
        """Validate command parameters against registered rules."""
        errors = []
        
        if command in self._rules:
            for rule in self._rules[command]:
                if rule.field in params:
                    if not rule.validator(params[rule.field]):
                        errors.append(rule.error_message)
        
        return errors

# Usage example
validator = CommandValidator()
validator.add_rule(
    "pub",
    ValidationRule(
        field="topic",
        validator=lambda x: x.startswith('/'),
        error_message="Topic must start with '/'"
    )
)
```

### Safety Middleware

```python
# onecode/middleware/safety.py
import re
from typing import List, Pattern

class SafetyChecker:
    """Validates commands for potentially dangerous operations."""
    
    DANGEROUS_PATTERNS: List[Pattern] = [
        re.compile(r'rm\s+-rf\s+/'),  # Dangerous file deletion
        re.compile(r'sudo\s+.*'),      # Elevated privileges
        re.compile(r':\(\)\{.*\}'),    # Fork bombs
    ]
    
    ROS_DESTRUCTIVE_COMMANDS = [
        'ros2 lifecycle set',
        'ros2 param delete',
        'killall',
    ]
    
    def check_command_safety(self, command: str) -> tuple[bool, str]:
        """
        Check if command is safe to execute.
        
        Returns:
            tuple: (is_safe, warning_message)
        """
        # Check for dangerous shell patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(command):
                return False, f"Command contains dangerous pattern: {pattern.pattern}"
        
        # Check for destructive ROS commands
        for dangerous_cmd in self.ROS_DESTRUCTIVE_COMMANDS:
            if dangerous_cmd in command:
                return False, f"Command contains destructive operation: {dangerous_cmd}"
        
        return True, ""
```

## AI Integration

### Natural Language Processing Pipeline

```python
# onecode/ai/processor.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CommandSuggestion:
    command: str
    confidence: float
    explanation: str
    parameters: Dict[str, Any]

class NLPProcessor:
    def __init__(self, engine: str = "openai"):
        self.engine = engine
        self.model_config = self._load_model_config()
        self.command_templates = self._load_command_templates()
    
    def process_query(self, query: str) -> List[CommandSuggestion]:
        """
        Process natural language query and return command suggestions.
        
        Args:
            query: Natural language input from user
            
        Returns:
            List of command suggestions with confidence scores
        """
        # Preprocessing
        normalized_query = self._normalize_query(query)
        intent = self._extract_intent(normalized_query)
        entities = self._extract_entities(normalized_query)
        
        # Command generation
        suggestions = self._generate_commands(intent, entities, normalized_query)
        
        # Post-processing and validation
        validated_suggestions = self._validate_suggestions(suggestions)
        
        return validated_suggestions
    
    def _normalize_query(self, query: str) -> str:
        """Normalize and clean user input."""
        # Remove extra whitespace, convert to lowercase, etc.
        return query.strip().lower()
    
    def _extract_intent(self, query: str) -> str:
        """Extract user intent from query."""
        intent_patterns = {
            'launch': ['launch', 'start', 'run', 'begin'],
            'stop': ['stop', 'shutdown', 'kill', 'end'],
            'publish': ['publish', 'send', 'emit'],
            'echo': ['listen', 'monitor', 'watch', 'echo'],
            'navigate': ['go to', 'navigate', 'move to'],
        }
        
        for intent, keywords in intent_patterns.items():
            if any(keyword in query for keyword in keywords):
                return intent
        
        return 'unknown'
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities like topics, coordinates, etc."""
        entities = {}
        
        # Extract topic names (words starting with /)
        topic_pattern = r'/\w+'
        topics = re.findall(topic_pattern, query)
        if topics:
            entities['topics'] = topics
        
        # Extract coordinates
        coord_pattern = r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)'
        coords = re.findall(coord_pattern, query)
        if coords:
            entities['coordinates'] = coords
        
        return entities
```

### AI Safety and Validation

```python
# onecode/ai/safety.py
class AISafetyValidator:
    """Validates AI-generated commands for safety and correctness."""
    
    def __init__(self):
        self.safety_checker = SafetyChecker()
        self.command_validator = CommandValidator()
    
    def validate_ai_command(self, command: str, context: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate AI-generated command for safety and correctness.
        
        Args:
            command: Generated command string
            context: Context information about the request
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Safety check
        is_safe, safety_msg = self.safety_checker.check_command_safety(command)
        if not is_safe:
            return False, f"Safety violation: {safety_msg}"
        
        # Syntax validation
        if not self._validate_command_syntax(command):
            return False, "Invalid command syntax"
        
        # Context validation
        if not self._validate_command_context(command, context):
            return False, "Command doesn't match context"
        
        return True, ""
    
    def _validate_command_syntax(self, command: str) -> bool:
        """Validate command syntax."""
        # Check if command starts with known CLI commands
        valid_prefixes = ['onecode', 'ros2', 'python']
        return any(command.startswith(prefix) for prefix in valid_prefixes)
    
    def _validate_command_context(self, command: str, context: Dict[str, Any]) -> bool:
        """Validate command against provided context."""
        # Ensure command matches the intended operation
        return True  # Simplified implementation
```

## Testing Strategies

### Unit Testing Patterns

```python
# tests/unit/test_plugin_manager.py
import pytest
from unittest.mock import Mock, patch
from onecode.plugins.manager import PluginManager
from onecode.plugins.base_plugin import BasePlugin

class TestPluginManager:
    
    @pytest.fixture
    def plugin_manager(self):
        return PluginManager()
    
    @pytest.fixture
    def mock_plugin(self):
        plugin = Mock(spec=BasePlugin)
        plugin._name = "test_plugin"
        plugin.initialize.return_value = True
        return plugin
    
    def test_plugin_loading(self, plugin_manager, mock_plugin):
        """Test successful plugin loading."""
        with patch.object(plugin_manager, '_load_plugin', return_value=mock_plugin):
            plugin_manager._load_plugins_from_directory(Path("/fake/path"))
            assert "test_plugin" in plugin_manager._plugins
    
    def test_plugin_initialization_failure(self, plugin_manager):
        """Test handling of plugin initialization failure."""
        failing_plugin = Mock(spec=BasePlugin)
        failing_plugin.initialize.return_value = False
        
        with patch.object(plugin_manager, '_load_plugin', return_value=None):
            plugin_manager._load_plugins_from_directory(Path("/fake/path"))
            assert len(plugin_manager._plugins) == 0
```

### Integration Testing

```python
# tests/integration/test_cli_commands.py
import subprocess
import pytest
from pathlib import Path

class TestCLIIntegration:
    
    def test_cli_help_command(self):
        """Test CLI help command works."""
        result = subprocess.run(
            ["python", "-m", "onecode.cli", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "OneCodePlant" in result.stdout
    
    def test_plugin_list_command(self):
        """Test plugin listing functionality."""
        result = subprocess.run(
            ["python", "-m", "onecode.cli", "plugins"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Loaded plugins:" in result.stdout
    
    @pytest.mark.requires_ros
    def test_ros_environment_check(self):
        """Test ROS environment validation."""
        result = subprocess.run(
            ["python", "-m", "onecode.cli", "env"],
            capture_output=True,
            text=True
        )
        # Should work regardless of ROS installation
        assert result.returncode == 0
```

### Performance Testing

```python
# tests/performance/test_startup_time.py
import time
import subprocess
import pytest

class TestPerformance:
    
    def test_cli_startup_time(self):
        """Test CLI startup performance."""
        start_time = time.time()
        
        result = subprocess.run(
            ["python", "-m", "onecode.cli", "--version"],
            capture_output=True
        )
        
        end_time = time.time()
        startup_time = end_time - start_time
        
        assert result.returncode == 0
        assert startup_time < 2.0  # Should start within 2 seconds
    
    def test_plugin_loading_performance(self):
        """Test plugin loading performance."""
        start_time = time.time()
        
        result = subprocess.run(
            ["python", "-m", "onecode.cli", "plugins"],
            capture_output=True
        )
        
        end_time = time.time()
        loading_time = end_time - start_time
        
        assert result.returncode == 0
        assert loading_time < 5.0  # Should load plugins within 5 seconds
```

## Performance Considerations

### Lazy Loading Strategy

```python
# onecode/core/lazy_loader.py
from typing import Any, Callable, Optional

class LazyLoader:
    """Lazy loading utility for expensive operations."""
    
    def __init__(self, loader: Callable[[], Any]):
        self._loader = loader
        self._value: Optional[Any] = None
        self._loaded = False
    
    def __call__(self) -> Any:
        if not self._loaded:
            self._value = self._loader()
            self._loaded = True
        return self._value
    
    def reset(self):
        """Reset the loader to reload on next access."""
        self._loaded = False
        self._value = None

# Usage in plugin system
class PluginManager:
    def __init__(self):
        self._plugins = {}
        self._lazy_loaders = {}
    
    def register_lazy_plugin(self, name: str, loader: Callable):
        """Register a plugin with lazy loading."""
        self._lazy_loaders[name] = LazyLoader(loader)
    
    def get_plugin(self, name: str):
        """Get plugin with lazy loading."""
        if name in self._lazy_loaders:
            return self._lazy_loaders[name]()
        return self._plugins.get(name)
```

### Caching Strategy

```python
# onecode/core/cache.py
import time
from typing import Any, Optional, Callable
from functools import wraps

class TTLCache:
    """Time-to-live cache implementation."""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            if time.time() - self._timestamps[key] < self.ttl:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        self._cache[key] = value
        self._timestamps[key] = time.time()

def cached(ttl: int = 300):
    """Decorator for caching function results."""
    cache = TTLCache(ttl)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            result = cache.get(key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        return wrapper
    return decorator
```

## Security Guidelines

### Input Validation

```python
# onecode/security/validation.py
import re
from typing import List, Pattern

class SecurityValidator:
    """Security validation for user inputs."""
    
    # Patterns for potentially dangerous inputs
    INJECTION_PATTERNS: List[Pattern] = [
        re.compile(r'[;&|`$\(\)]'),  # Shell metacharacters
        re.compile(r'\.\.\/'),       # Path traversal
        re.compile(r'<script'),      # XSS (if web interface added)
    ]
    
    @classmethod
    def validate_topic_name(cls, topic: str) -> bool:
        """Validate ROS topic name format."""
        if not topic.startswith('/'):
            return False
        
        # Topic names should only contain alphanumeric, underscore, dash
        pattern = re.compile(r'^/[a-zA-Z0-9_/-]+$')
        return bool(pattern.match(topic))
    
    @classmethod
    def validate_node_name(cls, node: str) -> bool:
        """Validate ROS node name format."""
        if node.startswith('/'):
            node = node[1:]  # Remove leading slash
        
        pattern = re.compile(r'^[a-zA-Z0-9_]+$')
        return bool(pattern.match(node))
    
    @classmethod
    def check_for_injection(cls, input_str: str) -> bool:
        """Check input for potential injection attacks."""
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(input_str):
                return True
        return False
```

### API Key Management

```python
# onecode/security/secrets.py
import os
from typing import Optional
from cryptography.fernet import Fernet

class SecretManager:
    """Secure management of API keys and secrets."""
    
    def __init__(self):
        self.key_file = Path.home() / ".onecode" / ".key"
        self.secrets_file = Path.home() / ".onecode" / ".secrets"
        self._encryption_key = self._get_or_create_key()
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            self.key_file.parent.mkdir(exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            return key
    
    def store_secret(self, name: str, value: str) -> None:
        """Store encrypted secret."""
        fernet = Fernet(self._encryption_key)
        encrypted_value = fernet.encrypt(value.encode())
        
        # Store in encrypted format
        secrets = self._load_secrets()
        secrets[name] = encrypted_value.decode()
        self._save_secrets(secrets)
    
    def get_secret(self, name: str) -> Optional[str]:
        """Retrieve and decrypt secret."""
        secrets = self._load_secrets()
        if name not in secrets:
            # Fallback to environment variable
            return os.getenv(name)
        
        fernet = Fernet(self._encryption_key)
        encrypted_value = secrets[name].encode()
        return fernet.decrypt(encrypted_value).decode()
```

## Deployment and Packaging

### Distribution Configuration

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "onecode-plant"
dynamic = ["version"]
description = "AI-enhanced CLI tool for robotics development"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "OneCodePlant Team", email = "info@onecodeplant.com"}]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.11"
dependencies = [
    "click>=8.2.1",
    "psutil>=7.0.0",
]

[project.optional-dependencies]
ai = [
    "anthropic>=0.52.2",
    "openai>=1.84.0",
]
dev = [
    "pytest>=8.4.0",
    "pytest-cov>=6.1.1",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
]

[project.scripts]
onecode = "onecode.cli:main"

[project.urls]
Homepage = "https://github.com/onecodeplant/onecode-plant"
Repository = "https://github.com/onecodeplant/onecode-plant"
Documentation = "https://docs.onecodeplant.com"
"Bug Tracker" = "https://github.com/onecodeplant/onecode-plant/issues"

[tool.setuptools.dynamic]
version = {attr = "onecode.__version__"}

[tool.setuptools.packages.find]
where = ["."]
include = ["onecode*"]
exclude = ["tests*"]
```

### Continuous Integration

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    
    - name: Run tests
      run: |
        pytest --cov=onecode --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

This comprehensive developer guide provides the foundation for understanding and extending OneCodePlant's architecture, implementing new features, and maintaining code quality standards.