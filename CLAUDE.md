# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentFrameWork is an advanced, multi-functional AI Agent framework designed to build, manage, and coordinate intelligent agents capable of autonomously executing complex multi-step tasks. The framework has evolved significantly from static workflows to dynamic, adaptive task execution, representing a paradigm shift from traditional agent frameworks to cognitive workflow systems.

### Project Evolution
The framework has undergone significant architectural evolution:

1. **Early Stage (`enhancedAgent_v2.py`)**: Established foundational concepts including multi-agent collaboration, state management, prompt templates, and response parsers, but with relatively fixed workflows.

2. **Mid-Stage (`MultiStepAgent_v3.py`)**: Iterative optimization of early versions with improved core logic but still with limitations.

3. **Current State**: Three major advanced systems:
   - **CognitiveWorkflow**: Revolutionary dynamic navigation with planner-decider-executor roles
   - **TaskMasterAgent**: Integration with external "Task Master AI" for intelligent task decomposition
   - **EmbodiedCognitiveWorkflow**: Four-layer cognitive architecture with natural language state management

## Core Architecture

### 🧠 Foundational Design Principle: Natural Language First

**The entire framework is built on a fundamental principle: ALL communication and state management uses natural language.**

- **Instructions are Natural Language**: User commands, task descriptions, and agent communications are all in natural language
- **States are Natural Language**: All cognitive states, evaluations, and context information are stored and transmitted as natural language descriptions
- **No Hard-coded Enums**: The system avoids rigid state enumerations, instead using flexible natural language descriptions
- **Human-Readable Transparency**: Every aspect of the cognitive process can be understood and audited by humans
- **AI-Model Friendly**: Natural language states are inherently compatible with Large Language Models

This design enables:
- **Cognitive Transparency**: All agent thinking processes are human-readable
- **Dynamic Flexibility**: States can evolve and adapt without code changes
- **Cross-Agent Communication**: Different agent types can understand each other's states
- **Debugging Simplicity**: All states and decisions are in plain language
- **Extensibility**: New cognitive patterns can be added without structural changes

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

#### 2. Embodied Cognitive Workflow System (`embodied_cognitive_workflow/`)
**The most advanced natural language cognitive architecture featuring four-layer intelligence:**

**🧠 Four-Layer Cognitive Architecture:**
- **SuperEgo (超我)**: Meta-cognitive supervision and ethical constraints with UltraThink capabilities
- **Ego (自我)**: Rational analysis and decision-making with state analysis and action planning
- **Id (本我)**: Value-driven evaluation and goal monitoring with task specification management
- **Body (身体)**: Execution and perception layer based on existing Agent systems

**🌟 Natural Language State Management:**
- **WorkflowContext**: Central context manager with natural language state representation
  - `current_state`: Natural language description of cognitive analysis by Ego
  - `id_evaluation`: Natural language evaluation results from Id
  - `goal_achieved`: Boolean control variable for workflow termination
- **Dynamic Navigation**: Real-time cognitive cycle based on natural language state analysis
- **Incremental Planning (增量式规划)**: Step-by-step adaptive execution without predefined workflows

**🔄 Cognitive Cycle Process:**
1. **Complexity Assessment**: Ego evaluates if task needs cognitive cycle
2. **State Analysis**: Ego analyzes current situation in natural language
3. **Decision Making**: Ego decides next action based on state analysis
4. **Value Evaluation**: Id evaluates goal achievement using natural language assessment
5. **Body Execution**: Body executes concrete actions
6. **Cycle Control**: WorkflowContext.goal_achieved determines continuation

**💡 Key Innovations:**
- **Natural Language Preconditions**: Replace static dependencies with flexible language descriptions
- **Cognitive Debugging**: CognitiveDebugger provides step-by-step execution analysis
- **Streaming Support**: Real-time cognitive process observation
- **JSON-based Evaluation**: Structured goal achievement assessment
- **Multi-modal Evaluation**: Both internal (Id) and external (Body observation) evaluation modes

#### 3. TaskMasterAgent System (`task_master_agent.py`)
Integration with external "Task Master AI" system:
- Intelligent task decomposition and complexity analysis
- Advanced dependency management
- Automated task expansion and prioritization

#### 4. Legacy Foundation Systems

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
# Embodied Cognitive Workflow demos (Most Advanced - Recommended)
cd embodied_cognitive_workflow
python debug_demo.py
python test_goal_achieved_fix_final.py
python demo_workflow_context_docstring.py

# CognitiveWorkflow demos
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

#### Embodied Cognitive Workflow System (`embodied_cognitive_workflow/`)
**🧠 Four-Layer Cognitive Architecture with Natural Language State Management**
- `embodied_cognitive_workflow.py` - Main CognitiveAgent with four-layer architecture
- `super_ego_agent.py` - SuperEgo intelligence with UltraThink capabilities  
- `ego_agent.py` - Ego intelligence for rational analysis and decision-making
- `id_agent.py` - Id intelligence for value-driven evaluation and goal monitoring
- `cognitive_debugger.py` - Advanced debugging system with step-by-step cognitive analysis
- `demo_workflow_context_docstring.py` - Natural language state management demonstration
- `debug_demo.py` - Complete cognitive debugging workflow demonstration
- `test_goal_achieved_fix_final.py` - WorkflowContext.goal_achieved control validation

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

