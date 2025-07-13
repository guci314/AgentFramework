# 调用aider编程

## 概述

本文档介绍如何通过Agent的`loadKnowledge`方法给智能体注入aider编程知识，让Agent具备调用aider自动编程的能力。aider是一个强大的AI编程助手，可以通过命令行自动生成和修改代码。

## 前提条件

- ✅ aider已经安装好
- ✅ 配置好相关的API密钥（如DEEPSEEK_API_KEY等）
- ✅ Agent系统已正确配置

## 核心概念

### 什么是loadKnowledge方法

`loadKnowledge`方法是Agent系统中的核心功能，用于向智能体注入特定领域的知识。通过这个方法，我们可以：

1. **知识注入**：将aider的使用方法、命令参数等知识注入到Agent的记忆中
2. **持久化记忆**：注入的知识会被标记为`protected`，避免被内存管理删除
3. **上下文感知**：Agent在后续对话中可以利用这些知识进行aider编程

### aider编程知识结构

需要注入的aider知识包括：

1. **基础命令格式**
2. **常用参数说明**
3. **模型配置方法**
4. **环境变量设置**
5. **最佳实践和注意事项**

## 项目目录结构

为了更好地组织代码，请先创建一个专门的目录来存放所有相关文件：

```bash
# 在项目根目录下创建aider_demo目录
mkdir aider_demo
cd aider_demo
```

项目文件结构如下：
```
aider_demo/
├── aider_knowledge.py          # aider知识库定义
├── use_aider_agent.py          # 展示如何使用标准Agent
├── test_aider_agent.py         # 单元测试文件
├── integration_test_aider.py   # 集成测试文件
├── interactive_test.py         # 交互式测试文件
├── performance_test.py         # 性能测试文件
├── examples/                   # 示例代码目录
│   ├── create_calculator.py    # 创建计算器示例
│   ├── modify_files.py         # 修改文件示例
│   └── batch_process.py        # 批量处理示例
└── README.md                   # 项目说明文件
```

## 实现方案

### 1. 准备aider知识库

首先在`aider_demo`目录下创建`aider_knowledge.py`文件：

```python
#!/usr/bin/env python3
"""
aider知识库定义
"""

aider_knowledge = """
# Aider编程知识库

## 基础命令结构
aider是一个AI编程助手，基本使用格式：
```bash
aider [选项] [文件路径] --message "编程指令"
```

## 常用参数说明
- `--model`: 指定AI模型，如 deepseek/deepseek-chat
- `--message`: 直接传递编程指令
- `--no-git`: 禁用Git操作
- `--yes`: 自动确认所有操作
- `--watch`: 监控模式，自动处理文件变化
- `--map-tokens`: 设置代码地图的token限制

## 支持的模型
- deepseek/deepseek-chat (推荐，性价比高)
- gpt-4o-mini
- claude-3-5-sonnet
- gemini/gemini-pro

## 环境变量配置
需要设置对应模型的API密钥：
- DEEPSEEK_API_KEY: DeepSeek模型密钥
- OPENAI_API_KEY: OpenAI模型密钥
- ANTHROPIC_API_KEY: Claude模型密钥
- GEMINI_API_KEY: Gemini模型密钥

## 编程任务示例
1. 创建新文件：
   ```bash
   aider --model deepseek/deepseek-chat --message "创建一个hello.py文件，包含main函数"
   ```

2. 修改现有文件：
   ```bash
   aider --model deepseek/deepseek-chat existing_file.py --message "添加错误处理逻辑"
   ```

3. 批量处理：
   ```bash
   aider --model deepseek/deepseek-chat *.py --message "为所有Python文件添加类型注解"
   ```

## 最佳实践
1. 使用具体明确的指令
2. 指定目标文件路径
3. 适当的模型选择
4. 设置合适的token限制
5. 使用--no-git避免Git冲突

## 注意事项
- 确保API密钥正确设置
- 注意文件路径的准确性
- 大型项目建议使用--map-tokens限制
- 重要文件建议先备份
"""
```

