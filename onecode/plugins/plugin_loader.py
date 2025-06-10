"""
Plugin loader for OneCodePlant plugin system.

This module handles the discovery, loading, and management of plugins
from the plugins directory using dynamic imports and registry tracking.
"""

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
import traceback

from .base_plugin import BasePlugin


class PluginLoader:
    """
    Plugin loader that discovers and loads plugins from the plugins directory.
    
    This class manages the plugin lifecycle including discovery, loading,
    initialization, and registry management.
    """
    
    def __init__(self, plugins_dir: Optional[Path] = None, registry_file: Optional[Path] = None):
        """
        Initialize the plugin loader.
        
        Args:
            plugins_dir: Directory containing plugins (defaults to ./plugins)
            registry_file: Path to plugin registry file (defaults to ./plugin_registry.json)
        """
        self.plugins_dir = plugins_dir or Path(__file__).parent
        self.registry_file = registry_file or Path(__file__).parent.parent / "plugin_registry.json"
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.registry: Dict[str, Any] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """
        Load the plugin registry from disk.
        
        Creates a new registry file if it doesn't exist.
        """
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self.registry = json.load(f)
            else:
                self.registry = {"plugins": {}, "version": "1.0"}
                self._save_registry()
        except Exception as e:
            print(f"Warning: Could not load plugin registry: {e}")
            self.registry = {"plugins": {}, "version": "1.0"}
    
    def _save_registry(self) -> None:
        """
        Save the plugin registry to disk.
        """
        try:
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save plugin registry: {e}")
    
    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in the plugins directory.
        
        Returns:
            List of plugin directory names
        """
        plugin_dirs = []
        
        if not self.plugins_dir.exists():
            return plugin_dirs
        
        for item in self.plugins_dir.iterdir():
            if (item.is_dir() and 
                not item.name.startswith('_') and 
                item.name != '__pycache__' and
                (item / '__init__.py').exists()):
                plugin_dirs.append(item.name)
        
        return plugin_dirs
    
    def load_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Load a specific plugin by name.
        
        Args:
            plugin_name: Name of the plugin to load
            
        Returns:
            Loaded plugin instance or None if loading failed
        """
        try:
            plugin_dir = self.plugins_dir / plugin_name
            
            if not plugin_dir.exists():
                print(f"Plugin directory not found: {plugin_dir}")
                return None
            
            # Import the plugin module
            plugin_module_path = plugin_dir / 'plugin.py'
            if not plugin_module_path.exists():
                print(f"Plugin module not found: {plugin_module_path}")
                return None
            
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(
                f"onecode.plugins.{plugin_name}.plugin",
                plugin_module_path
            )
            
            if spec is None or spec.loader is None:
                print(f"Could not create module spec for {plugin_name}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Find the plugin class (should inherit from BasePlugin)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BasePlugin) and 
                    attr is not BasePlugin):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                print(f"No valid plugin class found in {plugin_name}")
                return None
            
            # Instantiate and initialize the plugin
            plugin_instance = plugin_class()
            
            if plugin_instance.initialize():
                self.loaded_plugins[plugin_name] = plugin_instance
                self._update_registry(plugin_name, plugin_instance)
                return plugin_instance
            else:
                print(f"Plugin {plugin_name} failed to initialize")
                return None
                
        except Exception as e:
            print(f"Error loading plugin {plugin_name}: {e}")
            traceback.print_exc()
            return None
    
    def load_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        Discover and load all available plugins.
        
        Returns:
            Dictionary mapping plugin names to plugin instances
        """
        discovered_plugins = self.discover_plugins()
        
        for plugin_name in discovered_plugins:
            if plugin_name not in self.loaded_plugins:
                plugin = self.load_plugin(plugin_name)
                if plugin:
                    print(f"Loaded plugin: {plugin_name}")
                else:
                    print(f"Failed to load plugin: {plugin_name}")
        
        return self.loaded_plugins.copy()
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin.
        
        Args:
            plugin_name: Name of the plugin to unload
            
        Returns:
            True if unloading was successful, False otherwise
        """
        try:
            if plugin_name in self.loaded_plugins:
                plugin = self.loaded_plugins[plugin_name]
                plugin.cleanup()
                del self.loaded_plugins[plugin_name]
                
                # Remove from sys.modules
                module_name = f"onecode.plugins.{plugin_name}.plugin"
                if module_name in sys.modules:
                    del sys.modules[module_name]
                
                return True
            return False
        except Exception as e:
            print(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get a loaded plugin by name.
        
        Args:
            plugin_name: Name of the plugin to retrieve
            
        Returns:
            Plugin instance or None if not found
        """
        return self.loaded_plugins.get(plugin_name)
    
    def list_loaded_plugins(self) -> Dict[str, BasePlugin]:
        """
        Get all loaded plugins.
        
        Returns:
            Dictionary of loaded plugins
        """
        return self.loaded_plugins.copy()
    
    def _update_registry(self, plugin_name: str, plugin: BasePlugin) -> None:
        """
        Update the plugin registry with plugin information.
        
        Args:
            plugin_name: Name of the plugin
            plugin: Plugin instance
        """
        # Ensure the registry has the correct format
        if "plugins" not in self.registry:
            # Convert old format to new format if needed
            if plugin_name in self.registry:
                # Registry is in new format, just update
                if "source" not in self.registry[plugin_name]:
                    self.registry[plugin_name].update({
                        "source": "local",
                        "path": f"onecode/plugins/{plugin_name}",
                        "status": "installed"
                    })
            else:
                # Add new plugin entry
                self.registry[plugin_name] = {
                    "source": "local",
                    "path": f"onecode/plugins/{plugin_name}",
                    "version": plugin.version,
                    "status": "installed"
                }
        else:
            # Old format with "plugins" wrapper - migrate to new format
            old_plugins = self.registry.get("plugins", {})
            self.registry = {}
            for name, info in old_plugins.items():
                self.registry[name] = {
                    "source": "local",
                    "path": f"onecode/plugins/{name}",
                    "version": info.get("version", "1.0.0"),
                    "status": "installed"
                }
        
        self._save_registry()
    
    def get_registry(self) -> Dict[str, Any]:
        """
        Get the current plugin registry.
        
        Returns:
            Plugin registry dictionary
        """
        return self.registry.copy()
    
    def validate_plugin_dependencies(self) -> Dict[str, List[str]]:
        """
        Validate dependencies for all loaded plugins.
        
        Returns:
            Dictionary mapping plugin names to lists of missing dependencies
        """
        missing_deps = {}
        
        for plugin_name, plugin in self.loaded_plugins.items():
            if not plugin.validate_dependencies(self.loaded_plugins):
                missing = []
                for dep in plugin.dependencies:
                    if dep not in self.loaded_plugins:
                        missing.append(dep)
                if missing:
                    missing_deps[plugin_name] = missing
        
        return missing_deps
