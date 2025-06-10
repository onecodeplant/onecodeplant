"""
Unit tests for OneCodePlant middleware components.

Tests ROS utilities, environment checks, logging, and simulator management
without requiring actual ROS installation or external dependencies.
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from onecode.middleware.ros_utils import ROSUtils
from onecode.middleware.checks import ROSEnvironmentChecker
from onecode.middleware.logger import cli_logger
from onecode.middleware.simulators import SimulatorManager


class TestROSUtils:
    """Test ROS utilities middleware."""
    
    def test_ros_utils_initialization(self):
        """Test ROS utilities initialization."""
        ros_utils = ROSUtils(dry_run=False)
        assert ros_utils.dry_run is False
        
        ros_utils_dry = ROSUtils(dry_run=True)
        assert ros_utils_dry.dry_run is True
    
    @patch('subprocess.run')
    def test_publish_message_success(self, mock_subprocess):
        """Test successful message publishing."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Message published successfully",
            stderr=""
        )
        
        ros_utils = ROSUtils(dry_run=False)
        result = ros_utils.publish_message(
            topic="/test_topic",
            message_type="std_msgs/String",
            rate=1.0,
            data='{"data": "test"}',
            count=1
        )
        
        assert result['success'] is True
        assert "Message published successfully" in result['stdout']
        mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_publish_message_failure(self, mock_subprocess):
        """Test failed message publishing."""
        mock_subprocess.side_effect = Exception("ROS command failed")
        
        ros_utils = ROSUtils(dry_run=False)
        result = ros_utils.publish_message(
            topic="/test_topic",
            message_type="std_msgs/String",
            rate=1.0,
            data='{"data": "test"}',
            count=1
        )
        
        assert result['success'] is False
        assert "ROS command failed" in result['stderr']
    
    def test_publish_message_dry_run(self):
        """Test message publishing in dry-run mode."""
        ros_utils = ROSUtils(dry_run=True)
        result = ros_utils.publish_message(
            topic="/test_topic",
            message_type="std_msgs/String",
            rate=1.0,
            data='{"data": "test"}',
            count=1
        )
        
        assert result['success'] is True
        assert "DRY RUN" in result['stdout']
    
    @patch('subprocess.run')
    def test_echo_topic_success(self, mock_subprocess):
        """Test successful topic echoing."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Topic data received",
            stderr=""
        )
        
        ros_utils = ROSUtils(dry_run=False)
        result = ros_utils.echo_topic("/test_topic", count=5, timeout=2.0)
        
        assert result['success'] is True
        assert "Topic data received" in result['stdout']
    
    def test_echo_topic_dry_run(self):
        """Test topic echoing in dry-run mode."""
        ros_utils = ROSUtils(dry_run=True)
        result = ros_utils.echo_topic("/test_topic", count=5, timeout=2.0)
        
        assert result['success'] is True
        assert "DRY RUN" in result['stdout']
    
    @patch('subprocess.run')
    def test_get_node_info_success(self, mock_subprocess):
        """Test successful node info retrieval."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Node: /test_node\nSubscriptions:\n  /topic1",
            stderr=""
        )
        
        ros_utils = ROSUtils(dry_run=False)
        result = ros_utils.get_node_info("/test_node")
        
        assert result['success'] is True
        assert "/test_node" in result['stdout']
    
    @patch('subprocess.run')
    def test_set_parameter_success(self, mock_subprocess):
        """Test successful parameter setting."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Parameter set successfully",
            stderr=""
        )
        
        ros_utils = ROSUtils(dry_run=False)
        result = ros_utils.set_parameter("/node", "param", "value")
        
        assert result['success'] is True
        assert "Parameter set successfully" in result['stdout']
    
    @patch('subprocess.run')
    def test_get_parameter_success(self, mock_subprocess):
        """Test successful parameter retrieval."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Parameter value: 42",
            stderr=""
        )
        
        ros_utils = ROSUtils(dry_run=False)
        result = ros_utils.get_parameter("/node", "param")
        
        assert result['success'] is True
        assert "Parameter value: 42" in result['stdout']