### 2. 使用标准Agent加载aider知识

在`aider_demo`目录下创建`use_aider_agent.py`文件，展示如何使用标准Agent：

```python
#!/usr/bin/env python3
"""
使用标准Agent加载aider知识
"""
import sys
import os

# 添加父目录到Python路径以导入Agent框架
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
from aider_knowledge import aider_knowledge

# 创建标准Agent
llm = get_model('deepseek_v3')
agent = Agent(llm=llm, stateful=True)

# 通过loadKnowledge注入aider知识
agent.loadKnowledge(aider_knowledge)

# 设置Agent的API规范（可选）
agent.set_api_specification("""
我是一个具备aider编程知识的智能体。我了解：
1. aider的各种命令和参数
2. 如何使用aider生成和修改代码
3. aider支持的AI模型
4. 最佳实践和注意事项
""")

# Agent现在已经具备了aider编程知识，可以回答相关问题和生成aider命令
```

### 3. 使用示例

#### 3.1 创建新文件示例

在`aider_demo/examples`目录下创建`create_calculator.py`：

```python
#!/usr/bin/env python3
"""
示例：使用Agent创建计算器程序
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
from aider_knowledge import aider_knowledge

def main():
    # 初始化标准Agent
    llm = get_model('deepseek_v3')
    agent = Agent(llm=llm, stateful=True)
    
    # 注入aider知识
    agent.loadKnowledge(aider_knowledge)
    
    # 指令：创建一个计算器程序
    instruction = """
    请使用aider创建一个名为calculator.py的简单计算器程序，包含以下功能：
    1. 加法、减法、乘法、除法
    2. 主函数with命令行交互
    3. 错误处理
    使用deepseek模型
    """
    
    print("🚀 开始创建计算器程序...")
    result = agent.execute_sync(instruction)
    print(f"执行结果: {result.return_value}")

if __name__ == '__main__':
    main()
```

#### 3.2 修改现有文件示例

在`aider_demo/examples`目录下创建`modify_files.py`：

```python
#!/usr/bin/env python3
"""
示例：使用Agent修改现有文件
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
from aider_knowledge import aider_knowledge

def main():
    # 初始化标准Agent
    llm = get_model('deepseek_v3')
    agent = Agent(llm=llm, stateful=True)
    
    # 注入aider知识
    agent.loadKnowledge(aider_knowledge)
    
    # 首先创建一个示例文件
    with open('existing_script.py', 'w') as f:
        f.write('''
def main():
    print("This is a simple script")
    return 0

if __name__ == "__main__":
    main()
''')
    
    # 指令：为现有文件添加功能
    instruction = """
    请使用aider修改existing_script.py文件，添加以下功能：
    1. 日志记录功能
    2. 配置文件读取
    3. 命令行参数解析
    使用deepseek模型，不要使用git
    """
    
    print("🔧 开始修改文件...")
    result = agent.execute_sync(instruction)
    print(f"修改结果: {result.return_value}")

if __name__ == '__main__':
    main()
```

#### 3.3 批量处理示例

在`aider_demo/examples`目录下创建`batch_process.py`：

