"""
Test configuration and fixtures for OneCodePlant test suite.

This module provides shared fixtures and configuration for all tests,
including mock objects, temporary directories, and test plugins.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from onecode.cli import OneCodeCLI
from onecode.config import Config
from onecode.plugins.base_plugin import BasePlugin
from onecode.plugins.plugin_manager import PluginManager


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""
    
    def __init__(self, name: str = "test_plugin", version: str = "1.0.0"):
        super().__init__()
        self._name = name
        self._version = version
        self._description = "Test plugin for unit testing"
        self._author = "Test Suite"
    
    def initialize(self) -> bool:
        return True
    
    def get_commands(self) -> Dict[str, Any]:
        return {
            'test_cmd': lambda: "Test command executed"
        }


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=Config)
    config.ai.default_engine = "openai"
    config.ai.openai_api_key = "test-key"
    config.ai.openai_model = "gpt-4"
    config.ai.max_tokens = 1000
    config.ai.temperature = 0.1
    config.cli.default_dry_run = False
    config.cli.auto_execute = False
    config.cli.safety_checks = True
    return config


@pytest.fixture
def mock_plugin():
    """Create a mock plugin for testing."""
    return MockPlugin()


@pytest.fixture
def mock_plugin_registry(temp_dir):
    """Create a mock plugin registry file."""
    registry_data = {
        "test_plugin": {
            "source": "local",
            "path": str(temp_dir / "test_plugin"),
            "version": "1.0.0",
            "status": "installed"
        },
        "another_plugin": {
            "source": "pypi",
            "package": "onecode-another-plugin",
            "version": "2.0.0",
            "status": "installed"
        }
    }
    
    registry_file = temp_dir / "plugin_registry.json"
    with open(registry_file, 'w') as f:
        json.dump(registry_data, f, indent=2)
    
    return registry_file


@pytest.fixture
def mock_cli(mock_config):
    """Create a mock CLI instance for testing."""
    cli = Mock(spec=OneCodeCLI)
    cli.dry_run = False
    cli.plugins = {}
    cli.config = mock_config
    return cli


@pytest.fixture
def mock_ros_utils():
    """Create a mock ROS utilities object."""
    ros_utils = Mock()
    ros_utils.publish_message.return_value = {
        'success': True,
        'stdout': 'Message published successfully',
        'stderr': ''
    }
    ros_utils.echo_topic.return_value = {
        'success': True,
        'stdout': 'Topic data received',
        'stderr': ''
    }
    ros_utils.get_node_info.return_value = {
        'success': True,
        'stdout': 'Node information',
        'stderr': ''
    }
    return ros_utils


@pytest.fixture
def mock_nlp_processor():
    """Create a mock NLP processor for AI testing."""
    processor = Mock()
    
    # Mock successful parsing result
    mock_result = Mock()
    mock_result.success = True
    mock_result.commands = ["onecode sim launch gazebo"]
    mock_result.explanation = "Launch Gazebo simulation"
    mock_result.confidence = 0.95
    mock_result.warnings = []
    mock_result.errors = []
    
    processor.parse.return_value = mock_result
    processor.execute.return_value = {
        'executed': ['cmd_1'],
        'failed': [],
        'outputs': {'cmd_1': 'Command executed successfully'},
        'errors': {}
    }
    
    processor.get_engine_info.return_value = {
        'engine': 'openai',
        'model': 'gpt-4',
        'max_tokens': 1000,
        'temperature': 0.1,
        'safety_checks': True,
        'available_engines': ['openai', 'anthropic']
    }
    
    return processor


@pytest.fixture
def mock_env_checker():
    """Create a mock environment checker."""
    checker = Mock()
    checker.get_environment_summary.return_value = {
        'installation': {
            'installed': True,
            'distro': 'humble',
            'version': '2',
            'issues': []
        },
        'sourcing': {
            'sourced': True,
            'missing_vars': []
        },
        'commands': {
            'ros2': True,
            'ros2 node': True,
            'ros2 topic': True,
            'ros2 param': True
        },
        'ready': True,
        'warnings': [],
        'errors': []
    }
    
    checker.get_setup_instructions.return_value = [
        "ROS 2 environment is properly configured",
        "No additional setup required"
    ]
    
    return checker


@pytest.fixture
def mock_simulator_manager():
    """Create a mock simulator manager."""
    manager = Mock()
    manager.launch.return_value = {
        'success': True,
        'message': 'Simulator launched successfully'
    }
    manager.pause.return_value = {
        'success': True,
        'message': 'Simulator paused'
    }
    manager.resume.return_value = {
        'success': True,
        'message': 'Simulator resumed'
    }
    manager.shutdown.return_value = {
        'success': True,
        'message': 'Simulator shutdown'
    }
    manager.get_status.return_value = {
        'gazebo': 'running',
        'webots': 'stopped'
    }
    manager.list_simulators.return_value = {
        'gazebo': {'installed': True, 'version': '11.0'},
        'webots': {'installed': False, 'version': None}
    }
    return manager


@pytest.fixture
def mock_plugin_manager(temp_dir, mock_plugin_registry):
    """Create a mock plugin manager."""
    manager = Mock(spec=PluginManager)
    manager.registry_file = mock_plugin_registry
    
    manager.list_plugins.return_value = [
        {
            'name': 'test_plugin',
            'source': 'local',
            'status': 'installed',
            'version': '1.0.0',
            'path': str(temp_dir / 'test_plugin')
        }
    ]
    
    manager.install.return_value = {
        'name': 'new_plugin',
        'source_type': 'local',
        'status': 'success',
        'metadata': {'source': 'local', 'version': '1.0.0'}
    }
    
    manager.remove.return_value = {
        'name': 'test_plugin',
        'status': 'removed'
    }
    
    manager.get_plugin_info.return_value = {
        'source': 'local',
        'path': str(temp_dir / 'test_plugin'),
        'version': '1.0.0',
        'status': 'installed'
    }
    
    return manager


@pytest.fixture
def isolated_filesystem(temp_dir, monkeypatch):
    """Isolate filesystem operations to temporary directory."""
    # Change to temp directory for test isolation
    original_cwd = Path.cwd()
    monkeypatch.chdir(temp_dir)
    
    # Create basic directory structure
    (temp_dir / "onecode").mkdir()
    (temp_dir / "onecode" / "plugins").mkdir()
    
    yield temp_dir
    
    # Cleanup is handled by temp_dir fixture


@pytest.fixture(autouse=True)
def disable_real_external_calls(monkeypatch):
    """Disable real external API calls and system commands during testing."""
    # Mock subprocess calls
    mock_subprocess = Mock()
    mock_subprocess.run.return_value = Mock(
        returncode=0,
        stdout="Mock output",
        stderr="",
        check=True
    )
    monkeypatch.setattr("subprocess.run", mock_subprocess.run)
    
    # Mock requests for external APIs only if requests is available
    try:
        import requests
        mock_requests = Mock()
        mock_requests.post.return_value = Mock(
            status_code=200,
            json=lambda: {"choices": [{"message": {"content": "Mock response"}}]}
        )
        monkeypatch.setattr("requests.post", mock_requests.post)
    except ImportError:
        # requests not available, skip mocking
        pass


# Markers for different test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require external systems"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take significant time to run"
    )
    config.addinivalue_line(
        "markers", "requires_ros: Tests that require ROS 2 environment"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on location."""
    for item in items:
        # Add unit marker to all tests in unit/ directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to all tests in integration/ directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)