# MultiStepAgent_v3 - 静态工作流智能体

MultiStepAgent_v3是一个基于静态工作流架构的多步骤智能体系统，采用声明式控制流实现高性能、可预测的任务执行。

## 核心特性

### 🏗️ 声明式工作流配置
- JSON/YAML格式的工作流定义
- 完整的控制流支持（sequential、conditional、loop、parallel）
- 变量插值和动态配置
- Schema验证和完整性检查

### ⚡ 高性能执行
- 预定义的执行路径，无运行时LLM决策开销
- 并行步骤执行支持
- 确定性的控制流执行
- 高效的状态管理

### 🔧 完整的错误处理
- 预定义的错误恢复策略
- 自动重试和回退机制
- 超时和资源限制控制
- 详细的执行日志记录

### 🤖 智能体集成
- 与现有Agent系统完全兼容
- 支持多智能体协作
- 状态共享和数据传递
- 灵活的智能体注册机制

## 架构概览

```
MultiStepAgent_v3
├── 静态工作流引擎 (StaticWorkflowEngine)
│   ├── 状态机执行器
│   ├── 并行任务处理器
│   └── 控制规则评估器
├── 工作流定义系统 (WorkflowDefinition)
│   ├── Schema验证器
│   ├── JSON/YAML加载器
│   └── 配置验证器
├── 控制流评估器 (ControlFlowEvaluator)
│   ├── 安全表达式评估
│   ├── 变量插值器
│   └── 条件判断引擎
└── 智能体管理器
    ├── 智能体注册
    ├── 任务分发
    └── 结果收集
```

## 快速开始

### 1. 环境设置

```bash
# 设置DeepSeek API密钥
export DEEPSEEK_API_KEY="your_deepseek_api_key_here"

# 安装依赖
pip install langchain-openai
```

### 2. 基础使用

```python
import os
from langchain_openai import ChatOpenAI
from pythonTask import Agent
from static_workflow import MultiStepAgent_v3

# 配置DeepSeek模型
llm_deepseek = ChatOpenAI(
    temperature=0,
    model="deepseek-chat",  
    base_url="https://api.deepseek.com",
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    max_tokens=8192
)

# 初始化MultiStepAgent_v3
agent_v3 = MultiStepAgent_v3(llm=llm_deepseek)

# 注册智能体团队
coder = Agent(llm=llm_deepseek, stateful=True)
tester = Agent(llm=llm_deepseek, stateful=True)

agent_v3.register_agent("coder", coder, "Python开发专家")
agent_v3.register_agent("tester", tester, "软件测试专家")

# 执行预定义工作流
result = agent_v3.execute_workflow_from_file("calculator_workflow.json")

print(f"执行结果: {'成功' if result.success else '失败'}")
print(f"完成步骤: {result.completed_steps}/{result.total_steps}")
```

### 3. 自定义工作流

```python
# 创建自定义工作流
custom_workflow = {
    "workflow_metadata": {
        "name": "hello_world",
        "version": "1.0",
        "description": "Hello World 工作流"
    },
    "global_variables": {
        "greeting": "Hello, World!"
    },
    "steps": [
        {
            "id": "create_program",
            "name": "创建程序",
            "agent_name": "coder",
            "instruction": "创建一个打印 '${greeting}' 的Python程序",
            "instruction_type": "execution",
            "expected_output": "Python程序",
            "control_flow": {
                "type": "sequential",
                "success_next": "test_program",
                "failure_next": None
            }
        },
        {
            "id": "test_program",
            "name": "测试程序",
            "agent_name": "tester",
            "instruction": "运行程序并验证输出",
            "instruction_type": "execution",
            "expected_output": "测试结果",
            "control_flow": {
                "type": "terminal"
            }
        }
    ],
    "control_rules": [],
    "error_handling": {
        "default_strategy": "retry_with_backoff"
    }
}

# 执行自定义工作流
workflow_def = agent_v3.create_workflow_from_dict(custom_workflow)
result = agent_v3.execute_workflow(workflow_def)
```

## 工作流配置详解

### 控制流类型

#### 1. Sequential（顺序执行）
```json
{
    "control_flow": {
        "type": "sequential",
        "success_next": "下一步骤ID",
        "failure_next": "失败处理步骤ID"
    }
}
```

#### 2. Conditional（条件分支）
```json
{
    "control_flow": {
        "type": "conditional",
        "condition": "success_rate >= 0.8",
        "success_next": "成功分支步骤ID",
        "failure_next": "失败分支步骤ID"
    }
}
```

#### 3. Loop（循环控制）
```json
{
    "control_flow": {
        "type": "loop",
        "loop_condition": "retry_count < max_retries",
        "loop_target": "循环目标步骤ID",
        "max_iterations": 3,
        "exit_on_max": "退出时跳转步骤ID"
    }
}
```

#### 4. Parallel（并行执行）
```json
{
    "control_flow": {
        "type": "parallel",
        "parallel_steps": ["step1", "step2", "step3"],
        "join_condition": "all_complete",
        "success_next": "合并后下一步",
        "timeout": 120
    }
}
```

#### 5. Terminal（终止执行）
```json
{
    "control_flow": {
        "type": "terminal"
    }
}
```

### 变量插值

工作流支持动态变量插值：

