# AI-Powered Command Examples for OneCodePlant

This document provides comprehensive examples of using OneCodePlant's AI features to convert natural language instructions into executable CLI commands. The AI system supports multiple providers (OpenAI, Anthropic, Google) and includes safety validation.

## Setup Requirements

Before using AI features, configure at least one API key:

```bash
# OpenAI (GPT models)
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic (Claude models)
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google AI (Gemini models)
export GOOGLE_API_KEY="your-google-api-key"
```

## Basic AI Command Usage

### Simple Command Generation

```bash
# Basic AI query
onecode ai "launch gazebo simulator"
# Output: onecode sim launch gazebo

# Move robot forward
onecode ai "move robot forward at 1 meter per second"
# Output: onecode pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 1.0}}'

# Check system status
onecode ai "check if ROS is working properly"
# Output: onecode env
```

### AI with Different Engines

```bash
# Use specific AI engine
onecode ai --engine openai "start navigation system"
onecode ai --engine anthropic "publish hello message"
onecode ai --engine google "list all active nodes"
```

### Interactive AI Mode

```bash
# Start interactive session
onecode ai --interactive

# In interactive mode:
> launch turtlebot3 in gazebo
> move robot in a circle
> stop all movement
> exit
```

## Simulation and Robot Control

### Launching Simulations

```bash
# Launch basic simulation
onecode ai "start gazebo with empty world"
# Output: onecode sim launch gazebo --world empty.world

# Launch with specific robot
onecode ai "launch gazebo with turtlebot3 burger robot"
# Output: onecode sim launch gazebo --robot-model turtlebot3_burger

# Launch specific world
onecode ai "start gazebo simulation with house world"
# Output: onecode sim launch gazebo --world house.world

# Headless simulation
onecode ai "launch gazebo without graphics for testing"
# Output: onecode sim launch gazebo --headless
```

### Robot Movement Commands

```bash
# Basic movement
onecode ai "move robot forward"
# Output: onecode pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 0.5}}'

# Precise movement
onecode ai "move robot forward at 2 meters per second"
# Output: onecode pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 2.0}}'

# Rotation
onecode ai "rotate robot clockwise"
# Output: onecode pub /cmd_vel geometry_msgs/Twist --data '{"angular": {"z": -0.5}}'

# Complex movement
onecode ai "move robot forward and turn left simultaneously"
# Output: onecode pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 0.5}, "angular": {"z": 0.3}}'

# Stop movement
onecode ai "stop robot movement immediately"
# Output: onecode pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 0.0}, "angular": {"z": 0.0}}'
```

### Navigation Commands

```bash
# Start navigation
onecode ai "begin autonomous navigation"
# Output: onecode pub /goal_pose geometry_msgs/PoseStamped --data '{"pose": {"position": {"x": 0.0, "y": 0.0}}}'

# Go to specific location
onecode ai "navigate to coordinates 3,4"
# Output: onecode pub /goal_pose geometry_msgs/PoseStamped --data '{"pose": {"position": {"x": 3.0, "y": 4.0}}}'

# Start mapping
onecode ai "start creating a map of the environment"
# Output: onecode pub /start_mapping std_msgs/Bool --data '{"data": true}'
```

## ROS System Management

### Node Operations

```bash
# List nodes
onecode ai "show me all running ROS nodes"
# Output: onecode node --list

# Get node information
onecode ai "get details about the navigation node"
# Output: onecode node --info /navigation

# Kill specific node
onecode ai "stop the camera node"
# Output: onecode node --kill /camera_node
```

### Topic Operations

```bash
# List topics
onecode ai "show all available topics"
# Output: onecode echo --list-topics

# Monitor sensor data
onecode ai "listen to laser scan data"
# Output: onecode echo /scan

# Monitor specific number of messages
onecode ai "show me 5 odometry messages"
# Output: onecode echo /odom --count 5

# Publish custom message
onecode ai "publish hello world to chatter topic"
# Output: onecode pub /chatter std_msgs/String --data '{"data": "hello world"}'
```

### Parameter Management

```bash
# List parameters
onecode ai "show all system parameters"
# Output: onecode param list

# Get specific parameter
onecode ai "get the maximum velocity parameter"
# Output: onecode param get /robot_controller max_velocity

# Set parameter value
onecode ai "set robot speed limit to 1.5"
# Output: onecode param set /robot_controller max_velocity 1.5
```

## Sensor Data and Monitoring

### Sensor Data Access

```bash
# Camera data
onecode ai "show camera feed"
# Output: onecode echo /camera/image_raw

# Lidar data
onecode ai "monitor lidar readings"
# Output: onecode echo /scan --count 10

# IMU data
onecode ai "check robot orientation from IMU"
# Output: onecode echo /imu/data

# GPS data
onecode ai "get current GPS position"
# Output: onecode echo /gps/fix
```

### System Diagnostics

```bash
# General health check
onecode ai "check if everything is working properly"
# Output: onecode env

# Battery status
onecode ai "check robot battery level"
# Output: onecode echo /battery_state

# System performance
onecode ai "monitor system CPU and memory usage"
# Output: onecode echo /diagnostics
```

## Advanced AI Features

### Showing Reasoning

