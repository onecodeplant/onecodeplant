"""
Plugin system for OneCodePlant.

This package contains the plugin architecture components including
the base plugin interface and plugin loading mechanisms.
"""

from .base_plugin import BasePlugin
from .plugin_loader import PluginLoader

__all__ = ['BasePlugin', 'PluginLoader']
