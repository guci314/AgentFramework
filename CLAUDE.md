# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentFrameWork is an advanced, multi-functional AI Agent framework designed to build, manage, and coordinate intelligent agents capable of autonomously executing complex multi-step tasks. The framework has evolved significantly from static workflows to dynamic, adaptive task execution, representing a paradigm shift from traditional agent frameworks to cognitive workflow systems.

### Project Evolution
The framework has undergone significant architectural evolution:

1. **Early Stage (`enhancedAgent_v2.py`)**: Established foundational concepts including multi-agent collaboration, state management, prompt templates, and response parsers, but with relatively fixed workflows.

2. **Mid-Stage (`MultiStepAgent_v3.py`)**: Iterative optimization of early versions with improved core logic but still with limitations.

3. **Current State**: Two major advanced systems:
   - **CognitiveWorkflow**: Revolutionary dynamic navigation with planner-decider-executor roles
   - **TaskMasterAgent**: Integration with external "Task Master AI" for intelligent task decomposition

## Core Architecture

### Current Advanced Systems

#### 1. CognitiveWorkflow System (`CognitiveWorkflow/`)
The most advanced implementation featuring dynamic navigation and adaptive execution:

- **CognitivePlanner**: Divergent thinking, generates comprehensive task lists with all possibilities
- **CognitiveDecider**: Runtime dynamic orchestration, state satisfaction checking, plan modification
- **CognitiveExecutor**: Pure execution unit focused on task completion
- **Key Innovation**: Replaces static dependencies with natural language preconditions
- **Dynamic Navigation**: Real-time path construction instead of predefined flow charts

##### 1.1 Production Rule Workflow System (`cognitive_workflow_rule_base/`)
Advanced production rule-based cognitive workflow engine with DDD architecture:
- **Domain Driven Design**: Clean separation of concerns with domain, service, application, and infrastructure layers
- **CognitiveAgent**: Application layer wrapper providing intelligent instruction classification and multi-step execution
- **TaskTranslator**: Solves context pollution in hierarchical cognitive architectures
- **Production Rule Engine**: IF-THEN natural language rule execution with adaptive optimization
- **Context Pollution Solution**: Hierarchical cognitive architecture with task translation layer for filtering complex upper-layer context

#### 2. TaskMasterAgent System (`task_master_agent.py`)
Integration with external "Task Master AI" system:
- Intelligent task decomposition and complexity analysis
- Advanced dependency management
- Automated task expansion and prioritization

#### 3. Legacy Foundation Systems

##### Agent System
- **AgentBase** (`agent_base.py`): Base class for all agents with memory management, chat and execution capabilities
- **Agent**: Enhanced agent with stateful execution capabilities using StatefulExecutor
- **MultiStepAgent_v2** (`enhancedAgent_v2.py`): Original multi-step orchestrator (now superseded)
- **MultiStepAgent_v3** (`MultiStepAgent_v3.py`): Improved version with better execution model

##### Key Components
- **StatefulExecutor** (`pythonTask.py`): Provides code execution environment with variable management (IPython-based)
- **WorkflowState**: Manages workflow execution state including loop counters and context variables
- **AgentSpecification**: Stores agent metadata and instances for team coordination
- **GlobalState**: Natural language state management for cognitive workflows
- **StateConditionChecker**: State satisfaction checker for precondition validation

### Memory Management
- Uses tiktoken for accurate token counting
- Advanced memory optimization with multiple strategies:
  - `@reduce_memory_decorator`: Token-based memory reduction
  - `@reduce_memory_decorator_compress`: Compression-based memory reduction using summarization
- Memory compression via `message_compress.py`
- Protected messages system for preserving important context
- Configurable via `AGENT_MAX_TOKENS` environment variable (default: 60,000 tokens)

## Development Commands

### Testing
```bash
# Core framework tests
python test_basic.py
python test_calculator.py
python test_compression.py
python test_jump_fix.py

# CognitiveWorkflow tests
cd CognitiveWorkflow
python test_cognitive_workflow.py
python test_basic_functionality.py
python test_three_phase_planning.py

# Comprehensive test suites
cd tests
python run_all_tests.py
python test_stress_boundary.py

# Static workflow tests
cd static_workflow/tests
python test_static_workflow.py
python test_workflow_examples.py
```

