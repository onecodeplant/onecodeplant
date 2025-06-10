# OneCodePlant Phase 2.5: Simulator Control Support

## Overview

Phase 2.5 extends the OneCodePlant CLI framework with comprehensive simulator control support for Gazebo and Webots. This enhancement provides a unified interface for launching, controlling, and managing robot simulations through the existing middleware architecture.

## Features

### 🎮 Simulator Abstraction Layer

- **BaseSimulator**: Abstract interface defining common operations
- **GazeboSimulator**: Implementation for Gazebo Classic and Gazebo Garden/Harmonic
- **WebotsSimulator**: Implementation for Webots with ROS 2 bridge support
- **SimulatorManager**: Unified manager for handling multiple simulator types

### 🛠️ Supported Operations

| Operation | Gazebo | Webots | Description |
|-----------|--------|--------|-------------|
| `launch`  | ✅     | ✅     | Start simulation with custom worlds/launch files |
| `pause`   | ✅     | ✅     | Pause simulation execution |
| `resume`  | ✅     | ✅     | Resume paused simulation |
| `reset`   | ✅     | ✅     | Reset simulation to initial state |
| `shutdown`| ✅     | ✅     | Gracefully shutdown simulation |
| `status`  | ✅     | ✅     | Check installation and runtime status |
| `list`    | ✅     | ✅     | List all available simulators |

### ⚙️ Configuration Support

#### Custom Launch Files
```bash
# Use ROS 2 launch files
onecode sim launch gazebo --launch-file robot.launch.py
onecode sim launch webots --launch-file examples/webots_launch.py
```

#### Custom Worlds
```bash
# Load specific world files
onecode sim launch gazebo --world my_world.sdf
onecode sim launch webots --world robot_world.wbt
```

#### Simulation Modes
```bash
# Headless execution
onecode sim launch gazebo --headless
onecode sim launch webots --headless

# With robot models
onecode sim launch gazebo --robot-model turtlebot3_burger
```

## CLI Commands

### Basic Usage

```bash
# List available simulators
onecode sim list

# Check simulator status
onecode sim status gazebo
onecode sim status webots

# Launch simulators
onecode sim launch gazebo
onecode sim launch webots

# Control simulation
onecode sim pause gazebo
onecode sim resume gazebo
onecode sim reset gazebo
onecode sim shutdown gazebo
```

### Advanced Usage

```bash
# Launch with custom world
onecode sim launch gazebo --world examples/my_world.sdf --headless

# Launch with custom launch file
onecode sim launch webots --launch-file examples/webots_launch.py

# Launch with robot model
onecode sim launch gazebo --robot-model turtlebot3_waffle --world warehouse.sdf
```

## System Requirements

### Gazebo Requirements
- **Gazebo Garden/Harmonic**: `gz` command available in PATH
- **Gazebo Classic**: `gazebo` command available in PATH
- **ROS 2**: For launch file support and ROS integration

### Webots Requirements
- **Webots**: `webots` executable in PATH or common installation locations
- **ROS 2**: For bridge functionality and launch file support
- **webots_ros2_driver**: For ROS 2 integration (optional)

## Installation Detection

The system automatically detects installations by:

1. **Command availability**: Checking if executables are in PATH
2. **Version verification**: Testing command execution and version output
3. **Common paths**: Searching standard installation locations
4. **Dependency checks**: Verifying ROS 2 availability for bridge functionality

## Dry Run Support

All simulator operations support dry-run mode for testing and validation:

```bash
# Test operations without execution
onecode --dry-run sim launch gazebo --world test.sdf
onecode --dry-run sim pause webots
```

## Error Handling

### Installation Issues
- Clear error messages when simulators not found
- Specific guidance for installation requirements
- Fallback detection for different installation paths

### Runtime Issues
- Graceful handling of launch failures
- Process management and cleanup
- Timeout handling for long-running operations

### Validation
- World file existence checking
- Launch file validation
- Parameter validation and error reporting

## Integration with Phase 2 Middleware

### Logging Integration
- All operations logged to `.onecode/logs/cli.log`
- Structured logging with operation details
- Error tracking and debugging support

### ROS Utils Integration
- Leverages existing ROS 2 environment checking
- Consistent error handling patterns
- Unified command execution framework

### Environment Checking
- Integrated with existing environment validation
- Simulator-specific requirement checking
- Clear setup guidance for missing dependencies

## Example Files

### Gazebo Launch File (`examples/gazebo_launch.py`)
```python
def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='empty_world.sdf'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('robot_model', default_value='turtlebot3_burger'),
        # ... launch configuration
    ])
```

### Webots Launch File (`examples/webots_launch.py`)
```python
def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='worlds/empty.wbt'),
        DeclareLaunchArgument('mode', default_value='realtime'),
        # ... launch configuration
    ])
```

### Custom World File (`examples/my_world.sdf`)
```xml
<sdf version="1.6">
  <world name="my_world">
    <include><uri>model://ground_plane</uri></include>
    <include><uri>model://sun</uri></include>
    <!-- Custom world elements -->
  </world>
</sdf>
```

## Future Extensions

The simulator abstraction layer is designed for extensibility:

- **Plugin Support**: Easy addition of new simulator backends
- **Custom Controllers**: Support for simulator-specific control interfaces
- **Advanced Features**: Multi-robot scenarios, distributed simulations
- **Integration**: Deep integration with other OneCodePlant modules

## Architecture

```
onecode/
├── middleware/
│   └── simulators.py          # Phase 2.5 implementation
├── cli.py                     # Enhanced sim command group
└── examples/
    ├── gazebo_launch.py       # Example Gazebo launch
    ├── webots_launch.py       # Example Webots launch
    └── my_world.sdf          # Example world file
```

The Phase 2.5 implementation seamlessly integrates with the existing Phase 2 middleware layer, maintaining consistency with the established architecture while adding powerful new simulation capabilities.