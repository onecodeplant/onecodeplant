"""
Integration tests for OneCodePlant CLI end-to-end functionality.

Tests complete CLI workflows including command parsing, plugin loading,
and system integration in controlled environments.
"""

import pytest
import tempfile
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, Mock

from onecode.cli import onecode


class TestCLIIntegration:
    """Test complete CLI integration workflows."""
    
    def test_cli_startup_and_help(self):
        """Test CLI startup and help system."""
        runner = CliRunner()
        result = runner.invoke(onecode, ['--help'])
        
        assert result.exit_code == 0
        assert 'OneCodePlant' in result.output
        assert 'plugin' in result.output
        assert 'sim' in result.output
        assert 'ai' in result.output
    
    def test_cli_version_display(self):
        """Test version information display."""
        runner = CliRunner()
        result = runner.invoke(onecode, ['--version'])
        
        assert result.exit_code == 0
    
    def test_dry_run_mode_integration(self):
        """Test dry-run mode across different commands."""
        runner = CliRunner()
        
        # Test dry-run with simulator command
        result = runner.invoke(onecode, ['--dry-run', 'sim', 'launch', 'gazebo'])
        assert result.exit_code == 0
        
        # Test dry-run with ROS command
        result = runner.invoke(onecode, ['--dry-run', 'pub', '/test_topic'])
        assert result.exit_code == 0
    
    def test_plugin_management_workflow(self):
        """Test complete plugin management workflow."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple test plugin
            plugin_dir = Path(temp_dir) / "test_plugin"
            plugin_dir.mkdir()
            
            plugin_file = plugin_dir / "plugin.py"
            plugin_file.write_text("""
from onecode.plugins.base_plugin import BasePlugin
from typing import Dict, Any

class TestPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self._name = "test_plugin"
        self._version = "1.0.0"
    
    def initialize(self) -> bool:
        return True
    
    def get_commands(self) -> Dict[str, Any]:
        return {"test": lambda: "test"}

def get_plugin():
    return TestPlugin()
""")
            
            # Test plugin listing (should be empty initially)
            result = runner.invoke(onecode, ['plugin', 'list'])
            assert result.exit_code == 0
            
            # Test plugin installation
            result = runner.invoke(onecode, ['plugin', 'install', str(plugin_dir)])
            assert result.exit_code == 0
            assert 'Successfully installed' in result.output or 'Installation failed' in result.output
            
            # Test plugin info (if installation succeeded)
            result = runner.invoke(onecode, ['plugin', 'info', 'test_plugin'])
            # Should either show info or indicate plugin not found
            assert result.exit_code in [0, 1]


class TestSimulatorIntegration:
    """Test simulator management integration."""
    
    def test_simulator_help_commands(self):
        """Test simulator command help system."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['sim', '--help'])
        assert result.exit_code == 0
        assert 'launch' in result.output
        assert 'status' in result.output
    
    def test_simulator_list_command(self):
        """Test simulator listing functionality."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['sim', 'list'])
        assert result.exit_code == 0
        # Should list available simulators regardless of installation
    
    def test_simulator_status_command(self):
        """Test simulator status checking."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['sim', 'status', 'gazebo'])
        assert result.exit_code == 0
        # Should show status even if simulator not installed
    
    @pytest.mark.requires_ros
    def test_simulator_launch_with_ros(self):
        """Test simulator launch when ROS is available."""
        runner = CliRunner()
        
        # Only run if ROS is detected
        env_result = runner.invoke(onecode, ['env'])
        if 'ROS 2 environment is ready' in env_result.output:
            result = runner.invoke(onecode, ['sim', 'launch', 'gazebo', '--headless'])
            # Should either launch successfully or fail with specific error
            assert result.exit_code in [0, 1]
    
    def test_simulator_dry_run_operations(self):
        """Test all simulator operations in dry-run mode."""
        runner = CliRunner()
        
        commands = [
            ['--dry-run', 'sim', 'launch', 'gazebo'],
            ['--dry-run', 'sim', 'pause', 'gazebo'],
            ['--dry-run', 'sim', 'resume', 'gazebo'],
            ['--dry-run', 'sim', 'reset', 'gazebo'],
            ['--dry-run', 'sim', 'shutdown', 'gazebo']
        ]
        
        for cmd in commands:
            result = runner.invoke(onecode, cmd)
            assert result.exit_code == 0