### Running Examples
```bash
# CognitiveWorkflow demos (Recommended)
cd CognitiveWorkflow
python demo_cognitive_workflow.py
python hello_world.py

# Legacy examples
python simple_calculator.py
python enhancedAgent_v2.py
python demo_agent_compression.py

# TaskMaster integration
python examples/basic_task_master.py
python examples/observability_demo.py

# MCP (Model Context Protocol) examples
cd mcp_examples
python simple_mcp_demo.py
python deepseek_mcp_example.py
```

### Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Additional dependencies for MCP examples
cd mcp_examples
pip install -r requirements.txt
```

## Key Files Structure

### Current Advanced Systems

#### CognitiveWorkflow System (`CognitiveWorkflow/`)
- `cognitive_workflow.py` - Core cognitive workflow engine (1000+ lines)
- `cognitive_workflow_adapter.py` - Compatibility adapter for legacy systems
- `demo_cognitive_workflow.py` - Complete demonstration program
- `认知工作流的核心理念.md` - Core philosophy and concepts (Chinese)
- `cognitive_workflow_rule_base/` - Production rule workflow system
  - `engine/production_rule_workflow_engine.py` - Rule-based execution engine
  - `services/` - Various cognitive services (optimization, pattern recognition)
  - `examples/` - Cognitive workflow examples and demos

#### TaskMaster Integration
- `task_master_agent.py` - TaskMaster AI integration
- `task_master/` - TaskMaster client and data mapping
- `examples/basic_task_master.py` - TaskMaster usage examples

#### Static Workflow System (`static_workflow/`)
- `MultiStepAgent_v3.py` - Enhanced multi-step agent
- `static_workflow_engine.py` - Static workflow execution engine
- `workflow_definitions.py` - Workflow definition structures
- `workflow_examples/` - JSON workflow definitions

### Core Foundation Files
- `agent_base.py` - Base agent class with memory management
- `enhancedAgent_v2.py` - Legacy multi-step agent implementation
- `pythonTask.py` - Stateful executor and enhanced agent classes
- `response_parser_v2.py` - Advanced response parsing system

### Configuration & Prompts
- `prompts.py` - System messages and prompt templates for different agent roles
- `config.yaml` - Main configuration file
- `config_system.py` - Configuration management system

### MCP Integration (`mcp_examples/`)
- `simple_mcp_demo.py` - Basic MCP demonstration
- `deepseek_mcp_example.py` - DeepSeek MCP integration
- `enhanced_server.py` - Enhanced MCP server implementation

### Testing & Quality Assurance
- `tests/` - Comprehensive test suite with boundary stress tests
- `test_*.py` - Unit tests for various components (60+ test files)
- `run_tests.sh` - Test execution scripts
- Various integration and stress tests

### Documentation (`docs/`)
- `README.md` - Main documentation
- `TASK_MASTER_AI_TUTORIAL.md` - TaskMaster integration guide
- `COGNITIVE_WORKFLOW_REFACTOR_SUMMARY.md` - Refactoring documentation
- `USER_QUICK_START_GUIDE.md` - User getting started guide
- Chinese documentation for various components

### Examples and Demos
- Calculator project examples in multiple implementations
- Sales data analysis examples
- Performance monitoring and observability demos

## Agent Interaction Patterns

### CognitiveWorkflow Execution (Recommended)
```python
# Direct usage
from CognitiveWorkflow.cognitive_workflow import CognitiveWorkflowEngine
engine = CognitiveWorkflowEngine(llm=llm, agents=agents)
result = engine.execute_cognitive_workflow("high-level goal")