```python
#!/usr/bin/env python3
"""
示例：使用Agent批量处理文件
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
from aider_knowledge import aider_knowledge

def create_sample_files():
    """创建示例文件用于批量处理"""
    # 创建src目录
    os.makedirs('src', exist_ok=True)
    
    # 创建几个示例Python文件
    sample_files = {
        'src/utils.py': '''
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def find_max(items):
    if not items:
        return None
    max_val = items[0]
    for item in items[1:]:
        if item > max_val:
            max_val = item
    return max_val
''',
        'src/processor.py': '''
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def add_data(self, item):
        self.data.append(item)
    
    def process(self):
        results = []
        for item in self.data:
            results.append(item * 2)
        return results
''',
        'src/helpers.py': '''
def format_string(text, upper):
    if upper:
        return text.upper()
    else:
        return text.lower()

def validate_email(email):
    return '@' in email and '.' in email
'''
    }
    
    for filename, content in sample_files.items():
        with open(filename, 'w') as f:
            f.write(content)
    
    print("✅ 创建了示例文件：", list(sample_files.keys()))

def main():
    # 初始化标准Agent
    llm = get_model('deepseek_v3')
    agent = Agent(llm=llm, stateful=True)
    
    # 注入aider知识
    agent.loadKnowledge(aider_knowledge)
    
    # 创建示例文件
    create_sample_files()
    
    # 指令：批量优化代码
    instruction = """
    请使用aider批量处理src目录下的所有Python文件，进行以下优化：
    1. 添加类型注解
    2. 优化代码结构
    3. 添加文档字符串
    使用deepseek模型，设置适当的token限制
    """
    
    print("\n📦 开始批量处理文件...")
    result = agent.execute_sync(instruction)
    print(f"批量处理结果: {result.return_value}")

if __name__ == '__main__':
    main()
```

## 高级功能

### 1. 流式执行监控

```python
# 使用标准Agent的流式执行监控
agent = Agent(llm=get_model('deepseek_v3'), stateful=True)
agent.loadKnowledge(aider_knowledge)

for chunk in agent.execute_stream("使用aider创建一个Flask web应用"):
    if isinstance(chunk, str):
        print(f"进度: {chunk}")
    elif isinstance(chunk, Result):
        print(f"最终结果: {chunk.return_value}")
```

### 2. 环境变量动态配置

```python
# 动态配置不同模型的API密钥
def configure_aider_env(model_type):
    if model_type == "deepseek":
        return {"DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY")}
    elif model_type == "openai":
        return {"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")}
    elif model_type == "claude":
        return {"ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")}
    else:
        return {}

# 使用特定模型
instruction = """
请使用aider和Claude模型创建一个数据分析脚本，
包含数据清洗、统计分析和可视化功能
"""

result = agent.execute_sync(instruction)
```

### 3. 智能错误处理

```python
# 创建具有aider知识的Agent
agent = Agent(llm=get_model('deepseek_v3'), stateful=True)
agent.loadKnowledge(aider_knowledge)

# Agent会自动处理aider执行中的错误
instruction = """
请使用aider修复broken_script.py中的语法错误，
如果修复失败，请分析错误原因并提供解决方案
"""

result = agent.execute_sync(instruction)
if result.success:
    print("修复成功")
else:
    print(f"修复失败，错误信息: {result.stderr}")
```

## 实际应用场景

### 1. 自动化代码生成

- **项目初始化**：自动生成项目骨架
- **模板代码**：快速生成常用代码模板
- **测试代码**：自动生成单元测试

### 2. 代码重构优化

- **代码规范化**：统一代码风格
- **性能优化**：识别并优化性能瓶颈
- **错误修复**：自动修复常见错误

### 3. 文档生成

- **API文档**：自动生成API文档
- **注释补充**：为代码添加详细注释
- **README生成**：自动生成项目说明

## 最佳实践

### 1. 知识管理

```python
# 定期更新aider知识库
def update_aider_knowledge(agent):
    updated_knowledge = """
    # 更新的aider知识
    最新版本特性：
    - 支持新的模型
    - 改进的错误处理
    - 更好的性能优化
    """
    agent.loadKnowledge(updated_knowledge)

# 使用示例
agent = Agent(llm=get_model('deepseek_v3'), stateful=True)
agent.loadKnowledge(aider_knowledge)
update_aider_knowledge(agent)
```

### 2. 安全考虑

```python
# 添加安全检查
def safe_aider_call(agent, instruction):
    # 检查指令是否包含危险操作
    dangerous_patterns = ['rm -rf', 'del /f', 'format']
    if any(pattern in instruction.lower() for pattern in dangerous_patterns):
        return "指令包含危险操作，已拒绝执行"
    
    return agent.execute_sync(instruction)

# 使用示例
agent = Agent(llm=get_model('deepseek_v3'), stateful=True)
agent.loadKnowledge(aider_knowledge)
result = safe_aider_call(agent, "使用aider创建一个文件")
```

