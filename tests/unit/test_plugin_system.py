"""
Unit tests for OneCodePlant plugin system.

Tests plugin discovery, loading, registry management, and plugin manager
functionality without external dependencies.
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from onecode.plugins.plugin_loader import PluginLoader
from onecode.plugins.plugin_manager import PluginManager
from onecode.plugins.base_plugin import BasePlugin


class TestPluginLoader:
    """Test the PluginLoader class."""
    
    def test_plugin_loader_initialization(self):
        """Test plugin loader initialization."""
        with patch('onecode.plugins.plugin_loader.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            loader = PluginLoader()
            assert loader.plugins_dir is not None
            assert loader.registry_file is not None
    
    def test_load_registry_file_exists(self, temp_dir):
        """Test loading existing registry file."""
        registry_data = {"test": {"version": "1.0.0"}}
        registry_file = temp_dir / "registry.json"
        
        with open(registry_file, 'w') as f:
            json.dump(registry_data, f)
        
        with patch('onecode.plugins.plugin_loader.PluginLoader._get_registry_path') as mock_path:
            mock_path.return_value = registry_file
            loader = PluginLoader()
            result = loader._load_registry()
            
            assert result == registry_data
    
    def test_load_registry_file_missing(self, temp_dir):
        """Test loading when registry file doesn't exist."""
        registry_file = temp_dir / "missing.json"
        
        with patch('onecode.plugins.plugin_loader.PluginLoader._get_registry_path') as mock_path:
            mock_path.return_value = registry_file
            loader = PluginLoader()
            result = loader._load_registry()
            
            assert result == {}
    
    def test_save_registry(self, temp_dir):
        """Test saving registry to file."""
        registry_data = {"test": {"version": "1.0.0"}}
        registry_file = temp_dir / "registry.json"
        
        with patch('onecode.plugins.plugin_loader.PluginLoader._get_registry_path') as mock_path:
            mock_path.return_value = registry_file
            loader = PluginLoader()
            loader.registry = registry_data
            loader._save_registry()
            
            assert registry_file.exists()
            with open(registry_file) as f:
                saved_data = json.load(f)
            assert saved_data == registry_data
    
    @patch('onecode.plugins.plugin_loader.importlib.util')
    def test_load_plugin_success(self, mock_importlib, mock_plugin):
        """Test successful plugin loading."""
        # Mock the importlib behavior
        mock_spec = Mock()
        mock_module = Mock()
        mock_plugin_class = Mock(return_value=mock_plugin)
        
        mock_importlib.spec_from_file_location.return_value = mock_spec
        mock_importlib.module_from_spec.return_value = mock_module
        mock_spec.loader.exec_module = Mock()
        
        # Mock finding plugin class
        with patch('onecode.plugins.plugin_loader.PluginLoader._find_plugin_class') as mock_find:
            mock_find.return_value = mock_plugin_class
            
            loader = PluginLoader()
            plugin_path = Path("test_plugin.py")
            
            result = loader.load_plugin("test_plugin", plugin_path)
            
            assert result == mock_plugin
            mock_plugin_class.assert_called_once()
    
    def test_find_plugin_class_found(self, mock_plugin):
        """Test finding plugin class in module."""
        mock_module = Mock()
        mock_class = Mock()
        mock_class.__bases__ = (BasePlugin,)
        mock_module.__dict__ = {'TestPlugin': mock_class, 'other': 'value'}
        
        loader = PluginLoader()
        result = loader._find_plugin_class(mock_module)
        
        assert result == mock_class
    
    def test_find_plugin_class_not_found(self):
        """Test when no plugin class is found in module."""
        mock_module = Mock()
        mock_module.__dict__ = {'other': 'value', 'function': lambda: None}
        
        loader = PluginLoader()
        result = loader._find_plugin_class(mock_module)
        
        assert result is None
    
    @patch('onecode.plugins.plugin_loader.PluginLoader.load_plugin')
    def test_load_all_plugins(self, mock_load_plugin, mock_plugin):
        """Test loading all plugins from directory."""
        mock_load_plugin.return_value = mock_plugin
        
        with patch('onecode.plugins.plugin_loader.Path') as mock_path_class:
            mock_plugins_dir = Mock()
            mock_plugin_dir = Mock()
            mock_plugin_dir.is_dir.return_value = True
            mock_plugin_dir.name = "test_plugin"
            mock_plugin_file = Mock()
            mock_plugin_file.name = "plugin.py"
            mock_plugin_dir.iterdir.return_value = [mock_plugin_file]
            mock_plugins_dir.iterdir.return_value = [mock_plugin_dir]
            mock_path_class.return_value = mock_plugins_dir
            
            loader = PluginLoader()
            loader.plugins_dir = mock_plugins_dir
            
            result = loader.load_all_plugins()
            
            assert len(result) == 1
            assert "test_plugin" in result
            assert result["test_plugin"] == mock_plugin