class TestROSEnvironmentChecker:
    """Test ROS environment checking middleware."""
    
    @patch('shutil.which')
    @patch('os.environ.get')
    def test_check_ros_installation_found(self, mock_env_get, mock_which):
        """Test ROS installation detection when ROS is available."""
        mock_which.return_value = "/usr/bin/ros2"
        mock_env_get.side_effect = lambda key, default=None: {
            'ROS_DISTRO': 'humble',
            'ROS_VERSION': '2'
        }.get(key, default)
        
        checker = ROSEnvironmentChecker()
        result = checker.check_ros_installation()
        
        assert result['installed'] is True
        assert result['distro'] == 'humble'
        assert result['version'] == '2'
        assert len(result['issues']) == 0
    
    @patch('shutil.which')
    @patch('os.environ.get')
    def test_check_ros_installation_not_found(self, mock_env_get, mock_which):
        """Test ROS installation detection when ROS is not available."""
        mock_which.return_value = None
        mock_env_get.return_value = None
        
        checker = ROSEnvironmentChecker()
        result = checker.check_ros_installation()
        
        assert result['installed'] is False
        assert result['distro'] is None
        assert len(result['issues']) > 0
    
    @patch('os.environ.get')
    def test_check_environment_sourcing_complete(self, mock_env_get):
        """Test environment sourcing when all variables are set."""
        mock_env_get.side_effect = lambda key, default=None: {
            'ROS_DISTRO': 'humble',
            'ROS_VERSION': '2',
            'AMENT_PREFIX_PATH': '/opt/ros/humble',
            'COLCON_PREFIX_PATH': '/workspace/install'
        }.get(key, default)
        
        checker = ROSEnvironmentChecker()
        result = checker.check_environment_sourcing()
        
        assert result['sourced'] is True
        assert len(result['missing_vars']) == 0
    
    @patch('os.environ.get')
    def test_check_environment_sourcing_incomplete(self, mock_env_get):
        """Test environment sourcing when variables are missing."""
        mock_env_get.side_effect = lambda key, default=None: {
            'ROS_DISTRO': 'humble'
        }.get(key, default)
        
        checker = ROSEnvironmentChecker()
        result = checker.check_environment_sourcing()
        
        assert result['sourced'] is False
        assert 'ROS_VERSION' in result['missing_vars']
        assert 'AMENT_PREFIX_PATH' in result['missing_vars']
    
    @patch('shutil.which')
    def test_check_command_availability_available(self, mock_which):
        """Test command availability when commands exist."""
        mock_which.side_effect = lambda cmd: "/usr/bin/ros2" if "ros2" in cmd else None
        
        checker = ROSEnvironmentChecker()
        result = checker.check_command_availability()
        
        assert result['ros2'] is True
        assert result['ros2 node'] is True
        assert result['ros2 topic'] is True
    
    @patch('shutil.which')
    def test_check_command_availability_missing(self, mock_which):
        """Test command availability when commands are missing."""
        mock_which.return_value = None
        
        checker = ROSEnvironmentChecker()
        result = checker.check_command_availability()
        
        assert result['ros2'] is False
        assert result['ros2 node'] is False
        assert result['ros2 topic'] is False
    
    def test_get_environment_summary_ready(self):
        """Test environment summary when ROS is ready."""
        checker = ROSEnvironmentChecker()
        
        with patch.object(checker, 'check_ros_installation') as mock_install, \
             patch.object(checker, 'check_environment_sourcing') as mock_sourcing, \
             patch.object(checker, 'check_command_availability') as mock_commands:
            
            mock_install.return_value = {
                'installed': True,
                'distro': 'humble',
                'version': '2',
                'issues': []
            }
            mock_sourcing.return_value = {
                'sourced': True,
                'missing_vars': []
            }
            mock_commands.return_value = {
                'ros2': True,
                'ros2 node': True,
                'ros2 topic': True,
                'ros2 param': True
            }
            
            result = checker.get_environment_summary()
            
            assert result['ready'] is True
            assert len(result['errors']) == 0
    
    def test_get_environment_summary_not_ready(self):
        """Test environment summary when ROS is not ready."""
        checker = ROSEnvironmentChecker()
        
        with patch.object(checker, 'check_ros_installation') as mock_install, \
             patch.object(checker, 'check_environment_sourcing') as mock_sourcing, \
             patch.object(checker, 'check_command_availability') as mock_commands:
            
            mock_install.return_value = {
                'installed': False,
                'distro': None,
                'version': None,
                'issues': ['ROS not found']
            }
            mock_sourcing.return_value = {
                'sourced': False,
                'missing_vars': ['ROS_DISTRO']
            }
            mock_commands.return_value = {
                'ros2': False,
                'ros2 node': False
            }
            
            result = checker.get_environment_summary()
            
            assert result['ready'] is False
            assert len(result['errors']) > 0
    
    def test_get_setup_instructions(self):
        """Test setup instructions generation."""
        checker = ROSEnvironmentChecker()
        instructions = checker.get_setup_instructions()
        
        assert isinstance(instructions, list)
        assert len(instructions) > 0
        assert any("install" in inst.lower() for inst in instructions)


class TestCLILogger:
    """Test CLI logging middleware."""
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        assert cli_logger is not None
    
    def test_log_command_success(self):
        """Test logging successful command execution."""
        with patch.object(cli_logger.logger, 'info') as mock_info:
            cli_logger.log_command('test_cmd', {'arg': 'value'}, True)
            mock_info.assert_called()
    
    def test_log_command_failure(self):
        """Test logging failed command execution."""
        with patch.object(cli_logger.logger, 'error') as mock_error:
            cli_logger.log_command('test_cmd', {'arg': 'value'}, False)
            mock_error.assert_called()
    
    def test_log_plugin_operation(self):
        """Test logging plugin operations."""
        with patch.object(cli_logger.logger, 'info') as mock_info:
            cli_logger.log_plugin_operation('install', 'test_plugin', True)
            mock_info.assert_called()
    
    def test_log_system_event(self):
        """Test logging system events."""
        with patch.object(cli_logger.logger, 'info') as mock_info:
            cli_logger.log_system_event('startup', 'CLI initialized')
            mock_info.assert_called()