### 3. 性能优化

```python
# 使用缓存避免重复调用
from functools import lru_cache

# 缓存Agent响应
agent_cache = {}

def cached_aider_call(agent, instruction):
    if instruction in agent_cache:
        return agent_cache[instruction]
    
    result = agent.execute_sync(instruction)
    agent_cache[instruction] = result
    return result

# 使用示例
agent = Agent(llm=get_model('deepseek_v3'), stateful=True)
agent.loadKnowledge(aider_knowledge)
result = cached_aider_call(agent, "使用aider创建hello.py")
```

## 故障排除

### 常见问题及解决方案

1. **API密钥错误**
   - 检查环境变量设置
   - 验证密钥有效性

2. **aider命令不存在**
   - 确认aider已正确安装
   - 检查PATH环境变量

3. **文件权限问题**
   - 确保对目标文件有写入权限
   - 使用适当的用户权限运行

4. **模型响应超时**
   - 适当设置超时参数
   - 选择更快的模型

## 项目README文件

在`aider_demo`目录下创建`README.md`：

```markdown
# 使用Agent + aider知识库实现AI编程助手

## 简介

本项目展示如何通过Agent的`loadKnowledge`方法注入aider编程知识，让标准Agent具备调用aider的能力，实现自动化代码生成、修改和优化功能。

## 快速开始

### 1. 环境准备

```bash
# 安装aider
pip install aider-chat

# 设置API密钥
export DEEPSEEK_API_KEY="your-api-key"
```

### 2. 运行示例

```bash
# 创建计算器程序
python examples/create_calculator.py

# 修改现有文件
python examples/modify_files.py

# 批量处理文件
python examples/batch_process.py
```

### 3. 交互式测试

```bash
python interactive_test.py
```

## 文件说明

- `aider_knowledge.py` - aider知识库定义
- `use_aider_agent.py` - 展示如何使用标准Agent加载aider知识
- `test_*.py` - 各种测试文件
- `examples/` - 使用示例

## 功能特性

- ✅ 自动代码生成
- ✅ 智能代码修改
- ✅ 批量文件处理
- ✅ 多模型支持
- ✅ 错误处理机制
- ✅ 流式执行监控

## 测试

运行所有测试：
```bash
python test_aider_agent.py
python integration_test_aider.py
python performance_test.py
```

## 许可证

MIT License
```

## 开发成功验证方法

### 1. 单元测试验证

在`aider_demo`目录下创建测试文件 `test_aider_agent.py`：

