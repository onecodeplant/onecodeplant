"""
CLI Logger for OneCodePlant.

This module provides centralized logging functionality for the CLI tool,
with support for file-based logging and different log levels.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class CLILogger:
    """
    Centralized logger for OneCodePlant CLI operations.
    
    Provides file-based logging with rotation and different log levels
    for tracking CLI operations, errors, and debugging information.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the CLI logger.
        
        Args:
            log_dir: Directory for log files (defaults to .onecode/logs/)
        """
        self.log_dir = log_dir or Path.home() / ".onecode" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / "cli.log"
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup the logger with file handler and formatting."""
        self.logger = logging.getLogger("onecode_cli")
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)
    
    def log_command(self, command: str, args: dict, success: bool = True) -> None:
        """
        Log a CLI command execution.
        
        Args:
            command: Command name that was executed
            args: Command arguments
            success: Whether the command succeeded
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"Command '{command}' {status} - Args: {args}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_ros_operation(self, operation: str, details: dict, success: bool = True) -> None:
        """
        Log a ROS 2 operation.
        
        Args:
            operation: Type of ROS operation (pub, echo, param, etc.)
            details: Operation details
            success: Whether the operation succeeded
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"ROS Operation '{operation}' {status} - Details: {details}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def get_log_path(self) -> Path:
        """Get the path to the log file."""
        return self.log_file
    
    def clear_logs(self) -> None:
        """Clear the log file."""
        try:
            self.log_file.unlink(missing_ok=True)
            self._setup_logger()
            self.info("Log file cleared")
        except Exception as e:
            self.error(f"Failed to clear log file: {e}")


# Global logger instance
cli_logger = CLILogger()