```json
{
    "global_variables": {
        "max_retries": 3,
        "project_name": "my_project"
    },
    "steps": [
        {
            "instruction": "为项目 ${project_name} 重试最多 ${max_retries} 次"
        }
    ]
}
```

### 条件表达式

支持丰富的条件表达式：

```json
{
    "condition": "retry_count < max_retries AND success_rate >= 0.8",
    "loop_condition": "test_passed == false OR retry_count < 3"
}
```

## 示例工作流

### 1. 计算器实现工作流
```bash
# 查看示例
cat static_workflow/workflow_examples/calculator_workflow.json

# 执行示例
python demo_static_workflow.py
```

### 2. 数据处理工作流
```bash
# 查看并行处理示例
cat static_workflow/workflow_examples/data_processing.json
```

### 3. 代码测试工作流
```bash
# 查看复杂循环和条件分支示例
cat static_workflow/workflow_examples/code_test_workflow.json
```

## API参考

### MultiStepAgent_v3

#### 主要方法

- `register_agent(name, instance, description)`: 注册智能体
- `execute_workflow_from_file(workflow_file)`: 从文件执行工作流
- `execute_workflow(workflow_definition)`: 执行工作流定义
- `create_workflow_from_dict(workflow_dict)`: 从字典创建工作流
- `list_available_workflows()`: 列出可用工作流
- `get_workflow_info(workflow_file)`: 获取工作流信息

#### 初始化参数

```python
MultiStepAgent_v3(
    llm=llm_instance,                    # 语言模型实例
    registered_agents=None,              # 预注册的智能体列表
    max_retries=3,                       # 最大重试次数
    max_parallel_workers=4,              # 最大并行工作进程数
    workflow_base_path="path/to/workflows"  # 工作流配置基础路径
)
```

### WorkflowExecutionResult

执行结果对象包含：

```python
result.success              # 执行是否成功
result.workflow_name        # 工作流名称
result.total_steps          # 总步骤数
result.completed_steps      # 完成步骤数
result.failed_steps         # 失败步骤数
result.skipped_steps        # 跳过步骤数
result.execution_time       # 执行时间（秒）
result.step_results         # 各步骤详细结果
result.error_message        # 错误信息（如有）
```

## 测试

### 运行单元测试
```bash
# 基础组件测试
python -m pytest static_workflow/tests/test_static_workflow.py -v

# 工作流示例测试
python -m pytest static_workflow/tests/test_workflow_examples.py -v
```

### 运行演示
```bash
# 完整演示（需要DEEPSEEK_API_KEY）
python demo_static_workflow.py

# 基础组件测试（无需API密钥）
python -c "
import sys; sys.path.append('.')
from static_workflow import WorkflowLoader
loader = WorkflowLoader()
workflow = loader.load_from_file('static_workflow/workflow_examples/calculator_workflow.json')
print(f'成功加载: {workflow.workflow_metadata.name}')
"
```

## 与MultiStepAgent_v2的对比

| 特征 | MultiStepAgent_v2 (认知工作流) | MultiStepAgent_v3 (静态工作流) |
|------|---------------------------|---------------------------|
| **决策机制** | LLM动态决策 | 预定义规则决策 |
| **控制流** | 运行时生成 | 设计时定义 |
| **性能** | 较慢（LLM调用） | 高性能（无LLM开销） |
| **可预测性** | 不确定 | 完全确定 |
| **配置方式** | 代码定义 | JSON配置文件 |
| **调试性** | 困难 | 易于调试和分析 |
| **并行支持** | 有限 | 完整支持 |
| **适用场景** | 探索性任务 | 生产环境、标准化流程 |

## 最佳实践

### 1. 工作流设计原则
- **模块化**: 将复杂任务分解为独立的步骤
- **可重用**: 设计可在不同场景重用的步骤
- **容错性**: 为每个步骤定义失败处理策略
- **可观测**: 确保每步都有清晰的输出和状态

### 2. 性能优化
- **并行化**: 识别可并行执行的步骤
- **缓存**: 利用智能体的状态管理避免重复工作
- **超时控制**: 为长时间运行的步骤设置合理超时
- **资源管理**: 控制并行度避免资源过载

### 3. 错误处理
- **分层处理**: 步骤级、工作流级和全局级错误处理
- **优雅降级**: 在部分失败时仍能产生有用结果
- **详细日志**: 记录足够的信息用于问题诊断
- **人工干预**: 为复杂问题提供升级机制

### 4. 测试策略
- **单元测试**: 测试各个组件的独立功能
- **集成测试**: 测试完整工作流的执行
- **性能测试**: 验证执行效率和资源使用
- **边界测试**: 测试异常情况和边界条件

## 贡献指南

欢迎为MultiStepAgent_v3贡献代码和改进建议！

### 开发环境设置
```bash
# 克隆项目
git clone <repository_url>
cd AgentFrameWork

# 安装开发依赖
pip install -r requirements.txt
pip install pytest

# 运行测试
python -m pytest static_workflow/tests/ -v
```

### 提交规范
- 确保所有测试通过
- 添加适当的文档和注释
- 遵循现有的代码风格
- 提供清晰的提交信息

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 联系方式

如有问题或建议，请创建 Issue 或联系项目维护者。