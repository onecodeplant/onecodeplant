"""
Example Plugin for OneCodePlant

This serves as a template and example for developers creating custom plugins.
It demonstrates the basic plugin structure, command registration, and integration patterns.
"""

from onecode.plugins.base_plugin import BasePlugin
from typing import Dict, Any, Optional
import click
import logging


class ExamplePlugin(BasePlugin):
    """
    Example plugin demonstrating OneCodePlant plugin development patterns.
    
    This plugin provides sample commands that showcase:
    - Basic command structure
    - Parameter handling
    - Configuration management
    - Error handling
    - Logging integration
    """
    
    def __init__(self):
        super().__init__()
        self._name = "example_plugin"
        self._version = "1.0.0"
        self._description = "Example plugin for OneCodePlant development"
        self._dependencies = []
        self.logger = logging.getLogger(f"onecode.{self._name}")
    
    def initialize(self) -> bool:
        """
        Initialize the example plugin.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info(f"Initializing {self._name} plugin")
            
            # Perform any required setup here
            self._setup_default_config()
            
            self.logger.info(f"Successfully initialized {self._name} plugin")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self._name} plugin: {e}")
            return False
    
    def get_commands(self) -> Dict[str, Any]:
        """
        Return the commands provided by this plugin.
        
        Returns:
            Dict[str, Any]: Dictionary mapping command names to command functions
        """
        return {
            'hello': self.hello_command,
            'config': self.config_command,
            'status': self.status_command
        }
    
    def _setup_default_config(self) -> None:
        """Setup default configuration for the plugin."""
        default_config = {
            'greeting': 'Hello from OneCodePlant!',
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        }
        
        # Merge with any existing config
        for key, value in default_config.items():
            if key not in self._config:
                self._config[key] = value
    
    @click.command()
    @click.option('--name', '-n', default='World', help='Name to greet')
    @click.option('--uppercase', '-u', is_flag=True, help='Use uppercase greeting')
    @click.pass_context
    def hello_command(self, ctx: click.Context, name: str, uppercase: bool):
        """
        Example hello command with customizable greeting.
        
        This command demonstrates:
        - Click integration
        - Parameter handling
        - Configuration usage
        - Output formatting
        """
        try:
            greeting = self._config.get('greeting', 'Hello from OneCodePlant!')
            message = f"{greeting} Nice to meet you, {name}!"
            
            if uppercase:
                message = message.upper()
            
            click.echo(click.style(message, fg='green', bold=True))
            
            # Log the interaction
            self.logger.info(f"Greeted user: {name}")
            
            return {"status": "success", "message": message}
            
        except Exception as e:
            error_msg = f"Failed to execute hello command: {e}"
            self.logger.error(error_msg)
            click.echo(click.style(f"Error: {error_msg}", fg='red'))
            return {"status": "error", "message": error_msg}
    
    @click.command()
    @click.option('--show', '-s', is_flag=True, help='Show current configuration')
    @click.option('--set', '-S', nargs=2, metavar='KEY VALUE', help='Set configuration value')
    @click.pass_context
    def config_command(self, ctx: click.Context, show: bool, set: Optional[tuple]):
        """
        Manage plugin configuration.
        
        Examples:
            onecode example config --show
            onecode example config --set greeting "Custom greeting!"
        """
        try:
            if show:
                click.echo("Current configuration:")
                for key, value in self._config.items():
                    click.echo(f"  {key}: {value}")
                return {"status": "success", "config": self._config}
            
            if set:
                key, value = set
                # Try to parse value as appropriate type
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                
                self._config[key] = value
                click.echo(f"Set {key} = {value}")
                self.logger.info(f"Configuration updated: {key} = {value}")
                return {"status": "success", "updated": {key: value}}
            
            # If no options provided, show help
            click.echo(ctx.get_help())
            return {"status": "info", "message": "No action specified"}
            
        except Exception as e:
            error_msg = f"Failed to manage configuration: {e}"
            self.logger.error(error_msg)
            click.echo(click.style(f"Error: {error_msg}", fg='red'))
            return {"status": "error", "message": error_msg}
    
    @click.command()
    @click.option('--verbose', '-v', is_flag=True, help='Show detailed status')
    @click.pass_context
    def status_command(self, ctx: click.Context, verbose: bool):
        """
        Show plugin status and health information.
        
        This command demonstrates how to provide status information
        and health checks for your plugin.
        """
        try:
            status_info = {
                "name": self._name,
                "version": self._version,
                "status": "active",
                "commands": len(self.get_commands()),
                "config_items": len(self._config)
            }
            
            click.echo(f"Plugin: {self._name} v{self._version}")
            click.echo(f"Status: {click.style('Active', fg='green')}")
            click.echo(f"Commands available: {status_info['commands']}")
            
            if verbose:
                click.echo(f"Configuration items: {status_info['config_items']}")
                click.echo("Available commands:")
                for cmd_name in self.get_commands().keys():
                    click.echo(f"  - {cmd_name}")
                
                if self._dependencies:
                    click.echo("Dependencies:")
                    for dep in self._dependencies:
                        click.echo(f"  - {dep}")
            
            return {"status": "success", "info": status_info}
            
        except Exception as e:
            error_msg = f"Failed to get status: {e}"
            self.logger.error(error_msg)
            click.echo(click.style(f"Error: {error_msg}", fg='red'))
            return {"status": "error", "message": error_msg}
    
    def cleanup(self) -> None:
        """
        Cleanup plugin resources.
        
        This method is called when the plugin is being unloaded
        or the application is shutting down.
        """
        try:
            self.logger.info(f"Cleaning up {self._name} plugin")
            # Perform any necessary cleanup here
            # Close connections, save state, etc.
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


def get_plugin():
    """
    Plugin entry point.
    
    This function is called by the OneCodePlant plugin system
    to instantiate the plugin.
    
    Returns:
        ExamplePlugin: Instance of the plugin
    """
    return ExamplePlugin()


# Additional helper functions can be defined here
def validate_plugin_environment() -> bool:
    """
    Validate that the environment is suitable for this plugin.
    
    Returns:
        bool: True if environment is valid, False otherwise
    """
    # Add environment validation logic here
    return True


if __name__ == "__main__":
    # This allows testing the plugin standalone
    plugin = get_plugin()
    if plugin.initialize():
        print(f"Plugin {plugin._name} initialized successfully")
        print(f"Available commands: {list(plugin.get_commands().keys())}")
    else:
        print(f"Failed to initialize plugin {plugin._name}")