class TestPluginManager:
    """Test the PluginManager class."""
    
    def test_plugin_manager_initialization(self, temp_dir):
        """Test plugin manager initialization."""
        with patch('onecode.plugins.plugin_manager.Path') as mock_path:
            mock_path.return_value = temp_dir
            manager = PluginManager()
            assert manager.plugins_dir is not None
            assert manager.registry_file is not None
    
    def test_detect_source_type_github_url(self):
        """Test detecting GitHub URL source type."""
        manager = PluginManager()
        
        assert manager._detect_source_type("https://github.com/user/repo.git") == "github"
        assert manager._detect_source_type("http://github.com/user/repo") == "github"
        assert manager._detect_source_type("user/repo") == "github"
    
    def test_detect_source_type_local(self, temp_dir):
        """Test detecting local source type."""
        local_path = temp_dir / "plugin"
        local_path.mkdir()
        
        manager = PluginManager()
        assert manager._detect_source_type(str(local_path)) == "local"
        assert manager._detect_source_type("./plugin") == "local"
    
    def test_detect_source_type_pypi(self):
        """Test detecting PyPI source type."""
        manager = PluginManager()
        assert manager._detect_source_type("my-package") == "pypi"
        assert manager._detect_source_type("onecode-plugin") == "pypi"
    
    @patch('subprocess.run')
    def test_install_from_pypi_success(self, mock_subprocess):
        """Test successful PyPI installation."""
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('pkg_resources.get_distribution') as mock_pkg:
            mock_pkg.return_value.version = "1.0.0"
            
            manager = PluginManager()
            result = manager._install_from_pypi("test-package")
            
            assert result['source'] == 'pypi'
            assert result['package'] == 'test-package'
            assert result['version'] == '1.0.0'
            assert result['status'] == 'installed'
    
    @patch('subprocess.run')
    def test_install_from_pypi_failure(self, mock_subprocess):
        """Test failed PyPI installation."""
        mock_subprocess.side_effect = Exception("Installation failed")
        
        manager = PluginManager()
        
        with pytest.raises(Exception, match="PyPI installation failed"):
            manager._install_from_pypi("test-package")
    
    @patch('subprocess.run')
    @patch('shutil.copytree')
    @patch('tempfile.TemporaryDirectory')
    def test_install_from_github_success(self, mock_tempdir, mock_copytree, mock_subprocess):
        """Test successful GitHub installation."""
        mock_tempdir.return_value.__enter__.return_value = "/tmp/test"
        mock_subprocess.return_value = Mock(returncode=0)
        
        manager = PluginManager()
        result = manager._install_from_github("user/repo")
        
        assert result['source'] == 'github'
        assert result['url'] == 'https://github.com/user/repo.git'
        assert result['status'] == 'installed'
    
    @patch('shutil.copytree')
    def test_install_from_local_success(self, mock_copytree, temp_dir):
        """Test successful local installation."""
        source_dir = temp_dir / "source_plugin"
        source_dir.mkdir()
        
        manager = PluginManager()
        manager.plugins_dir = temp_dir / "plugins"
        manager.plugins_dir.mkdir()
        
        result = manager._install_from_local(str(source_dir))
        
        assert result['source'] == 'local'
        assert result['status'] == 'installed'
        mock_copytree.assert_called_once()
    
    def test_install_from_local_missing_path(self):
        """Test local installation with missing source path."""
        manager = PluginManager()
        
        with pytest.raises(Exception, match="Local path does not exist"):
            manager._install_from_local("/nonexistent/path")
    
    def test_list_plugins_empty(self, temp_dir):
        """Test listing plugins when none are installed."""
        registry_file = temp_dir / "registry.json"
        with open(registry_file, 'w') as f:
            json.dump({}, f)
        
        with patch.object(PluginManager, '_load_registry') as mock_load:
            mock_load.return_value = {}
            
            manager = PluginManager()
            result = manager.list_plugins()
            
            assert result == []
    
    def test_list_plugins_with_data(self, temp_dir):
        """Test listing plugins with installed plugins."""
        registry_data = {
            "test_plugin": {
                "source": "local",
                "path": "/path/to/plugin",
                "version": "1.0.0",
                "status": "installed"
            }
        }
        
        with patch.object(PluginManager, '_load_registry') as mock_load:
            mock_load.return_value = registry_data
            
            manager = PluginManager()
            result = manager.list_plugins()
            
            assert len(result) == 1
            assert result[0]['name'] == 'test_plugin'
            assert result[0]['source'] == 'local'
            assert result[0]['version'] == '1.0.0'
    
    def test_get_plugin_info_exists(self):
        """Test getting info for existing plugin."""
        registry_data = {
            "test_plugin": {
                "source": "local",
                "version": "1.0.0"
            }
        }
        
        with patch.object(PluginManager, '_load_registry') as mock_load:
            mock_load.return_value = registry_data
            
            manager = PluginManager()
            result = manager.get_plugin_info("test_plugin")
            
            assert result == registry_data["test_plugin"]
    
    def test_get_plugin_info_missing(self):
        """Test getting info for non-existent plugin."""
        with patch.object(PluginManager, '_load_registry') as mock_load:
            mock_load.return_value = {}
            
            manager = PluginManager()
            result = manager.get_plugin_info("missing_plugin")
            
            assert result is None
    
    @patch('shutil.rmtree')
    def test_remove_plugin_success(self, mock_rmtree):
        """Test successful plugin removal."""
        registry_data = {
            "test_plugin": {
                "source": "local",
                "path": "/path/to/plugin"
            }
        }
        
        with patch.object(PluginManager, '_load_registry') as mock_load, \
             patch.object(PluginManager, '_save_registry') as mock_save:
            mock_load.return_value = registry_data.copy()
            
            manager = PluginManager()
            result = manager.remove("test_plugin", confirm=True)
            
            assert result['name'] == 'test_plugin'
            assert result['status'] == 'removed'
            mock_save.assert_called_once()
    
    def test_remove_plugin_not_installed(self):
        """Test removing plugin that's not installed."""
        with patch.object(PluginManager, '_load_registry') as mock_load:
            mock_load.return_value = {}
            
            manager = PluginManager()
            
            with pytest.raises(Exception, match="Plugin 'missing' is not installed"):
                manager.remove("missing", confirm=True)
    
    def test_remove_plugin_no_confirmation(self):
        """Test removing plugin without confirmation."""
        registry_data = {"test_plugin": {"source": "local"}}
        
        with patch.object(PluginManager, '_load_registry') as mock_load:
            mock_load.return_value = registry_data
            
            manager = PluginManager()
            
            with pytest.raises(Exception, match="Removal requires confirmation"):
                manager.remove("test_plugin", confirm=False)


