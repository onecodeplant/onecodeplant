"""
Unit tests for OneCodePlant CLI core functionality.

Tests the main CLI class, command dispatch, and core operations
without external dependencies.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import json

from onecode.cli import OneCodeCLI, onecode
from onecode.plugins.base_plugin import BasePlugin


class TestOneCodeCLI:
    """Test the main OneCodeCLI class."""
    
    def test_cli_initialization(self, mock_config):
        """Test CLI initialization with default settings."""
        with patch('onecode.cli.PluginLoader') as mock_loader:
            mock_loader.return_value.load_all_plugins.return_value = {}
            
            cli = OneCodeCLI(dry_run=False)
            
            assert cli.dry_run is False
            assert cli.plugins == {}
            mock_loader.assert_called_once()
    
    def test_cli_dry_run_mode(self, mock_config):
        """Test CLI initialization in dry-run mode."""
        with patch('onecode.cli.PluginLoader') as mock_loader:
            mock_loader.return_value.load_all_plugins.return_value = {}
            
            cli = OneCodeCLI(dry_run=True)
            
            assert cli.dry_run is True
            assert cli.simulator_manager.dry_run is True
    
    def test_plugin_loading(self, mock_config, mock_plugin):
        """Test plugin loading during CLI initialization."""
        with patch('onecode.cli.PluginLoader') as mock_loader:
            mock_loader.return_value.load_all_plugins.return_value = {
                'test_plugin': mock_plugin
            }
            
            cli = OneCodeCLI()
            
            assert 'test_plugin' in cli.plugins
            assert cli.plugins['test_plugin'] == mock_plugin
    
    def test_get_plugin(self, mock_config, mock_plugin):
        """Test retrieving a specific plugin."""
        with patch('onecode.cli.PluginLoader') as mock_loader:
            mock_loader.return_value.load_all_plugins.return_value = {
                'test_plugin': mock_plugin
            }
            
            cli = OneCodeCLI()
            plugin = cli.get_plugin('test_plugin')
            
            assert plugin == mock_plugin
    
    def test_get_nonexistent_plugin(self, mock_config):
        """Test retrieving a plugin that doesn't exist."""
        with patch('onecode.cli.PluginLoader') as mock_loader:
            mock_loader.return_value.load_all_plugins.return_value = {}
            
            cli = OneCodeCLI()
            plugin = cli.get_plugin('nonexistent')
            
            assert plugin is None
    
    def test_list_plugins(self, mock_config, mock_plugin):
        """Test listing all loaded plugins."""
        with patch('onecode.cli.PluginLoader') as mock_loader:
            mock_loader.return_value.load_all_plugins.return_value = {
                'test_plugin': mock_plugin
            }
            
            cli = OneCodeCLI()
            plugins = cli.list_plugins()
            
            assert len(plugins) == 1
            assert 'test_plugin' in plugins
            assert plugins['test_plugin'] == mock_plugin


class TestCLICommands:
    """Test individual CLI commands."""
    
    def test_main_help_command(self):
        """Test the main help command."""
        runner = CliRunner()
        result = runner.invoke(onecode, ['--help'])
        
        assert result.exit_code == 0
        assert 'OneCodePlant' in result.output
        assert 'AI-enhanced CLI tool' in result.output
    
    def test_version_command(self):
        """Test the version command."""
        runner = CliRunner()
        result = runner.invoke(onecode, ['--version'])
        
        assert result.exit_code == 0
    
    @patch('onecode.cli.OneCodeCLI')
    def test_dry_run_flag(self, mock_cli_class):
        """Test that dry-run flag is properly passed."""
        mock_cli_instance = Mock()
        mock_cli_class.return_value = mock_cli_instance
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['--dry-run', 'env'])
        
        mock_cli_class.assert_called_once()
        # Check that dry_run was set on the CLI instance
        assert mock_cli_instance.dry_run is True or mock_cli_class.call_args[1].get('dry_run') is True
    
    @patch('onecode.cli.OneCodeCLI')
    def test_verbose_flag(self, mock_cli_class):
        """Test that verbose flag is properly handled."""
        mock_cli_instance = Mock()
        mock_cli_class.return_value = mock_cli_instance
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['--verbose', 'env'])
        
        mock_cli_class.assert_called_once()


class TestPluginCommands:
    """Test plugin management commands."""
    
    @patch('onecode.cli.PluginManager')
    def test_plugin_list_command(self, mock_manager_class):
        """Test plugin list command."""
        mock_manager = Mock()
        mock_manager.list_plugins.return_value = [
            {
                'name': 'test_plugin',
                'source': 'local',
                'status': 'installed',
                'version': '1.0.0'
            }
        ]
        mock_manager_class.return_value = mock_manager
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['plugin', 'list'])
        
        assert result.exit_code == 0
        assert 'test_plugin' in result.output
        assert 'local' in result.output
        assert 'installed' in result.output
    
    @patch('onecode.cli.PluginManager')
    def test_plugin_install_command(self, mock_manager_class):
        """Test plugin install command."""
        mock_manager = Mock()
        mock_manager.install.return_value = {
            'name': 'new_plugin',
            'source_type': 'local',
            'status': 'success'
        }
        mock_manager_class.return_value = mock_manager
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['plugin', 'install', './test_plugin'])
        
        assert result.exit_code == 0
        assert 'Successfully installed' in result.output
        mock_manager.install.assert_called_once_with('./test_plugin', force=False)
    
    @patch('onecode.cli.PluginManager')
    def test_plugin_install_with_force(self, mock_manager_class):
        """Test plugin install command with force flag."""
        mock_manager = Mock()
        mock_manager.install.return_value = {
            'name': 'new_plugin',
            'source_type': 'local',
            'status': 'success'
        }
        mock_manager_class.return_value = mock_manager
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['plugin', 'install', '--force', './test_plugin'])
        
        assert result.exit_code == 0
        mock_manager.install.assert_called_once_with('./test_plugin', force=True)
    
    @patch('onecode.cli.PluginManager')
    def test_plugin_remove_command(self, mock_manager_class):
        """Test plugin remove command."""
        mock_manager = Mock()
        mock_manager.remove.return_value = {
            'name': 'test_plugin',
            'status': 'removed'
        }
        mock_manager_class.return_value = mock_manager
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['plugin', 'remove', '--yes', 'test_plugin'])
        
        assert result.exit_code == 0
        assert 'Successfully removed' in result.output
        mock_manager.remove.assert_called_once_with('test_plugin', confirm=True)
    
    @patch('onecode.cli.PluginManager')
    def test_plugin_info_command(self, mock_manager_class):
        """Test plugin info command."""
        mock_manager = Mock()
        mock_manager.get_plugin_info.return_value = {
            'source': 'local',
            'version': '1.0.0',
            'status': 'installed'
        }
        mock_manager_class.return_value = mock_manager
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['plugin', 'info', 'test_plugin'])
        
        assert result.exit_code == 0
        assert 'test_plugin' in result.output
        assert 'local' in result.output
        mock_manager.get_plugin_info.assert_called_once_with('test_plugin')


