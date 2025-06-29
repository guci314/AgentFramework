# 📁 Examples Directory

This directory contains demonstration code and examples for the Cognitive Workflow Rule Base system, including the powerful CognitiveAgent wrapper.

## 🚀 Available Examples

### 1. **basic_example.py**
Basic usage demonstration of the production rule workflow system.
- Shows how to create agents and initialize workflows
- Demonstrates simple goal execution
- Good starting point for understanding the system

### 2. **advanced_example.py**
Advanced features demonstration with specialized agents.
- Custom rules and error recovery
- Performance analysis and monitoring
- Complex workflow scenarios

### 3. **cognitive_agent_wrapper_demo.py** ⭐
**Complete demonstration of the CognitiveAgent wrapper** - this is the main demonstration file moved from the root directory.
- **Intelligent instruction classification**
- **Smart execution routing (chat/execute/workflow)**
- **Sync and stream execution modes**
- **Performance monitoring and statistics**

### 4. **simple_cognitive_demo.py**
Simplified CognitiveAgent demonstration focused on core functionality.
- Quick start guide for the wrapper
- Avoids complex workflow scenarios
- Perfect for understanding basics

### 5. **cognitive_agent_wrapper_test.py**
Comprehensive test suite for the CognitiveAgent wrapper.
- **Classification accuracy testing**
- **Functional testing of all features**
- **Real-world usage scenarios**
- **Performance benchmarking**

### 6. **test_api_specification.py** 🆕
Tests for the new api_specification property feature.
- **Automatic API specification inheritance from base_agent**
- **Property getter and setter functionality**
- **Fallback handling for agents without api_specification**
- **Usage demonstration with specialized agents**

### 7. **test_workflow_result_deduplication.py** 🆕
Verification of WorkflowExecutionResult deduplication solution.
- **Verifies removal of duplicate class definitions**
- **Confirms use of authoritative dataclass from domain layer**
- **Tests fallback mechanism for component unavailability**
- **Validates CognitiveAgent integration**

## 🎯 CognitiveAgent Wrapper Examples

The CognitiveAgent wrapper provides **seamless intelligence enhancement** to any basic Agent through:

### Key Features Demonstrated:

#### 🧠 **Intelligent Classification**
```python
# Automatic instruction type detection
instruction_type, execution_mode = cognitive_agent.classify_instruction("开发一个Web应用")
# Returns: ("executable", "multi_step")
```

#### ⚡ **Smart Execution Routing**
```python
# Automatically routes to optimal execution method
result1 = cognitive_agent.execute_instruction_syn("什么是Python？")  # → chat_sync
result2 = cognitive_agent.execute_instruction_syn("打印hello world")  # → execute_sync  
result3 = cognitive_agent.execute_instruction_syn("创建博客系统")     # → cognitive workflow
```

#### 🔄 **Stream Processing**
```python
# Real-time streaming execution
for update in cognitive_agent.execute_instruction_stream("解释Python特点"):
    if isinstance(update, str):
        print(update, flush=True)  # Process updates
    else:
        final_result = update      # Final result
```

#### 📊 **Performance Monitoring**
```python
# Comprehensive performance statistics
stats = cognitive_agent.get_performance_stats()
print(f"Classification accuracy: {stats['cache_info']['hit_rate_percent']}%")
print(f"Execution distribution: {stats['execution_distribution']}")
```

#### 🔧 **API Specification Inheritance** 🆕
```python
# API specification automatically inherited from base_agent
base_agent.api_specification = "Python专家，精通Web开发和数据分析"
cognitive_agent = CognitiveAgent(base_agent)

# Access API specification through the wrapper
print(cognitive_agent.api_specification)  # → "Python专家，精通Web开发和数据分析"

# Modify through the wrapper (updates base_agent)
cognitive_agent.api_specification = "更新后的API规范"
```

## 🚀 Quick Start

### Option 1: Simple Demo (Recommended for beginners)
```bash
cd CognitiveWorkflow/cognitive_workflow_rule_base/examples
python simple_cognitive_demo.py
```

### Option 2: Complete Demo (Full features)
```bash
cd CognitiveWorkflow/cognitive_workflow_rule_base/examples
python cognitive_agent_wrapper_demo.py
```

### Option 3: Run Tests (For validation)
```bash
cd CognitiveWorkflow/cognitive_workflow_rule_base/examples
python cognitive_agent_wrapper_test.py
```

### Option 4: Test API Specification Feature (New)
```bash
cd CognitiveWorkflow/cognitive_workflow_rule_base/examples
python test_api_specification.py
```

## 📋 Usage Patterns

### Basic Usage
```python
from pythonTask import Agent, llm_deepseek
from cognitive_workflow_rule_base.cognitive_workflow_agent_wrapper import CognitiveAgent

# Create base agent
base_agent = Agent(llm=llm_deepseek)

# Optional: Set API specification for the base agent
base_agent.api_specification = "Python编程专家，精通Web开发和数据分析"

# Wrap with cognitive capabilities
cognitive_agent = CognitiveAgent(
    base_agent=base_agent,
    enable_auto_recovery=True,
    classification_cache_size=50
)

# API specification is automatically inherited
print(cognitive_agent.api_specification)  # → "Python编程专家，精通Web开发和数据分析"

# Use enhanced agent
result = cognitive_agent.execute_instruction_syn("创建一个计算器程序")
```

### Classification Testing
```python
# Test instruction classification
instruction_type, execution_mode = cognitive_agent.classify_instruction("什么是机器学习？")
print(f"Type: {instruction_type}, Mode: {execution_mode}")
# Output: Type: informational, Mode: chat
```

### Stream Processing
```python
# Stream processing for real-time feedback
for update in cognitive_agent.execute_instruction_stream("解释深度学习"):
    if isinstance(update, str):
        print(f"Progress: {update}")
    else:
        print(f"Final result: {update}")
```

## 🔧 System Requirements

- Python 3.8+
- All dependencies from `requirements.txt`
- Access to LLM services (configured in `pythonTask.py`)

## 📖 Related Documentation

- **Main Implementation**: `../cognitive_workflow_agent_wrapper.py`
- **Architecture Guide**: `../基于产生式规则的Agent包装器.md`
- **Usage Guide**: `../使用示例_Agent包装器.md`
- **System Architecture**: `../认知工作流系统架构文档.md`

## 🎉 What Makes This Special

The CognitiveAgent wrapper transforms any basic Agent into an intelligent system that can:

1. **🔍 Automatically analyze** instruction types and complexity
2. **🎯 Route execution** to the most appropriate method
3. **🧠 Handle complex tasks** through cognitive workflow planning
4. **⚡ Optimize performance** with intelligent caching
5. **📊 Provide insights** through comprehensive monitoring

**Result**: Any Agent instantly becomes capable of cognitive reasoning and complex task planning!