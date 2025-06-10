"""
Main CLI entry point for OneCodePlant.

This module provides the primary command-line interface using click,
with support for plugin-based subcommands and modular architecture.
"""

import click
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json

from .plugins.plugin_loader import PluginLoader
from .plugins.base_plugin import BasePlugin
from .middleware.ros_utils import ROSUtils
from .middleware.checks import ROSEnvironmentChecker
from .middleware.logger import cli_logger
from .middleware.simulators import simulator_manager
from .config import config


class OneCodeCLI:
    """
    Main CLI class that manages command routing and plugin integration.
    
    This class serves as the central hub for all CLI operations, managing
    plugin loading, command registration, and execution flow.
    """
    
    def __init__(self, dry_run: bool = False):
        """Initialize the CLI with plugin loader and registry."""
        self.plugin_loader = PluginLoader()
        self.plugins: Dict[str, BasePlugin] = {}
        self.dry_run = dry_run
        self.ros_utils = ROSUtils(dry_run=dry_run)
        self.env_checker = ROSEnvironmentChecker()
        self.simulator_manager = simulator_manager
        self.simulator_manager.dry_run = dry_run
        self._load_plugins()
    
    def _load_plugins(self) -> None:
        """
        Load all available plugins from the plugins directory.
        
        This method discovers and initializes all plugins, handling
        any loading errors gracefully.
        """
        try:
            self.plugins = self.plugin_loader.load_all_plugins()
            click.echo(f"Loaded {len(self.plugins)} plugins successfully.")
            cli_logger.info(f"Loaded {len(self.plugins)} plugins successfully")
        except Exception as e:
            click.echo(f"Warning: Error loading plugins: {e}", err=True)
            cli_logger.error(f"Error loading plugins: {e}")
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Retrieve a specific plugin by name.
        
        Args:
            name: The name of the plugin to retrieve
            
        Returns:
            The plugin instance if found, None otherwise
        """
        return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, BasePlugin]:
        """
        Get all loaded plugins.
        
        Returns:
            Dictionary mapping plugin names to plugin instances
        """
        return self.plugins.copy()


# Global CLI instance - will be set based on context
cli_instance = None


@click.group()
@click.version_option(version="0.1.0")
@click.option('--dry-run', is_flag=True, help='Simulate operations without executing them')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def onecode(ctx: click.Context, dry_run: bool, verbose: bool) -> None:
    """
    OneCodePlant - AI-enhanced CLI tool for robotics development.
    
    A modular command-line interface designed to simplify ROS 2 workflows
    and robotics development through an extensible plugin architecture.
    """
    global cli_instance
    cli_instance = OneCodeCLI(dry_run=dry_run)
    
    ctx.ensure_object(dict)
    ctx.obj['cli'] = cli_instance
    ctx.obj['dry_run'] = dry_run
    ctx.obj['verbose'] = verbose
    
    # Check ROS environment and warn if issues
    if not dry_run:
        env_summary = cli_instance.env_checker.get_environment_summary()
        if not env_summary['ready']:
            click.echo("⚠️  ROS 2 environment issues detected:", err=True)
            for error in env_summary['errors'][:3]:  # Show first 3 errors
                click.echo(f"   • {error}", err=True)
            click.echo("   Use --dry-run to simulate operations or check 'onecode env' for details", err=True)


@onecode.command()
@click.option('--type', '-t', default='node', 
              help='Type of code to generate (node, launch, etc.)')
@click.option('--name', '-n', required=True, 
              help='Name of the generated component')
@click.option('--template', default='basic', 
              help='Template to use for generation')
@click.pass_context
def gen(ctx: click.Context, type: str, name: str, template: str) -> None:
    """
    Generate ROS 2 code templates and boilerplate.
    
    This command creates various ROS 2 components including nodes,
    launch files, and other common robotics development artifacts.
    """
    click.echo(f"Generating {type} named '{name}' using template '{template}'")
    
    # Check if any plugins can handle code generation
    cli = ctx.obj['cli']
    for plugin_name, plugin in cli.list_plugins().items():
        if hasattr(plugin, 'generate_code'):
            try:
                result = plugin.generate_code(type, name, template)
                if result:
                    click.echo(f"Code generation completed by {plugin_name}")
                    return
            except Exception as e:
                click.echo(f"Error in plugin {plugin_name}: {e}", err=True)
    
    click.echo("Code generation functionality will be implemented in future plugins.")


@onecode.group()
def gen():
    """
    Code generation commands (including natural language to ROS 2 code).
    """
    pass

@gen.command('roscribe')
@click.argument('prompt', required=True)
@click.option('--yes', is_flag=True, help='Write files without confirmation')
@click.option('--open', 'open_file', is_flag=True, help='Open generated node file in editor')
@click.pass_context
def roscribe_cmd(ctx, prompt, yes, open_file):
    """
    Generate a ROS 2 Python package from a natural language prompt.
    """
    cli = ctx.obj['cli']
    plugin = cli.get_plugin('roscribe_plugin')
    if not plugin:
        click.echo('❌ roscribe_plugin not loaded', err=True)
        ctx.exit(1)
    result = plugin.run(prompt, yes=yes, open_file=open_file)
    if result.get('status') == 'success':
        click.echo(f"✅ Generated package at {result['package']}")
        click.echo(f"  Node: {result['node_file']}")
        click.echo(f"  Launch: {result['launch_file']}")
    elif result.get('status') == 'cancelled':
        click.echo('Cancelled by user.')
    else:
        click.echo('❌ Generation failed', err=True)


@onecode.group()
@click.pass_context
def sim(ctx: click.Context) -> None:
    """
    Launch and manage robot simulations.
    
    This command group provides interface for controlling various simulation
    environments including Gazebo and Webots with support for launch, pause,
    resume, reset, and shutdown operations.
    """
    pass


@sim.command()
@click.argument('simulator', type=click.Choice(['gazebo', 'webots'], case_sensitive=False))
@click.option('--world', '-w', help='World file or name to load')
@click.option('--launch-file', '-l', help='Custom launch file to use')
@click.option('--headless', is_flag=True, help='Run simulation without GUI')
@click.option('--robot-model', '-r', help='Robot model to simulate')
@click.pass_context
def launch(ctx: click.Context, simulator: str, world: str, launch_file: str, headless: bool, robot_model: str) -> None:
    """
    Launch a simulation environment.
    
    Examples:
        onecode sim launch gazebo
        onecode sim launch gazebo --world my_world.sdf
        onecode sim launch webots --launch robot.launch.py
        onecode sim launch gazebo --headless --robot-model turtlebot3
    """
    cli = ctx.obj['cli']
    
    # Get the simulator instance
    sim_instance = cli.simulator_manager.get_simulator(simulator)
    if not sim_instance:
        click.echo(f"❌ Simulator '{simulator}' not supported", err=True)
        return
    
    # Check installation
    install_check = sim_instance.check_installation()
    if not install_check['installed']:
        click.echo(f"❌ {simulator.title()} is not installed or not found in PATH", err=True)
        click.echo("Issues found:")
        for issue in install_check['issues']:
            click.echo(f"  • {issue}")
        return
    
    click.echo(f"🚀 Launching {simulator.title()} simulator...")
    
    # Prepare launch arguments
    kwargs = {}
    if robot_model:
        kwargs['robot_model'] = robot_model
    
    # Launch the simulator
    result = sim_instance.launch(
        world=world,
        launch_file=launch_file,
        headless=headless,
        **kwargs
    )
    
    if result['success']:
        click.echo(f"✅ {result['message']}")
        if result.get('pid'):
            click.echo(f"   Process ID: {result['pid']}")
    else:
        click.echo(f"❌ {result['message']}", err=True)


@sim.command()
@click.argument('simulator', type=click.Choice(['gazebo', 'webots'], case_sensitive=False))
@click.pass_context
def pause(ctx: click.Context, simulator: str) -> None:
    """
    Pause a running simulation.
    
    Examples:
        onecode sim pause gazebo
        onecode sim pause webots
    """
    cli = ctx.obj['cli']
    
    sim_instance = cli.simulator_manager.get_simulator(simulator)
    if not sim_instance:
        click.echo(f"❌ Simulator '{simulator}' not supported", err=True)
        return
    
    click.echo(f"⏸️  Pausing {simulator.title()} simulation...")
    
    result = sim_instance.pause()
    
    if result['success']:
        click.echo(f"✅ {result['message']}")
    else:
        click.echo(f"❌ {result['message']}", err=True)


@sim.command()
@click.argument('simulator', type=click.Choice(['gazebo', 'webots'], case_sensitive=False))
@click.pass_context
def resume(ctx: click.Context, simulator: str) -> None:
    """
    Resume a paused simulation.
    
    Examples:
        onecode sim resume gazebo
        onecode sim resume webots
    """
    cli = ctx.obj['cli']
    
    sim_instance = cli.simulator_manager.get_simulator(simulator)
    if not sim_instance:
        click.echo(f"❌ Simulator '{simulator}' not supported", err=True)
        return
    
    click.echo(f"▶️  Resuming {simulator.title()} simulation...")
    
    result = sim_instance.resume()
    
    if result['success']:
        click.echo(f"✅ {result['message']}")
    else:
        click.echo(f"❌ {result['message']}", err=True)


@sim.command()
@click.argument('simulator', type=click.Choice(['gazebo', 'webots'], case_sensitive=False))
@click.pass_context
def reset(ctx: click.Context, simulator: str) -> None:
    """
    Reset a simulation to its initial state.
    
    Examples:
        onecode sim reset gazebo
        onecode sim reset webots
    """
    cli = ctx.obj['cli']
    
    sim_instance = cli.simulator_manager.get_simulator(simulator)
    if not sim_instance:
        click.echo(f"❌ Simulator '{simulator}' not supported", err=True)
        return
    
    click.echo(f"🔄 Resetting {simulator.title()} simulation...")
    
    result = sim_instance.reset()
    
    if result['success']:
        click.echo(f"✅ {result['message']}")
    else:
        click.echo(f"❌ {result['message']}", err=True)


@sim.command()
@click.argument('simulator', type=click.Choice(['gazebo', 'webots'], case_sensitive=False))
@click.pass_context
def shutdown(ctx: click.Context, simulator: str) -> None:
    """
    Shutdown a running simulation.
    
    Examples:
        onecode sim shutdown gazebo
        onecode sim shutdown webots
    """
    cli = ctx.obj['cli']
    
    sim_instance = cli.simulator_manager.get_simulator(simulator)
    if not sim_instance:
        click.echo(f"❌ Simulator '{simulator}' not supported", err=True)
        return
    
    click.echo(f"🛑 Shutting down {simulator.title()} simulator...")
    
    result = sim_instance.shutdown()
    
    if result['success']:
        click.echo(f"✅ {result['message']}")
    else:
        click.echo(f"❌ {result['message']}", err=True)


@sim.command()
@click.argument('simulator', type=click.Choice(['gazebo', 'webots'], case_sensitive=False))
@click.pass_context
def status(ctx: click.Context, simulator: str) -> None:
    """
    Check the status of a simulation.
    
    Examples:
        onecode sim status gazebo
        onecode sim status webots
    """
    cli = ctx.obj['cli']
    
    sim_instance = cli.simulator_manager.get_simulator(simulator)
    if not sim_instance:
        click.echo(f"❌ Simulator '{simulator}' not supported", err=True)
        return
    
    # Check installation
    install_check = sim_instance.check_installation()
    click.echo(f"📊 {simulator.title()} Status:")
    click.echo(f"   Installation: {'✅ Installed' if install_check['installed'] else '❌ Not found'}")
    
    if install_check['installed']:
        if install_check.get('version'):
            click.echo(f"   Version: {install_check['version']}")
        
        # Check runtime status
        status_info = sim_instance.get_status()
        click.echo(f"   Running: {'✅ Yes' if status_info['running'] else '❌ No'}")
        
        if status_info['running']:
            click.echo(f"   Process ID: {status_info['pid']}")
            if status_info.get('world'):
                click.echo(f"   World: {status_info['world']}")
            if status_info.get('launch_file'):
                click.echo(f"   Launch file: {status_info['launch_file']}")
    else:
        click.echo("   Issues:")
        for issue in install_check['issues']:
            click.echo(f"     • {issue}")


@sim.command('list')
@click.pass_context
def list_simulators(ctx: click.Context) -> None:
    """
    List all available simulators and their installation status.
    
    Example:
        onecode sim list
    """
    cli = ctx.obj['cli']
    
    click.echo("🎮 Available Simulators:")
    click.echo("-" * 40)
    
    installations = cli.simulator_manager.check_all_installations()
    
    for name, install_info in installations.items():
        status_icon = "✅" if install_info['installed'] else "❌"
        click.echo(f"{status_icon} {name.title()}")
        
        if install_info['installed']:
            if install_info.get('version'):
                click.echo(f"   Version: {install_info['version']}")
            if install_info.get('executables'):
                click.echo(f"   Executables: {', '.join(install_info['executables'].keys())}")
        else:
            click.echo(f"   Issues: {', '.join(install_info['issues'])}")
        click.echo()


@onecode.command()
@click.argument('topic')
@click.option('--message-type', '-t', default='std_msgs/String', 
              help='Message type for the topic')
@click.option('--rate', '-r', default=1.0, type=float, 
              help='Publishing rate in Hz')
@click.option('--data', '-d', help='Data to publish (JSON format)')
@click.option('--count', '-c', default=1, type=int,
              help='Number of messages to publish (0 for infinite)')
@click.pass_context
def pub(ctx: click.Context, topic: str, message_type: str, rate: float, data: str, count: int) -> None:
    """
    Publish messages to ROS 2 topics.
    
    This command allows publishing messages to specified topics
    with configurable message types and publishing rates.
    
    Examples:
        onecode pub /cmd_vel geometry_msgs/Twist --data '{"linear": {"x": 1.0}}'
        onecode pub /chatter std_msgs/String --data '{"data": "Hello World"}'
    """
    cli = ctx.obj['cli']
    
    click.echo(f"Publishing to topic '{topic}' at {rate} Hz")
    click.echo(f"Message type: {message_type}")
    if data:
        click.echo(f"Data: {data}")
    if count == 0:
        click.echo("Publishing continuously (Ctrl+C to stop)")
    else:
        click.echo(f"Publishing {count} message(s)")
    
    # Use middleware layer for ROS operations
    result = None
    success = False
    try:
        result = cli.ros_utils.publish_message(topic, message_type, rate, data, count)
        success = result['success']
        
        if result['success']:
            click.echo("✓ Publishing completed successfully")
            if result['stdout']:
                click.echo(result['stdout'])
        else:
            click.echo(f"✗ Publishing failed: {result['stderr']}", err=True)
            
    except Exception as e:
        click.echo(f"✗ Error during publishing: {e}", err=True)
        cli_logger.error(f"Publishing error: {e}")
    
    # Log the command execution
    cli_logger.log_command('pub', {
        'topic': topic,
        'message_type': message_type,
        'rate': rate,
        'count': count
    }, success)


@onecode.command()
@click.argument('topic')
@click.option('--count', '-c', default=0, type=int, 
              help='Number of messages to echo (0 for infinite)')
@click.option('--timeout', default=5.0, type=float, 
              help='Timeout for message reception')
@click.pass_context
def echo(ctx: click.Context, topic: str, count: int, timeout: float) -> None:
    """
    Echo messages from ROS 2 topics.
    
    This command listens to specified topics and displays
    received messages in real-time.
    
    Examples:
        onecode echo /scan
        onecode echo /cmd_vel --count 5
    """
    cli = ctx.obj['cli']
    
    click.echo(f"Echoing messages from topic '{topic}'")
    if count > 0:
        click.echo(f"Will echo {count} messages")
    else:
        click.echo("Echoing indefinitely (Ctrl+C to stop)")
    
    # Use middleware layer for ROS operations
    result = None
    success = False
    try:
        result = cli.ros_utils.echo_topic(topic, count, timeout)
        success = result['success']
        
        if result['success']:
            if result['stdout']:
                click.echo(result['stdout'])
        else:
            click.echo(f"✗ Echo failed: {result['stderr']}", err=True)
            
    except KeyboardInterrupt:
        click.echo("\n✓ Echo stopped by user")
    except Exception as e:
        click.echo(f"✗ Error during echo: {e}", err=True)
        cli_logger.error(f"Echo error: {e}")
    
    # Log the command execution
    cli_logger.log_command('echo', {
        'topic': topic,
        'count': count,
        'timeout': timeout
    }, success)


@onecode.command()
@click.argument('operation', type=click.Choice(['get', 'set', 'list']), required=False)
@click.argument('node_name', required=False)
@click.argument('param_name', required=False)
@click.argument('value', required=False)
@click.pass_context
def param(ctx: click.Context, operation: str, node_name: str, param_name: str, value: str) -> None:
    """
    Manage ROS 2 parameters.
    
    This command provides interface for getting, setting, and listing
    ROS 2 parameters across different nodes.
    
    Examples:
        onecode param list
        onecode param list /my_node
        onecode param get /my_node my_param
        onecode param set /my_node my_param 1.5
    """
    cli = ctx.obj['cli']
    
    if not operation:
        click.echo("Usage: onecode param <get|set|list> [node_name] [param_name] [value]")
        return
    
    result = None
    success = False
    
    try:
        if operation == 'list':
            result = cli.ros_utils.list_parameters(node_name)
            if result['success']:
                click.echo("Parameters:")
                if result['stdout']:
                    click.echo(result['stdout'])
                else:
                    click.echo("No parameters found")
            else:
                click.echo(f"✗ Failed to list parameters: {result['stderr']}", err=True)
        
        elif operation == 'get':
            if not node_name or not param_name:
                click.echo("Usage: onecode param get <node_name> <param_name>")
                return
            
            result = cli.ros_utils.get_parameter(node_name, param_name)
            if result['success']:
                click.echo(f"Parameter '{param_name}' on node '{node_name}':")
                click.echo(result['stdout'])
            else:
                click.echo(f"✗ Failed to get parameter: {result['stderr']}", err=True)
        
        elif operation == 'set':
            if not node_name or not param_name or not value:
                click.echo("Usage: onecode param set <node_name> <param_name> <value>")
                return
            
            result = cli.ros_utils.set_parameter(node_name, param_name, value)
            if result['success']:
                click.echo(f"✓ Set parameter '{param_name}' to '{value}' on node '{node_name}'")
            else:
                click.echo(f"✗ Failed to set parameter: {result['stderr']}", err=True)
        
        success = result['success'] if result else False
        
    except Exception as e:
        click.echo(f"✗ Error during parameter operation: {e}", err=True)
        cli_logger.error(f"Parameter operation error: {e}")
    
    # Log the command execution
    cli_logger.log_command('param', {
        'operation': operation,
        'node_name': node_name,
        'param_name': param_name,
        'value': value
    }, success)


@onecode.command()
@click.option('--list', 'list_nodes', is_flag=True, 
              help='List all active nodes')
@click.option('--info', help='Get information about a specific node')
@click.option('--kill', help='Kill a specific node')
@click.pass_context
def node(ctx: click.Context, list_nodes: bool, info: str, kill: str) -> None:
    """
    Manage ROS 2 nodes.
    
    This command provides interface for listing, inspecting,
    and managing ROS 2 nodes in the system.
    
    Examples:
        onecode node --list
        onecode node --info /my_node
        onecode node --kill /my_node
    """
    cli = ctx.obj['cli']
    
    if not any([list_nodes, info, kill]):
        click.echo("Please specify an operation (--list, --info, or --kill)")
        return
    
    result = None
    success = False
    
    try:
        if list_nodes:
            click.echo("Listing all active nodes...")
            result = cli.ros_utils.list_nodes()
            if result['success']:
                if result.get('nodes'):
                    click.echo("Active nodes:")
                    for node in result['nodes']:
                        click.echo(f"  • {node}")
                else:
                    click.echo("No active nodes found")
            else:
                click.echo(f"✗ Failed to list nodes: {result['stderr']}", err=True)
        
        elif info:
            click.echo(f"Getting information for node '{info}'")
            result = cli.ros_utils.get_node_info(info)
            if result['success']:
                click.echo(f"Node information for '{info}':")
                click.echo(result['stdout'])
            else:
                click.echo(f"✗ Failed to get node info: {result['stderr']}", err=True)
        
        elif kill:
            click.echo(f"Attempting to kill node '{kill}'")
            result = cli.ros_utils.kill_node(kill)
            if result['success']:
                click.echo(f"✓ Node '{kill}' terminated")
            else:
                click.echo(f"✗ Failed to kill node: {result['stderr']}", err=True)
        
        success = result['success'] if result else False
        
    except Exception as e:
        click.echo(f"✗ Error during node operation: {e}", err=True)
        cli_logger.error(f"Node operation error: {e}")
    
    # Log the command execution
    cli_logger.log_command('node', {
        'list_nodes': list_nodes,
        'info': info,
        'kill': kill
    }, success)


@onecode.command()
@click.argument('query', required=False)
@click.option('--engine', '-e', type=click.Choice(['openai', 'anthropic', 'google'], case_sensitive=False),
              help='AI engine to use (openai, anthropic, google)')
@click.option('--model', '-m', help='Specific model to use (overrides engine default)')
@click.option('--interactive', '-i', is_flag=True, help='Start interactive AI session')
@click.option('--auto-execute', '-x', is_flag=True, help='Auto-execute generated commands without confirmation')
@click.option('--show-reasoning', '-r', is_flag=True, help='Show AI reasoning and confidence scores')
@click.pass_context
def ai(ctx: click.Context, query: str, engine: str, model: str, interactive: bool, auto_execute: bool, show_reasoning: bool) -> None:
    """
    AI-powered natural language to CLI command conversion.
    
    Convert natural language instructions into executable OneCodePlant CLI commands
    using advanced language models. Supports multiple AI providers and includes
    safety validation before execution.
    
    Examples:
        onecode ai "launch gazebo with turtlebot3 robot"
        onecode ai "create a navigation node and start mapping"
        onecode ai "publish move forward command to robot"
        onecode ai --interactive
    """
    cli = ctx.obj['cli']
    
    if interactive:
        click.echo("🤖 Starting interactive AI assistant...")
        click.echo("Enter natural language instructions to convert to CLI commands.")
        click.echo("Type 'exit' to quit, 'help' for assistance, or 'status' for engine info.")
        click.echo()
        
        # Initialize NLP processor for interactive session
        try:
            from .ai.nlp_processor import NLPProcessor
            processor = NLPProcessor(engine=engine)
            
            if show_reasoning:
                engine_info = processor.get_engine_info()
                click.echo(f"Using {engine_info['engine']} engine with model {engine_info['model']}")
                click.echo()
        except Exception as e:
            click.echo(f"❌ Failed to initialize AI engine: {str(e)}", err=True)
            _show_ai_setup_help()
            return
        
        while True:
            try:
                user_input = click.prompt("🤖 AI Assistant", type=str).strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    click.echo("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    _show_interactive_help()
                    continue
                elif user_input.lower() == 'status':
                    _show_engine_status(processor)
                    continue
                elif not user_input:
                    continue
                
                # Process the natural language input
                _process_ai_query(user_input, processor, cli, auto_execute, show_reasoning)
                
            except KeyboardInterrupt:
                click.echo("\n👋 Goodbye!")
                break
            except Exception as e:
                click.echo(f"❌ Error: {str(e)}", err=True)
    
    elif query:
        # Single query mode
        try:
            from .ai.nlp_processor import NLPProcessor
            processor = NLPProcessor(engine=engine)
            
            if show_reasoning:
                engine_info = processor.get_engine_info()
                click.echo(f"Using {engine_info['engine']} engine with model {engine_info['model']}")
            
            _process_ai_query(query, processor, cli, auto_execute, show_reasoning)
            
        except Exception as e:
            click.echo(f"❌ Failed to process query: {str(e)}", err=True)
            _show_ai_setup_help()
    
    else:
        click.echo("Please provide a query or use --interactive mode")
        click.echo("Example: onecode ai \"launch gazebo with turtlebot3\"")


def _process_ai_query(query: str, processor, cli, auto_execute: bool, show_reasoning: bool) -> None:
    """Process a natural language query and optionally execute the results."""
    click.echo(f"🧠 Processing: {query}")
    
    # Parse the natural language input
    result = processor.parse(query)
    
    if not result.success:
        click.echo(f"❌ Failed to parse query: {result.explanation}", err=True)
        if result.errors:
            for error in result.errors:
                click.echo(f"   • {error}", err=True)
        return
    
    if show_reasoning:
        click.echo(f"💭 Explanation: {result.explanation}")
        click.echo(f"🎯 Confidence: {result.confidence:.1%}")
    
    # Display generated commands
    click.echo(f"\n📋 Generated {len(result.commands)} command(s):")
    for i, cmd in enumerate(result.commands, 1):
        click.echo(f"  {i}. {cmd}")
    
    # Show warnings if any
    if result.warnings and show_reasoning:
        click.echo(f"\n⚠️  Warnings:")
        for warning in result.warnings:
            click.echo(f"   • {warning}")
    
    # Handle execution
    if auto_execute or config.cli.auto_execute:
        click.echo(f"\n🚀 Auto-executing commands...")
        _execute_commands(result.commands, processor, cli.dry_run)
    else:
        # Ask for confirmation
        click.echo()
        if click.confirm("Do you want to execute these commands?"):
            _execute_commands(result.commands, processor, cli.dry_run)
        else:
            click.echo("Commands not executed.")


def _execute_commands(commands: list, processor, dry_run: bool) -> None:
    """Execute the generated commands."""
    exec_result = processor.execute(commands, dry_run=dry_run)
    
    if dry_run:
        click.echo("🧪 Dry run completed:")
        for cmd_id in exec_result['executed']:
            click.echo(f"   ✓ {exec_result['outputs'][cmd_id]}")
    else:
        # Show execution results
        if exec_result['executed']:
            click.echo(f"✅ Successfully executed {len(exec_result['executed'])} command(s)")
        
        if exec_result['failed']:
            click.echo(f"❌ Failed to execute {len(exec_result['failed'])} command(s)")
            for cmd_id in exec_result['failed']:
                click.echo(f"   • {exec_result['errors'][cmd_id]}")


def _show_interactive_help() -> None:
    """Show help for interactive mode."""
    click.echo("🔍 Interactive AI Assistant Commands:")
    click.echo("  exit/quit/bye - Exit the session")
    click.echo("  help          - Show this help")
    click.echo("  status        - Show AI engine status")
    click.echo()
    click.echo("💡 Example queries:")
    click.echo("  \"launch gazebo with empty world\"")
    click.echo("  \"create a navigation node in python\"")
    click.echo("  \"publish velocity command to move robot forward\"")
    click.echo("  \"start slam mapping and behavior tree\"")


def _show_engine_status(processor) -> None:
    """Show AI engine status information."""
    engine_info = processor.get_engine_info()
    click.echo("🔧 AI Engine Status:")
    click.echo(f"  Engine: {engine_info['engine']}")
    click.echo(f"  Model: {engine_info['model']}")
    click.echo(f"  Max tokens: {engine_info['max_tokens']}")
    click.echo(f"  Temperature: {engine_info['temperature']}")
    click.echo(f"  Safety checks: {'Enabled' if engine_info['safety_checks'] else 'Disabled'}")
    click.echo(f"  Available engines: {', '.join(engine_info['available_engines'])}")


def _show_ai_setup_help() -> None:
    """Show setup help for AI functionality."""
    available_engines = config.get_available_engines()
    
    if not available_engines:
        click.echo("❌ No AI engines configured. Please set up API keys:")
        click.echo("   • OpenAI: Set OPENAI_API_KEY environment variable")
        click.echo("   • Anthropic: Set ANTHROPIC_API_KEY environment variable") 
        click.echo("   • Google: Set GOOGLE_API_KEY environment variable")
    else:
        click.echo(f"✅ Available engines: {', '.join(available_engines)}")
        click.echo("💡 Try installing missing dependencies:")
        click.echo("   pip install openai anthropic google-generativeai")


@onecode.group()
@click.pass_context
def plugin(ctx: click.Context) -> None:
    """
    Plugin management commands.
    
    Install, remove, and manage OneCodePlant plugins from various sources
    including PyPI, GitHub repositories, and local directories.
    """
    pass


@plugin.command()
@click.argument('source')
@click.option('--force', is_flag=True, help='Force reinstallation if plugin already exists')
@click.pass_context
def install(ctx: click.Context, source: str, force: bool) -> None:
    """
    Install a plugin from various sources.
    
    SOURCES:
        PyPI package: onecode-my-plugin
        GitHub repo: user/repo or https://github.com/user/repo.git
        Local path: /path/to/plugin or ./my_plugin
    
    Examples:
        onecode plugin install onecode-navigation-plugin
        onecode plugin install robotics-team/ros2-helpers
        onecode plugin install ./my_custom_plugin
        onecode plugin install https://github.com/user/awesome-plugin.git
    """
    from .plugins.plugin_manager import PluginManager
    
    click.echo(f"Installing plugin from: {source}")
    
    try:
        manager = PluginManager()
        result = manager.install(source, force=force)
        
        click.echo(f"Successfully installed '{result['name']}'")
        click.echo(f"Source type: {result['source_type']}")
        click.echo(f"Status: {result['status']}")
        
        if ctx.obj['cli'].dry_run:
            click.echo("(Dry run - no actual installation performed)")
            
    except Exception as e:
        click.echo(f"Installation failed: {str(e)}", err=True)
        ctx.exit(1)


@plugin.command()
@click.argument('name')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def remove(ctx: click.Context, name: str, yes: bool) -> None:
    """
    Remove an installed plugin.
    
    Examples:
        onecode plugin remove my-plugin
        onecode plugin remove navigation-plugin --yes
    """
    from .plugins.plugin_manager import PluginManager
    
    if not yes:
        if not click.confirm(f"Are you sure you want to remove '{name}'?"):
            click.echo("Removal cancelled.")
            return
    
    try:
        manager = PluginManager()
        result = manager.remove(name, confirm=True)
        
        click.echo(f"Successfully removed '{result['name']}'")
        
        if ctx.obj['cli'].dry_run:
            click.echo("(Dry run - no actual removal performed)")
            
    except Exception as e:
        click.echo(f"Removal failed: {str(e)}", err=True)
        ctx.exit(1)


@plugin.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed plugin information')
@click.pass_context
def list(ctx: click.Context, detailed: bool) -> None:
    """
    List all installed plugins.
    
    Examples:
        onecode plugin list
        onecode plugin list --detailed
    """
    from .plugins.plugin_manager import PluginManager
    
    try:
        manager = PluginManager()
        plugins = manager.list_plugins()
        
        if not plugins:
            click.echo("No plugins are currently installed.")
            return
        
        click.echo(f"Installed plugins ({len(plugins)}):")
        click.echo("-" * 50)
        
        for plugin_info in plugins:
            click.echo(f"• {plugin_info['name']}")
            click.echo(f"  Source: {plugin_info['source']}")
            click.echo(f"  Status: {plugin_info['status']}")
            
            if 'version' in plugin_info:
                click.echo(f"  Version: {plugin_info['version']}")
            
            if detailed and 'path' in plugin_info:
                click.echo(f"  Path: {plugin_info['path']}")
            
            if plugin_info['status'] == 'missing':
                click.echo("  ⚠️  Plugin files are missing")
            
            click.echo()
            
    except Exception as e:
        click.echo(f"Failed to list plugins: {str(e)}", err=True)
        ctx.exit(1)


@plugin.command()
@click.argument('name')
@click.pass_context
def info(ctx: click.Context, name: str) -> None:
    """
    Show detailed information about a specific plugin.
    
    Examples:
        onecode plugin info my-plugin
    """
    from .plugins.plugin_manager import PluginManager
    
    try:
        manager = PluginManager()
        info = manager.get_plugin_info(name)
        
        if not info:
            click.echo(f"Plugin '{name}' not found.")
            ctx.exit(1)
        
        click.echo(f"Plugin: {name}")
        click.echo("-" * (len(name) + 8))
        
        for key, value in info.items():
            click.echo(f"{key.title()}: {value}")
            
    except Exception as e:
        click.echo(f"Failed to get plugin info: {str(e)}", err=True)
        ctx.exit(1)


@plugin.command()
@click.pass_context
def refresh(ctx: click.Context) -> None:
    """
    Refresh the plugin registry by checking plugin states.
    
    This command checks if installed plugins are still available
    and updates their status accordingly.
    
    Examples:
        onecode plugin refresh
    """
    from .plugins.plugin_manager import PluginManager
    
    try:
        manager = PluginManager()
        manager.refresh_registry()
        click.echo("Plugin registry refreshed successfully.")
        
    except Exception as e:
        click.echo(f"Failed to refresh registry: {str(e)}", err=True)
        ctx.exit(1)


@onecode.command()
@click.pass_context  
def plugins(ctx: click.Context) -> None:
    """
    List all available plugins and their status.
    
    This command shows information about loaded plugins,
    their versions, and capabilities.
    """
    cli = ctx.obj['cli']
    loaded_plugins = cli.list_plugins()
    
    if not loaded_plugins:
        click.echo("No plugins are currently loaded.")
        return
    
    click.echo("Loaded plugins:")
    click.echo("-" * 50)
    
    for name, plugin in loaded_plugins.items():
        click.echo(f"• {name}")
        click.echo(f"  Version: {getattr(plugin, 'version', 'Unknown')}")
        click.echo(f"  Description: {getattr(plugin, 'description', 'No description available')}")
        click.echo()


@onecode.command()
@click.option('--setup', is_flag=True, help='Show ROS 2 setup instructions')
@click.pass_context
def env(ctx: click.Context, setup: bool) -> None:
    """
    Check ROS 2 environment status and configuration.
    
    This command verifies ROS 2 installation, environment variables,
    and provides setup guidance if issues are detected.
    """
    cli = ctx.obj['cli']
    
    click.echo("Checking ROS 2 environment...")
    
    try:
        env_summary = cli.env_checker.get_environment_summary()
        
        # Display installation status
        installation = env_summary['installation']
        click.echo(f"\n📦 ROS 2 Installation:")
        if installation['installed']:
            click.echo(f"  ✓ Status: Installed")
            click.echo(f"  ✓ Distribution: {installation['distro'] or 'Unknown'}")
            click.echo(f"  ✓ Version: ROS {installation['version'] or 'Unknown'}")
        else:
            click.echo(f"  ✗ Status: Not installed or not found")
            for issue in installation['issues']:
                click.echo(f"    • {issue}")
        
        # Display sourcing status
        sourcing = env_summary['sourcing']
        click.echo(f"\n🔧 Environment Sourcing:")
        if sourcing['sourced']:
            click.echo(f"  ✓ Status: Properly sourced")
        else:
            click.echo(f"  ✗ Status: Not properly sourced")
            if sourcing['missing_vars']:
                click.echo(f"  Missing variables:")
                for var in sourcing['missing_vars']:
                    click.echo(f"    • {var}")
        
        # Display command availability
        commands = env_summary['commands']
        click.echo(f"\n⚡ Command Availability:")
        for cmd, available in commands.items():
            status = "✓" if available else "✗"
            click.echo(f"  {status} {cmd}")
        
        # Overall status
        click.echo(f"\n🎯 Overall Status:")
        if env_summary['ready']:
            click.echo("  ✓ ROS 2 environment is ready for OneCodePlant")
        else:
            click.echo("  ✗ ROS 2 environment needs configuration")
        
        # Show warnings and errors
        if env_summary['warnings']:
            click.echo(f"\n⚠️  Warnings:")
            for warning in env_summary['warnings']:
                click.echo(f"    • {warning}")
        
        if env_summary['errors']:
            click.echo(f"\n🚨 Errors:")
            for error in env_summary['errors']:
                click.echo(f"    • {error}")
        
        # Show setup instructions if requested or if there are issues
        if setup or not env_summary['ready']:
            instructions = cli.env_checker.get_setup_instructions()
            click.echo(f"\n📋 Setup Instructions:")
            for instruction in instructions:
                click.echo(f"  {instruction}")
        
        # Log file location
        log_path = cli_logger.get_log_path()
        click.echo(f"\n📝 Logs: {log_path}")
        
    except Exception as e:
        click.echo(f"✗ Error checking environment: {e}", err=True)
        cli_logger.error(f"Environment check error: {e}")


def main() -> None:
    """
    Main entry point for the OneCodePlant CLI application.
    
    This function serves as the primary entry point when the
    application is invoked from the command line.
    """
    try:
        onecode()
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
