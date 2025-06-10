"""
Base plugin interface for OneCodePlant plugin system.

This module defines the abstract base class that all plugins must inherit from,
providing a consistent interface for plugin registration and execution.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePlugin(ABC):
    """
    Abstract base class for all OneCodePlant plugins.
    
    This class defines the interface that all plugins must implement,
    ensuring consistency across the plugin ecosystem and providing
    essential metadata and lifecycle methods.
    """
    
    def __init__(self):
        """Initialize the base plugin with default metadata."""
        self._name: str = self.__class__.__name__
        self._version: str = "1.0.0"
        self._description: str = "A OneCodePlant plugin"
        self._author: str = "Unknown"
        self._dependencies: list = []
    
    @property
    def name(self) -> str:
        """Get the plugin name."""
        return self._name
    
    @property
    def version(self) -> str:
        """Get the plugin version."""
        return self._version
    
    @property
    def description(self) -> str:
        """Get the plugin description."""
        return self._description
    
    @property
    def author(self) -> str:
        """Get the plugin author."""
        return self._author
    
    @property
    def dependencies(self) -> list:
        """Get the list of plugin dependencies."""
        return self._dependencies.copy()
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        This method is called when the plugin is loaded and should
        perform any necessary setup operations.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_commands(self) -> Dict[str, Any]:
        """
        Get the commands provided by this plugin.
        
        Returns:
            Dictionary mapping command names to command handlers
        """
        pass
    
    def cleanup(self) -> None:
        """
        Cleanup resources used by the plugin.
        
        This method is called when the plugin is unloaded or the
        application is shutting down. Override this method to
        perform cleanup operations.
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get plugin metadata.
        
        Returns:
            Dictionary containing plugin metadata
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'dependencies': self.dependencies
        }
    
    def validate_dependencies(self, available_plugins: Dict[str, 'BasePlugin']) -> bool:
        """
        Validate that all plugin dependencies are satisfied.
        
        Args:
            available_plugins: Dictionary of available plugins
            
        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        for dependency in self.dependencies:
            if dependency not in available_plugins:
                return False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the plugin.
        
        Returns:
            Dictionary containing plugin status information
        """
        return {
            'name': self.name,
            'version': self.version,
            'initialized': hasattr(self, '_initialized') and self._initialized,
            'active': True
        }
