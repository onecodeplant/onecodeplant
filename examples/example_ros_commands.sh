#!/bin/bash

# OneCodePlant CLI - Example ROS Commands
# This script demonstrates common ROS 2 operations using the OneCodePlant CLI
# 
# Usage: ./example_ros_commands.sh [mode]
# Modes: basic, navigation, simulation, monitoring, all
#
# Requirements:
# - OneCodePlant CLI installed
# - ROS 2 environment properly configured
# - Appropriate ROS packages for specific examples

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ROBOT_MODEL="turtlebot3_burger"
WORLD_FILE="turtlebot3_world"
SIMULATION_TIME=30
DRY_RUN=${DRY_RUN:-false}

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_onecode() {
    if ! command -v onecode &> /dev/null; then
        log_error "OneCodePlant CLI not found. Please install it first."
        echo "Installation: pip install onecode-plant"
        exit 1
    fi
    log_success "OneCodePlant CLI found"
}

check_ros_environment() {
    log_info "Checking ROS 2 environment..."
    if $DRY_RUN; then
        onecode --dry-run env
    else
        onecode env
    fi
}

# Basic ROS Operations
demo_basic_operations() {
    log_info "=== Basic ROS Operations Demo ==="
    
    # Check environment
    log_info "Checking ROS environment status..."
    check_ros_environment
    
    # List available plugins
    log_info "Listing available OneCodePlant plugins..."
    onecode plugins
    
    # Node management examples
    log_info "Node management operations..."
    
    if $DRY_RUN; then
        log_info "DRY RUN: Would list all active nodes"
        onecode --dry-run node --list
    else
        onecode node --list
    fi
    
    # Topic operations
    log_info "Topic operations..."
    
    # Example: Publishing velocity commands
    log_info "Publishing velocity command to /cmd_vel..."
    if $DRY_RUN; then
        onecode --dry-run pub /cmd_vel geometry_msgs/Twist \
            --data '{"linear": {"x": 0.5, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.2}}'
    else
        onecode pub /cmd_vel geometry_msgs/Twist \
            --data '{"linear": {"x": 0.5, "y": 0.0, "z": 0.0}, "angular": {"x": 0.0, "y": 0.0, "z": 0.2}}' \
            --count 1
    fi
    
    # Example: Publishing string message
    log_info "Publishing string message to /chatter..."
    if $DRY_RUN; then
        onecode --dry-run pub /chatter std_msgs/String \
            --data '{"data": "Hello from OneCodePlant!"}'
    else
        onecode pub /chatter std_msgs/String \
            --data '{"data": "Hello from OneCodePlant!"}' \
            --count 1
    fi
    
    # Parameter management
    log_info "Parameter management operations..."
    
    if $DRY_RUN; then
        log_info "DRY RUN: Would list all parameters"
        onecode --dry-run param list
    else
        onecode param list
    fi
    
    log_success "Basic operations demo completed"
}

# Navigation and Movement
demo_navigation() {
    log_info "=== Navigation Demo ==="
    
    # Movement commands
    log_info "Robot movement commands..."
    
    # Move forward
    log_info "Moving robot forward..."
    if $DRY_RUN; then
        onecode --dry-run pub /cmd_vel geometry_msgs/Twist \
            --data '{"linear": {"x": 1.0}}' --rate 2 --count 10
    else
        onecode pub /cmd_vel geometry_msgs/Twist \
            --data '{"linear": {"x": 1.0}}' --rate 2 --count 10 &
        MOVE_PID=$!
        sleep 5
        kill $MOVE_PID 2>/dev/null || true
    fi
    
    # Rotate
    log_info "Rotating robot..."
    if $DRY_RUN; then
        onecode --dry-run pub /cmd_vel geometry_msgs/Twist \
            --data '{"angular": {"z": 0.5}}' --rate 2 --count 10
    else
        onecode pub /cmd_vel geometry_msgs/Twist \
            --data '{"angular": {"z": 0.5}}' --rate 2 --count 10 &
        ROTATE_PID=$!
        sleep 3
        kill $ROTATE_PID 2>/dev/null || true
    fi
    
    # Stop robot
    log_info "Stopping robot..."
    if $DRY_RUN; then
        onecode --dry-run pub /cmd_vel geometry_msgs/Twist \
            --data '{"linear": {"x": 0.0}, "angular": {"z": 0.0}}'
    else
        onecode pub /cmd_vel geometry_msgs/Twist \
            --data '{"linear": {"x": 0.0}, "angular": {"z": 0.0}}' --count 1
    fi
    
    log_success "Navigation demo completed"
}