class TestSimulatorManager:
    """Test simulator management middleware."""
    
    def test_simulator_manager_initialization(self):
        """Test simulator manager initialization."""
        manager = SimulatorManager()
        assert manager.dry_run is False
        assert isinstance(manager.supported_simulators, dict)
    
    def test_set_dry_run_mode(self):
        """Test setting dry-run mode."""
        manager = SimulatorManager()
        manager.dry_run = True
        assert manager.dry_run is True
    
    @patch('subprocess.run')
    def test_launch_gazebo_success(self, mock_subprocess):
        """Test successful Gazebo launch."""
        mock_subprocess.return_value = Mock(returncode=0)
        
        manager = SimulatorManager()
        result = manager.launch('gazebo')
        
        assert result['success'] is True
        assert 'gazebo' in result['message'].lower()
    
    def test_launch_gazebo_dry_run(self):
        """Test Gazebo launch in dry-run mode."""
        manager = SimulatorManager()
        manager.dry_run = True
        
        result = manager.launch('gazebo')
        
        assert result['success'] is True
        assert 'DRY RUN' in result['message']
    
    def test_launch_unsupported_simulator(self):
        """Test launching unsupported simulator."""
        manager = SimulatorManager()
        result = manager.launch('unsupported_sim')
        
        assert result['success'] is False
        assert 'not supported' in result['message']
    
    @patch('subprocess.run')
    def test_pause_simulator_success(self, mock_subprocess):
        """Test successful simulator pause."""
        mock_subprocess.return_value = Mock(returncode=0)
        
        manager = SimulatorManager()
        result = manager.pause('gazebo')
        
        assert result['success'] is True
    
    @patch('subprocess.run')
    def test_resume_simulator_success(self, mock_subprocess):
        """Test successful simulator resume."""
        mock_subprocess.return_value = Mock(returncode=0)
        
        manager = SimulatorManager()
        result = manager.resume('gazebo')
        
        assert result['success'] is True
    
    @patch('subprocess.run')
    def test_shutdown_simulator_success(self, mock_subprocess):
        """Test successful simulator shutdown."""
        mock_subprocess.return_value = Mock(returncode=0)
        
        manager = SimulatorManager()
        result = manager.shutdown('gazebo')
        
        assert result['success'] is True
    
    @patch('subprocess.run')
    def test_get_status_running(self, mock_subprocess):
        """Test getting simulator status when running."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="gazebo_process"
        )
        
        manager = SimulatorManager()
        result = manager.get_status('gazebo')
        
        assert 'gazebo' in result
    
    @patch('shutil.which')
    def test_list_simulators(self, mock_which):
        """Test listing available simulators."""
        mock_which.side_effect = lambda cmd: "/usr/bin/gazebo" if cmd == "gazebo" else None
        
        manager = SimulatorManager()
        result = manager.list_simulators()
        
        assert 'gazebo' in result
        assert result['gazebo']['installed'] is True
    
    def test_validate_simulator_supported(self):
        """Test validating supported simulator."""
        manager = SimulatorManager()
        assert manager._validate_simulator('gazebo') is True
    
    def test_validate_simulator_unsupported(self):
        """Test validating unsupported simulator."""
        manager = SimulatorManager()
        assert manager._validate_simulator('unsupported') is False


class TestMiddlewareIntegration:
    """Test middleware component integration."""
    
    def test_ros_utils_with_env_checker(self):
        """Test ROS utilities integration with environment checker."""
        checker = ROSEnvironmentChecker()
        ros_utils = ROSUtils(dry_run=True)
        
        # In a real scenario, ros_utils could use checker to validate environment
        # For now, just test they can coexist
        assert checker is not None
        assert ros_utils is not None
    
    def test_logger_with_simulator_manager(self):
        """Test logger integration with simulator manager."""
        manager = SimulatorManager()
        
        with patch.object(cli_logger.logger, 'info') as mock_info:
            # Simulate logging a simulator operation
            cli_logger.log_system_event('simulator', 'Gazebo launched')
            mock_info.assert_called()
    
    def test_dry_run_consistency(self):
        """Test dry-run mode consistency across middleware."""
        ros_utils = ROSUtils(dry_run=True)
        sim_manager = SimulatorManager()
        sim_manager.dry_run = True
        
        assert ros_utils.dry_run is True
        assert sim_manager.dry_run is True
        
        # Both should handle dry-run mode properly
        ros_result = ros_utils.publish_message("/test", "std_msgs/String", 1.0, "{}", 1)
        sim_result = sim_manager.launch('gazebo')
        
        assert ros_result['success'] is True
        assert sim_result['success'] is True
        assert 'DRY RUN' in ros_result['stdout']
        assert 'DRY RUN' in sim_result['message']