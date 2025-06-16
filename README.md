# AgentFrameWork

一个基于LangChain的多智能体协作框架，支持复杂任务的分解、规划和执行。

## 🌟 特性

- **多步骤任务规划**: 自动将复杂任务分解为可执行的步骤
- **智能体协作**: 支持多个智能体协同工作
- **动态控制流**: 支持循环、条件分支等复杂执行逻辑
- **记忆管理**: 智能的记忆压缩和管理机制
- **状态管理**: 完整的执行状态跟踪
- **全面测试框架**: 包含单元测试、集成测试和覆盖率分析

## 📁 项目结构

```
AgentFrameWork/
├── enhancedAgent_v2.py          # 核心多步骤智能体实现
├── agent_base.py                # 基础智能体类
├── pythonTask.py               # Python任务执行器
├── prompts.py                  # 提示词模板
├── tests/                      # 测试目录
│   └── test_multi_step_agent_v2.py  # 单元测试套件
├── htmlcov/                    # HTML覆盖率报告
├── run_tests.sh                # 完整测试脚本
├── run_tests_enhanced.sh       # 增强测试脚本
├── run_coverage_simple.sh      # 简化覆盖率测试脚本
├── .coveragerc                 # 覆盖率配置
└── README.md                   # 项目文档
```

## 🚀 安装

### 前置要求

- Python 3.8+
- pip 包管理器

### 安装依赖

```bash
pip install -r requirements.txt
```

### 开发依赖（测试相关）

```bash
pip install pytest coverage
```

## 🏁 快速开始

### 基本使用

```python
from enhancedAgent_v2 import MultiStepAgent_v2, AgentSpecification
from pythonTask import Agent
from langchain_openai import ChatOpenAI

# 初始化LLM
llm = ChatOpenAI(model="gpt-4")

# 创建多步骤智能体
multi_agent = MultiStepAgent_v2(llm=llm)

# 注册成员智能体
coder = Agent(llm=llm)
multi_agent.register_agent("coder", coder)

# 执行任务
result = multi_agent.execute_multi_step("请用python写一个计算器程序并测试")
print(result)
```

### 高级配置

```python
# 使用自定义计划模板
custom_template = """
自定义任务规划模板...
{main_instruction}
{available_agents_str}
"""

multi_agent = MultiStepAgent_v2(
    llm=llm,
    planning_prompt_template=custom_template,
    use_autonomous_planning=False,
    max_retries=5
)
```

## 🧪 测试框架

### 测试结构

项目包含全面的测试套件，覆盖了以下方面：

1. **基本组件测试** - 类初始化、属性验证
2. **Agent注册测试** - 智能体注册和管理
3. **计划执行测试** - 任务规划功能
4. **步骤选择测试** - 智能步骤选择逻辑
5. **执行方法测试** - 核心执行方法
6. **异常处理测试** - 错误处理和容错机制
7. **边界条件测试** - 极端情况处理
8. **代码覆盖率分析** - 测试覆盖度量

### 运行测试

#### 1. 快速测试（推荐）

运行不需要API调用的核心测试：

```bash
# 使用简化覆盖率脚本
chmod +x run_coverage_simple.sh
./run_coverage_simple.sh
```

#### 2. 增强测试

运行选定的重要测试用例：

```bash
chmod +x run_tests_enhanced.sh
./run_tests_enhanced.sh
```

#### 3. 完整测试套件

运行所有测试（需要AI API密钥）：

```bash
chmod +x run_tests.sh
./run_tests.sh
```

#### 4. 手动运行特定测试

```bash
# 运行特定测试方法
python -m pytest tests/test_multi_step_agent_v2.py::TestMultiStepAgentV2::test_import_and_initialization -v

# 运行特定类别的测试
python -m pytest tests/test_multi_step_agent_v2.py -k "boundary" -v

# 运行所有测试
python -m pytest tests/test_multi_step_agent_v2.py -v
```

### 代码覆盖率

#### 生成覆盖率报告

```bash
# 清理旧数据
coverage erase

# 运行测试并收集覆盖率
coverage run --source=enhancedAgent_v2 -m pytest tests/test_multi_step_agent_v2.py::TestMultiStepAgentV2::test_import_and_initialization -v

# 生成控制台报告
coverage report -m

# 生成HTML报告
coverage html
```

#### 查看覆盖率报告

1. **控制台报告**: 直接在终端查看
2. **HTML报告**: 打开 `htmlcov/index.html` 文件
3. **专项报告**: 查看 `htmlcov/enhancedAgent_v2_py.html`