# Using adapter for compatibility
from CognitiveWorkflow.cognitive_workflow_adapter import CognitiveMultiStepAgent
agent = CognitiveMultiStepAgent(llm=llm, registered_agents=agents, use_cognitive_workflow=True)
result = agent.execute_multi_step("task description")
```

### Legacy Execution Methods
- `execute_sync(instruction)` - Synchronous code execution
- `execute_stream(instruction)` - Streaming execution with real-time output
- `chat_sync(message)` - Synchronous conversation
- `chat_stream(message)` - Streaming conversation

### Team Coordination
- **CognitiveWorkflow**: Dynamic agent selection based on task requirements and state
- **Legacy**: Agents registered via `AgentSpecification` with name, instance, and description
- State sharing through StatefulExecutor variables and GlobalState
- Memory loading via `loadKnowledge(knowledge_string)`
- Natural language preconditions for intelligent task orchestration

## Memory Management Best Practices

### Token Limits
- Default: 60,000 tokens (configurable via `AGENT_MAX_TOKENS` environment variable)
- Automatic memory reduction at 80-90% threshold
- Protected messages preserved during reduction
- CognitiveWorkflow uses intelligent memory optimization

### Memory Strategies
1. **Token-based**: Preserves recent conversation pairs and protected messages
2. **Compression**: Intelligently compresses middle conversations while preserving context
3. **Cognitive**: Dynamic memory management based on task relevance and state importance
4. **Caching**: SQLite-based LLM response caching for performance optimization

## Code Conventions

### Error Handling
- All code execution wrapped in try-catch blocks
- Comprehensive logging with different verbosity levels
- Task completion validation using assertions
- CognitiveWorkflow includes automatic error recovery and task generation

### Agent Development
- **New Projects**: Use CognitiveWorkflow system directly
- **Legacy Migration**: Use CognitiveMultiStepAgent adapter
- **Foundation**: Inherit from `AgentBase` for basic functionality
- **Stateful Execution**: Use `Agent` class with StatefulExecutor
- **Streaming**: Implement streaming methods for real-time feedback
- **Memory**: Add memory decorators for automatic memory management
- **Natural Language**: Use natural language preconditions for task dependencies

### Testing Patterns
- Use `unittest.TestCase` for structured testing
- Include both success and failure scenarios
- Test data setup in `setUp()` methods
- Comprehensive assertion checking
- Boundary and stress testing in `tests/` directory
- CognitiveWorkflow specific tests in `CognitiveWorkflow/` directory

## Environment Variables

- `AGENT_MAX_TOKENS` - Maximum token limit for agent memory (default: 60,000)
- Standard LangChain environment variables for LLM configuration
- Proxy settings for network requests (see pythonTask.py configuration)
- TaskMaster AI integration configuration variables

## Integration Notes

### LLM Support
- **OpenAI models** via `langchain_openai.ChatOpenAI`
- **Cohere models** via `langchain_cohere.ChatCohere` 
- **Anthropic models** via `anthropic` package
- **DeepSeek integration** via MCP examples
- **Caching enabled** via SQLite for performance optimization
- **Model switching** support in CognitiveWorkflow

### External Tools & Integrations
- **IPython integration** for code execution via StatefulExecutor
- **Jupyter notebook support** for interactive development
- **MCP (Model Context Protocol)** integration for external tool access
- **TaskMaster AI** for intelligent task decomposition
- **HTTP client** with proxy configuration
- **File system operations** and data analysis capabilities
- **Performance monitoring** and observability tools

### Key Integration Patterns
- **Production Rule System**: Rule-based workflow execution
- **Adaptive Hyperparameter Optimization**: Dynamic parameter tuning
- **Intelligent Performance Benchmarking**: Automated performance analysis
- **Predictive Optimization Framework**: Machine learning-based optimization

## Working with This Codebase

### Priority Areas for Understanding
1. **CognitiveWorkflow System** - The most advanced and recommended approach
2. **Memory Management** - Critical for production deployments
3. **Agent Workflow Patterns** - Understanding execution models
4. **State Management** - Both GlobalState and WorkflowState systems

### Recommended Development Path
1. Start with CognitiveWorkflow examples (`CognitiveWorkflow/demo_cognitive_workflow.py`)
2. Understand the three-role architecture (Planner-Decider-Executor)
3. Explore natural language preconditions and state satisfaction
4. Use the adapter pattern for legacy system integration
5. Implement comprehensive testing following the established patterns

### Migration Strategy
- **New features**: Use CognitiveWorkflow directly
- **Existing code**: Use CognitiveMultiStepAgent adapter
- **Performance critical**: Consider static workflow for deterministic behavior
- **Complex tasks**: Leverage TaskMaster AI integration

This framework represents a paradigm shift from static to dynamic agent workflows, with CognitiveWorkflow being the current state-of-the-art implementation.