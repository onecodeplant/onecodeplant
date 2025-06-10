"""
Simulator Control Abstraction Layer for OneCodePlant.

This module provides unified interfaces for controlling various robot simulators
including Gazebo and Webots, with support for launch, pause, resume, reset, and shutdown operations.
"""

import os
import shutil
import subprocess
import time
import signal
import psutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from .logger import cli_logger


class BaseSimulator(ABC):
    """
    Abstract base class for robot simulator controllers.
    
    This class defines the interface that all simulator implementations must follow,
    ensuring consistency across different simulator backends.
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize the base simulator.
        
        Args:
            dry_run: If True, simulate operations without executing them
        """
        self.dry_run = dry_run
        self.process = None
        self.is_running = False
        self.world_file = None
        self.launch_file = None
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the simulator name."""
        pass
    
    @property
    @abstractmethod
    def executable(self) -> str:
        """Get the main executable name."""
        pass
    
    @abstractmethod
    def check_installation(self) -> Dict[str, Any]:
        """
        Check if the simulator is installed and available.
        
        Returns:
            Dictionary with installation status and details
        """
        pass
    
    @abstractmethod
    def launch(self, world: Optional[str] = None, launch_file: Optional[str] = None, 
               headless: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Launch the simulator.
        
        Args:
            world: World file or name to load
            launch_file: Custom launch file to use
            headless: Run without GUI
            **kwargs: Additional simulator-specific options
            
        Returns:
            Dictionary with launch results
        """
        pass
    
    @abstractmethod
    def pause(self) -> Dict[str, Any]:
        """
        Pause the simulation.
        
        Returns:
            Dictionary with pause operation results
        """
        pass
    
    @abstractmethod
    def resume(self) -> Dict[str, Any]:
        """
        Resume the simulation.
        
        Returns:
            Dictionary with resume operation results
        """
        pass
    
    @abstractmethod
    def reset(self) -> Dict[str, Any]:
        """
        Reset the simulation to initial state.
        
        Returns:
            Dictionary with reset operation results
        """
        pass
    
    def shutdown(self) -> Dict[str, Any]:
        """
        Shutdown the simulator.
        
        Returns:
            Dictionary with shutdown results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name
        }
        
        if self.dry_run:
            result['success'] = True
            result['message'] = f"[DRY RUN] Would shutdown {self.name} simulator"
            cli_logger.info(f"[DRY RUN] Simulated shutdown of {self.name}")
            return result
        
        try:
            if self.process and self.process.poll() is None:
                # Graceful shutdown
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown fails
                    self.process.kill()
                    self.process.wait()
                
                self.is_running = False
                result['success'] = True
                result['message'] = f"{self.name} simulator shutdown successfully"
                cli_logger.info(f"Shutdown {self.name} simulator (PID: {self.process.pid})")
            else:
                result['success'] = True
                result['message'] = f"{self.name} simulator was not running"
                cli_logger.info(f"{self.name} simulator was not running")
                
        except Exception as e:
            result['message'] = f"Error shutting down {self.name}: {str(e)}"
            cli_logger.error(f"Error shutting down {self.name}: {str(e)}")
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the simulator.
        
        Returns:
            Dictionary with simulator status information
        """
        status = {
            'simulator': self.name,
            'running': False,
            'pid': None,
            'world': self.world_file,
            'launch_file': self.launch_file
        }
        
        if self.process and self.process.poll() is None:
            status['running'] = True
            status['pid'] = self.process.pid
        
        return status
    
    def _execute_command(self, command: List[str], timeout: Optional[float] = None,
                        capture_output: bool = True, background: bool = False) -> Dict[str, Any]:
        """
        Execute a command with proper error handling.
        
        Args:
            command: Command to execute as list of strings
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
            background: Whether to run command in background
            
        Returns:
            Dictionary with execution results
        """
        result = {
            'success': False,
            'stdout': '',
            'stderr': '',
            'returncode': None,
            'command': ' '.join(command)
        }
        
        if self.dry_run:
            result['success'] = True
            result['stdout'] = f"[DRY RUN] Would execute: {' '.join(command)}"
            cli_logger.info(f"[DRY RUN] Command: {' '.join(command)}")
            return result
        
        try:
            if background:
                # Start process in background
                self.process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE if capture_output else None,
                    stderr=subprocess.PIPE if capture_output else None,
                    preexec_fn=os.setsid if os.name != 'nt' else None
                )
                result['success'] = True
                result['stdout'] = f"Process started with PID: {self.process.pid}"
                cli_logger.info(f"Started background process: {' '.join(command)} (PID: {self.process.pid})")
            else:
                # Run synchronous command
                process = subprocess.run(
                    command,
                    capture_output=capture_output,
                    text=True,
                    timeout=timeout
                )
                
                result['returncode'] = process.returncode
                result['success'] = process.returncode == 0
                
                if capture_output:
                    result['stdout'] = process.stdout
                    result['stderr'] = process.stderr
                
                cli_logger.debug(f"Command executed: {' '.join(command)} (exit code: {process.returncode})")
                
        except subprocess.TimeoutExpired:
            result['stderr'] = f"Command timed out after {timeout} seconds"
            cli_logger.error(f"Command timeout: {' '.join(command)}")
        except subprocess.CalledProcessError as e:
            result['returncode'] = e.returncode
            result['stderr'] = str(e)
            cli_logger.error(f"Command failed: {' '.join(command)} - {str(e)}")
        except Exception as e:
            result['stderr'] = str(e)
            cli_logger.error(f"Command error: {' '.join(command)} - {str(e)}")
        
        return result