# Simulation Management
demo_simulation() {
    log_info "=== Simulation Management Demo ==="
    
    # Check available simulators
    log_info "Listing available simulators..."
    onecode sim list
    
    # Launch Gazebo simulation
    log_info "Launching Gazebo simulation..."
    if $DRY_RUN; then
        onecode --dry-run sim launch gazebo --robot-model $ROBOT_MODEL --world $WORLD_FILE
    else
        # Launch in background for demo
        log_warning "This would launch Gazebo. In production, run without background."
        # onecode sim launch gazebo --robot-model $ROBOT_MODEL --world $WORLD_FILE &
        # GAZEBO_PID=$!
        # sleep 10
    fi
    
    # Check simulation status
    log_info "Checking simulation status..."
    if $DRY_RUN; then
        onecode --dry-run sim status gazebo
    else
        onecode sim status gazebo
    fi
    
    # Simulation control examples
    if ! $DRY_RUN; then
        # Only if simulation is actually running
        log_info "Simulation control examples..."
        
        # Pause simulation
        log_info "Pausing simulation..."
        # onecode sim pause gazebo
        
        # Resume simulation
        log_info "Resuming simulation..."
        # onecode sim resume gazebo
        
        # Reset simulation
        log_info "Resetting simulation..."
        # onecode sim reset gazebo
        
        # Shutdown simulation
        log_info "Shutting down simulation..."
        # kill $GAZEBO_PID 2>/dev/null || true
        # onecode sim shutdown gazebo
    fi
    
    log_success "Simulation demo completed"
}

# Monitoring and Diagnostics
demo_monitoring() {
    log_info "=== Monitoring and Diagnostics Demo ==="
    
    # Monitor topics
    log_info "Monitoring robot topics..."
    
    # Echo odometry data
    log_info "Monitoring odometry (5 messages)..."
    if $DRY_RUN; then
        onecode --dry-run echo /odom --count 5
    else
        onecode echo /odom --count 5 --timeout 10 || log_warning "Odometry topic not available"
    fi
    
    # Echo laser scan data
    log_info "Monitoring laser scan (3 messages)..."
    if $DRY_RUN; then
        onecode --dry-run echo /scan --count 3
    else
        onecode echo /scan --count 3 --timeout 10 || log_warning "Laser scan topic not available"
    fi
    
    # Echo joint states
    log_info "Monitoring joint states (2 messages)..."
    if $DRY_RUN; then
        onecode --dry-run echo /joint_states --count 2
    else
        onecode echo /joint_states --count 2 --timeout 10 || log_warning "Joint states topic not available"
    fi
    
    # Parameter monitoring
    log_info "Monitoring system parameters..."
    if $DRY_RUN; then
        onecode --dry-run param list
    else
        onecode param list | head -20  # Show first 20 parameters
    fi
    
    log_success "Monitoring demo completed"
}

# AI-Powered Commands Demo
demo_ai_commands() {
    log_info "=== AI-Powered Commands Demo ==="
    
    # Check if AI functionality is available
    log_info "Checking AI engine availability..."
    
    if [[ -z "$OPENAI_API_KEY" && -z "$ANTHROPIC_API_KEY" && -z "$GOOGLE_API_KEY" ]]; then
        log_warning "No AI API keys found. AI commands will not work."
        log_info "To use AI features, set one of these environment variables:"
        log_info "  export OPENAI_API_KEY='your-openai-key'"
        log_info "  export ANTHROPIC_API_KEY='your-anthropic-key'"
        log_info "  export GOOGLE_API_KEY='your-google-key'"
        return
    fi
    
    # Example AI commands (dry-run only for safety)
    log_info "Example AI command conversions..."
    
    echo "Natural language: 'Launch gazebo with turtlebot3 robot'"
    if $DRY_RUN; then
        onecode --dry-run ai "launch gazebo with turtlebot3 robot"
    else
        onecode ai "launch gazebo with turtlebot3 robot" --show-reasoning
    fi
    
    echo ""
    echo "Natural language: 'move robot forward at 0.5 m/s'"
    if $DRY_RUN; then
        onecode --dry-run ai "move robot forward at 0.5 m/s"
    else
        onecode ai "move robot forward at 0.5 m/s" --show-reasoning
    fi
    
    echo ""
    echo "Natural language: 'check robot battery level'"
    if $DRY_RUN; then
        onecode --dry-run ai "check robot battery level"
    else
        onecode ai "check robot battery level" --show-reasoning
    fi
    
    log_success "AI commands demo completed"
}

# Batch Operations
demo_batch_operations() {
    log_info "=== Batch Operations Demo ==="
    
    # Create a temporary script for batch operations
    BATCH_SCRIPT="/tmp/onecode_batch_demo.sh"
    
    cat > $BATCH_SCRIPT << 'EOF'
#!/bin/bash
# Batch ROS operations script

echo "Starting batch operations..."

# Initialize system
onecode env

# Start simulation (in dry-run mode)
echo "Setting up simulation environment..."
onecode --dry-run sim launch gazebo --robot-model turtlebot3_burger

# Wait for simulation to start
sleep 5

# Execute navigation sequence
echo "Executing navigation sequence..."
onecode --dry-run pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 0.5}}' --count 5
sleep 2
onecode --dry-run pub /cmd_vel geometry_msgs/Twist --data '{"angular": {"z": 0.5}}' --count 5
sleep 2
onecode --dry-run pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 0.0}, "angular": {"z": 0.0}}' --count 1