```bash
# Show AI reasoning process
onecode ai --show-reasoning "create a navigation launch file"
# Output includes explanation of command generation process

# Auto-execute with reasoning
onecode ai --auto-execute --show-reasoning "start basic robot movement"
# Executes command after showing reasoning
```

### Complex Workflows

```bash
# Multi-step operations
onecode ai "set up complete navigation system"
# Output: Multiple commands for launching navigation stack

# Batch operations
onecode ai "prepare robot for autonomous mission"
# Output: Series of initialization commands

# Safety checks
onecode ai "perform pre-flight safety checks"
# Output: Commands to verify all systems
```

### Context-Aware Commands

```bash
# Environment-specific commands
onecode ai "launch appropriate simulator for indoor navigation"
# Considers available simulators and chooses best option

# Robot-specific commands
onecode ai "configure settings for turtlebot3"
# Adapts commands based on robot type

# Task-specific commands
onecode ai "set up for SLAM mapping mission"
# Configures appropriate parameters and launches required nodes
```

## AI Safety and Validation

### Safety Features

```bash
# Safe command validation
onecode ai "delete all files"  # Will be rejected for safety

# Dry-run mode
onecode --dry-run ai "restart all ROS nodes"
# Shows what would be executed without running

# Command confirmation
onecode ai "shutdown robot systems"
# Prompts for confirmation before executing
```

### Error Handling

```bash
# Invalid requests
onecode ai "make coffee"
# AI will respond that this is not a robotics command

# Ambiguous requests
onecode ai "start something"
# AI will ask for clarification

# Unsafe requests
onecode ai "override safety limits"
# AI will reject and explain safety concerns
```

## Plugin-Specific AI Commands

### Navigation Plugin

```bash
onecode ai "start SLAM navigation"
# Output: Plugin-specific navigation commands

onecode ai "save current map as kitchen_map"
# Output: onecode navigation save-map kitchen_map
```

### Manipulation Plugin

```bash
onecode ai "move robot arm to home position"
# Output: onecode manipulation move-arm --position home

onecode ai "grasp the red object"
# Output: onecode manipulation grasp --target red_object
```

### Vision Plugin

```bash
onecode ai "detect people in camera feed"
# Output: onecode vision detect --type person --topic /camera/image_raw

onecode ai "start object tracking"
# Output: onecode vision track --enable
```

## Best Practices for AI Commands

### Effective Prompting

**Good Examples:**
- "launch gazebo with turtlebot3 robot"
- "move robot forward at 0.5 m/s"
- "monitor laser scan for 10 messages"
- "set maximum velocity to 2.0"

**Less Effective Examples:**
- "do something with the robot"
- "start stuff"
- "make it go"
- "fix the problem"

### Specific vs. General Commands

```bash
# Specific (Better)
onecode ai "publish twist message to cmd_vel with linear x velocity 1.0"

# General (Less precise)
onecode ai "make robot move"
```

### Context Provision

```bash
# With context
onecode ai "for indoor navigation, launch appropriate simulator"

# Without context
onecode ai "launch simulator"
```

## Troubleshooting AI Commands

### Common Issues

1. **No API Key Configured**
   ```bash
   Error: No AI engine available. Please configure API keys.
   Solution: Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY
   ```

2. **Ambiguous Request**
   ```bash
   AI Response: "Could you be more specific about which simulator to launch?"
   Solution: Provide more detailed instructions
   ```

3. **Safety Rejection**
   ```bash
   AI Response: "This command could be unsafe. Please use dry-run mode first."
   Solution: Use --dry-run flag to test
   ```

### Getting Help

```bash
# Show AI help
onecode ai --help

# Check available engines
onecode ai --engine list

# Interactive help
onecode ai --interactive
> help
```

## API Configuration Examples

### Multiple Engine Setup

```bash
# ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."

# Set preferred engine
export ONECODE_AI_ENGINE="anthropic"
```

### Configuration File

```json
// ~/.onecode/config.json
{
  "ai": {
    "default_engine": "openai",
    "openai_model": "gpt-4",
    "anthropic_model": "claude-3-sonnet",
    "google_model": "gemini-pro",
    "max_tokens": 1000,
    "temperature": 0.1,
    "auto_execute": false,
    "show_reasoning": true
  }
}
```

## Advanced Use Cases

### Research and Development

```bash
# Experimental commands
onecode ai "test new navigation algorithm with safety constraints"

# Performance analysis
onecode ai "benchmark robot movement for 30 seconds"

# Data collection
onecode ai "record sensor data for machine learning training"
```

### Production Deployment

```bash
# System initialization
onecode ai "initialize production robot for warehouse operation"

# Mission execution
onecode ai "execute delivery mission to station B"

# Monitoring
onecode ai "set up continuous health monitoring"
```

### Educational Use

```bash
# Learning exercises
onecode ai "demonstrate basic robot movement patterns"

# Explanation mode
onecode ai --show-reasoning "explain how to control robot velocity"

# Safe experimentation
onecode --dry-run ai "try advanced navigation features"
```

This comprehensive guide covers the full range of AI-powered command generation capabilities in OneCodePlant, from basic usage to advanced workflows and troubleshooting.