### 🧠 Embodied Cognitive Workflow Execution (Most Advanced - Recommended)
**Natural Language State Management with Four-Layer Cognitive Architecture**

```python
from embodied_cognitive_workflow import CognitiveAgent
import pythonTask

# Create cognitive agent with natural language state management
agent = CognitiveAgent(
    llm=pythonTask.llm_gemini_2_5_flash_google,
    max_cycles=5,                    # Maximum cognitive cycles
    verbose=True,                    # Show natural language process
    enable_super_ego=True,           # Enable meta-cognitive supervision
    evaluation_mode="external"       # Use JSON-based goal evaluation
)

# ✨ All instructions are natural language
instruction = "开发一个Python计算器程序，包含基本的四则运算功能"

# Synchronous execution with natural language states
result = agent.execute_sync(instruction)
print(f"Result: {result.return_value}")

# Streaming execution - observe natural language cognitive process
for chunk in agent.execute_stream(instruction):
    if isinstance(chunk, Result):
        print(f"Final Result: {chunk.return_value}")
    else:
        print(f"Cognitive Process: {chunk}")  # Natural language descriptions

# Chat mode with natural language state persistence
chat_result = agent.chat_sync("Please explain the calculator architecture")
```

**🔍 Natural Language Cognitive Debugging:**
```python
from embodied_cognitive_workflow.cognitive_debugger import CognitiveDebugger, StepType

# Create debugger for step-by-step natural language analysis
debugger = CognitiveDebugger(agent)
debugger.start_debug("计算 15 + 23 的结果")

# Single-step execution with natural language state inspection
while not debugger.debug_state.is_finished:
    step_result = debugger.run_one_step()
    if step_result.step_type == StepType.ID_EVALUATION:
        # Inspect natural language evaluation
        print(f"本我评估 (Natural Language): {step_result.output_data}")
        print(f"目标达成状态: {debugger.debug_state.workflow_context.goal_achieved}")
```

**🎯 Natural Language State Access:**
```python
# Access natural language states directly
context = agent.workflow_context  # If available from execution
print("Natural Language Context:")
print(f"- Current State: {context.current_state}")      # Natural language analysis
print(f"- Id Evaluation: {context.id_evaluation}")     # Natural language evaluation  
print(f"- Goal Achieved: {context.goal_achieved}")     # Boolean control variable
print(f"- Full Context:\n{context.get_current_context()}")  # Complete natural language context
```

### CognitiveWorkflow Execution
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
- **🧠 New Projects**: Use EmbodiedCognitiveWorkflow for natural language state management
- **Advanced Projects**: Use CognitiveWorkflow system for dynamic navigation
- **Legacy Migration**: Use CognitiveMultiStepAgent adapter
- **Foundation**: Inherit from `AgentBase` for basic functionality
- **Stateful Execution**: Use `Agent` class with StatefulExecutor
- **Streaming**: Implement streaming methods for real-time feedback
- **Memory**: Add memory decorators for automatic memory management
- **🌟 Natural Language First**: ALL states, instructions, and communications must be in natural language
  - Instructions: Always accept natural language user commands
  - States: Store all cognitive states as natural language descriptions
  - Evaluation: Use natural language assessment with JSON structure for parsing
  - Context: Maintain human-readable context for transparency
  - Avoid: Hard-coded enums, binary flags, or numeric state codes

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
1. **🧠 Embodied Cognitive Workflow System** - The most advanced natural language cognitive architecture
2. **🌟 Natural Language State Management** - Core principle: instructions and states are natural language
3. **CognitiveWorkflow System** - Advanced dynamic navigation approach
4. **Memory Management** - Critical for production deployments
5. **Agent Workflow Patterns** - Understanding execution models

### Recommended Development Path
1. **Start with Embodied Cognitive Workflow** (`embodied_cognitive_workflow/debug_demo.py`)
2. **Understand Natural Language Principles**: All states are natural language descriptions
3. **Explore Four-Layer Architecture**: SuperEgo → Ego → Id → Body cognitive layers
4. **Study WorkflowContext**: Natural language state management and goal_achieved control
5. **Use CognitiveDebugger**: Step-by-step natural language cognitive process analysis
6. **Explore CognitiveWorkflow** for dynamic navigation patterns
7. **Implement Testing**: Following natural language state validation patterns

### Migration Strategy
- **🧠 New features**: Use EmbodiedCognitiveWorkflow for natural language state management
- **Advanced features**: Use CognitiveWorkflow for dynamic navigation
- **Existing code**: Use CognitiveMultiStepAgent adapter for legacy integration
- **Performance critical**: Consider static workflow for deterministic behavior
- **Complex tasks**: Leverage TaskMaster AI integration
- **🌟 Always maintain**: Natural language first principle in all implementations

This framework represents a paradigm shift from static to dynamic agent workflows, with **EmbodiedCognitiveWorkflow** being the most advanced implementation featuring natural language state management and four-layer cognitive architecture.