# Monitor system
echo "Monitoring system status..."
onecode --dry-run node --list
onecode --dry-run param list | head -10

echo "Batch operations completed"
EOF

    chmod +x $BATCH_SCRIPT
    
    log_info "Executing batch operations script..."
    if $DRY_RUN; then
        log_info "Would execute: $BATCH_SCRIPT"
        cat $BATCH_SCRIPT
    else
        $BATCH_SCRIPT
    fi
    
    # Cleanup
    rm -f $BATCH_SCRIPT
    
    log_success "Batch operations demo completed"
}

# Plugin Development Demo
demo_plugin_development() {
    log_info "=== Plugin Development Demo ==="
    
    # Show plugin installation process
    log_info "Plugin installation examples..."
    
    # Install example plugin
    log_info "Installing example plugin..."
    if $DRY_RUN; then
        onecode --dry-run plugin install ./examples/example_plugin
    else
        # onecode plugin install ./examples/example_plugin
        log_info "Would install example plugin from local directory"
    fi
    
    # List installed plugins
    log_info "Listing installed plugins..."
    onecode plugin list
    
    # Show plugin information
    log_info "Plugin information examples..."
    onecode plugins
    
    # Plugin management operations
    log_info "Plugin management operations..."
    if $DRY_RUN; then
        onecode --dry-run plugin refresh
    else
        onecode plugin refresh
    fi
    
    log_success "Plugin development demo completed"
}

# Error Handling Demo
demo_error_handling() {
    log_info "=== Error Handling Demo ==="
    
    # Demonstrate graceful error handling
    log_info "Testing error handling with invalid commands..."
    
    # Invalid topic name
    log_info "Testing invalid topic name..."
    onecode --dry-run pub invalid_topic_name std_msgs/String --data '{"data": "test"}' || log_info "Expected error handled gracefully"
    
    # Invalid message type
    log_info "Testing invalid message type..."
    onecode --dry-run pub /test_topic InvalidMessageType --data '{"data": "test"}' || log_info "Expected error handled gracefully"
    
    # Invalid JSON data
    log_info "Testing invalid JSON data..."
    onecode --dry-run pub /test_topic std_msgs/String --data 'invalid json' || log_info "Expected error handled gracefully"
    
    log_success "Error handling demo completed"
}

# Main execution function
main() {
    local mode=${1:-"all"}
    
    log_info "OneCodePlant CLI - ROS Commands Demo"
    log_info "Mode: $mode"
    
    if $DRY_RUN; then
        log_warning "Running in DRY-RUN mode - no actual operations will be performed"
    fi
    
    # Initial setup
    check_onecode
    
    case $mode in
        "basic")
            demo_basic_operations
            ;;
        "navigation")
            demo_navigation
            ;;
        "simulation")
            demo_simulation
            ;;
        "monitoring")
            demo_monitoring
            ;;
        "ai")
            demo_ai_commands
            ;;
        "batch")
            demo_batch_operations
            ;;
        "plugins")
            demo_plugin_development
            ;;
        "errors")
            demo_error_handling
            ;;
        "all")
            demo_basic_operations
            echo ""
            demo_navigation
            echo ""
            demo_simulation
            echo ""
            demo_monitoring
            echo ""
            demo_ai_commands
            echo ""
            demo_batch_operations
            echo ""
            demo_plugin_development
            echo ""
            demo_error_handling
            ;;
        *)
            log_error "Invalid mode: $mode"
            echo "Available modes: basic, navigation, simulation, monitoring, ai, batch, plugins, errors, all"
            exit 1
            ;;
    esac
    
    log_success "Demo completed successfully!"
}

# Help function
show_help() {
    echo "OneCodePlant CLI - ROS Commands Demo Script"
    echo ""
    echo "Usage: $0 [mode] [options]"
    echo ""
    echo "Modes:"
    echo "  basic        - Basic ROS operations (nodes, topics, parameters)"
    echo "  navigation   - Navigation and movement commands"
    echo "  simulation   - Simulation management (Gazebo)"
    echo "  monitoring   - Monitoring and diagnostics"
    echo "  ai           - AI-powered command generation"
    echo "  batch        - Batch operations example"
    echo "  plugins      - Plugin development and management"
    echo "  errors       - Error handling demonstration"
    echo "  all          - Run all demos (default)"
    echo ""
    echo "Options:"
    echo "  --help       - Show this help message"
    echo "  --dry-run    - Run in dry-run mode (set DRY_RUN=true)"
    echo ""
    echo "Environment Variables:"
    echo "  DRY_RUN      - Set to 'true' for dry-run mode"
    echo "  ROBOT_MODEL  - Robot model to use (default: turtlebot3_burger)"
    echo "  WORLD_FILE   - World file to use (default: turtlebot3_world)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all demos"
    echo "  $0 basic              # Run basic operations only"
    echo "  DRY_RUN=true $0       # Run in dry-run mode"
    echo "  $0 navigation         # Run navigation demo"
}

# Check for help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# Check for dry-run flag
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    shift
fi

# Execute main function
main "$@"