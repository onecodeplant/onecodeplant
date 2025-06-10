# OneCodePlant Phase 3: AI Engine Integration

## Overview

Phase 3 introduces natural language processing capabilities to the OneCodePlant CLI framework, allowing users to input natural language instructions that are automatically converted into executable CLI commands using advanced language models.

## Features

### 🧠 Natural Language Processing
- **Multi-Provider Support**: OpenAI (GPT-4o), Anthropic (Claude-3.5-Sonnet), Google (Gemini)
- **Safety Validation**: Command sanitization and dangerous pattern detection
- **Confidence Scoring**: AI confidence assessment for generated commands
- **Interactive Mode**: Conversational AI session for continuous assistance

### 🛡️ Safety and Security
- **Command Validation**: Validates generated commands against dangerous patterns
- **Allowed Commands**: Restricts execution to safe, robotics-related commands
- **Dry Run Support**: Preview mode for testing without execution
- **User Confirmation**: Optional confirmation prompts before execution

### ⚙️ Configuration Management
- **Environment Variables**: Secure API key storage via environment variables
- **Multiple Engines**: Easy switching between AI providers
- **Model Selection**: Custom model specification per provider
- **Parameter Tuning**: Configurable temperature, max tokens, and timeouts

## Command Usage

### Basic Natural Language Commands

```bash
# Simple simulation launch
onecode ai "launch gazebo with turtlebot3 robot"

# Navigation and mapping
onecode ai "create a navigation node and start mapping"

# Robot control
onecode ai "publish move forward command to robot"

# Multiple operations
onecode ai "start slam mapping and create behavior tree"
```

### Advanced Options

```bash
# Specify AI engine
onecode ai --engine anthropic "launch webots simulation"

# Show reasoning and confidence
onecode ai --show-reasoning "create lidar-based slam node"

# Auto-execute without confirmation
onecode ai --auto-execute "echo laser scan data"

# Interactive mode
onecode ai --interactive
```

### Interactive Session

```bash
onecode ai --interactive
🤖 Starting interactive AI assistant...
Enter natural language instructions to convert to CLI commands.
Type 'exit' to quit, 'help' for assistance, or 'status' for engine info.

🤖 AI Assistant: launch gazebo with empty world
🧠 Processing: launch gazebo with empty world

📋 Generated 1 command(s):
  1. onecode sim launch gazebo --world empty_world.sdf

Do you want to execute these commands? [y/N]: y
```

## Configuration

### Environment Variables

```bash
# API Keys (set at least one)
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export GOOGLE_API_KEY="your_google_api_key"

# Engine Selection
export ONECODE_AI_ENGINE="openai"
export ONECODE_AI_MODEL="gpt-4o"

# AI Parameters
export ONECODE_AI_TEMPERATURE="0.1"
export ONECODE_AI_MAX_TOKENS="1000"

# CLI Behavior
export ONECODE_AUTO_EXECUTE="false"
export ONECODE_SAFETY_CHECKS="true"
```

### Configuration File

Create `~/.onecode/config.ini`:

```ini
[ai]
default_engine = openai
openai_model = gpt-4o
anthropic_model = claude-3-5-sonnet-20241022
google_model = gemini-pro
temperature = 0.1
max_tokens = 1000

[cli]
auto_execute = false
safety_checks = true
```

## Supported Commands

The AI engine can generate the following OneCodePlant commands:

### Simulation Control
```bash
onecode sim launch gazebo --world <world> --robot-model <model>
onecode sim pause/resume/reset/shutdown <simulator>
onecode sim status <simulator>
```

### Code Generation
```bash
onecode gen node <name> --template <language>
onecode gen behavior_tree <name>
onecode gen launch <name>
```

### ROS 2 Operations
```bash
onecode pub <topic> --message-type <type> --data <data>
onecode echo <topic> --count <count>
onecode param get/set/list <node> <param> <value>
onecode node --list/--info/--kill <node>
```

## Natural Language Examples

### Simulation Management
| Natural Language | Generated Command |
|------------------|-------------------|
| "launch gazebo with turtlebot3" | `onecode sim launch gazebo --robot-model turtlebot3_burger` |
| "start webots simulation headless" | `onecode sim launch webots --headless` |
| "pause the gazebo simulation" | `onecode sim pause gazebo` |

### Robot Control
| Natural Language | Generated Command |
|------------------|-------------------|
| "move robot forward" | `onecode pub /cmd_vel --message-type geometry_msgs/Twist --data '{"linear": {"x": 1.0}}'` |
| "stop the robot" | `onecode pub /cmd_vel --message-type geometry_msgs/Twist --data '{"linear": {"x": 0.0}}'` |
| "turn robot left" | `onecode pub /cmd_vel --message-type geometry_msgs/Twist --data '{"angular": {"z": 0.5}}'` |

