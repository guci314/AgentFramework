#!/usr/bin/env python3
"""
Aider 工具智能体工厂方法

提供预定义的 Aider 编程助手工具智能体实例创建功能。
该智能体专门用于通过 Aider 进行代码生成、修改和项目管理。
"""

import os
import sys
from typing import Optional

# 添加父目录到Python路径以导入核心模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from python_core import Agent
from llm_lazy import get_model

# Aider 知识库
aider_knowledge = """
# Aider Python API编程知识库

## 重要原则：优先使用Aider
**当用户要求编写、创建或生成Python文件时，应该调用aider来完成，而不是自己直接生成代码。**

### 判断何时使用Aider
- ✅ 用户说："创建一个Python文件"
- ✅ 用户说："编写一个类/函数/模块"
- ✅ 用户说："生成代码"
- ✅ 用户说："实现某个功能"
- ❌ 用户明确说："你直接写代码"
- ❌ 用户要求解释代码概念
- ❌ 用户询问语法问题

### 使用Aider的标准流程
当收到创建Python文件的请求时，判断是否需要使用aider：
- 如果用户指令包含"创建"、"编写"或"生成"，则使用aider
- 否则按正常流程处理

### 示例对比

#### ❌ 错误做法（直接生成代码）
不要直接在代码中写入文件内容，而应该调用aider来生成。

#### ✅ 正确做法（使用Aider）
```python
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

io = InputOutput(yes=True)
model = Model("deepseek/deepseek-chat")
coder = Coder.create(main_model=model, fnames=["calculator.py"], io=io)
coder.run("创建一个Calculator类，包含add方法")
```

### 实际应用示例

当用户说："请创建一个Python文件，实现数据处理功能"

**Agent应该这样响应：**
```python
# 我将使用aider来创建数据处理文件
try:
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
    
    io = InputOutput(yes=True)
    model = Model("deepseek/deepseek-chat")
    
    coder = Coder.create(
        main_model=model,
        fnames=["data_processor.py"],
        io=io,
        auto_commits=False,
        dirty_commits=False
    )
    
    coder.run("创建一个数据处理模块，包含读取、处理和保存数据的功能")
    print("已通过aider创建数据处理文件")
    
except Exception as e:
    # 如果aider失败，使用subprocess备选方案
    import subprocess
    cmd = [
        "aider", "--model", "deepseek/deepseek-chat",
        "--yes", "--no-git",
        "--message", "创建数据处理模块",
        "data_processor.py"
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=30)
```

## 概述
aider提供了Python API接口，可以在Python代码中直接调用aider的功能，而不需要使用命令行。

## 基本用法

### 1. 导入和初始化
```python
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

# 设置输入输出（yes=True表示自动确认）
io = InputOutput(yes=True)

# 创建模型（支持多种模型）
model = Model("deepseek/deepseek-chat")  # 或其他模型

# 创建Coder实例
coder = Coder.create(
    main_model=model,
    fnames=["file1.py", "file2.py"],  # 要编辑的文件列表
    io=io
)
```

### 2. 执行编程任务
```python
# 运行编程指令
coder.run("创建一个Calculator类，包含基本的数学运算方法")

# 连续执行多个任务
coder.run("添加单元测试")
coder.run("优化代码性能")
```

### 3. 高级配置
```python
# 完整的配置选项
coder = Coder.create(
    main_model=model,
    fnames=["app.py"],
    io=io,
    auto_commits=False,      # 不自动提交
    dirty_commits=False,     # 不提交未暂存的更改
    edit_format="diff",      # 编辑格式：diff、whole等
    stream=True,             # 流式输出
    use_git=True,           # 使用git
    map_tokens=1024,        # 映射token数
    verbose=True            # 详细输出
)
```

## 支持的模型

### OpenAI模型
```python
model = Model("gpt-4")
model = Model("gpt-3.5-turbo")
```

### Anthropic模型
```python
model = Model("claude-3-opus")
model = Model("claude-3-sonnet")
```

### 国产模型
```python
model = Model("deepseek/deepseek-chat")
model = Model("deepseek/deepseek-coder")
```

### 自定义模型配置
```python
# 使用自定义API端点
model = Model(
    "custom-model",
    api_base="https://api.example.com",
    api_key="your-api-key"
)
```

## 文件操作

### 添加文件到会话
```python
# 添加单个文件
coder.add_rel_fname("new_file.py")

# 添加多个文件
for fname in ["file1.py", "file2.py", "file3.py"]:
    coder.add_rel_fname(fname)
```

### 从会话移除文件
```python
# 移除文件
coder.drop_rel_fname("old_file.py")
```

### 查看当前文件列表
```python
# 获取当前编辑的文件列表
current_files = coder.get_inchat_relative_files()
print("当前编辑的文件:", current_files)
```

## 交互式编程

### 1. 循环交互模式
```python
while True:
    # 获取用户输入
    user_input = input("请输入编程指令 (输入'exit'退出): ")
    
    if user_input.lower() == 'exit':
        break
    
    # 执行指令
    coder.run(user_input)
```

### 2. 批处理模式
```python
# 批量执行任务
tasks = [
    "创建User类，包含用户基本信息",
    "添加用户验证方法",
    "创建对应的单元测试",
    "添加文档字符串"
]

for task in tasks:
    print(f"执行任务: {task}")
    coder.run(task)
```

## 错误处理

### 基本错误处理
```python
try:
    coder.run("创建复杂的功能")
except Exception as e:
    print(f"执行失败: {e}")
    # 使用备选方案
    fallback_solution()
```

### 完整的错误处理策略
使用try-except结构处理可能的错误，并提供备选方案（如subprocess调用）。

## 实用工具函数

### 1. 创建项目结构
使用aider创建完整的项目结构，包括必要的文件和目录。

### 2. 代码重构助手
提供不同类型的重构选项：优化、异步转换、添加类型注解、文档等。

### 3. 批量代码审查
对多个文件进行代码审查，检查bug、性能问题、安全漏洞等。

## 最佳实践

### 1. 使用上下文管理器
创建AiderContext类来管理aider会话的生命周期。

### 2. 任务队列处理
创建任务队列来批量处理多个编程任务。

### 3. 智能文件选择
使用glob模式智能选择需要编辑的文件，排除不必要的文件。

## 注意事项

1. **API密钥配置**
   - 设置环境变量：OPENAI_API_KEY、ANTHROPIC_API_KEY等
   - 或在代码中直接配置

2. **文件权限**
   - 确保对要编辑的文件有读写权限
   - 注意git仓库的状态

3. **性能优化**
   - 避免一次性加载过多文件
   - 使用合适的模型（代码任务用coder模型）
   - 合理设置token限制

4. **错误恢复**
   - 始终包含错误处理
   - 准备备选方案
   - 保存中间状态

这个知识库提供了使用aider Python API的完整指南，包括基本用法、高级功能、错误处理和最佳实践。
"""

