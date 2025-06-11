# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentFrameWork is a multi-agent collaboration framework based on LangChain that supports task decomposition, planning and execution. It implements a finite state machine workflow with intelligent memory management and supports complex task flows including loops and conditional branches.

## Core Architecture

### Agent System
- **AgentBase**: Base class for all agents with memory management, chat and execution capabilities
- **Agent**: Enhanced agent with stateful execution capabilities using StatefulExecutor
- **MultiStepAgent_v2**: Main orchestrator for multi-step task planning and execution

### Key Components
- **StatefulExecutor**: Provides code execution environment with variable management (IPython-based)
- **WorkflowState**: Manages workflow execution state including loop counters and context variables
- **AgentSpecification**: Stores agent metadata and instances for team coordination

### Memory Management
- Uses tiktoken for accurate token counting
- Two decorators available:
  - `@reduce_memory_decorator`: Token-based memory reduction
  - `@reduce_memory_decorator_compress`: Compression-based memory reduction
- Memory compression via `message_compress.py`
- Protected messages system for preserving important context

## Development Commands

### Testing
```bash
# Run basic tests
python test_basic.py

# Run calculator tests  
python test_calculator.py

# Run compression tests
python test_compression.py

# Run jump fix tests
python test_jump_fix.py
```

### Running Examples
```bash
# Basic calculator example
python simple_calculator.py

# Enhanced agent demo
python enhancedAgent_v2.py

# Compression demo
python demo_agent_compression.py
```

### Dependencies
```bash
# Install required packages
pip install -r requirements.txt
```

## Key Files Structure

### Core Agent Files
- `agent_base.py` - Base agent class with memory management
- `enhancedAgent_v2.py` - Main multi-step agent implementation
- `pythonTask.py` - Stateful executor and enhanced agent classes

### Configuration & Prompts
- `prompts.py` - System messages and prompt templates for different agent roles
- `field_mapping.json` - Field mapping configuration
- `metadata.json` - Project metadata

### Testing & Examples
- `test_*.py` - Unit tests for various components
- `simple_calculator.py` - Basic calculator example
- `demo_agent_compression.py` - Memory compression demonstration

### Data Processing
- `*.csv`, `*.json` files - Sample data and analysis results
- `sales_analysis_report.*` - Generated reports in various formats

## Agent Interaction Patterns

### Execution Methods
- `execute_sync(instruction)` - Synchronous code execution
- `execute_stream(instruction)` - Streaming execution with real-time output
- `chat_sync(message)` - Synchronous conversation
- `chat_stream(message)` - Streaming conversation

### Team Coordination
- Agents registered via `AgentSpecification` with name, instance, and description
- State sharing through StatefulExecutor variables
- Memory loading via `loadKnowledge(knowledge_string)`

## Memory Management Best Practices

### Token Limits
- Default: 60,000 tokens (configurable via `AGENT_MAX_TOKENS` environment variable)
- Automatic memory reduction at 80-90% threshold
- Protected messages preserved during reduction

### Memory Strategies
1. **Token-based**: Preserves recent conversation pairs and protected messages
2. **Compression**: Intelligently compresses middle conversations while preserving context

## Code Conventions

### Error Handling
- All code execution wrapped in try-catch blocks
- Comprehensive logging with different verbosity levels
- Task completion validation using assertions

### Agent Development
- Inherit from `AgentBase` for basic functionality
- Use `Agent` class for stateful execution needs
- Implement streaming methods for real-time feedback
- Add memory decorators for automatic memory management

### Testing Patterns
- Use `unittest.TestCase` for structured testing
- Include both success and failure scenarios
- Test data setup in `setUp()` methods
- Comprehensive assertion checking

## Environment Variables

- `AGENT_MAX_TOKENS` - Maximum token limit for agent memory
- Standard LangChain environment variables for LLM configuration
- Proxy settings for network requests (see pythonTask.py configuration)

## Integration Notes

### LLM Support
- OpenAI models via `langchain_openai.ChatOpenAI`
- Cohere models via `langchain_cohere.ChatCohere`
- Anthropic models via `anthropic` package
- Caching enabled via SQLite for performance

### External Tools
- IPython integration for code execution
- Jupyter notebook support
- HTTP client with proxy configuration
- File system operations and data analysis capabilities

When working with this codebase, prioritize understanding the agent workflow and memory management systems, as these are central to the framework's functionality.