class TestROSCommands:
    """Test ROS-related CLI commands."""
    
    @patch('onecode.cli.OneCodeCLI')
    def test_pub_command(self, mock_cli_class):
        """Test ROS topic publish command."""
        mock_cli_instance = Mock()
        mock_ros_utils = Mock()
        mock_ros_utils.publish_message.return_value = {
            'success': True,
            'stdout': 'Message published',
            'stderr': ''
        }
        mock_cli_instance.ros_utils = mock_ros_utils
        mock_cli_class.return_value = mock_cli_instance
        
        runner = CliRunner()
        result = runner.invoke(onecode, [
            'pub', '/test_topic', 
            '--message-type', 'std_msgs/String',
            '--data', '{"data": "test"}'
        ])
        
        mock_ros_utils.publish_message.assert_called_once()
    
    @patch('onecode.cli.OneCodeCLI')
    def test_echo_command(self, mock_cli_class):
        """Test ROS topic echo command."""
        mock_cli_instance = Mock()
        mock_ros_utils = Mock()
        mock_ros_utils.echo_topic.return_value = {
            'success': True,
            'stdout': 'Topic data',
            'stderr': ''
        }
        mock_cli_instance.ros_utils = mock_ros_utils
        mock_cli_class.return_value = mock_cli_instance
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['echo', '/test_topic'])
        
        mock_ros_utils.echo_topic.assert_called_once()
    
    @patch('onecode.cli.OneCodeCLI')
    def test_env_command(self, mock_cli_class):
        """Test ROS environment check command."""
        mock_cli_instance = Mock()
        mock_env_checker = Mock()
        mock_env_checker.get_environment_summary.return_value = {
            'installation': {'installed': True, 'distro': 'humble'},
            'sourcing': {'sourced': True},
            'commands': {'ros2': True},
            'ready': True,
            'warnings': [],
            'errors': []
        }
        mock_cli_instance.env_checker = mock_env_checker
        mock_cli_class.return_value = mock_cli_instance
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['env'])
        
        assert result.exit_code == 0
        mock_env_checker.get_environment_summary.assert_called_once()


class TestSimulatorCommands:
    """Test simulator management commands."""
    
    @patch('onecode.cli.OneCodeCLI')
    def test_sim_launch_command(self, mock_cli_class):
        """Test simulator launch command."""
        mock_cli_instance = Mock()
        mock_sim_manager = Mock()
        mock_sim_manager.launch.return_value = {
            'success': True,
            'message': 'Simulator launched'
        }
        mock_cli_instance.simulator_manager = mock_sim_manager
        mock_cli_class.return_value = mock_cli_instance
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['sim', 'launch', 'gazebo'])
        
        mock_sim_manager.launch.assert_called_once()
    
    @patch('onecode.cli.OneCodeCLI')
    def test_sim_status_command(self, mock_cli_class):
        """Test simulator status command."""
        mock_cli_instance = Mock()
        mock_sim_manager = Mock()
        mock_sim_manager.get_status.return_value = {
            'gazebo': 'running',
            'webots': 'stopped'
        }
        mock_cli_instance.simulator_manager = mock_sim_manager
        mock_cli_class.return_value = mock_cli_instance
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['sim', 'status', 'gazebo'])
        
        mock_sim_manager.get_status.assert_called_once()


class TestAICommands:
    """Test AI-powered CLI commands."""
    
    @patch('onecode.cli.OneCodeCLI')
    @patch('onecode.ai.processors.natural_language_processor.NLPProcessor')
    def test_ai_command_basic(self, mock_processor_class, mock_cli_class):
        """Test basic AI command processing."""
        mock_processor = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.commands = ['onecode sim launch gazebo']
        mock_result.explanation = 'Launch Gazebo simulation'
        mock_result.confidence = 0.95
        mock_result.warnings = []
        
        mock_processor.parse.return_value = mock_result
        mock_processor.execute.return_value = {
            'executed': ['cmd_1'],
            'failed': [],
            'outputs': {'cmd_1': 'Success'},
            'errors': {}
        }
        mock_processor_class.return_value = mock_processor
        
        mock_cli_instance = Mock()
        mock_cli_class.return_value = mock_cli_instance
        
        runner = CliRunner()
        result = runner.invoke(onecode, ['ai', 'launch gazebo simulator'], input='y\n')
        
        # Should not fail even if AI components are not fully available
        # This tests the command structure and flow