"""
ROS 2 Middleware Layer for OneCodePlant.

This package provides middleware utilities for interacting with ROS 2 systems,
including node management, topic operations, parameter handling, and environment checks.
"""

try:
    from .ros_utils import ROSUtils
    from .checks import ROSEnvironmentChecker
    from .logger import CLILogger
    from .simulators import SimulatorManager, GazeboSimulator, WebotsSimulator, simulator_manager
except ImportError:
    # Handle cases where modules might not be fully loaded yet
    ROSUtils = None
    ROSEnvironmentChecker = None
    CLILogger = None
    SimulatorManager = None
    GazeboSimulator = None
    WebotsSimulator = None
    simulator_manager = None

__all__ = ['ROSUtils', 'ROSEnvironmentChecker', 'CLILogger', 'SimulatorManager', 
           'GazeboSimulator', 'WebotsSimulator', 'simulator_manager']