class GazeboSimulator(BaseSimulator):
    """
    Gazebo simulator controller implementation.
    
    Provides control interface for Gazebo simulation environment
    using ros2 launch and gz CLI commands.
    """
    
    @property
    def name(self) -> str:
        """Get the simulator name."""
        return "gazebo"
    
    @property
    def executable(self) -> str:
        """Get the main executable name."""
        return "gz"
    
    def check_installation(self) -> Dict[str, Any]:
        """
        Check if Gazebo is installed and available.
        
        Returns:
            Dictionary with installation status and details
        """
        result = {
            'installed': False,
            'version': None,
            'executables': {},
            'issues': []
        }
        
        # Check for gz command (Gazebo Garden/Harmonic)
        gz_path = shutil.which('gz')
        if gz_path:
            result['executables']['gz'] = gz_path
            try:
                version_result = self._execute_command(['gz', '--version'], timeout=5)
                if version_result['success']:
                    result['version'] = version_result['stdout'].strip()
                    result['installed'] = True
            except Exception as e:
                result['issues'].append(f"Error checking gz version: {str(e)}")
        else:
            result['issues'].append("gz command not found in PATH")
        
        # Check for gazebo command (Legacy Gazebo Classic)
        gazebo_path = shutil.which('gazebo')
        if gazebo_path:
            result['executables']['gazebo'] = gazebo_path
            if not result['installed']:
                try:
                    version_result = self._execute_command(['gazebo', '--version'], timeout=5)
                    if version_result['success']:
                        result['version'] = version_result['stdout'].strip()
                        result['installed'] = True
                except Exception as e:
                    result['issues'].append(f"Error checking gazebo version: {str(e)}")
        
        # Check for ros2 command for launch files
        ros2_path = shutil.which('ros2')
        if ros2_path:
            result['executables']['ros2'] = ros2_path
        else:
            result['issues'].append("ros2 command not found in PATH")
        
        if not result['installed']:
            result['issues'].append("No working Gazebo installation found")
        
        return result
    
    def launch(self, world: Optional[str] = None, launch_file: Optional[str] = None,
               headless: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Launch Gazebo simulator.
        
        Args:
            world: World file (.sdf) or world name to load
            launch_file: Custom ROS 2 launch file to use
            headless: Run without GUI
            **kwargs: Additional options (robot_model, etc.)
            
        Returns:
            Dictionary with launch results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name,
            'pid': None
        }
        
        # Check installation first
        install_check = self.check_installation()
        if not install_check['installed']:
            result['message'] = f"Gazebo not installed: {', '.join(install_check['issues'])}"
            return result
        
        self.world_file = world
        self.launch_file = launch_file
        
        try:
            if launch_file:
                # Use custom launch file
                if not Path(launch_file).exists():
                    result['message'] = f"Launch file not found: {launch_file}"
                    return result
                
                command = ['ros2', 'launch', launch_file]
                if headless:
                    command.extend(['gui:=false'])
                
            else:
                # Use direct gz sim command
                command = ['gz', 'sim']
                
                if world:
                    if Path(world).exists():
                        command.extend([world])
                    else:
                        # Try to find world in common locations
                        world_paths = [
                            f"/usr/share/gazebo-11/worlds/{world}",
                            f"/usr/share/gazebo/worlds/{world}",
                            f"~/.gazebo/worlds/{world}",
                            world  # Use as-is if not found
                        ]
                        
                        found_world = None
                        for world_path in world_paths:
                            expanded_path = Path(world_path.replace('~', str(Path.home())))
                            if expanded_path.exists():
                                found_world = str(expanded_path)
                                break
                        
                        if found_world:
                            command.extend([found_world])
                        else:
                            command.extend([world])  # Let Gazebo handle the error
                
                if headless:
                    command.extend(['-s'])  # Server mode only
                
                # Add robot model if specified
                robot_model = kwargs.get('robot_model')
                if robot_model:
                    command.extend(['--ros-args', '-p', f'robot_model:={robot_model}'])
            
            # Execute command in background
            exec_result = self._execute_command(command, background=True)
            
            if exec_result['success']:
                self.is_running = True
                result['success'] = True
                result['pid'] = self.process.pid if self.process else None
                result['message'] = f"Gazebo launched successfully (PID: {result['pid']})"
                
                # Give Gazebo time to start
                time.sleep(2)
                
                cli_logger.info(f"Launched Gazebo with command: {' '.join(command)}")
            else:
                result['message'] = f"Failed to launch Gazebo: {exec_result.get('stderr', 'Unknown error')}"
                
        except Exception as e:
            result['message'] = f"Error launching Gazebo: {str(e)}"
            cli_logger.error(f"Error launching Gazebo: {str(e)}")
        
        return result
    
    def pause(self) -> Dict[str, Any]:
        """
        Pause Gazebo simulation.
        
        Returns:
            Dictionary with pause operation results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name
        }
        
        if not self.is_running:
            result['message'] = "Gazebo is not running"
            return result
        
        try:
            # Use gz service to pause simulation
            exec_result = self._execute_command(['gz', 'service', '-s', '/world/pause', '--reqtype', 'gz.msgs.Empty'])
            
            if exec_result['success']:
                result['success'] = True
                result['message'] = "Gazebo simulation paused"
                cli_logger.info("Paused Gazebo simulation")
            else:
                result['message'] = f"Failed to pause Gazebo: {exec_result.get('stderr', 'Unknown error')}"
                
        except Exception as e:
            result['message'] = f"Error pausing Gazebo: {str(e)}"
            cli_logger.error(f"Error pausing Gazebo: {str(e)}")
        
        return result
    
    def resume(self) -> Dict[str, Any]:
        """
        Resume Gazebo simulation.
        
        Returns:
            Dictionary with resume operation results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name
        }
        
        if not self.is_running:
            result['message'] = "Gazebo is not running"
            return result
        
        try:
            # Use gz service to resume simulation
            exec_result = self._execute_command(['gz', 'service', '-s', '/world/resume', '--reqtype', 'gz.msgs.Empty'])
            
            if exec_result['success']:
                result['success'] = True
                result['message'] = "Gazebo simulation resumed"
                cli_logger.info("Resumed Gazebo simulation")
            else:
                result['message'] = f"Failed to resume Gazebo: {exec_result.get('stderr', 'Unknown error')}"
                
        except Exception as e:
            result['message'] = f"Error resuming Gazebo: {str(e)}"
            cli_logger.error(f"Error resuming Gazebo: {str(e)}")
        
        return result
    
    def reset(self) -> Dict[str, Any]:
        """
        Reset Gazebo simulation to initial state.
        
        Returns:
            Dictionary with reset operation results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name
        }
        
        if not self.is_running:
            result['message'] = "Gazebo is not running"
            return result
        
        try:
            # Use gz service to reset simulation
            exec_result = self._execute_command(['gz', 'service', '-s', '/world/reset', '--reqtype', 'gz.msgs.Empty'])
            
            if exec_result['success']:
                result['success'] = True
                result['message'] = "Gazebo simulation reset"
                cli_logger.info("Reset Gazebo simulation")
            else:
                result['message'] = f"Failed to reset Gazebo: {exec_result.get('stderr', 'Unknown error')}"
                
        except Exception as e:
            result['message'] = f"Error resetting Gazebo: {str(e)}"
            cli_logger.error(f"Error resetting Gazebo: {str(e)}")
        
        return result


class WebotsSimulator(BaseSimulator):
    """
    Webots simulator controller implementation.
    
    Provides control interface for Webots simulation environment
    using webots executable and Webots ROS2 bridge.
    """
    
    @property
    def name(self) -> str:
        """Get the simulator name."""
        return "webots"
    
    @property
    def executable(self) -> str:
        """Get the main executable name."""
        return "webots"
    
    def check_installation(self) -> Dict[str, Any]:
        """
        Check if Webots is installed and available.
        
        Returns:
            Dictionary with installation status and details
        """
        result = {
            'installed': False,
            'version': None,
            'executables': {},
            'issues': []
        }
        
        # Check for webots command
        webots_path = shutil.which('webots')
        if webots_path:
            result['executables']['webots'] = webots_path
            try:
                version_result = self._execute_command(['webots', '--version'], timeout=5)
                if version_result['success']:
                    result['version'] = version_result['stdout'].strip()
                    result['installed'] = True
            except Exception as e:
                result['issues'].append(f"Error checking webots version: {str(e)}")
        else:
            # Check common installation paths
            common_paths = [
                '/usr/local/webots/webots',
                '/opt/webots/webots',
                '/Applications/Webots.app/Contents/MacOS/webots',
                os.path.expanduser('~/webots/webots')
            ]
            
            for path in common_paths:
                if Path(path).exists():
                    result['executables']['webots'] = path
                    try:
                        version_result = self._execute_command([path, '--version'], timeout=5)
                        if version_result['success']:
                            result['version'] = version_result['stdout'].strip()
                            result['installed'] = True
                            break
                    except Exception:
                        continue
            
            if not result['installed']:
                result['issues'].append("webots command not found in PATH or common locations")
        
        # Check for ros2 command for bridge
        ros2_path = shutil.which('ros2')
        if ros2_path:
            result['executables']['ros2'] = ros2_path
        else:
            result['issues'].append("ros2 command not found in PATH")
        
        return result
    
    def launch(self, world: Optional[str] = None, launch_file: Optional[str] = None,
               headless: bool = False, **kwargs) -> Dict[str, Any]:
        """
        Launch Webots simulator.
        
        Args:
            world: World file (.wbt) to load
            launch_file: Custom ROS 2 launch file to use
            headless: Run without GUI
            **kwargs: Additional options
            
        Returns:
            Dictionary with launch results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name,
            'pid': None
        }
        
        # Check installation first
        install_check = self.check_installation()
        if not install_check['installed']:
            result['message'] = f"Webots not installed: {', '.join(install_check['issues'])}"
            return result
        
        self.world_file = world
        self.launch_file = launch_file
        
        try:
            webots_exe = list(install_check['executables'].values())[0]  # Get webots executable
            
            if launch_file:
                # Use custom launch file
                if not Path(launch_file).exists():
                    result['message'] = f"Launch file not found: {launch_file}"
                    return result
                
                command = ['ros2', 'launch', launch_file]
                
            else:
                # Use direct webots command
                command = [webots_exe]
                
                if headless:
                    command.extend(['--no-rendering'])
                
                if world:
                    if Path(world).exists():
                        command.append(world)
                    else:
                        # Try to find world in common locations
                        world_paths = [
                            f"/usr/local/webots/projects/samples/worlds/{world}",
                            f"/opt/webots/projects/samples/worlds/{world}",
                            f"~/webots/projects/worlds/{world}",
                            world  # Use as-is if not found
                        ]
                        
                        found_world = None
                        for world_path in world_paths:
                            expanded_path = Path(world_path.replace('~', str(Path.home())))
                            if expanded_path.exists():
                                found_world = str(expanded_path)
                                break
                        
                        if found_world:
                            command.append(found_world)
                        else:
                            command.append(world)  # Let Webots handle the error
            
            # Execute command in background
            exec_result = self._execute_command(command, background=True)
            
            if exec_result['success']:
                self.is_running = True
                result['success'] = True
                result['pid'] = self.process.pid if self.process else None
                result['message'] = f"Webots launched successfully (PID: {result['pid']})"
                
                # Give Webots time to start
                time.sleep(3)
                
                cli_logger.info(f"Launched Webots with command: {' '.join(command)}")
            else:
                result['message'] = f"Failed to launch Webots: {exec_result.get('stderr', 'Unknown error')}"
                
        except Exception as e:
            result['message'] = f"Error launching Webots: {str(e)}"
            cli_logger.error(f"Error launching Webots: {str(e)}")
        
        return result
    
    def pause(self) -> Dict[str, Any]:
        """
        Pause Webots simulation.
        
        Returns:
            Dictionary with pause operation results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name
        }
        
        if not self.is_running:
            result['message'] = "Webots is not running"
            return result
        
        try:
            # Send SIGUSR1 signal to pause (if supported)
            if self.process:
                os.kill(self.process.pid, signal.SIGUSR1)
                result['success'] = True
                result['message'] = "Webots simulation paused"
                cli_logger.info("Paused Webots simulation")
            else:
                result['message'] = "Cannot pause: Webots process not found"
                
        except Exception as e:
            result['message'] = f"Error pausing Webots: {str(e)}"
            cli_logger.error(f"Error pausing Webots: {str(e)}")
        
        return result
    
    def resume(self) -> Dict[str, Any]:
        """
        Resume Webots simulation.
        
        Returns:
            Dictionary with resume operation results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name
        }
        
        if not self.is_running:
            result['message'] = "Webots is not running"
            return result
        
        try:
            # Send SIGUSR2 signal to resume (if supported)
            if self.process:
                os.kill(self.process.pid, signal.SIGUSR2)
                result['success'] = True
                result['message'] = "Webots simulation resumed"
                cli_logger.info("Resumed Webots simulation")
            else:
                result['message'] = "Cannot resume: Webots process not found"
                
        except Exception as e:
            result['message'] = f"Error resuming Webots: {str(e)}"
            cli_logger.error(f"Error resuming Webots: {str(e)}")
        
        return result
    
    def reset(self) -> Dict[str, Any]:
        """
        Reset Webots simulation to initial state.
        
        Returns:
            Dictionary with reset operation results
        """
        result = {
            'success': False,
            'message': '',
            'simulator': self.name
        }
        
        if not self.is_running:
            result['message'] = "Webots is not running"
            return result
        
        try:
            # For Webots, reset typically requires restarting the world
            # This is a simplified implementation
            result['success'] = True
            result['message'] = "Webots reset requested (implementation depends on world controller)"
            cli_logger.info("Reset requested for Webots simulation")
            
        except Exception as e:
            result['message'] = f"Error resetting Webots: {str(e)}"
            cli_logger.error(f"Error resetting Webots: {str(e)}")
        
        return result


