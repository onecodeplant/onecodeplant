"""
ROS Environment Checker for OneCodePlant.

This module provides utilities to check ROS 2 installation status,
environment variables, and system requirements.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from .logger import cli_logger


class ROSEnvironmentChecker:
    """
    Checker for ROS 2 environment and installation status.
    
    Provides methods to verify ROS 2 installation, sourcing status,
    and environment configuration for proper CLI operation.
    """
    
    def __init__(self):
        """Initialize the ROS environment checker."""
        self.ros_distro = os.getenv('ROS_DISTRO')
        self.ros_version = os.getenv('ROS_VERSION')
        self.ament_prefix_path = os.getenv('AMENT_PREFIX_PATH')
        
    def check_ros_installation(self) -> Dict[str, Any]:
        """
        Check if ROS 2 is installed on the system.
        
        Returns:
            Dictionary with installation status and details
        """
        result = {
            'installed': False,
            'distro': None,
            'version': None,
            'paths': [],
            'issues': []
        }
        
        try:
            # Check for ros2 command
            ros2_path = shutil.which('ros2')
            if ros2_path:
                result['installed'] = True
                result['paths'].append(ros2_path)
                cli_logger.debug(f"Found ros2 command at: {ros2_path}")
            else:
                result['issues'].append("ros2 command not found in PATH")
                cli_logger.warning("ros2 command not found in PATH")
            
            # Check ROS_DISTRO environment variable
            if self.ros_distro:
                result['distro'] = self.ros_distro
                cli_logger.debug(f"ROS_DISTRO: {self.ros_distro}")
            else:
                result['issues'].append("ROS_DISTRO environment variable not set")
                cli_logger.warning("ROS_DISTRO environment variable not set")
            
            # Check ROS_VERSION
            if self.ros_version:
                result['version'] = self.ros_version
                cli_logger.debug(f"ROS_VERSION: {self.ros_version}")
                
                # Ensure it's ROS 2
                if self.ros_version != '2':
                    result['issues'].append(f"Expected ROS 2, found ROS {self.ros_version}")
                    cli_logger.warning(f"Expected ROS 2, found ROS {self.ros_version}")
            else:
                result['issues'].append("ROS_VERSION environment variable not set")
                cli_logger.warning("ROS_VERSION environment variable not set")
            
            # Check AMENT_PREFIX_PATH
            if self.ament_prefix_path:
                paths = self.ament_prefix_path.split(':')
                result['paths'].extend(paths)
                cli_logger.debug(f"AMENT_PREFIX_PATH: {self.ament_prefix_path}")
            else:
                result['issues'].append("AMENT_PREFIX_PATH environment variable not set")
                cli_logger.warning("AMENT_PREFIX_PATH environment variable not set")
            
            # Final determination
            if result['issues']:
                result['installed'] = False
                
        except Exception as e:
            result['issues'].append(f"Error checking ROS installation: {e}")
            cli_logger.error(f"Error checking ROS installation: {e}")
        
        return result
    
    def check_ros_sourcing(self) -> Dict[str, Any]:
        """
        Check if ROS 2 is properly sourced.
        
        Returns:
            Dictionary with sourcing status and recommendations
        """
        result = {
            'sourced': False,
            'setup_files': [],
            'missing_vars': [],
            'recommendations': []
        }
        
        # Required environment variables for ROS 2
        required_vars = [
            'ROS_DISTRO',
            'ROS_VERSION',
            'AMENT_PREFIX_PATH',
            'COLCON_PREFIX_PATH'
        ]
        
        for var in required_vars:
            if os.getenv(var):
                cli_logger.debug(f"Found required variable: {var}")
            else:
                result['missing_vars'].append(var)
                cli_logger.debug(f"Missing required variable: {var}")
        
        # Check for common setup files
        common_setup_paths = [
            f"/opt/ros/{self.ros_distro}/setup.bash" if self.ros_distro else None,
            f"/opt/ros/{self.ros_distro}/setup.sh" if self.ros_distro else None,
            "~/ros2_ws/install/setup.bash",
            "~/dev_ws/install/setup.bash"
        ]
        
        for setup_path in common_setup_paths:
            if setup_path and Path(setup_path.replace('~', str(Path.home()))).exists():
                result['setup_files'].append(setup_path)
                cli_logger.debug(f"Found setup file: {setup_path}")
        
        # Determine if properly sourced
        result['sourced'] = len(result['missing_vars']) == 0
        
        # Generate recommendations
        if not result['sourced']:
            if self.ros_distro:
                result['recommendations'].append(f"Source ROS 2 setup: source /opt/ros/{self.ros_distro}/setup.bash")
            else:
                result['recommendations'].append("Install and source ROS 2")
            
            if not result['setup_files']:
                result['recommendations'].append("No ROS 2 setup files found in common locations")
        
        return result
    
    def verify_ros_commands(self) -> Dict[str, bool]:
        """
        Verify that essential ROS 2 commands are available.
        
        Returns:
            Dictionary mapping command names to availability status
        """
        commands = [
            'ros2',
            'ros2 node',
            'ros2 topic',
            'ros2 param',
            'ros2 service',
            'ros2 action'
        ]
        
        result = {}
        
        for cmd in commands:
            try:
                # Test command availability
                cmd_parts = cmd.split()
                if len(cmd_parts) == 1:
                    # Simple command check
                    available = shutil.which(cmd_parts[0]) is not None
                else:
                    # Test subcommand by running help
                    proc = subprocess.run(
                        cmd_parts + ['--help'],
                        capture_output=True,
                        timeout=5
                    )
                    available = proc.returncode == 0
                
                result[cmd] = available
                cli_logger.debug(f"Command '{cmd}' available: {available}")
                
            except Exception as e:
                result[cmd] = False
                cli_logger.debug(f"Error checking command '{cmd}': {e}")
        
        return result
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the ROS environment.
        
        Returns:
            Dictionary with complete environment assessment
        """
        installation = self.check_ros_installation()
        sourcing = self.check_ros_sourcing()
        commands = self.verify_ros_commands()
        
        summary = {
            'installation': installation,
            'sourcing': sourcing,
            'commands': commands,
            'ready': (installation['installed'] and 
                     sourcing['sourced'] and 
                     all(commands.values())),
            'warnings': [],
            'errors': []
        }
        
        # Collect warnings and errors
        if installation['issues']:
            summary['errors'].extend(installation['issues'])
        
        if sourcing['missing_vars']:
            summary['warnings'].extend([f"Missing variable: {var}" for var in sourcing['missing_vars']])
        
        unavailable_commands = [cmd for cmd, available in commands.items() if not available]
        if unavailable_commands:
            summary['warnings'].extend([f"Command unavailable: {cmd}" for cmd in unavailable_commands])
        
        # Log summary
        if summary['ready']:
            cli_logger.info("ROS 2 environment is ready")
        else:
            cli_logger.warning("ROS 2 environment has issues")
            for error in summary['errors']:
                cli_logger.error(error)
            for warning in summary['warnings']:
                cli_logger.warning(warning)
        
        return summary
    
    def get_setup_instructions(self) -> List[str]:
        """
        Get setup instructions for configuring ROS 2.
        
        Returns:
            List of setup instruction strings
        """
        instructions = []
        
        if not self.ros_distro:
            instructions.extend([
                "1. Install ROS 2 (recommended: Humble or Iron)",
                "   Ubuntu: sudo apt install ros-humble-desktop",
                "   Other: Follow official ROS 2 installation guide"
            ])
        
        if self.ros_distro:
            instructions.extend([
                f"2. Source ROS 2 setup in your shell profile:",
                f"   echo 'source /opt/ros/{self.ros_distro}/setup.bash' >> ~/.bashrc",
                f"   source ~/.bashrc"
            ])
        
        instructions.extend([
            "3. Verify installation:",
            "   ros2 --help",
            "   ros2 node list"
        ])
        
        return instructions