```python
#!/usr/bin/env python3
"""
AiderAgent单元测试
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
import tempfile
from python_core import Agent
from aider_knowledge import aider_knowledge

class TestAiderAgent(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        cls.llm = get_model('deepseek_v3')
        
        # 创建标准Agent并注入aider知识
        cls.agent = Agent(llm=cls.llm, stateful=True)
        cls.agent.loadKnowledge(aider_knowledge)
        
        # 创建临时测试目录
        cls.test_dir = tempfile.mkdtemp()
        os.chdir(cls.test_dir)
    
    def test_knowledge_loaded(self):
        """测试1: 验证知识是否成功加载"""
        # 检查memory中是否包含aider知识
        memory_content = str(self.agent.memory)
        self.assertIn("aider", memory_content.lower())
        self.assertIn("--model", memory_content)
        self.assertIn("deepseek", memory_content)
        print("✅ 测试1通过: aider知识成功加载到Agent记忆中")
    
    def test_api_specification_set(self):
        """测试2: 验证API规范是否设置"""
        self.assertIsNotNone(self.agent.api_specification)
        self.assertIn("aider编程能力", self.agent.api_specification)
        print("✅ 测试2通过: API规范正确设置")
    
    def test_create_simple_file(self):
        """测试3: 验证创建简单文件功能"""
        instruction = """
        请使用aider创建一个名为test_hello.py的文件，
        内容只需要一行：print("Hello from aider!")
        使用deepseek模型，不要使用git
        """
        
        result = self.agent.execute_sync(instruction)
        
        # 验证执行成功
        self.assertTrue(result.success)
        
        # 验证文件创建
        self.assertTrue(os.path.exists('test_hello.py'))
        
        # 验证文件内容
        with open('test_hello.py', 'r') as f:
            content = f.read()
            self.assertIn('print', content)
            self.assertIn('Hello from aider', content)
        
        print("✅ 测试3通过: 成功使用aider创建文件")
    
    def test_understand_aider_command(self):
        """测试4: 验证Agent理解aider命令"""
        # 询问Agent关于aider的问题
        result = self.agent.chat_sync("aider支持哪些模型？")
        
        self.assertTrue(result.success)
        response = result.return_value.lower()
        
        # 验证回答中包含已注入的模型信息
        self.assertIn("deepseek", response)
        self.assertIn("gpt", response)
        self.assertIn("claude", response)
        
        print("✅ 测试4通过: Agent正确理解aider相关知识")
    
    def test_error_handling(self):
        """测试5: 验证错误处理能力"""
        instruction = """
        请使用aider修改一个不存在的文件nonexistent.py，
        添加一个函数
        """
        
        result = self.agent.execute_sync(instruction)
        
        # Agent应该能够处理这个错误情况
        self.assertIsNotNone(result)
        
        print("✅ 测试5通过: Agent能够处理错误情况")

if __name__ == '__main__':
    unittest.main(verbosity=2)
```

### 2. 集成测试验证

在`aider_demo`目录下创建 `integration_test_aider.py`：

```python
#!/usr/bin/env python3
"""
集成测试：验证AiderAgent的完整功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
from python_core import Agent
from llm_lazy import get_model
from python_core import Agent
from aider_knowledge import aider_knowledge

def run_integration_tests():
    """运行集成测试"""
    print("🚀 开始AiderAgent集成测试...")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = "./aider_test_workspace"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    os.chdir(test_dir)
    
    # 初始化标准Agent
    llm = get_model('deepseek_v3')
    agent = Agent(llm=llm, stateful=True)
    agent.loadKnowledge(aider_knowledge)
    
    # 测试场景1: 创建计算器程序
    print("\n📝 测试场景1: 创建计算器程序")
    result1 = agent.execute_sync("""
    使用aider创建一个calculator.py文件，实现基本的加减乘除功能，
    包含main函数和错误处理，使用deepseek模型
    """)
    
    if os.path.exists('calculator.py'):
        print("✅ calculator.py创建成功")
        # 验证文件可执行
        try:
            exec(open('calculator.py').read())
            print("✅ calculator.py语法正确")
        except Exception as e:
            print(f"❌ calculator.py执行错误: {e}")
    else:
        print("❌ calculator.py创建失败")
    
    # 测试场景2: 批量处理文件
    print("\n📝 测试场景2: 批量添加类型注解")
    
    # 先创建几个测试文件
    with open('module1.py', 'w') as f:
        f.write("""
def add(a, b):
    return a + b

def multiply(x, y):
    return x * y
""")
    
    with open('module2.py', 'w') as f:
        f.write("""
def divide(a, b):
    if b == 0:
        return None
    return a / b
""")
    
    result2 = agent.execute_sync("""
    使用aider为module1.py和module2.py添加类型注解，
    使用deepseek模型，不要使用git
    """)
    
    # 验证类型注解是否添加
    with open('module1.py', 'r') as f:
        content = f.read()
        if '->' in content or 'typing' in content:
            print("✅ 类型注解成功添加到module1.py")
        else:
            print("❌ module1.py未添加类型注解")
    
    # 测试场景3: 智能对话能力
    print("\n📝 测试场景3: 智能对话能力")
    chat_result = agent.chat_sync("请解释一下aider的--map-tokens参数的作用")
    
    if "token" in chat_result.return_value.lower():
        print("✅ Agent能够正确解释aider参数")
    else:
        print("❌ Agent对aider参数理解不足")
    
    # 清理测试目录
    os.chdir('..')
    shutil.rmtree(test_dir)
    
    print("\n" + "=" * 60)
    print("✅ 集成测试完成")

if __name__ == '__main__':
    run_integration_tests()
```