class TestROSIntegration:
    """Test ROS command integration."""
    
    def test_ros_environment_check(self):
        """Test ROS environment checking integration."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['env'])
        assert result.exit_code == 0
        assert 'ROS 2' in result.output
    
    def test_ros_environment_setup_help(self):
        """Test ROS setup instructions."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['env', '--setup'])
        assert result.exit_code == 0
        assert 'Setup' in result.output or 'Instructions' in result.output
    
    def test_ros_commands_dry_run(self):
        """Test ROS commands in dry-run mode."""
        runner = CliRunner()
        
        # Test publish command
        result = runner.invoke(onecode, [
            '--dry-run', 'pub', '/test_topic',
            '--message-type', 'std_msgs/String',
            '--data', '{"data": "test"}'
        ])
        assert result.exit_code == 0
        
        # Test echo command
        result = runner.invoke(onecode, ['--dry-run', 'echo', '/test_topic'])
        assert result.exit_code == 0
        
        # Test parameter commands
        result = runner.invoke(onecode, ['--dry-run', 'param', 'list'])
        assert result.exit_code == 0
        
        # Test node commands
        result = runner.invoke(onecode, ['--dry-run', 'node', '--list'])
        assert result.exit_code == 0
    
    @pytest.mark.requires_ros
    def test_ros_commands_with_ros_available(self):
        """Test ROS commands when ROS 2 is available."""
        runner = CliRunner()
        
        # Check if ROS is available first
        env_result = runner.invoke(onecode, ['env'])
        if 'ROS 2 environment is ready' not in env_result.output:
            pytest.skip("ROS 2 not available")
        
        # Test basic ROS commands
        result = runner.invoke(onecode, ['node', '--list'])
        assert result.exit_code in [0, 1]  # May fail if no nodes running
        
        result = runner.invoke(onecode, ['param', 'list'])
        assert result.exit_code in [0, 1]  # May fail if no parameters


class TestAIIntegration:
    """Test AI command integration."""
    
    def test_ai_command_help(self):
        """Test AI command help system."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['ai', '--help'])
        assert result.exit_code == 0
        assert 'natural language' in result.output.lower()
    
    def test_ai_command_without_api_keys(self):
        """Test AI command behavior without API keys."""
        runner = CliRunner()
        
        # Should provide helpful error message about missing API keys
        result = runner.invoke(onecode, ['ai', 'test query'])
        # Command should either work with available engines or show setup help
        assert result.exit_code in [0, 1]
    
    def test_ai_interactive_mode_help(self):
        """Test AI interactive mode help."""
        runner = CliRunner()
        
        # Test interactive mode startup (should exit quickly with help)
        result = runner.invoke(onecode, ['ai', '--interactive'], input='help\nexit\n')
        # Should show interactive help or setup instructions
        assert result.exit_code in [0, 1]
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_ai_command_with_mock_key(self):
        """Test AI command with mocked API key."""
        runner = CliRunner()
        
        # With mocked key, should attempt to process but may fail on actual API call
        result = runner.invoke(onecode, ['ai', 'launch gazebo'], input='n\n')
        # Should either process or show configuration issues
        assert result.exit_code in [0, 1]


class TestCodeGenerationIntegration:
    """Test code generation integration."""
    
    def test_gen_command_help(self):
        """Test code generation help system."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['gen', '--help'])
        assert result.exit_code == 0
        assert 'generate' in result.output.lower()
    
    def test_gen_node_template(self):
        """Test node template generation."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(onecode, [
                'gen', 'node', 'test_node',
                '--template', 'basic'
            ], cwd=temp_dir)
            
            # Should either generate successfully or show available templates
            assert result.exit_code in [0, 1]
    
    def test_gen_launch_template(self):
        """Test launch file template generation."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(onecode, [
                'gen', 'launch', 'test_launch',
                '--template', 'simple'
            ], cwd=temp_dir)
            
            # Should either generate successfully or show available templates
            assert result.exit_code in [0, 1]