### Development Tasks
| Natural Language | Generated Command |
|------------------|-------------------|
| "create navigation node in python" | `onecode gen node navigation_node --template python` |
| "generate behavior tree for mapping" | `onecode gen behavior_tree mapping_bt` |
| "show laser scan data" | `onecode echo /scan --count 5` |

## Architecture

### Core Components

```
onecode/
├── ai/
│   ├── __init__.py              # AI module initialization
│   ├── nlp_processor.py         # Core NLP processing engine
│   └── prompts/
│       └── base_prompt.txt      # LLM prompt templates
├── config.py                   # Configuration management
└── cli.py                      # Enhanced AI command interface
```

### NLP Processing Pipeline

1. **Input Validation**: Check natural language input for safety
2. **Prompt Construction**: Build context-aware prompts using templates
3. **LLM Processing**: Send to configured AI provider (OpenAI/Anthropic/Google)
4. **Response Parsing**: Extract and clean CLI commands from response
5. **Safety Validation**: Validate commands against security patterns
6. **Confidence Assessment**: Calculate reliability score for suggestions
7. **User Confirmation**: Optional confirmation before execution
8. **Command Execution**: Execute validated commands with logging

### LLM Provider Abstraction

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_completion(self, prompt: str) -> str: pass
    
class OpenAIProvider(BaseLLMProvider):
    # Uses gpt-4o model with chat completions API
    
class AnthropicProvider(BaseLLMProvider):
    # Uses claude-3-5-sonnet-20241022 with messages API
    
class GoogleProvider(BaseLLMProvider):
    # Uses gemini-pro with generate_content API
```

## Safety Features

### Command Validation

The system validates all generated commands against:

- **Dangerous Patterns**: File deletion, system commands, elevated privileges
- **Allowed Commands**: Whitelist of safe robotics and development commands
- **Shell Operators**: Detection of potentially dangerous shell operations

### Error Handling

- **API Failures**: Graceful handling of LLM API errors
- **Invalid Responses**: Robust parsing with fallback mechanisms
- **Command Failures**: Detailed error reporting with suggested fixes
- **Network Issues**: Timeout handling and retry logic

### Security Measures

- **API Key Protection**: Secure environment variable storage
- **Command Sanitization**: Removal of dangerous command patterns
- **Execution Isolation**: Sandboxed command execution environment
- **Audit Logging**: Complete command history and execution logs

## Installation and Setup

### Prerequisites

```bash
# Install OneCodePlant dependencies
pip install click psutil

# Install AI provider dependencies (choose one or more)
pip install openai                    # For OpenAI GPT models
pip install anthropic                 # For Anthropic Claude models
pip install google-generativeai      # For Google Gemini models
```

### API Key Setup

1. **OpenAI**: Get API key from https://platform.openai.com/
2. **Anthropic**: Get API key from https://console.anthropic.com/
3. **Google**: Get API key from https://makersuite.google.com/

Set environment variables:
```bash
echo 'export OPENAI_API_KEY="your_key_here"' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="your_key_here"' >> ~/.bashrc
echo 'export GOOGLE_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

### Verification

```bash
# Test AI functionality
onecode ai "test command generation"

# Check available engines
onecode ai --interactive
status
```

## Troubleshooting

### Common Issues

#### No API Keys Configured
```
❌ No AI engines configured. Please set up API keys:
   • OpenAI: Set OPENAI_API_KEY environment variable
   • Anthropic: Set ANTHROPIC_API_KEY environment variable
   • Google: Set GOOGLE_API_KEY environment variable
```

**Solution**: Set at least one API key as shown in setup section.

#### Missing Dependencies
```
ImportError: OpenAI package not installed. Install with: pip install openai
```

**Solution**: Install required AI provider packages.

#### Command Validation Errors
```
❌ Dangerous pattern detected: rm.*-rf
```

**Solution**: The AI generated an unsafe command. Review the natural language input and try rephrasing.

### Debug Mode

Enable detailed logging:
```bash
export ONECODE_LOG_LEVEL=DEBUG
onecode ai --show-reasoning "your query here"
```

## Future Enhancements

### Planned Features
- **Local Model Support**: Integration with local LLM models
- **Context Memory**: Session-based conversation history
- **Custom Prompts**: User-defined prompt templates
- **Multi-Modal Input**: Image and voice input support
- **Learning Feedback**: Model fine-tuning from user corrections

### Plugin Integration
- **Behavior Tree Generation**: Enhanced BT creation with AI
- **Code Completion**: AI-powered code suggestions
- **Debugging Assistant**: Intelligent error diagnosis
- **Documentation Generation**: Automatic README and docs creation

The Phase 3 AI Engine Integration transforms OneCodePlant into an intelligent robotics development assistant, making complex CLI operations accessible through natural language interaction.