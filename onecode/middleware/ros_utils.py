"""
ROS 2 Utilities for OneCodePlant.

This module provides core utilities for interacting with ROS 2 systems,
including node operations, topic management, parameter handling, and service calls.
"""

import subprocess
import json
import time
import threading
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .logger import cli_logger
from .checks import ROSEnvironmentChecker


class ROSUtils:
    """
    Core utilities for ROS 2 operations.
    
    Provides methods for publishing, subscribing, parameter management,
    node operations, and other ROS 2 middleware interactions.
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize ROS utilities.
        
        Args:
            dry_run: If True, simulate operations without executing them
        """
        self.dry_run = dry_run
        self.env_checker = ROSEnvironmentChecker()
        self._running_processes = []
        
        # Setup signal handler for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle signals for cleanup."""
        self.cleanup_processes()
        sys.exit(0)
    
    def _execute_command(self, command: List[str], timeout: Optional[float] = None, 
                        capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute a ROS command with proper error handling.
        
        Args:
            command: Command to execute as list of strings
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dictionary with execution results
        """
        result = {
            'success': False,
            'stdout': '',
            'stderr': '',
            'returncode': -1,
            'command': ' '.join(command)
        }
        
        if self.dry_run:
            cli_logger.info(f"DRY RUN: Would execute: {result['command']}")
            result['success'] = True
            result['stdout'] = f"DRY RUN: Command would be executed: {result['command']}"
            return result
        
        try:
            cli_logger.debug(f"Executing command: {result['command']}")
            
            proc = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            result['returncode'] = proc.returncode
            result['success'] = proc.returncode == 0
            
            if capture_output:
                result['stdout'] = proc.stdout.strip()
                result['stderr'] = proc.stderr.strip()
            
            if result['success']:
                cli_logger.debug(f"Command succeeded: {result['command']}")
            else:
                cli_logger.error(f"Command failed: {result['command']} - {result['stderr']}")
                
        except subprocess.TimeoutExpired:
            result['stderr'] = f"Command timed out after {timeout} seconds"
            cli_logger.error(f"Command timed out: {result['command']}")
        except Exception as e:
            result['stderr'] = str(e)
            cli_logger.error(f"Command execution error: {result['command']} - {e}")
        
        return result
    
    def check_environment(self) -> bool:
        """
        Check if ROS 2 environment is ready.
        
        Returns:
            True if environment is ready, False otherwise
        """
        env_summary = self.env_checker.get_environment_summary()
        return env_summary['ready']
    
    def publish_message(self, topic: str, message_type: str, rate: float = 1.0, 
                       data: Optional[str] = None, count: int = 1) -> Dict[str, Any]:
        """
        Publish messages to a ROS 2 topic.
        
        Args:
            topic: Topic name to publish to
            message_type: ROS message type (e.g., 'std_msgs/String')
            rate: Publishing rate in Hz
            data: Message data as string or JSON
            count: Number of messages to publish (0 for infinite)
            
        Returns:
            Dictionary with publishing results
        """
        command = ['ros2', 'topic', 'pub']
        
        if count == 0:
            # Infinite publishing
            pass
        elif count == 1:
            command.append('--once')
        else:
            command.extend(['--times', str(count)])
        
        if rate != 1.0:
            command.extend(['--rate', str(rate)])
        
        command.append(topic)
        command.append(message_type)
        
        if data:
            command.append(data)
        else:
            # Default empty message based on type
            if 'String' in message_type:
                command.append('"{data: "Hello from OneCodePlant"}"')
            elif 'Twist' in message_type:
                command.append('"{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"')
            else:
                command.append('"{}"')
        
        result = self._execute_command(command, timeout=30)
        
        cli_logger.log_ros_operation('publish', {
            'topic': topic,
            'message_type': message_type,
            'rate': rate,
            'count': count
        }, result['success'])
        
        return result
    
    def echo_topic(self, topic: str, count: int = 0, timeout: float = 5.0) -> Dict[str, Any]:
        """
        Echo messages from a ROS 2 topic.
        
        Args:
            topic: Topic name to echo from
            count: Number of messages to echo (0 for infinite)
            timeout: Timeout for receiving messages
            
        Returns:
            Dictionary with echo results
        """
        command = ['ros2', 'topic', 'echo']
        
        if count > 0:
            command.extend(['--once' if count == 1 else '--times', str(count)])
        
        command.append(topic)
        
        # For infinite echo, we need special handling
        if count == 0 and not self.dry_run:
            return self._start_continuous_echo(topic, timeout)
        
        result = self._execute_command(command, timeout=timeout)
        
        cli_logger.log_ros_operation('echo', {
            'topic': topic,
            'count': count,
            'timeout': timeout
        }, result['success'])
        
        return result
    
    def _start_continuous_echo(self, topic: str, timeout: float) -> Dict[str, Any]:
        """Start continuous topic echo in a separate process."""
        try:
            print(f"Echoing topic '{topic}' (Press Ctrl+C to stop)")
            
            proc = subprocess.Popen(
                ['ros2', 'topic', 'echo', topic],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self._running_processes.append(proc)
            
            # Wait for process or user interruption
            try:
                proc.wait()
            except KeyboardInterrupt:
                proc.terminate()
                proc.wait()
                print("\nTopic echo stopped by user")
            
            return {
                'success': True,
                'stdout': 'Continuous echo completed',
                'stderr': '',
                'returncode': 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def get_parameter(self, node_name: str, param_name: str) -> Dict[str, Any]:
        """
        Get a parameter value from a ROS 2 node.
        
        Args:
            node_name: Name of the node
            param_name: Name of the parameter
            
        Returns:
            Dictionary with parameter value and metadata
        """
        command = ['ros2', 'param', 'get', node_name, param_name]
        result = self._execute_command(command)
        
        cli_logger.log_ros_operation('get_parameter', {
            'node': node_name,
            'parameter': param_name
        }, result['success'])
        
        return result
    
    def set_parameter(self, node_name: str, param_name: str, value: str) -> Dict[str, Any]:
        """
        Set a parameter value on a ROS 2 node.
        
        Args:
            node_name: Name of the node
            param_name: Name of the parameter
            value: Parameter value as string
            
        Returns:
            Dictionary with operation results
        """
        command = ['ros2', 'param', 'set', node_name, param_name, value]
        result = self._execute_command(command)
        
        cli_logger.log_ros_operation('set_parameter', {
            'node': node_name,
            'parameter': param_name,
            'value': value
        }, result['success'])
        
        return result
    
    def list_parameters(self, node_name: Optional[str] = None) -> Dict[str, Any]:
        """
        List parameters from a node or all nodes.
        
        Args:
            node_name: Name of the node (None for all nodes)
            
        Returns:
            Dictionary with parameter list
        """
        command = ['ros2', 'param', 'list']
        if node_name:
            command.append(node_name)
        
        result = self._execute_command(command)
        
        cli_logger.log_ros_operation('list_parameters', {
            'node': node_name or 'all'
        }, result['success'])
        
        return result
    
    def list_nodes(self) -> Dict[str, Any]:
        """
        List all active ROS 2 nodes.
        
        Returns:
            Dictionary with node list
        """
        command = ['ros2', 'node', 'list']
        result = self._execute_command(command)
        
        if result['success'] and result['stdout']:
            # Parse node list
            nodes = [line.strip() for line in result['stdout'].split('\n') if line.strip()]
            result['nodes'] = nodes
        else:
            result['nodes'] = []
        
        cli_logger.log_ros_operation('list_nodes', {}, result['success'])
        
        return result
    
    def get_node_info(self, node_name: str) -> Dict[str, Any]:
        """
        Get information about a specific node.
        
        Args:
            node_name: Name of the node
            
        Returns:
            Dictionary with node information
        """
        command = ['ros2', 'node', 'info', node_name]
        result = self._execute_command(command)
        
        cli_logger.log_ros_operation('get_node_info', {
            'node': node_name
        }, result['success'])
        
        return result
    
    def kill_node(self, node_name: str) -> Dict[str, Any]:
        """
        Kill a specific ROS 2 node.
        
        Args:
            node_name: Name of the node to kill
            
        Returns:
            Dictionary with operation results
        """
        # ROS 2 doesn't have a direct kill command, so we simulate it
        if self.dry_run:
            return {
                'success': True,
                'stdout': f'DRY RUN: Would kill node {node_name}',
                'stderr': '',
                'returncode': 0
            }
        
        # In practice, this would require process management
        # For now, we provide a placeholder implementation
        result = {
            'success': False,
            'stdout': '',
            'stderr': 'Node killing not implemented - use system process management',
            'returncode': -1
        }
        
        cli_logger.log_ros_operation('kill_node', {
            'node': node_name
        }, result['success'])
        
        return result
    
    def list_topics(self) -> Dict[str, Any]:
        """
        List all active ROS 2 topics.
        
        Returns:
            Dictionary with topic list
        """
        command = ['ros2', 'topic', 'list']
        result = self._execute_command(command)
        
        if result['success'] and result['stdout']:
            topics = [line.strip() for line in result['stdout'].split('\n') if line.strip()]
            result['topics'] = topics
        else:
            result['topics'] = []
        
        cli_logger.log_ros_operation('list_topics', {}, result['success'])
        
        return result
    
    def get_topic_info(self, topic: str) -> Dict[str, Any]:
        """
        Get information about a specific topic.
        
        Args:
            topic: Name of the topic
            
        Returns:
            Dictionary with topic information
        """
        command = ['ros2', 'topic', 'info', topic]
        result = self._execute_command(command)
        
        cli_logger.log_ros_operation('get_topic_info', {
            'topic': topic
        }, result['success'])
        
        return result
    
    def cleanup_processes(self) -> None:
        """Clean up any running processes."""
        for proc in self._running_processes:
            try:
                if proc.poll() is None:  # Process is still running
                    proc.terminate()
                    proc.wait(timeout=5)
            except Exception as e:
                cli_logger.error(f"Error cleaning up process: {e}")
        
        self._running_processes.clear()
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive ROS 2 system information.
        
        Returns:
            Dictionary with system information
        """
        info = {
            'environment': self.env_checker.get_environment_summary(),
            'nodes': self.list_nodes(),
            'topics': self.list_topics(),
            'dry_run': self.dry_run
        }
        
        return info