class SimulatorManager:
    """
    Manager class for handling multiple simulator types.
    
    Provides a unified interface for managing different simulators
    and routing commands to the appropriate simulator implementation.
    """
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize the simulator manager.
        
        Args:
            dry_run: If True, simulate operations without executing them
        """
        self.dry_run = dry_run
        self.simulators = {
            'gazebo': GazeboSimulator(dry_run=dry_run),
            'webots': WebotsSimulator(dry_run=dry_run)
        }
        
    def get_simulator(self, name: str) -> Optional[BaseSimulator]:
        """
        Get a simulator instance by name.
        
        Args:
            name: Name of the simulator ('gazebo' or 'webots')
            
        Returns:
            Simulator instance if found, None otherwise
        """
        return self.simulators.get(name.lower())
    
    def list_simulators(self) -> Dict[str, BaseSimulator]:
        """
        Get all available simulators.
        
        Returns:
            Dictionary mapping simulator names to instances
        """
        return self.simulators.copy()
    
    def check_all_installations(self) -> Dict[str, Dict[str, Any]]:
        """
        Check installation status of all simulators.
        
        Returns:
            Dictionary mapping simulator names to installation status
        """
        results = {}
        for name, simulator in self.simulators.items():
            results[name] = simulator.check_installation()
        return results
    
    def get_available_simulators(self) -> List[str]:
        """
        Get list of installed and available simulators.
        
        Returns:
            List of simulator names that are installed
        """
        available = []
        for name, simulator in self.simulators.items():
            install_check = simulator.check_installation()
            if install_check['installed']:
                available.append(name)
        return available


# Global simulator manager instance
simulator_manager = SimulatorManager()