class TestBasePlugin:
    """Test the BasePlugin abstract class."""
    
    def test_base_plugin_cannot_instantiate(self):
        """Test that BasePlugin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BasePlugin()
    
    def test_mock_plugin_properties(self, mock_plugin):
        """Test plugin property access."""
        assert mock_plugin.name == "test_plugin"
        assert mock_plugin.version == "1.0.0"
        assert mock_plugin.description == "Test plugin for unit testing"
        assert mock_plugin.author == "Test Suite"
        assert isinstance(mock_plugin.dependencies, list)
    
    def test_mock_plugin_methods(self, mock_plugin):
        """Test plugin method implementations."""
        assert mock_plugin.initialize() is True
        
        commands = mock_plugin.get_commands()
        assert isinstance(commands, dict)
        assert 'test_cmd' in commands
        
        metadata = mock_plugin.get_metadata()
        assert metadata['name'] == mock_plugin.name
        assert metadata['version'] == mock_plugin.version


class TestPluginValidation:
    """Test plugin validation functionality."""
    
    @patch('importlib.util.spec_from_file_location')
    def test_validate_plugin_success(self, mock_spec_from_file):
        """Test successful plugin validation."""
        # Mock a valid plugin module
        mock_spec = Mock()
        mock_module = Mock()
        mock_plugin_class = Mock()
        mock_plugin_class.__bases__ = (BasePlugin,)
        
        mock_spec.loader = Mock()
        mock_spec_from_file.return_value = mock_spec
        mock_module.__dict__ = {'TestPlugin': mock_plugin_class}
        
        with patch('importlib.util.module_from_spec', return_value=mock_module):
            manager = PluginManager()
            plugin_path = Path("test_plugin")
            
            result = manager._validate_plugin(plugin_path)
            
            assert result is True
    
    @patch('importlib.util.spec_from_file_location')
    def test_validate_plugin_no_base_plugin(self, mock_spec_from_file):
        """Test plugin validation when no BasePlugin implementation found."""
        mock_spec = Mock()
        mock_module = Mock()
        mock_other_class = Mock()
        mock_other_class.__bases__ = (object,)
        
        mock_spec.loader = Mock()
        mock_spec_from_file.return_value = mock_spec
        mock_module.__dict__ = {'OtherClass': mock_other_class}
        
        with patch('importlib.util.module_from_spec', return_value=mock_module):
            manager = PluginManager()
            plugin_path = Path("test_plugin")
            
            result = manager._validate_plugin(plugin_path)
            
            assert result is False
    
    def test_validate_plugin_exception(self):
        """Test plugin validation when exception occurs."""
        manager = PluginManager()
        plugin_path = Path("nonexistent")
        
        result = manager._validate_plugin(plugin_path)
        
        assert result is False