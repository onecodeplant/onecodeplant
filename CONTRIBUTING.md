# Contributing to OneCodePlant

Thank you for your interest in contributing to OneCodePlant! This document provides guidelines and instructions for setting up your development environment and contributing to the project.

## Code of Conduct

This project and everyone participating in it is governed by the [OneCodePlant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Submitting Changes](#submitting-changes)

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Basic understanding of ROS 2 concepts (helpful but not required)
- Familiarity with CLI development and the Click framework

### Quick Setup

1. **Fork the repository** on GitHub.

2. **Clone your fork locally:**

   ```bash
   git clone https://github.com/YOUR_USERNAME/onecode-plant.git
   cd onecode-plant
   ```

3. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies:**

   ```bash
   pip install -e .[dev]
   ```

5. **Verify your installation:**

   ```bash
   onecode --help
   pytest
   ```

## Development Setup

### Environment Configuration

1. **Set up development environment variables:**

   ```bash
   export ONECODE_DEV_MODE=true
   export ONECODE_LOG_LEVEL=DEBUG
   ```

2. **Configure pre-commit hooks** (optional but recommended):

   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **IDE Setup:**

   - **VS Code**: Install the Python extension and configure your settings.
   - **PyCharm**: Configure the Python interpreter to use the virtual environment.

### Development Mode

Run OneCodePlant in development mode with enhanced debugging:

```bash
# Enable dry-run mode for safe testing
onecode --dry-run --verbose <command>

# Test without a ROS 2 environment
export ONECODE_SKIP_ROS_CHECK=true
onecode env
```

## Project Structure

```text
onecode-plant/
├── onecode/                 # Main package
│   ├── __init__.py         # Package initialization
│   ├── cli.py             # Main CLI entry point
│   ├── config.py          # Configuration management
│   ├── ai/                # AI integration modules
│   ├── middleware/        # Middleware components
│   └── plugins/           # Plugin system
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── conftest.py       # Test configuration
├── examples/             # Example usage and plugins
├── docs/                # Documentation
├── pyproject.toml       # Project configuration
└── README.md           # Project overview
```

## Development Workflow

### Branching Strategy

- `main`: Stable release branch
- `develop`: Integration branch for features
- `feature/feature-name`: Individual feature branches
- `bugfix/issue-description`: Bug fix branches

### Making Changes

1. **Create a Feature Branch:**

   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make Changes:**

   - Write clean, well-documented code.
   - Follow existing code style and patterns.
   - Add tests for new functionality.

3. **Test Changes:**

   ```bash
   # Run all tests
   pytest

   # Run specific test categories
   pytest tests/unit/
   pytest tests/integration/

   # Test with coverage
   pytest --cov=onecode --cov-report=html
   ```

4. **Commit Changes:**

   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

### Commit Message Format

Use the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format:

```text
type(scope): description

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples:**

```text
feat(ai): add support for Claude-3 models
fix(cli): resolve plugin loading issue on Windows
docs: update installation instructions
test(plugins): add unit tests for plugin manager
```

## Testing

### Test Categories

1. **Unit Tests** (`tests/unit/`):

   - Test individual functions and classes.
   - Mock external dependencies.
   - Fast execution.

2. **Integration Tests** (`tests/integration/`):

   - Test component interactions.
   - May require external systems.
   - Slower execution.

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_cli.py

# Test with coverage
pytest --cov=onecode --cov-report=term-missing

# Test in dry-run mode (no external dependencies)
pytest --dry-run
```

### Writing Tests

```python
# tests/unit/test_example.py
import pytest
from onecode.cli import OneCodeCLI

def test_cli_initialization():
    """Test CLI initialization with default settings."""
    cli = OneCodeCLI(dry_run=True)
    assert cli.dry_run is True

@pytest.mark.integration
def test_plugin_loading():
    """Test plugin loading functionality."""
    # Integration test example
    pass

@pytest.mark.requires_ros
def test_ros_commands():
    """Test ROS command functionality."""
    # Test requiring ROS environment
    pass
```

## Code Quality

### Code Style

- Follow PEP 8 guidelines.
- Use Black for code formatting.
- Use isort for import sorting.
- Use type hints where appropriate.

```bash
# Format code
black onecode/ tests/

# Sort imports
isort onecode/ tests/

# Check style
flake8 onecode/ tests/

# Type checking
mypy onecode/
```

### Documentation

- Write clear docstrings for all public functions and classes.
- Update `README.md` for user-facing changes.
- Add inline comments for complex logic.
- Update type hints.

```python
from typing import Any, Dict

def process_command(command: str, options: Dict[str, Any]) -> None:
    """
    Process a CLI command with the given options.

    Args:
        command: The command string to process.
        options: A dictionary of command options.

    Raises:
        ValueError: If the command format is invalid.
    """
    pass
```

## Submitting Changes

### Pull Request Process

1. **Ensure Quality:**

   - All tests pass.
   - Code follows style guidelines.
   - Documentation is updated.
   - No merge conflicts.

2. **Create a Pull Request:**

   - Use a descriptive title.
   - Fill out the PR template.
   - Link to related issues.
   - Add reviewers.

3. **Address Feedback:**

   - Respond to code review comments.
   - Make the requested changes.
   - Update tests if needed.

### Pull Request Template

```markdown
## Description

Brief description of the changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] All tests pass
```


### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_cli.py

# Test with coverage
pytest --cov=onecode --cov-report=term-missing

# Test in dry-run mode (no external dependencies)
pytest --dry-run
```

### Writing Tests

```python
# tests/unit/test_example.py
import pytest
from onecode.cli import OneCodeCLI

def test_cli_initialization():
    """Test CLI initialization with default settings."""
    cli = OneCodeCLI(dry_run=True)
    assert cli.dry_run is True

@pytest.mark.integration
def test_plugin_loading():
    """Test plugin loading functionality."""
    # Integration test example
    pass

@pytest.mark.requires_ros
def test_ros_commands():
    """Test ROS command functionality."""
    # Test requiring ROS environment
    pass
```

## Code Quality

### Code Style

- Follow PEP 8 guidelines.
- Use Black for code formatting.
- Use isort for import sorting.
- Use type hints where appropriate.

```bash
# Format code
black onecode/ tests/

# Sort imports
isort onecode/ tests/

# Check style
flake8 onecode/ tests/

# Type checking
mypy onecode/
```

### Documentation

- Write clear docstrings for all public functions and classes.
- Update `README.md` for user-facing changes.
- Add inline comments for complex logic.
- Update type hints.

```python
from typing import Any, Dict

def process_command(command: str, options: Dict[str, Any]) -> None:
    """
    Process a CLI command with the given options.

    Args:
        command: The command string to process.
        options: A dictionary of command options.

    Raises:
        ValueError: If the command format is invalid.
    """
    pass
```

## Submitting Changes

### Pull Request Process

1. **Ensure Quality:**
   - All tests pass.
   - Code follows style guidelines.
   - Documentation is updated.
   - No merge conflicts.

2. **Create a Pull Request:**
   - Use a descriptive title.
   - Fill out the PR template.
   - Link to related issues.
   - Add reviewers.

3. **Address Feedback:**
   - Respond to code review comments.
   - Make the requested changes.
   - Update tests if needed.

### Pull Request Template

```markdown
## Description

Brief description of the changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] All tests pass
```
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers learn
- Focus on the code, not the person

### Getting Help

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Documentation**: Check existing documentation first
- **Community**: Join community discussions and contribute to solutions

### Reporting Issues

When reporting bugs:

1. Use the issue template
2. Provide clear reproduction steps
3. Include system information
4. Add relevant logs or error messages
5. Suggest potential solutions if you have ideas

### Suggesting Features

When suggesting features:

1. Check existing issues and discussions
2. Describe the use case clearly
3. Explain the expected behavior
4. Consider implementation complexity
5. Be open to alternative solutions

## Development Tips

### Plugin Development

```python
# Create custom plugin
from onecode.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self._name = "my_plugin"
        self._version = "1.0.0"
    
    def initialize(self) -> bool:
        return True
    
    def get_commands(self) -> Dict[str, Any]:
        return {"my_command": self.execute_command}
```

### Debugging

```bash
# Enable debug logging
export ONECODE_LOG_LEVEL=DEBUG
onecode --verbose <command>

# Use dry-run mode for safe testing
onecode --dry-run <command>

# Test without external dependencies
export ONECODE_SKIP_ROS_CHECK=true
```

### Performance Testing

```bash
# Profile CLI startup time
time onecode --help

# Memory usage testing
python -m memory_profiler onecode/cli.py

# Load testing for plugins
pytest tests/performance/ -v
```

## Release Process

For maintainers only:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release tag
4. Build and upload to PyPI
5. Update documentation

Thank you for contributing to OneCodePlant! Your efforts help make robotics development more accessible and efficient for everyone.