### 3. 交互式验证

在`aider_demo`目录下创建 `interactive_test.py`：

```python
#!/usr/bin/env python3
"""
交互式测试：手动验证AiderAgent功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_core import Agent
from llm_lazy import get_model
from python_core import Agent
from aider_knowledge import aider_knowledge
from agent_base import Result

def interactive_test():
    """交互式测试环境"""
    print("🎯 Agent + aider知识库交互式测试环境")
    print("=" * 60)
    print("这是一个交互式测试环境，您可以直接与具有aider知识的Agent对话")
    print("输入 'exit' 退出，输入 'help' 查看帮助")
    print("=" * 60)
    
    # 初始化标准Agent
    llm = get_model('deepseek_v3')
    agent = Agent(llm=llm, stateful=True)
    agent.loadKnowledge(aider_knowledge)
    
    # 测试命令列表
    test_commands = {
        '1': "创建一个hello.py文件，打印Hello World",
        '2': "显示当前目录的文件列表",
        '3': "解释aider的--watch参数",
        '4': "创建一个包含异步函数的async_demo.py",
        '5': "检查我的aider知识是否正确加载"
    }
    
    while True:
        print("\n可用的测试命令:")
        for key, desc in test_commands.items():
            print(f"  {key}: {desc}")
        print("  或输入自定义指令")
        
        user_input = input("\n请输入指令 > ").strip()
        
        if user_input.lower() == 'exit':
            break
        elif user_input.lower() == 'help':
            print("\n帮助信息:")
            print("- 输入数字选择预设测试命令")
            print("- 直接输入自然语言指令")
            print("- Agent会自动判断是对话还是执行任务")
            continue
        
        # 处理预设命令
        if user_input in test_commands:
            instruction = test_commands[user_input]
            print(f"\n执行: {instruction}")
        else:
            instruction = user_input
        
        # 判断是聊天还是执行
        if agent.classify_instruction(instruction):
            # 执行任务
            print("\n🔧 执行任务中...")
            for chunk in agent.execute_stream(instruction):
                if isinstance(chunk, str):
                    print(chunk, end='', flush=True)
                elif isinstance(chunk, Result):
                    print(f"\n\n✅ 执行完成")
                    print(f"成功: {chunk.success}")
                    if chunk.stdout:
                        print(f"输出: {chunk.stdout}")
        else:
            # 对话模式
            print("\n💬 对话模式...")
            result = agent.chat_sync(instruction)
            print(f"\n{result.return_value}")
    
    print("\n👋 测试结束")

if __name__ == '__main__':
    interactive_test()
```

### 4. 性能验证测试

在`aider_demo`目录下创建 `performance_test.py`：

