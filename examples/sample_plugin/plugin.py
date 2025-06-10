"""
Sample Plugin for OneCodePlant - Demonstrates plugin architecture.

This plugin serves as an example of how to create custom plugins
for the OneCodePlant CLI system.
"""

import click
from typing import Dict, Any
from onecode.plugins.base_plugin import BasePlugin


class SamplePlugin(BasePlugin):
    """
    Sample plugin demonstrating the OneCodePlant plugin architecture.
    
    This plugin provides example commands for testing the plugin
    management system and serves as a template for new plugins.
    """
    
    def __init__(self):
        """Initialize the sample plugin."""
        super().__init__()
        self._name = "sample_plugin"
        self._version = "1.0.0"
        self._description = "Sample plugin for demonstration and testing"
        self._author = "OneCodePlant Team"
    
    def register_commands(self, cli_group):
        """Register plugin commands with the CLI."""
        @cli_group.command()
        @click.option('--message', '-m', default='Hello from Sample Plugin!',
                      help='Message to display')
        def sample(message: str):
            """
            Sample command demonstrating plugin functionality.
            
            Examples:
                onecode sample
                onecode sample --message "Custom message"
            """
            click.echo(f"🔌 {message}")
            click.echo(f"📦 Plugin: {self.name} v{self.version}")
            click.echo(f"📝 {self.description}")
        
        @cli_group.command()
        @click.argument('name')
        def greet(name: str):
            """
            Greet a user by name.
            
            Examples:
                onecode greet Alice
                onecode greet "Robot Developer"
            """
            click.echo(f"👋 Hello, {name}! Welcome to OneCodePlant!")
            click.echo(f"🚀 Ready to build amazing robotics applications?")
    
    def initialize(self) -> bool:
        """Initialize the plugin."""
        return True
    
    def get_commands(self) -> Dict[str, Any]:
        """Return commands provided by this plugin."""
        return {
            'sample': self._sample_command,
            'greet': self._greet_command
        }
    
    def _sample_command(self, message: str = 'Hello from Sample Plugin!'):
        """Sample command implementation."""
        return f"🔌 {message}\n📦 Plugin: {self.name} v{self.version}\n📝 {self.description}"
    
    def _greet_command(self, name: str):
        """Greet command implementation."""
        return f"👋 Hello, {name}! Welcome to OneCodePlant!\n🚀 Ready to build amazing robotics applications?"
    
    def validate_environment(self) -> bool:
        """Validate that the plugin can run in the current environment."""
        return True
    
    def get_help_text(self) -> str:
        """Return detailed help text for the plugin."""
        return """
Sample Plugin - OneCodePlant Demo

This plugin demonstrates the OneCodePlant plugin architecture
and provides example commands for testing and development.

Available Commands:
  sample  - Display a sample message
  greet   - Greet a user by name

Use 'onecode <command> --help' for detailed command information.
        """.strip()


def get_plugin():
    """Plugin entry point - returns plugin instance."""
    return SamplePlugin()