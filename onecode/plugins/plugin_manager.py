"""
Plugin Manager for OneCodePlant.

This module provides dynamic plugin installation, removal, and management
capabilities with support for PyPI, GitHub, and local plugin sources.
"""

import json
import subprocess
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse
import importlib.util
import sys
import os

from ..config import Config


class PluginManager:
    """
    Plugin Manager for OneCodePlant.
    
    Handles dynamic installation, removal, and management of plugins
    from various sources including PyPI, GitHub, and local directories.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the plugin manager."""
        self.config = config or Config()
        self.plugins_dir = Path("onecode/plugins")
        # Use the main registry file at project root
        self.registry_file = Path("onecode/plugin_registry.json")
        self.log_dir = Path.home() / ".onecode" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "plugin.log"
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Ensure registry exists
        self._ensure_registry()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for plugin operations."""
        logger = logging.getLogger("onecode.plugin_manager")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _ensure_registry(self) -> None:
        """Ensure plugin registry file exists."""
        if not self.registry_file.exists():
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_registry({})
    
    def _load_registry(self) -> Dict:
        """Load plugin registry from file."""
        try:
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_registry(self, registry: Dict) -> None:
        """Save plugin registry to file."""
        with open(self.registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def _detect_source_type(self, source: str) -> str:
        """Detect the type of plugin source."""
        if source.startswith(('http://', 'https://')):
            return 'github'
        elif '/' in source and not source.startswith('.'):
            # Likely a GitHub shorthand (user/repo)
            return 'github'
        elif os.path.exists(source):
            return 'local'
        else:
            return 'pypi'
    
    def _install_from_pypi(self, package_name: str) -> Dict:
        """Install plugin from PyPI."""
        try:
            # Install package
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', package_name],
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"Successfully installed {package_name} from PyPI")
            
            # Try to extract version info
            try:
                import pkg_resources
                version = pkg_resources.get_distribution(package_name).version
            except:
                version = "unknown"
            
            return {
                'source': 'pypi',
                'package': package_name,
                'version': version,
                'status': 'installed'
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install {package_name} from PyPI: {e.stderr}")
            raise Exception(f"PyPI installation failed: {e.stderr}")
    
    def _install_from_github(self, source: str) -> Dict:
        """Install plugin from GitHub."""
        try:
            # Handle shorthand format (user/repo)
            if not source.startswith(('http://', 'https://')):
                source = f"https://github.com/{source}.git"
            
            # Extract repo name for plugin name
            parsed = urlparse(source)
            repo_name = Path(parsed.path).stem.replace('.git', '')
            
            # Clone to temporary directory first
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / repo_name
                
                subprocess.run(
                    ['git', 'clone', source, str(temp_path)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Copy to plugins directory
                plugin_path = self.plugins_dir / repo_name
                if plugin_path.exists():
                    shutil.rmtree(plugin_path)
                
                shutil.copytree(temp_path, plugin_path)
                
                self.logger.info(f"Successfully installed {repo_name} from GitHub")
                
                return {
                    'source': 'github',
                    'url': source,
                    'path': str(plugin_path),
                    'status': 'installed'
                }
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to install from GitHub {source}: {e.stderr}")
            raise Exception(f"GitHub installation failed: {e.stderr}")
    
    def _install_from_local(self, source: str) -> Dict:
        """Install plugin from local directory."""
        try:
            source_path = Path(source).resolve()
            if not source_path.exists():
                raise Exception(f"Local path does not exist: {source}")
            
            plugin_name = source_path.name
            plugin_path = self.plugins_dir / plugin_name
            
            if plugin_path.exists():
                shutil.rmtree(plugin_path)
            
            # Copy or symlink
            shutil.copytree(source_path, plugin_path)
            
            self.logger.info(f"Successfully installed {plugin_name} from local directory")
            
            return {
                'source': 'local',
                'original_path': str(source_path),
                'path': str(plugin_path),
                'status': 'installed'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to install from local {source}: {str(e)}")
            raise Exception(f"Local installation failed: {str(e)}")
    
    def _validate_plugin(self, plugin_path: Path) -> bool:
        """Validate that the plugin implements BasePlugin interface."""
        try:
            # Look for Python files that might contain plugin classes
            for py_file in plugin_path.glob("**/*.py"):
                if py_file.name.startswith('__'):
                    continue
                
                spec = importlib.util.spec_from_file_location(
                    py_file.stem, py_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Check for BasePlugin implementation
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (hasattr(attr, '__bases__') and 
                            any('BasePlugin' in str(base) for base in attr.__bases__)):
                            return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Plugin validation failed: {str(e)}")
            return False
    
    def install(self, source: str, force: bool = False) -> Dict:
        """
        Install a plugin from various sources.
        
        Args:
            source: Plugin source (PyPI package, GitHub URL, or local path)
            force: Force reinstallation if plugin already exists
            
        Returns:
            Dictionary with installation details
        """
        registry = self._load_registry()
        source_type = self._detect_source_type(source)
        
        # Generate plugin name based on source
        if source_type == 'pypi':
            plugin_name = source
        elif source_type == 'github':
            parsed = urlparse(source if source.startswith('http') else f"https://github.com/{source}")
            plugin_name = Path(parsed.path).stem.replace('.git', '')
        else:  # local
            plugin_name = Path(source).name
        
        # Check if already installed
        if plugin_name in registry and not force:
            raise Exception(f"Plugin '{plugin_name}' is already installed. Use --force to reinstall.")
        
        # Install based on source type
        try:
            if source_type == 'pypi':
                metadata = self._install_from_pypi(source)
            elif source_type == 'github':
                metadata = self._install_from_github(source)
            else:  # local
                metadata = self._install_from_local(source)
            
            # Validate plugin if it's a local installation
            if source_type in ['github', 'local']:
                plugin_path = Path(metadata['path'])
                if not self._validate_plugin(plugin_path):
                    self.logger.warning(f"Plugin {plugin_name} may not implement BasePlugin interface")
            
            # Update registry
            registry[plugin_name] = metadata
            self._save_registry(registry)
            
            return {
                'name': plugin_name,
                'source_type': source_type,
                'status': 'success',
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error(f"Installation failed for {source}: {str(e)}")
            raise
    
    def remove(self, name: str, confirm: bool = False) -> Dict:
        """
        Remove a plugin.
        
        Args:
            name: Plugin name to remove
            confirm: Skip confirmation prompt
            
        Returns:
            Dictionary with removal details
        """
        registry = self._load_registry()
        
        if name not in registry:
            raise Exception(f"Plugin '{name}' is not installed")
        
        plugin_info = registry[name]
        
        if not confirm:
            # In CLI context, this would prompt user
            # For now, we'll require explicit confirmation
            raise Exception("Removal requires confirmation. Use --yes flag.")
        
        try:
            # Remove based on source type
            if plugin_info['source'] == 'pypi':
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'uninstall', '-y', plugin_info['package']],
                    capture_output=True,
                    text=True,
                    check=True
                )
            elif 'path' in plugin_info:
                plugin_path = Path(plugin_info['path'])
                if plugin_path.exists():
                    shutil.rmtree(plugin_path)
            
            # Remove from registry
            del registry[name]
            self._save_registry(registry)
            
            self.logger.info(f"Successfully removed plugin {name}")
            
            return {
                'name': name,
                'status': 'removed'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to remove plugin {name}: {str(e)}")
            raise
    
    def list_plugins(self) -> List[Dict]:
        """
        List all installed plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        registry = self._load_registry()
        plugins = []
        
        for name, metadata in registry.items():
            plugin_info = {
                'name': name,
                'source': metadata.get('source', 'unknown'),
                'status': metadata.get('status', 'unknown')
            }
            
            # Add version if available
            if 'version' in metadata:
                plugin_info['version'] = metadata['version']
            
            # Add path for local/github plugins
            if 'path' in metadata:
                plugin_info['path'] = metadata['path']
                # Check if path still exists
                if not Path(metadata['path']).exists():
                    plugin_info['status'] = 'missing'
            
            plugins.append(plugin_info)
        
        return plugins
    
    def get_plugin_info(self, name: str) -> Optional[Dict]:
        """Get detailed information about a specific plugin."""
        registry = self._load_registry()
        return registry.get(name)
    
    def refresh_registry(self) -> None:
        """Refresh plugin registry by checking actual plugin states."""
        registry = self._load_registry()
        updated = False
        
        for name, metadata in list(registry.items()):
            if 'path' in metadata:
                if not Path(metadata['path']).exists():
                    metadata['status'] = 'missing'
                    updated = True
                elif metadata.get('status') == 'missing':
                    metadata['status'] = 'installed'
                    updated = True
        
        if updated:
            self._save_registry(registry)
            self.logger.info("Plugin registry refreshed")