```python
#!/usr/bin/env python3
"""
性能测试：验证具有aider知识的Agent性能指标
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from python_core import Agent
from llm_lazy import get_model
from python_core import Agent
from aider_knowledge import aider_knowledge

def performance_test():
    """性能测试"""
    print("⚡ Agent + aider知识库性能测试")
    print("=" * 60)
    
    # 测试1: 知识加载时间
    start_time = time.time()
    llm = get_model('deepseek_v3')
    agent = Agent(llm=llm, stateful=True)
    agent.loadKnowledge(aider_knowledge)
    load_time = time.time() - start_time
    
    print(f"✅ Agent初始化时间: {load_time:.2f}秒")
    
    # 测试2: 简单任务执行时间
    start_time = time.time()
    result = agent.execute_sync("创建一个空的test.py文件")
    exec_time = time.time() - start_time
    
    print(f"✅ 简单任务执行时间: {exec_time:.2f}秒")
    
    # 测试3: 内存使用情况
    import psutil
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    
    print(f"✅ 内存使用: {memory_mb:.2f}MB")
    
    # 测试4: Token使用统计
    tokens_used = agent.calculate_memory_tokens()
    print(f"✅ Token使用: {tokens_used} tokens")
    
    # 测试5: 响应时间测试
    response_times = []
    for i in range(3):
        start_time = time.time()
        agent.chat_sync(f"aider的第{i+1}个优点是什么？")
        response_time = time.time() - start_time
        response_times.append(response_time)
    
    avg_response_time = sum(response_times) / len(response_times)
    print(f"✅ 平均响应时间: {avg_response_time:.2f}秒")
    
    print("\n" + "=" * 60)
    print("性能测试完成")

if __name__ == '__main__':
    performance_test()
```

### 5. 验证清单

在文档末尾添加验证清单：

```markdown
## 快速开始指南

### 1. 创建项目目录

```bash
# 在项目根目录下执行
mkdir aider_demo
cd aider_demo
mkdir examples
```

### 2. 创建所有必要文件

按照文档中的代码创建以下文件：
- `aider_knowledge.py` - aider知识库
- `use_aider_agent.py` - 如何使用标准Agent示例
- `test_aider_agent.py` - 单元测试
- `integration_test_aider.py` - 集成测试
- `interactive_test.py` - 交互式测试
- `performance_test.py` - 性能测试
- `examples/create_calculator.py` - 创建计算器示例
- `examples/modify_files.py` - 修改文件示例
- `examples/batch_process.py` - 批量处理示例
- `README.md` - 项目说明

### 3. 安装依赖

```bash
# 安装aider
pip install aider-chat

# 设置环境变量
export DEEPSEEK_API_KEY="your-api-key"
```

### 4. 运行测试

```bash
# 运行单元测试
python test_aider_agent.py

# 运行交互式测试
python interactive_test.py

# 运行示例
python examples/create_calculator.py
```

## 开发验证清单

完成AiderAgent开发后，请按照以下清单进行验证：

### ✅ 基础功能验证
- [ ] Agent能够成功加载aider知识
- [ ] Agent能够理解aider相关问题
- [ ] Agent能够生成正确的aider命令
- [ ] Agent能够处理aider执行结果

### ✅ 核心功能验证
- [ ] 创建新文件功能正常
- [ ] 修改现有文件功能正常
- [ ] 批量处理功能正常
- [ ] 错误处理机制有效

### ✅ 集成验证
- [ ] 与现有Agent系统兼容
- [ ] 内存管理功能正常
- [ ] 流式执行功能正常
- [ ] API规范设置正确

### ✅ 性能验证
- [ ] 初始化时间 < 5秒
- [ ] 简单任务执行时间 < 10秒
- [ ] 内存使用 < 500MB
- [ ] Token使用在限制范围内

### ✅ 可靠性验证
- [ ] 连续执行10个任务无错误
- [ ] 能够从错误中恢复
- [ ] 长时间运行稳定
- [ ] 并发请求处理正常

通过所有验证项目后，AiderAgent即可投入使用。
```

## 总结

通过`loadKnowledge`方法注入aider编程知识，我们可以让标准Agent具备调用aider的能力。这种方法的优势：

1. **简单直接**：无需创建新类，直接使用标准Agent
2. **知识持久化**：注入的知识不会被内存管理删除
3. **上下文感知**：Agent能够理解和使用aider命令
4. **灵活性高**：可以随时更新或添加新的知识
5. **易于维护**：知识与代码分离，便于管理

这种方法展示了Agent系统的强大扩展能力：通过简单的知识注入，就能让Agent掌握新的技能。开发者无需修改Agent核心代码，只需构造合适的知识字符串，就能让Agent具备相应的能力。
