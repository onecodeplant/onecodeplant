"""
AI Engine Integration for OneCodePlant.

This package provides natural language processing capabilities for converting
human instructions into executable OneCodePlant CLI commands using various LLM providers.
"""

try:
    from .nlp_processor import NLPProcessor, ParseResult, CommandValidator
except ImportError:
    # Handle cases where AI dependencies might not be available
    NLPProcessor = None
    ParseResult = None
    CommandValidator = None

__all__ = ['NLPProcessor', 'ParseResult', 'CommandValidator']