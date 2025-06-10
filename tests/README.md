# OneCodePlant Testing Framework

This directory contains comprehensive tests for the OneCodePlant CLI framework, ensuring robustness, modularity, and production readiness.

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── unit/                 # Unit tests for individual components
│   ├── test_cli_core.py      # CLI core functionality
│   ├── test_plugin_system.py # Plugin discovery and management
│   ├── test_middleware.py    # ROS utilities and environment checks
│   └── test_config.py        # Configuration management
├── integration/          # End-to-end integration tests
│   └── test_cli_integration.py # Complete CLI workflows
└── README.md            # This file
```

## Running Tests

### All Tests
```bash
# Run complete test suite
pytest

# Run with coverage
pytest --cov=onecode --cov-report=html
```

### Unit Tests Only
```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_cli_core.py

# Run with coverage
pytest tests/unit/ --cov=onecode --cov-report=term-missing
```

### Integration Tests Only
```bash
# Run all integration tests
pytest tests/integration/

# Run integration tests in dry-run mode (no ROS required)
pytest tests/integration/ --dry-run

# Run only tests that don't require ROS
pytest tests/integration/ -m "not requires_ros"
```

### Coverage Reporting
```bash
# Generate HTML coverage report
pytest --cov=onecode --cov-report=html

# View coverage in terminal
pytest --cov=onecode --cov-report=term-missing

# Generate coverage for specific modules
pytest --cov=onecode.cli --cov=onecode.plugins --cov-report=html
```

## Test Categories

### Unit Tests
- **CLI Core**: Command dispatch, argument parsing, plugin integration
- **Plugin System**: Plugin discovery, loading, registry management
- **Middleware**: ROS utilities, environment checks, logging, simulator management
- **Configuration**: Config loading, API key management, environment variables

### Integration Tests
- **CLI Integration**: End-to-end command workflows
- **Plugin Management**: Complete plugin installation and removal workflows
- **Simulator Control**: Full simulator lifecycle management
- **ROS Integration**: Complete ROS command workflows
- **AI Processing**: Natural language to CLI command conversion

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run only tests that require ROS (when available)
pytest -m requires_ros

# Run tests excluding ROS requirements
pytest -m "not requires_ros"
```

## Test Environment

### Dependencies
- `pytest`: Test framework
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Enhanced mocking capabilities

### Environment Variables
Tests automatically mock external dependencies and API calls. For testing with real services:

```bash
# Optional: Set API keys for AI testing
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

# Optional: Enable ROS testing
export ROS_DISTRO="humble"
```

### Isolation
- Tests run in isolated environments using temporary directories
- External API calls are automatically mocked
- No persistent state changes to the system
- Plugin registry operations use temporary files

## Writing Tests

### Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch
from onecode.cli import OneCodeCLI

def test_cli_initialization(mock_config):
    """Test CLI initialization with mocked dependencies."""
    with patch('onecode.cli.PluginLoader') as mock_loader:
        mock_loader.return_value.load_all_plugins.return_value = {}
        
        cli = OneCodeCLI(dry_run=False)
        
        assert cli.dry_run is False
        assert cli.plugins == {}
```

### Integration Test Example
```python
from click.testing import CliRunner
from onecode.cli import onecode

def test_complete_workflow():
    """Test complete CLI workflow."""
    runner = CliRunner()
    
    # Test command execution
    result = runner.invoke(onecode, ['--dry-run', 'sim', 'launch', 'gazebo'])
    
    assert result.exit_code == 0
    assert 'DRY RUN' in result.output
```

### Fixtures Usage
```python
def test_with_temp_plugin(mock_plugin_registry, temp_dir):
    """Test using shared fixtures."""
    # Use temporary directory and mock registry
    assert temp_dir.exists()
    assert mock_plugin_registry.exists()
```

## Coverage Goals

- **CLI Core**: 90%+ coverage
- **Plugin System**: 85%+ coverage  
- **Middleware**: 80%+ coverage
- **Configuration**: 85%+ coverage
- **Overall Project**: 80%+ coverage

## Continuous Integration

Tests run automatically on:
- Pull requests
- Main branch pushes
- Release preparations

CI configuration includes:
- Multiple Python versions
- Different operating systems
- Coverage reporting
- Dry-run mode for environments without ROS

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on external state
2. **Mocking**: Mock all external dependencies (ROS, APIs, file system operations)
3. **Clear Assertions**: Use descriptive assertion messages
4. **Test Data**: Use realistic but safe test data
5. **Error Cases**: Test both success and failure scenarios
6. **Performance**: Keep unit tests fast, mark slow tests appropriately

## Debugging Tests

```bash
# Run tests with verbose output
pytest -v

# Run single test with debug output
pytest -v -s tests/unit/test_cli_core.py::TestOneCodeCLI::test_cli_initialization

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s
```

## Contributing

When adding new features:
1. Write unit tests for core functionality
2. Add integration tests for user-facing workflows
3. Ensure all tests pass with `pytest`
4. Maintain or improve coverage percentage
5. Update this README if adding new test categories