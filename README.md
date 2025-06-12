# OneCodePlant

### A modular AI-enhanced CLI tool for robotics development

OneCodePlant simplifies ROS 2 workflows and robotics development through an extensible plugin architecture, natural language AI integration, and comprehensive simulator management.

<!-- TODO: Add your project's badges here -->

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Installation](#installation)
  - [Basic Usage](#basic-usage)
- [Core Commands](#core-commands)
- [Configuration](#configuration)
- [Supported Systems](#supported-systems)
- [Plugin Development](#plugin-development)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- **AI-Powered Commands**: Convert natural language to CLI commands using OpenAI, Anthropic, or Google AI.
- **Plugin System**: Extensible architecture with dynamic plugin installation from PyPI, GitHub, or local sources.
- **ROS 2 Integration**: Seamless publishing, echoing, parameter management, and node control.
- **Simulator Management**: Launch and control Gazebo, Webots, and other robotics simulators.
- **Environment Validation**: Automatic ROS 2 environment checking and setup guidance.
- **Dry-Run Mode**: Test commands safely without executing actual operations.

## Quick Start

### Installation

```bash


# Install development version from source
# git clone <your-repo-url>
cd onecode-plant
pip install -e .[dev]
```

### Basic Usage

```bash
# Check help and available commands
onecode --help

# Verify ROS 2 environment
onecode env

# List available plugins
onecode plugins

# Launch Gazebo simulator
onecode sim launch gazebo

# Publish ROS message
onecode pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 1.0}}'

# Use AI to generate commands
onecode ai "launch gazebo with turtlebot3 robot"
```

## Core Commands

*Details for `sim`, `ros`, `plugin`, and `ai` commands...*

## Configuration

*Details on environment variables and config file...*

## Supported Systems

*Details on supported ROS 2 distributions, simulators, and AI providers...*

## Plugin Development

*Details on how to create and install custom plugins...*

## Development

### Setup Development Environment

1. **Clone the repository:**

   ```bash
   git clone https://github.com/onecodeplant/onecode-plant.git
   cd onecode-plant
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in editable mode with development dependencies:**

   ```bash
   pip install -e .[dev]
   ```

### Running Tests

- **Run all tests:**

  ```bash
  pytest
  ```

- **Run unit tests only:**

  ```bash
  pytest tests/unit/
  ```

- **Run integration tests:**

  ```bash
  pytest tests/integration/
  ```

- **Run tests with coverage:**

  ```bash
  pytest --cov=onecode --cov-report=html
  ```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more details on how to get started. All contributors are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md).

### Quick Contribution Steps

1. **Fork the repository.**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes and add tests.**
4. **Ensure all tests pass:** `pytest`
5. **Submit a pull request.**

## Documentation

- [Developer Guide](DEV_GUIDE.md) - Detailed development information
- [Plugin Development](docs/plugin_development.md) - Creating custom plugins
- [AI Integration](docs/ai_engine_integration.md) - Natural language features
- [Simulator Control](docs/simulator_control.md) - Managing simulators
- [Testing Framework](docs/testing_framework_overview.md) - Test development

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/onecodeplant/onecode-plant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/onecodeplant/onecode-plant/discussions)
- **Documentation**: [docs.onecodeplant.com](https://docs.onecodeplant.com)

## Roadmap

- [ ] Visual plugin manager interface
- [ ] ROS 1 compatibility layer
- [ ] Docker containerization
- [ ] Web dashboard for remote control
- [ ] Advanced AI model fine-tuning
- [ ] Cloud deployment automation

---

**Made with ❤️ for the robotics community**
