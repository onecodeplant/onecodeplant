# OneCodePlant Plugin Manager System

## Overview

The Plugin Manager System provides dynamic installation, removal, and management of OneCodePlant plugins from multiple sources including PyPI, GitHub repositories, and local directories.

## Features

- **Multi-source Installation**: Support for PyPI packages, GitHub repositories, and local directories
- **Plugin Registry**: Centralized tracking of installed plugins with metadata
- **Validation**: Plugin structure validation and compatibility checking
- **Conflict Resolution**: Duplicate installation prevention and version management
- **Comprehensive Logging**: Detailed operation logs for troubleshooting

## Usage

### List Installed Plugins
```bash
# Basic listing
onecode plugin list

# Detailed view with paths
onecode plugin list --detailed
```

### Install Plugins

#### From PyPI
```bash
onecode plugin install ros2-navigation-plugin
onecode plugin install onecode-mapping-tools
```

#### From GitHub
```bash
# Using shorthand
onecode plugin install robotics-team/awesome-plugin

# Using full URL
onecode plugin install https://github.com/user/ros2-helpers.git
```

#### From Local Directory
```bash
onecode plugin install ./my_custom_plugin
onecode plugin install /path/to/plugin
```

### Plugin Information
```bash
# Show detailed plugin info
onecode plugin info my-plugin

# Refresh plugin registry
onecode plugin refresh
```

### Remove Plugins
```bash
# With confirmation prompt
onecode plugin remove my-plugin

# Skip confirmation
onecode plugin remove my-plugin --yes
```

## Plugin Registry Format

The plugin registry (`onecode/plugin_registry.json`) tracks all installed plugins:

```json
{
  "plugin_name": {
    "source": "local|pypi|github",
    "path": "onecode/plugins/plugin_name",
    "version": "1.0.0",
    "status": "installed|missing"
  }
}
```

## Plugin Structure Validation

The system validates that plugins:
- Implement the BasePlugin interface
- Contain required metadata
- Have proper directory structure
- Include valid Python modules

## Error Handling

- **Installation Failures**: Detailed error messages with resolution suggestions
- **Missing Dependencies**: Automatic detection and reporting
- **Plugin Conflicts**: Prevention of duplicate installations
- **Validation Errors**: Clear feedback on plugin structure issues

## Logging

All plugin operations are logged to `~/.onecode/logs/plugin.log` for debugging and audit purposes.

## Security Considerations

- Source validation for GitHub repositories
- Package verification for PyPI installations
- Local path validation for security
- No automatic execution of untrusted code

## Integration with CLI

The plugin manager integrates seamlessly with the OneCodePlant CLI system, automatically updating the plugin loader registry and providing immediate access to newly installed plugins after CLI restart.