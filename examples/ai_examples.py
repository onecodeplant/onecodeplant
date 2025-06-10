#!/usr/bin/env python3
"""
OneCodePlant Phase 3 AI Engine Integration Examples.

This file demonstrates the natural language processing capabilities
and shows how users can interact with the AI-powered CLI system.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from onecode.ai.nlp_processor import NLPProcessor, CommandValidator, ParseResult
from onecode.config import config


def demo_command_validation():
    """Demonstrate the command validation system."""
    print("=" * 60)
    print("AI COMMAND VALIDATION DEMONSTRATION")
    print("=" * 60)
    
    validator = CommandValidator()
    
    # Test safe commands
    safe_examples = [
        "onecode sim launch gazebo --robot-model turtlebot3_burger",
        "onecode pub /cmd_vel --message-type geometry_msgs/Twist --data '{\"linear\": {\"x\": 1.0}}'",
        "onecode echo /scan --count 5",
        "onecode gen node navigation_node --template python",
        "ros2 topic list",
        "gz sim --version"
    ]
    
    # Test unsafe commands
    unsafe_examples = [
        "sudo rm -rf /",
        "chmod 777 /etc/passwd",
        "dd if=/dev/zero of=/dev/sda",
        "reboot now",
        "shutdown -h now"
    ]
    
    print("\nSAFE COMMANDS:")
    for cmd in safe_examples:
        is_safe = validator.validate_command(cmd)
        status = "✓ APPROVED" if is_safe else "✗ BLOCKED"
        print(f"  {status}: {cmd}")
        if validator.warnings:
            for warning in validator.warnings:
                print(f"    Warning: {warning}")
    
    print("\nUNSAFE COMMANDS (automatically blocked):")
    for cmd in unsafe_examples:
        is_safe = validator.validate_command(cmd)
        status = "✓ APPROVED" if is_safe else "✗ BLOCKED"
        print(f"  {status}: {cmd}")
        if validator.errors:
            for error in validator.errors:
                print(f"    Reason: {error}")


def demo_natural_language_examples():
    """Show natural language input examples and expected CLI outputs."""
    print("\n" + "=" * 60)
    print("NATURAL LANGUAGE TO CLI COMMAND EXAMPLES")
    print("=" * 60)
    
    examples = [
        {
            "input": "launch gazebo with turtlebot3 robot",
            "expected": "onecode sim launch gazebo --robot-model turtlebot3_burger"
        },
        {
            "input": "create a navigation node in python",
            "expected": "onecode gen node navigation_node --template python"
        },
        {
            "input": "move robot forward at 1 m/s",
            "expected": "onecode pub /cmd_vel --message-type geometry_msgs/Twist --data '{\"linear\": {\"x\": 1.0}}'"
        },
        {
            "input": "show laser scan data for 10 messages",
            "expected": "onecode echo /scan --count 10"
        },
        {
            "input": "pause the gazebo simulation",
            "expected": "onecode sim pause gazebo"
        },
        {
            "input": "check parameter battery_level on robot_node",
            "expected": "onecode param get /robot_node battery_level"
        },
        {
            "input": "list all active ros nodes",
            "expected": "onecode node --list"
        },
        {
            "input": "start webots simulation without GUI",
            "expected": "onecode sim launch webots --headless"
        }
    ]
    
    print("\nNATURAL LANGUAGE → CLI COMMAND MAPPING:")
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. Input: \"{example['input']}\"")
        print(f"   Output: {example['expected']}")


def demo_ai_configuration():
    """Show AI configuration and available engines."""
    print("\n" + "=" * 60)
    print("AI ENGINE CONFIGURATION")
    print("=" * 60)
    
    print(f"\nDefault Engine: {config.ai.default_engine}")
    print(f"Available Engines: {config.get_available_engines() or 'None (no API keys configured)'}")
    print(f"Safety Checks: {'Enabled' if config.cli.safety_checks else 'Disabled'}")
    print(f"Auto Execute: {'Enabled' if config.cli.auto_execute else 'Disabled'}")
    
    print(f"\nModel Configuration:")
    print(f"  OpenAI: {config.ai.openai_model}")
    print(f"  Anthropic: {config.ai.anthropic_model}")
    print(f"  Google: {config.ai.google_model}")
    
    print(f"\nAI Parameters:")
    print(f"  Temperature: {config.ai.temperature}")
    print(f"  Max Tokens: {config.ai.max_tokens}")
    print(f"  Timeout: {config.ai.timeout}s")


def demo_interactive_commands():
    """Show examples of interactive AI session commands."""
    print("\n" + "=" * 60)
    print("INTERACTIVE AI SESSION EXAMPLES")
    print("=" * 60)
    
    print("\nTo start an interactive AI session:")
    print("  onecode ai --interactive")
    
    print("\nInteractive session commands:")
    print("  help          - Show help information")
    print("  status        - Show AI engine status")
    print("  exit/quit/bye - Exit the session")
    
    print("\nExample interactive session:")
    print("  🤖 AI Assistant: launch gazebo with empty world")
    print("  🧠 Processing: launch gazebo with empty world")
    print("  📋 Generated 1 command(s):")
    print("    1. onecode sim launch gazebo --world empty_world.sdf")
    print("  Do you want to execute these commands? [y/N]: y")
    print("  ✅ Successfully executed 1 command(s)")


def demo_advanced_features():
    """Demonstrate advanced AI features."""
    print("\n" + "=" * 60)
    print("ADVANCED AI FEATURES")
    print("=" * 60)
    
    print("\nCommand-line options:")
    print("  --engine openai              Use specific AI engine")
    print("  --show-reasoning             Show AI confidence and explanation")
    print("  --auto-execute               Execute without confirmation")
    print("  --dry-run                    Preview commands without execution")
    
    print("\nMulti-step operations:")
    print("  Input: \"start slam mapping and create behavior tree\"")
    print("  Output:")
    print("    1. onecode gen node slam_node --template cpp")
    print("    2. onecode gen behavior_tree mapping_bt")
    print("    3. onecode sim launch gazebo --robot-model turtlebot3_burger")
    
    print("\nSafety features:")
    print("  ✓ Command validation against dangerous patterns")
    print("  ✓ Whitelist of approved command prefixes")
    print("  ✓ Confidence scoring for AI suggestions")
    print("  ✓ Optional user confirmation before execution")
    print("  ✓ Comprehensive logging and audit trail")


def demo_setup_instructions():
    """Show setup instructions for AI integration."""
    print("\n" + "=" * 60)
    print("SETUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1. Install AI provider dependencies:")
    print("   pip install openai                    # For OpenAI GPT models")
    print("   pip install anthropic                 # For Anthropic Claude models")
    print("   pip install google-generativeai      # For Google Gemini models")
    
    print("\n2. Set up API keys (choose one or more):")
    print("   export OPENAI_API_KEY=\"your_openai_key\"")
    print("   export ANTHROPIC_API_KEY=\"your_anthropic_key\"")
    print("   export GOOGLE_API_KEY=\"your_google_key\"")
    
    print("\n3. Optional configuration:")
    print("   export ONECODE_AI_ENGINE=\"openai\"")
    print("   export ONECODE_AI_TEMPERATURE=\"0.1\"")
    print("   export ONECODE_SAFETY_CHECKS=\"true\"")
    
    print("\n4. Test the setup:")
    print("   onecode ai \"test command generation\"")
    print("   onecode ai --interactive")


def main():
    """Run all demonstrations."""
    print("OneCodePlant Phase 3: AI Engine Integration Demonstration")
    print("This demo shows the natural language processing capabilities.")
    
    try:
        demo_command_validation()
        demo_natural_language_examples()
        demo_ai_configuration()
        demo_interactive_commands()
        demo_advanced_features()
        demo_setup_instructions()
        
        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("\nPhase 3 AI Engine Integration is fully operational!")
        print("Ready to convert natural language to CLI commands.")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())