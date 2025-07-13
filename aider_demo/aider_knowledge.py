#!/usr/bin/env python3
"""
aider知识库定义
"""

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
```python
# 当收到创建Python文件的请求时
if "创建" in 用户指令 or "编写" in 用户指令 or "生成" in 用户指令:
    # 使用aider而不是直接写代码
    use_aider_to_create_file()
else:
    # 其他情况正常处理
    handle_normally()
```

### 示例对比

#### ❌ 错误做法（直接生成代码）
```python
# 不要这样做
def create_calculator():
    code = '''
class Calculator:
    def add(self, a, b):
        return a + b
'''
    with open('calculator.py', 'w') as f:
        f.write(code)
```

#### ✅ 正确做法（使用Aider）
```python
# 应该这样做
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

## 环境变量配置
需要设置对应模型的API密钥：
- DEEPSEEK_API_KEY: DeepSeek模型密钥
- OPENAI_API_KEY: OpenAI模型密钥
- ANTHROPIC_API_KEY: Claude模型密钥
- GEMINI_API_KEY: Gemini模型密钥

## 支持的模型
- deepseek/deepseek-chat (推荐，性价比高)
- gpt-4o-mini
- claude-3-5-sonnet
- gemini/gemini-pro

## 基本用法

### 导入必要模块
```python
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
```

### 创建新文件
```python
# 指定要创建的文件
fnames = ["calculator.py"]

# 使用deepseek模型
model = Model("deepseek/deepseek-chat")

# 创建coder对象
coder = Coder.create(main_model=model, fnames=fnames)

# 执行创建文件的指令
coder.run("创建一个Calculator类，包含加减乘除方法")
```

### 修改现有文件
```python
# 指定要修改的文件
fnames = ["existing_file.py"]

# 创建coder对象
coder = Coder.create(main_model=model, fnames=fnames)

# 执行修改指令
coder.run("为所有函数添加类型注解和文档字符串")
```

### 批量处理多个文件
```python
# 指定多个文件
fnames = ["file1.py", "file2.py", "file3.py"]

# 创建coder对象
coder = Coder.create(main_model=model, fnames=fnames)

# 批量处理
coder.run("优化所有文件的代码结构，添加错误处理")
```

### 使用只读参考文件
```python
# 可编辑的文件
editable_files = ["main.py", "utils.py"]

# 只读参考文件（将被包含在上下文中但不会被修改）
read_only_files = ["config.py", "constants.py", "README.md", "api_docs.txt"]

# 创建包含只读文件的coder对象
coder = Coder.create(
    main_model=model,
    fnames=editable_files,           # 可以被修改的文件
    read_only_fnames=read_only_files, # 只读参考文件
    io=io
)

# 现在aider可以参考只读文件的内容来修改可编辑文件
coder.run("根据config.py中的配置更新main.py的数据库连接")
coder.run("使用constants.py中定义的常量替换main.py中的硬编码值")
```

## 高级用法

### 自动确认模式（重要）
```python
# 创建自动确认的IO对象（避免交互式提示）
io = InputOutput(yes=True)

# 使用自动确认模式，禁用命令执行
coder = Coder.create(
    main_model=model, 
    fnames=fnames, 
    io=io,
    auto_commits=False,  # 避免自动git提交
    dirty_commits=False  # 避免在有未提交更改时继续
)

# 重要：避免让aider执行shell命令，只让它修改文件
# 不要在指令中包含"运行"、"测试"、"执行"等词
```

### 连续执行多个指令
```python
# 创建coder对象
coder = Coder.create(main_model=model, fnames=["app.py"])

# 执行一系列指令
coder.run("创建一个Flask应用的基础结构")
coder.run("添加用户认证功能")
coder.run("实现RESTful API端点")
coder.run("添加数据库模型")
```

### 使用特定的Git设置
```python
# 禁用Git操作
coder = Coder.create(
    main_model=model,
    fnames=fnames,
    git=False  # 相当于--no-git
)
```

### 查看token使用情况
```python
# 执行指令后查看token使用
coder.run("实现一个功能")
coder.run("/tokens")  # 查看token统计
```

## 常用参数说明

### Coder.create()参数
- `main_model`: Model对象，指定使用的AI模型
- `fnames`: 文件名列表，要处理的文件
- `read_only_fnames`: 只读文件列表，作为参考但不会被修改
- `io`: InputOutput对象，控制输入输出行为
- `git`: 布尔值，是否启用Git操作
- `auto_commits`: 布尔值，是否自动提交更改
- `dirty_commits`: 布尔值，是否允许在有未提交更改时继续
- `dry_run`: 布尔值，只显示将要做的更改而不实际执行

### Model()参数
- 模型名称字符串，如"deepseek/deepseek-chat"
- 支持的模型取决于配置的API密钥

## 实际应用示例

### 创建完整的Python项目
```python
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

# 自动确认模式
io = InputOutput(yes=True)
model = Model("deepseek/deepseek-chat")

