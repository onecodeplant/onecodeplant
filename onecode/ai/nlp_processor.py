"""
Natural Language Processing module for OneCodePlant AI Engine Integration.

This module provides the core NLP functionality for converting natural language
instructions into executable OneCodePlant CLI commands using various LLM providers.
"""

import os
import re
import json
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from ..config import config
from ..middleware.logger import cli_logger


@dataclass
class ParseResult:
    """Result of natural language parsing."""
    success: bool
    commands: List[str]
    explanation: str
    confidence: float
    warnings: List[str]
    errors: List[str]


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, model: str, **kwargs):
        """Initialize the LLM provider."""
        self.api_key = api_key
        self.model = model
        self.timeout = kwargs.get('timeout', 30)
        self.max_tokens = kwargs.get('max_tokens', 1000)
        self.temperature = kwargs.get('temperature', 0.1)
    
    @abstractmethod
    def generate_completion(self, prompt: str) -> str:
        """Generate completion from the LLM."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the provider name."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", **kwargs):
        super().__init__(api_key, model, **kwargs)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
    
    @property
    def name(self) -> str:
        return "openai"
    
    def generate_completion(self, prompt: str) -> str:
        """Generate completion using OpenAI API."""
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that converts natural language to CLI commands."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            cli_logger.error(f"OpenAI API error: {str(e)}")
            raise


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(api_key, model, **kwargs)
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    def generate_completion(self, prompt: str) -> str:
        """Generate completion using Anthropic Claude API."""
        try:
            # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            cli_logger.error(f"Anthropic API error: {str(e)}")
            raise


class GoogleProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        super().__init__(api_key, model, **kwargs)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Install with: pip install google-generativeai")
    
    @property
    def name(self) -> str:
        return "google"
    
    def generate_completion(self, prompt: str) -> str:
        """Generate completion using Google Gemini API."""
        try:
            response = self.client.generate_content(
                prompt,
                generation_config={
                    'temperature': self.temperature,
                    'max_output_tokens': self.max_tokens,
                }
            )
            return response.text
        except Exception as e:
            cli_logger.error(f"Google API error: {str(e)}")
            raise


class CommandValidator:
    """Validates and sanitizes generated commands for safety."""
    
    DANGEROUS_PATTERNS = [
        r'rm\s+.*-rf',  # Dangerous file deletion
        r'sudo\s+',     # Elevated privileges
        r'chmod\s+777', # Overly permissive permissions
        r'dd\s+if=',    # Disk operations
        r'mkfs\.',      # Filesystem creation
        r'fdisk',       # Disk partitioning
        r'reboot',      # System restart
        r'shutdown',    # System shutdown
        r'>\s*/dev/',   # Writing to device files
    ]
    
    ALLOWED_COMMANDS = [
        'onecode',      # OneCodePlant commands
        'ros2',         # ROS 2 commands
        'gz',           # Gazebo commands
        'webots',       # Webots commands
        'echo',         # Safe output
        'cat',          # Safe file reading
        'ls',           # Safe directory listing
        'pwd',          # Current directory
        'which',        # Command location
    ]
    
    def __init__(self):
        self.warnings = []
        self.errors = []
    
    def validate_command(self, command: str) -> bool:
        """
        Validate a single command for safety.
        
        Args:
            command: Command string to validate
            
        Returns:
            True if command is safe, False otherwise
        """
        self.warnings.clear()
        self.errors.clear()
        
        # Strip whitespace and comments
        cmd = command.strip()
        if not cmd or cmd.startswith('#'):
            return True
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                self.errors.append(f"Dangerous pattern detected: {pattern}")
                return False
        
        # Extract the base command
        base_cmd = cmd.split()[0] if cmd.split() else ""
        
        # Check if command is in allowed list
        if not any(base_cmd.startswith(allowed) for allowed in self.ALLOWED_COMMANDS):
            self.warnings.append(f"Command '{base_cmd}' not in allowed list")
        
        # Check for shell operators that might be dangerous
        dangerous_operators = ['&&', '||', '|', '>', '>>', '<', '$(', '`']
        for op in dangerous_operators:
            if op in cmd and not cmd.startswith('onecode'):
                self.warnings.append(f"Shell operator '{op}' detected")
        
        return True
    
    def validate_commands(self, commands: List[str]) -> bool:
        """
        Validate a list of commands.
        
        Args:
            commands: List of command strings
            
        Returns:
            True if all commands are safe, False otherwise
        """
        all_safe = True
        combined_warnings = []
        combined_errors = []
        
        for i, cmd in enumerate(commands):
            if not self.validate_command(cmd):
                all_safe = False
                combined_errors.extend([f"Command {i+1}: {err}" for err in self.errors])
            combined_warnings.extend([f"Command {i+1}: {warn}" for warn in self.warnings])
        
        self.warnings = combined_warnings
        self.errors = combined_errors
        return all_safe


class NLPProcessor:
    """
    Main NLP processor for converting natural language to CLI commands.
    
    Supports multiple LLM providers and includes safety validation,
    command parsing, and execution capabilities.
    """
    
    def __init__(self, engine: Optional[str] = None, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the NLP processor.
        
        Args:
            engine: LLM engine to use (openai, anthropic, google)
            api_key: API key for the engine
            **kwargs: Additional configuration options
        """
        self.engine = engine or config.ai.default_engine
        self.api_key = api_key or config.get_api_key(self.engine)
        self.model = config.get_model(self.engine)
        
        # Load configuration
        self.max_tokens = kwargs.get('max_tokens', config.ai.max_tokens)
        self.temperature = kwargs.get('temperature', config.ai.temperature)
        self.timeout = kwargs.get('timeout', config.ai.timeout)
        self.safety_checks = kwargs.get('safety_checks', config.cli.safety_checks)
        
        # Initialize provider
        self.provider = self._create_provider()
        self.validator = CommandValidator()
        
        # Load base prompt
        self.base_prompt = self._load_base_prompt()
        
        cli_logger.info(f"Initialized NLP processor with {self.engine} engine")
    
    def _create_provider(self) -> BaseLLMProvider:
        """Create the appropriate LLM provider."""
        if not self.api_key:
            available_engines = config.get_available_engines()
            if available_engines:
                # Fall back to first available engine
                self.engine = available_engines[0]
                self.api_key = config.get_api_key(self.engine)
                self.model = config.get_model(self.engine)
            else:
                raise ValueError("No API keys configured for any LLM provider")
        
        provider_kwargs = {
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'timeout': self.timeout
        }
        
        if self.engine == "openai":
            return OpenAIProvider(self.api_key, self.model, **provider_kwargs)
        elif self.engine == "anthropic":
            return AnthropicProvider(self.api_key, self.model, **provider_kwargs)
        elif self.engine == "google":
            return GoogleProvider(self.api_key, self.model, **provider_kwargs)
        else:
            raise ValueError(f"Unsupported engine: {self.engine}")
    
    def _load_base_prompt(self) -> str:
        """Load the base prompt template."""
        prompt_path = Path(__file__).parent / "prompts" / "base_prompt.txt"
        try:
            return prompt_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            cli_logger.warning(f"Base prompt file not found: {prompt_path}")
            return "Convert this natural language instruction to OneCodePlant CLI commands:"
    
    def _clean_response(self, response: str) -> List[str]:
        """
        Clean and extract commands from LLM response.
        
        Args:
            response: Raw response from LLM
            
        Returns:
            List of cleaned command strings
        """
        lines = response.strip().split('\n')
        commands = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Remove common prefixes
            if line.startswith('Output: '):
                line = line[8:]
            elif line.startswith('Command: '):
                line = line[9:]
            elif line.startswith('$ '):
                line = line[2:]
            elif line.startswith('> '):
                line = line[2:]
            
            # Remove backticks and code block markers
            line = line.strip('`')
            if line.startswith('bash') or line.startswith('sh'):
                continue
            
            # Only include lines that look like commands
            if line and (line.startswith('onecode') or 
                        line.startswith('ros2') or 
                        line.startswith('gz') or 
                        line.startswith('webots')):
                commands.append(line)
        
        return commands
    
    def parse(self, prompt: str) -> ParseResult:
        """
        Parse natural language instruction into CLI commands.
        
        Args:
            prompt: Natural language instruction
            
        Returns:
            ParseResult with commands and metadata
        """
        cli_logger.info(f"Parsing natural language prompt with {self.engine}")
        
        try:
            # Construct full prompt
            full_prompt = f"{self.base_prompt}\n\nInstruction: {prompt}"
            
            # Generate completion
            start_time = time.time()
            response = self.provider.generate_completion(full_prompt)
            elapsed_time = time.time() - start_time
            
            cli_logger.debug(f"LLM response received in {elapsed_time:.2f}s")
            
            # Clean and extract commands
            commands = self._clean_response(response)
            
            if not commands:
                return ParseResult(
                    success=False,
                    commands=[],
                    explanation="No valid commands found in response",
                    confidence=0.0,
                    warnings=[],
                    errors=["Failed to extract valid commands from LLM response"]
                )
            
            # Validate commands if safety checks enabled
            warnings = []
            errors = []
            safe = True
            
            if self.safety_checks:
                safe = self.validator.validate_commands(commands)
                warnings = self.validator.warnings
                errors = self.validator.errors
            
            # Calculate confidence based on response quality
            confidence = self._calculate_confidence(commands, response)
            
            result = ParseResult(
                success=safe and len(commands) > 0,
                commands=commands,
                explanation=f"Generated {len(commands)} command(s) using {self.engine}",
                confidence=confidence,
                warnings=warnings,
                errors=errors
            )
            
            cli_logger.info(f"Parsed {len(commands)} commands with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            cli_logger.error(f"Error parsing natural language: {str(e)}")
            return ParseResult(
                success=False,
                commands=[],
                explanation=f"Error: {str(e)}",
                confidence=0.0,
                warnings=[],
                errors=[str(e)]
            )
    
    def _calculate_confidence(self, commands: List[str], response: str) -> float:
        """Calculate confidence score for the parsed commands."""
        if not commands:
            return 0.0
        
        score = 0.8  # Base score
        
        # Boost for valid OneCodePlant commands
        onecode_count = sum(1 for cmd in commands if cmd.startswith('onecode'))
        if onecode_count > 0:
            score += 0.1 * min(onecode_count / len(commands), 1.0)
        
        # Reduce for warnings
        if hasattr(self.validator, 'warnings') and self.validator.warnings:
            score -= 0.05 * len(self.validator.warnings)
        
        # Reduce for very short or very long responses
        if len(response) < 50:
            score -= 0.1
        elif len(response) > 1000:
            score -= 0.05
        
        return max(0.0, min(1.0, score))
    
    def execute(self, commands: List[str], dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute the parsed commands.
        
        Args:
            commands: List of commands to execute
            dry_run: If True, only simulate execution
            
        Returns:
            Dictionary with execution results
        """
        results = {
            'executed': [],
            'failed': [],
            'outputs': {},
            'errors': {},
            'dry_run': dry_run
        }
        
        for i, command in enumerate(commands):
            cmd_id = f"cmd_{i+1}"
            
            if dry_run:
                results['executed'].append(cmd_id)
                results['outputs'][cmd_id] = f"[DRY RUN] Would execute: {command}"
                cli_logger.info(f"[DRY RUN] Command {i+1}: {command}")
                continue
            
            try:
                cli_logger.info(f"Executing command {i+1}: {command}")
                
                # Execute command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if result.returncode == 0:
                    results['executed'].append(cmd_id)
                    results['outputs'][cmd_id] = result.stdout
                    cli_logger.info(f"Command {i+1} executed successfully")
                else:
                    results['failed'].append(cmd_id)
                    results['errors'][cmd_id] = result.stderr
                    cli_logger.error(f"Command {i+1} failed: {result.stderr}")
                
            except subprocess.TimeoutExpired:
                results['failed'].append(cmd_id)
                results['errors'][cmd_id] = f"Command timed out after {self.timeout}s"
                cli_logger.error(f"Command {i+1} timed out")
            except Exception as e:
                results['failed'].append(cmd_id)
                results['errors'][cmd_id] = str(e)
                cli_logger.error(f"Command {i+1} error: {str(e)}")
        
        return results
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the current engine configuration."""
        return {
            'engine': self.engine,
            'provider': self.provider.name,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'safety_checks': self.safety_checks,
            'available_engines': config.get_available_engines()
        }