```bash
# 在浏览器中打开HTML报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 测试配置

#### .coveragerc 配置

```ini
[run]
source = enhancedAgent_v2
omit = 
    tests/*
    */site-packages/*

[report]
show_missing = True
precision = 2

[html]
directory = htmlcov
```

### 测试结果解释

#### 成功测试输出示例

```
test_import_and_initialization PASSED                           [100%]
========================== 1 passed in 8.28s ==========================
✅ 测试执行成功

📊 覆盖率报告：
Name               Stmts   Miss  Cover   Missing
------------------------------------------------
enhancedAgent_v2     667    584    12%   ...
------------------------------------------------
TOTAL                667    584    12%
```

#### 覆盖率指标说明

- **Stmts**: 总代码行数
- **Miss**: 未被测试覆盖的行数
- **Cover**: 覆盖率百分比
- **Missing**: 具体未覆盖的行号

#### 失败诊断

如果测试失败，检查以下内容：

1. **API密钥**: 确保AI服务API密钥正确配置
2. **依赖**: 确认所有依赖包正确安装
3. **网络**: 检查网络连接和代理设置
4. **日志**: 查看详细的错误输出信息

## 🏗️ 核心组件

### MultiStepAgent_v2

主要的多步骤智能体类，提供以下功能：

- **任务规划**: `plan_execution()`
- **步骤执行**: `execute_single_step()`
- **智能调度**: `select_next_executable_step()`
- **决策制定**: `make_decision()`
- **控制流**: 支持循环、跳转等

### Agent

基础智能体类，提供：

- **代码执行**: `execute_stream()`
- **对话处理**: `chat_stream()`
- **记忆管理**: 自动记忆压缩
- **状态跟踪**: 有状态执行

### StatefulExecutor

状态执行器，支持：

- **Python代码执行**: 安全的代码执行环境
- **变量管理**: 跨步骤的变量共享
- **状态持久化**: 执行状态保存

### AgentSpecification

智能体规格类，用于：

- **智能体元数据管理**: 名称、描述、实例
- **注册机制**: 智能体注册和查找
- **能力描述**: API规格说明

## 🔧 开发和调试

### 日志配置

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 或者只对特定模块设置
logger = logging.getLogger('enhancedAgent_v2')
logger.setLevel(logging.DEBUG)
```

### 调试技巧

1. **使用交互模式**: `execute_multi_step(task, interactive=True)`
2. **检查计划**: 查看生成的执行计划JSON
3. **分析决策**: 观察决策制定过程
4. **监控状态**: 跟踪工作流状态变化

### 扩展开发

#### 添加新的智能体类型

```python
class CustomAgent(Agent):
    def __init__(self, llm, specialty="custom"):
        super().__init__(llm)
        self.api_specification = f"专门处理{specialty}任务的智能体"
    
    def specialized_method(self):
        # 自定义方法实现
        pass
```

#### 自定义决策逻辑

```python
class CustomMultiStepAgent(MultiStepAgent_v2):
    def make_decision(self, current_result, task_history=None, context=None):
        # 自定义决策逻辑
        custom_decision = super().make_decision(current_result, task_history, context)
        # 添加自定义处理
        return custom_decision
```

## 📚 API参考

### MultiStepAgent_v2 主要方法

| 方法 | 描述 | 参数 |
|------|------|------|
| `__init__()` | 初始化智能体 | `llm`, `agent_specs`, `max_retries` |
| `register_agent()` | 注册新智能体 | `name`, `instance` |
| `execute_multi_step()` | 执行多步骤任务 | `main_instruction`, `interactive` |
| `plan_execution()` | 规划执行步骤 | `main_instruction` |
| `execute_single_step()` | 执行单个步骤 | `step`, `task_history` |
| `make_decision()` | 制定执行决策 | `current_result`, `task_history` |

### 配置参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `use_autonomous_planning` | bool | True | 是否使用自主规划模式 |
| `max_retries` | int | 3 | 最大重试次数 |
| `planning_prompt_template` | str | None | 自定义规划模板 |

## 🤝 贡献指南

### 代码贡献

1. Fork 项目
2. 创建功能分支
3. 编写测试
4. 确保测试通过
5. 提交Pull Request

### 测试贡献

1. 为新功能编写测试用例
2. 确保代码覆盖率
3. 添加边界条件测试
4. 更新文档

### 代码风格

- 遵循PEP 8标准
- 添加类型注解
- 编写详细的文档字符串
- 包含示例代码

## 🐛 问题报告

如果遇到问题，请：

1. 检查[常见问题](#常见问题)
2. 搜索现有Issues
3. 提供完整的错误信息
4. 包含复现步骤
5. 说明环境信息

## 📖 常见问题

### Q: 测试运行很慢怎么办？

A: 使用快速测试脚本 `./run_coverage_simple.sh`，它只运行不需要API调用的核心测试。

### Q: 覆盖率报告显示"No data was collected"？

A: 这通常是因为模块已经被导入。使用我们提供的测试脚本会自动清理缓存。

### Q: 如何添加新的测试用例？

A: 在 `tests/test_multi_step_agent_v2.py` 中添加新的测试方法，遵循现有的命名约定。

### Q: 如何配置AI服务？

A: 根据你使用的LLM服务，配置相应的API密钥和端点。

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至项目维护者

---

**注意**: 运行完整测试套件需要AI服务API密钥。对于快速验证，推荐使用 `run_coverage_simple.sh` 脚本。 