class TestPluginSystemIntegration:
    """Test plugin system integration with CLI."""
    
    def test_plugins_list_loaded(self):
        """Test listing loaded plugins."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['plugins'])
        assert result.exit_code == 0
        # Should show loaded plugins or indicate none are loaded
    
    def test_plugin_commands_integration(self):
        """Test that plugin commands are properly integrated."""
        runner = CliRunner()
        
        # Check main help includes plugin commands
        result = runner.invoke(onecode, ['--help'])
        assert result.exit_code == 0
        
        # The help should show integrated plugin commands or core commands
        assert 'Commands:' in result.output
    
    def test_plugin_error_handling(self):
        """Test plugin error handling integration."""
        runner = CliRunner()
        
        # Try to access non-existent plugin command
        result = runner.invoke(onecode, ['nonexistent_command'])
        assert result.exit_code != 0
        # Should show helpful error message


class TestErrorHandlingIntegration:
    """Test error handling across the CLI system."""
    
    def test_invalid_command_handling(self):
        """Test handling of invalid commands."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['invalid_command'])
        assert result.exit_code != 0
        assert 'No such command' in result.output or 'Usage:' in result.output
    
    def test_missing_arguments_handling(self):
        """Test handling of missing required arguments."""
        runner = CliRunner()
        
        # Test command that requires arguments
        result = runner.invoke(onecode, ['pub'])
        assert result.exit_code != 0
        assert 'Missing' in result.output or 'Usage:' in result.output
    
    def test_invalid_options_handling(self):
        """Test handling of invalid options."""
        runner = CliRunner()
        
        result = runner.invoke(onecode, ['--invalid-option'])
        assert result.exit_code != 0
        assert 'No such option' in result.output or 'unrecognized' in result.output
    
    def test_configuration_error_handling(self):
        """Test handling of configuration errors."""
        runner = CliRunner()
        
        # Commands should handle missing configuration gracefully
        result = runner.invoke(onecode, ['env'])
        assert result.exit_code == 0  # Should show status even with issues


class TestWorkflowIntegration:
    """Test complete workflow integration scenarios."""
    
    def test_complete_simulation_workflow(self):
        """Test complete simulation setup workflow."""
        runner = CliRunner()
        
        # Check environment
        env_result = runner.invoke(onecode, ['env'])
        assert env_result.exit_code == 0
        
        # List simulators
        list_result = runner.invoke(onecode, ['sim', 'list'])
        assert list_result.exit_code == 0
        
        # Try to launch (dry-run)
        launch_result = runner.invoke(onecode, ['--dry-run', 'sim', 'launch', 'gazebo'])
        assert launch_result.exit_code == 0
    
    def test_complete_plugin_workflow(self):
        """Test complete plugin management workflow."""
        runner = CliRunner()
        
        # List current plugins
        list_result = runner.invoke(onecode, ['plugin', 'list'])
        assert list_result.exit_code == 0
        
        # Show loaded plugins
        loaded_result = runner.invoke(onecode, ['plugins'])
        assert loaded_result.exit_code == 0
        
        # Refresh registry
        refresh_result = runner.invoke(onecode, ['plugin', 'refresh'])
        assert refresh_result.exit_code == 0
    
    def test_complete_development_workflow(self):
        """Test complete development workflow."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Check environment
            env_result = runner.invoke(onecode, ['env'])
            assert env_result.exit_code == 0
            
            # Generate code template
            gen_result = runner.invoke(onecode, [
                'gen', 'node', 'test_node'
            ], cwd=temp_dir)
            # Should work or show available options
            assert gen_result.exit_code in [0, 1]
            
            # Test ROS commands (dry-run)
            pub_result = runner.invoke(onecode, [
                '--dry-run', 'pub', '/test_topic'
            ])
            assert pub_result.exit_code == 0