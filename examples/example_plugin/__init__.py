"""
Example Plugin Package for OneCodePlant

This package demonstrates how to structure a OneCodePlant plugin
with proper module organization and metadata.
"""

__version__ = "1.0.0"
__author__ = "OneCodePlant Team"
__description__ = "Example plugin for OneCodePlant development"

from .plugin import ExamplePlugin, get_plugin

__all__ = ["ExamplePlugin", "get_plugin"]