# 创建项目主文件
coder = Coder.create(main_model=model, fnames=["main.py"], io=io)
coder.run("创建一个命令行待办事项应用的主程序")

# 创建数据模型
coder = Coder.create(main_model=model, fnames=["models.py"], io=io)
coder.run("创建Todo类，包含id、title、completed、created_at字段")

# 创建工具函数
coder = Coder.create(main_model=model, fnames=["utils.py"], io=io)
coder.run("创建文件读写和JSON序列化的工具函数")
```

### 重构现有代码
```python
# 重构单个文件
coder = Coder.create(main_model=model, fnames=["legacy_code.py"], io=io)
coder.run("将这个文件重构为面向对象的设计，提取重复代码为独立函数")

# 批量重构
files = ["module1.py", "module2.py", "module3.py"]
coder = Coder.create(main_model=model, fnames=files, io=io)
coder.run("统一所有模块的命名规范，使用snake_case，添加类型提示")
```

### 添加测试用例
```python
# 为现有代码添加测试
coder = Coder.create(
    main_model=model, 
    fnames=["calculator.py", "test_calculator.py"],
    io=io
)
coder.run("为calculator.py中的所有方法编写单元测试")
```

## 最佳实践

### 1. 明确的指令
```python
# 好的指令 - 具体明确
coder.run("创建一个User类，包含name(str)、email(str)、age(int)属性，添加validate_email方法")

# 避免模糊指令
# coder.run("创建一个用户类")
```

### 2. 分步执行复杂任务
```python
# 将复杂任务分解为多个步骤
coder.run("创建FastAPI应用的基础结构")
coder.run("添加用户模型和数据库schema")
coder.run("实现用户的CRUD端点")
coder.run("添加JWT认证中间件")
```

### 3. 合理的文件组织
```python
# 相关文件一起处理
coder = Coder.create(
    main_model=model,
    fnames=["models.py", "schemas.py", "database.py"],
    io=io
)
coder.run("创建SQLAlchemy数据库模型和Pydantic schemas")
```

### 4. 错误处理
```python
try:
    coder = Coder.create(main_model=model, fnames=["app.py"])
    coder.run("实现功能")
except Exception as e:
    print(f"Aider执行出错: {e}")
```

### 5. 使用只读文件的场景
```python
# 场景1：参考API文档修改代码
coder = Coder.create(
    main_model=model,
    fnames=["client.py"],
    read_only_fnames=["api_documentation.md"],
    io=io
)
coder.run("根据api_documentation.md更新client.py中的API调用")

# 场景2：根据配置文件修改代码
coder = Coder.create(
    main_model=model,
    fnames=["app.py"],
    read_only_fnames=["config.json", "settings.py"],
    io=io
)
coder.run("更新app.py以使用config.json中的数据库配置")

# 场景3：参考测试用例修改实现
coder = Coder.create(
    main_model=model,
    fnames=["calculator.py"],
    read_only_fnames=["test_calculator.py"],
    io=io
)
coder.run("修改calculator.py使其通过test_calculator.py中的所有测试")
```

## 注意事项

- 确保API密钥正确设置在环境变量中
- 文件路径使用相对路径或绝对路径都可以
- 大型文件处理时注意token限制
- 重要操作前建议备份文件
- 使用io=InputOutput(yes=True)避免交互式确认
- git=False可以禁用Git操作，适合非Git项目
- **重要**：避免让aider执行shell命令，专注于文件的创建和修改
- **重要**：指令中不要包含"运行"、"测试"、"执行"等会触发shell命令的词汇
- **只读文件说明**：
  - 只读文件会被包含在聊天上下文中，但不会被修改
  - 适合用于提供参考信息、配置、文档等
  - 只读文件不存在时会显示警告并跳过
  - 可以同时使用多个只读文件

## 错误处理

### 使用subprocess作为备选方案
当Python API遇到交互式提示错误时，可以使用subprocess调用aider命令行：

```python
import subprocess
import os

# 构建aider命令
cmd = [
    "aider",
    "--model", "deepseek/deepseek-chat",
    "--yes",      # 自动确认所有提示
    "--no-git",   # 对新项目禁用git
    "--message", "你的指令（避免使用执行、测试等词）",
    "target_file.py"
]

# 执行命令
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    timeout=30  # 设置超时
)

if result.returncode == 0:
    print("成功:", result.stdout)
else:
    print("失败:", result.stderr)
```

### 避免交互式提示错误
```python
# 完整的非交互式配置
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

# 创建完全非交互的IO
io = InputOutput(
    yes=True,           # 自动确认
    pretty=False        # 简化输出
)

# 创建安全的coder实例
coder = Coder.create(
    main_model=model,
    fnames=fnames,
    io=io,
    auto_commits=False,
    dirty_commits=False,
    show_diffs=False  # 不显示差异
)

# 只使用文件操作指令，不触发shell命令
coder.run("创建一个Calculator类")  # 好
# coder.run("创建并测试Calculator类")  # 避免，会触发shell命令
```
"""