def create_aider_agent(model_name: str = 'deepseek_chat', stateful: bool = True) -> Agent:
    """
    创建预配置的 Aider 编程助手工具智能体
    
    Args:
        model_name (str): 语言模型名称，默认为 'deepseek_chat'
        stateful (bool): 是否使用有状态执行器，默认为 True
    
    Returns:
        Agent: 配置了 Aider 编程知识的智能体实例
    
    Example:
        >>> agent = create_aider_agent()
        >>> result = agent.execute_sync("创建一个Python计算器类")
        >>> print(result.return_value)
    """
    try:
        # 获取语言模型
        llm = get_model(model_name)
        if llm is None:
            raise ValueError(f"无法获取模型: {model_name}")
        
        # 创建智能体实例
        agent = Agent(llm=llm, stateful=stateful)
        
        # 注入 Aider 知识
        agent.loadKnowledge(aider_knowledge)
        
        # 设置智能体名称和API规范
        agent.set_agent_name("Aider 编程助手")
        agent.set_api_specification(
            "专门用于通过 Aider 进行代码生成、修改和项目管理的智能体工具。"
            "我了解 Aider 的各种命令和参数、支持的 AI 模型、最佳实践等。"
            "优先使用 Aider Python API 或命令行而不是直接生成代码。"
        )
        
        print(f"✅ 成功创建 Aider 编程助手智能体 (模型: {model_name})")
        return agent
        
    except Exception as e:
        print(f"❌ 创建 Aider 编程助手智能体失败: {e}")
        raise

def test_aider_agent():
    """测试 Aider 编程助手智能体功能"""
    print("=== 测试 Aider 编程助手智能体 ===\n")
    
    try:
        # 创建智能体
        agent = create_aider_agent()
        
        # 测试指令
        command = "创建Python计算器class，类名为Calculator，文件名为calculator.py。创建单元测试文件test_calculator.py。"
        
        print(f"测试指令: {command}\n")
        print("执行结果:")
        print("-" * 50)
        
        # 执行测试
        result = None
        for chunk in agent.execute_stream(command):
            if isinstance(chunk, str):
                print(chunk, end="", flush=True)
            result = chunk
        
        print("\n" + "-" * 50)
        
        if result:
            print(f"执行状态: {'成功' if result.success else '失败'}")
            
            if hasattr(result, 'return_value') and result.return_value:
                print(f"返回值类型: {type(result.return_value)}")
        
    except Exception as e:
        print(f"测试失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 运行测试
    test_aider_agent()