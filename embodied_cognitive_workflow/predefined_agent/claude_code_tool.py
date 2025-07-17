#!/usr/bin/env python3
"""
Claude Code 工具智能体工厂方法

提供预定义的 Claude Code CLI 工具智能体实例创建功能。
该智能体专门用于通过 Claude Code CLI 进行代码生成、文件操作和自动化任务。
"""

import os
import sys
from typing import Optional

# 添加父目录到Python路径以导入核心模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from python_core import Agent
from llm_lazy import get_model

# Claude Code CLI 知识库
claude_code_cli_knowledge = """
# Claude Code 命令行工具知识库

## 🚨 重要前置要求：必须设置代理服务器
**使用 Claude Code CLI 之前，必须确保已经设置了代理服务器环境变量，否则无法连接到 Claude API。**

### 必需的代理设置
```bash
# 在执行任何 claude 命令之前，必须设置以下环境变量：
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export NO_PROXY="localhost,127.0.0.1"

# 或在 Python 中设置：
import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
```

### 验证代理设置
```bash
# 检查代理是否设置正确
echo $HTTP_PROXY
echo $HTTPS_PROXY

# 测试连接（如果失败说明代理未设置或不可用）
claude --version
```

## 重要原则：Claude Code CLI 是命令行代码生成工具
**当用户要求执行编程任务、代码生成或文件操作时，应该使用 subprocess.run 调用 Claude Code CLI 命令，而不是自己生成代码。**

### 核心原则
🔥 **必须先设置代理服务器，否则无法使用 Claude Code**
🔥 **对于所有编程任务，使用 subprocess.run 运行 claude 命令**
🔥 **不要自己生成代码，要用 claude 命令行完成代码任务**
🔥 **Agent 的职责是调用 Claude CLI，不是直接写代码**
🔥 **必须打印 Claude Code 的执行结果，让用户看到输出**
🔥 **必须加上 --allowedTools "Edit,Read,Write" 参数，否则 Claude Code 无法操作文件**

### 判断何时使用 Claude Code CLI
- ✅ 用户说："写一个Python类"
- ✅ 用户说："创建一个脚本"
- ✅ 用户说："生成代码"
- ✅ 用户说："实现一个功能"
- ✅ 用户要求修改文件
- ✅ 用户要求添加功能
- ✅ 用户要求重构代码
- ✅ 用户要求生成测试
- ✅ 用户要求添加文档
- ❌ 用户明确说："不要用工具"
- ❌ 用户要求解释概念（而非生成代码）

### 标准工作流程
1. 识别用户的编程需求
2. 构建 claude 命令和参数（必须包含 --allowedTools）
3. 使用 subprocess.run 执行命令
4. **打印执行结果给用户看** 🔥
5. 处理执行结果和错误
6. 验证生成的代码或文件

### 重要：必须打印输出和使用正确参数
```python
# ❌ 错误做法1：不打印结果
result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)

# ❌ 错误做法2：没有 --allowedTools 参数
result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True)

# ✅ 正确做法：包含 --allowedTools 并打印结果
command = ["claude", "-p", prompt, "--allowedTools", "Edit,Read,Write"]
result = subprocess.run(command, capture_output=True, text=True)
print(f"Claude Code 执行结果：\n{result.stdout}")
if result.stderr:
    print(f"错误信息：{result.stderr}")
```

### 🔥 关于 --allowedTools 参数
Claude Code 需要明确的工具权限才能操作文件：
- **Edit**: 编辑现有文件
- **Read**: 读取文件内容
- **Write**: 创建新文件
- **Bash**: 执行系统命令（可选）

常用组合：
```bash
# 基本文件操作（推荐）
--allowedTools "Edit,Read,Write"

# 包含命令执行
--allowedTools "Edit,Read,Write,Bash"

# 只读模式
--allowedTools "Read"
```

## 基本命令行用法

### 1. 基本命令格式
```bash
# ❌ 错误：缺少 --allowedTools
claude "编写一个计算斐波那契数列的函数"

# ✅ 正确：包含 --allowedTools
claude -p "编写一个计算斐波那契数列的函数" --allowedTools "Edit,Read,Write"

# ✅ 使用 -p 参数指定提示（推荐）
claude -p "创建一个 Python 脚本，包含四则运算功能" --allowedTools "Edit,Read,Write"

# 交互式模式
claude --interactive

# 获取帮助
claude --help
```

### 2. 输出格式选项
```bash
# JSON 格式输出（便于脚本处理）
claude -p "生成代码" --allowedTools "Edit,Read,Write" --output-format json

# 普通文本输出（默认）
claude -p "生成代码" --allowedTools "Edit,Read,Write" --output-format text

# 将输出保存到文件
claude -p "生成代码" --allowedTools "Edit,Read,Write" > output.py
```

### 3. 常用选项
```bash
# 查看版本
claude --version

# 显示详细信息
claude -p "生成代码" --allowedTools "Edit,Read,Write" --verbose

# 设置工作目录
claude -p "处理项目文件" --allowedTools "Edit,Read,Write" --cwd /path/to/project

# 使用配置文件
claude -p "生成代码" --allowedTools "Edit,Read,Write" --config config.json
```

## 实际应用场景

### 1. 代码生成和重构
```bash
# ✅ 生成新的 Python 类（正确方式）
claude -p "创建一个 Calculator 类，包含加减乘除方法" --allowedTools "Edit,Read,Write"

# ✅ 生成完整的 Python 模块
claude -p "创建一个用户管理模块，包含User类和相关函数，保存为 user_manager.py" --allowedTools "Edit,Read,Write"

# ✅ 代码重构建议
claude -p "分析 legacy_code.py 并提供重构建议" --allowedTools "Read"
```

### 2. 文档和测试生成
```bash
# ✅ 生成项目文档
claude -p "为这个Python项目生成详细的README.md文档" --allowedTools "Edit,Read,Write"

# ✅ 生成单元测试
claude -p "为Calculator类生成完整的单元测试代码，保存为 test_calculator.py" --allowedTools "Edit,Read,Write"

# ✅ 为现有文件添加注释
claude -p "为 script.py 添加详细的函数注释" --allowedTools "Edit,Read"
```

### 3. 实用工具和自动化
```bash
# ✅ 代码质量检查
claude -p "分析 myfile.py 的代码质量" --allowedTools "Read"

# ✅ 性能优化建议
claude -p "分析 slow_code.py 并提供性能优化建议" --allowedTools "Read"

# ✅ 错误调试帮助
claude -p "分析 error_log.txt 中的错误并提供解决方案" --allowedTools "Read"
```

## 高级功能

### 1. 交互式对话
```bash
# 开始交互式会话
claude --interactive

# 在交互模式中可以连续对话
# 输入 "exit" 或 Ctrl+C 退出
```

### 2. 输出管道和处理
```bash
# ✅ 将输出传递给其他工具
claude -p "生成Python计算器代码" --allowedTools "Edit,Read,Write" | python -m py_compile

# ✅ 结合 jq 处理 JSON 输出
claude -p "生成配置信息" --allowedTools "Edit,Read,Write" --output-format json | jq '.config'

# ✅ 保存到文件并同时显示
claude -p "生成数据处理脚本" --allowedTools "Edit,Read,Write" | tee output.py
```

### 3. 实用技巧
```bash
# ✅ 使用环境变量
export PROMPT="创建一个数据分析脚本"
claude -p "$PROMPT" --allowedTools "Edit,Read,Write"

# ✅ 结合 shell 脚本
for file in *.py; do
    claude -p "为 $file 生成测试文件" --allowedTools "Edit,Read,Write"
done

# ✅ 快速原型开发
claude -p "创建一个简单的Web服务器，保存为 server.py" --allowedTools "Edit,Read,Write" && python server.py
```

## 常用命令模式

### 1. 快速代码生成
```bash
# 生成 Python 类
claude "创建一个 Calculator 类，包含 add, subtract, multiply, divide 方法" > calculator.py

# 生成测试文件
claude "为 Calculator 类生成 pytest 测试" > test_calculator.py

# 生成配置文件
claude "创建一个 Python 项目的 setup.py 文件" > setup.py
```

### 2. 代码分析和改进
```bash
# 代码质量检查
claude "分析这个 Python 文件的代码质量和潜在问题: $(cat myfile.py)"

# 性能优化建议
claude "为这段代码提供性能优化建议: $(cat slow_function.py)"

# 添加错误处理
claude "为这个函数添加适当的异常处理: $(cat function.py)"
```

### 3. 文档和注释
```bash
# 生成 README
claude "为这个 Python 项目生成详细的 README.md" > README.md

# 添加函数注释
claude "为这个 Python 文件的所有函数添加 docstring: $(cat module.py)" > documented_module.py

# 生成 API 文档
claude "为这个模块生成 API 文档: $(cat api_module.py)" > api_docs.md
```

## 最佳实践

### 1. 有效的提示词技巧
- 使用具体明确的描述
- 指定输出格式和要求
- 包含上下文信息
- 分步骤描述复杂任务

### 2. 常用模式
```bash
# 直接生成文件
claude "提示词" > output.py

# 分析现有代码
claude "分析任务: $(cat input.py)"

# 结合管道处理
claude "生成代码" | python -c "import sys; print(len(sys.stdin.read()))"
```

### 3. 与 Python SDK 的区别

**Claude Code CLI 适用于：**
- 快速命令行操作
- 一次性代码生成
- Shell 脚本集成
- 简单的文件处理

**Python SDK 适用于：**
- Python 应用程序集成
- 复杂的多轮对话
- 自定义消息处理
- 长时间运行的服务

## 实用示例

### 1. 完整的计算器生成命令
```bash
# 生成基础计算器类
claude "创建一个Python Calculator类，包含以下要求：
1. 实现 add, subtract, multiply, divide 四个方法
2. 每个方法接收两个数字参数
3. divide 方法要处理除零错误
4. 包含完整的类型注解和文档字符串
5. 添加 __str__ 和 __repr__ 方法" > calculator.py

# 生成对应的测试文件
claude "为Calculator类生成完整的pytest测试，包括：
1. 测试所有四个运算方法
2. 测试除零错误处理
3. 测试边界情况
4. 测试类型错误处理" > test_calculator.py

# 验证生成的代码
python -m py_compile calculator.py && echo "代码语法正确"
```

### 2. Python 脚本中调用 Claude Code CLI
```python
#!/usr/bin/env -S uv run --script

import subprocess
import os

# 🚨 必须设置代理（Claude Code 依赖代理连接 API）
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# 验证代理设置
if not os.environ.get("HTTP_PROXY") or not os.environ.get("HTTPS_PROXY"):
    raise RuntimeError("错误：必须设置 HTTP_PROXY 和 HTTPS_PROXY 环境变量才能使用 Claude Code")

# 定义提示词
prompt = "修改hello1.py, 让它输出Hello, World 123"

# 构建命令
command = ["claude", "-p", prompt, "--allowedTools", "Edit", "Bash", "Write"]

try:
    # 执行命令并捕获输出
    process = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    
    # 🔥 重要：必须打印输出让用户看到结果
    print("=" * 50)
    print("Claude Code 执行成功！")
    print("=" * 50)
    print(f"输出结果：\n{process.stdout}")
    print("=" * 50)
    
except subprocess.CalledProcessError as e:
    print(f"❌ Claude 命令执行失败: {e}")
    print(f"错误输出: {e.stderr}")
    print("请检查：")
    print("1. 代理服务器是否正在运行（端口 7890）")
    print("2. Claude Code CLI 是否已安装")
    print("3. API 密钥是否配置正确")
```

### 3. 批量处理脚本
```python
#!/usr/bin/env python3

import subprocess
import os
from pathlib import Path

# 🚨 首先设置代理服务器
def setup_proxy():
    '''设置代理服务器环境变量'''
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    
    # 验证设置
    if not os.environ.get("HTTP_PROXY"):
        raise RuntimeError("必须设置代理服务器才能使用 Claude Code")

def claude_process_file(file_path, instruction):
    '''使用 Claude Code CLI 处理单个文件'''
    command = [
        "claude", 
        "-p", 
        f"{instruction}: {file_path}",
        "--allowedTools", "Read,Write,Edit"
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ 成功处理 {file_path}")
        # 🔥 重要：打印执行结果
        print(f"📄 Claude Code 输出：")
        print("-" * 40)
        print(result.stdout)
        print("-" * 40)
        return result.stdout
    else:
        print(f"❌ 处理失败 {file_path}: {result.stderr}")
        if "proxy" in result.stderr.lower() or "connection" in result.stderr.lower():
            print("   提示：请检查代理服务器是否正常运行")
        return None

# 主程序
if __name__ == "__main__":
    # 设置代理
    setup_proxy()
    
    # 批量为 Python 文件添加类型注解
    python_files = Path(".").glob("*.py")
    for file in python_files:
        claude_process_file(file, "为这个Python文件添加完整的类型注解")
```

### 4. 工具参数使用
```bash
# 指定允许的工具
claude -p "修改文件内容" --allowedTools "Edit,Read,Write"

# 限制工具权限（仅读取）
claude -p "分析代码质量" --allowedTools "Read"

# 允许执行命令
claude -p "运行测试并修复错误" --allowedTools "Edit,Write,Bash"

# 组合使用
claude -p "重构代码并运行测试" --allowedTools "Read,Edit,Write,Bash"
```

### 5. 错误处理和重试
```python
import subprocess
import time
import os

def claude_with_retry(prompt, max_retries=3):
    '''带重试机制的 Claude Code CLI 调用'''
    
    # 🚨 确保代理已设置
    if not os.environ.get("HTTP_PROXY") or not os.environ.get("HTTPS_PROXY"):
        os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
        os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
        os.environ["NO_PROXY"] = "localhost,127.0.0.1"
        print("⚠️  自动设置代理服务器环境变量")
    
    for attempt in range(max_retries):
        try:
            # 🔥 必须包含 --allowedTools
            command = ["claude", "-p", prompt, "--allowedTools", "Edit,Read,Write"]
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=60  # 60秒超时
            )
            # 🔥 成功时必须打印输出
            print("\n✅ Claude Code 执行成功！")
            print("=" * 60)
            print(result.stdout)
            print("=" * 60)
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            print(f"尝试 {attempt + 1} 失败: {e.stderr}")
            
            # 检查是否是代理问题
            if "proxy" in e.stderr.lower() or "connection" in e.stderr.lower():
                print("💡 提示：错误可能与代理服务器有关")
                print("   1. 检查代理是否在运行: lsof -i :7890")
                print("   2. 检查代理设置: echo $HTTP_PROXY")
            
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                raise
        except subprocess.TimeoutExpired:
            print(f"尝试 {attempt + 1} 超时")
            print("💡 提示：超时可能因为：")
            print("   1. 代理服务器响应慢")
            print("   2. API 服务器响应慢")
            print("   3. 提示词过于复杂")
            
            if attempt < max_retries - 1:
                time.sleep(5)  # 超时后等待更久
            else:
                raise

# 使用示例
try:
    # 注意：结果已在函数内部打印，这里不需要再次打印
    result = claude_with_retry("生成一个复杂的数据处理脚本")
except Exception as e:
    print("最终失败:", e)
    print("\n请检查：")
    print("1. 代理服务器是否正常运行（端口 7890）")
    print("2. Claude Code CLI 是否已正确安装")
    print("3. API 密钥是否已配置")
```

## 🚨 重要提醒：代理服务器配置

### 为什么需要代理？
Claude Code CLI 需要连接到 Anthropic 的 API 服务器，在某些网络环境下必须通过代理服务器才能访问。

### 常见问题排查
1. **连接错误**：检查代理服务器是否正在运行
   ```bash
   # 检查端口 7890 是否被监听
   lsof -i :7890
   # 或
   netstat -an | grep 7890
   ```

2. **环境变量未生效**：确保在同一个 shell 会话中
   ```bash
   # 检查环境变量
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

3. **代理端口错误**：确认使用正确的代理端口
   - 常见端口：7890, 1080, 8080, 10808
   - 根据实际代理软件配置调整

### 永久配置代理
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export HTTP_PROXY="http://127.0.0.1:7890"
export HTTPS_PROXY="http://127.0.0.1:7890"
export NO_PROXY="localhost,127.0.0.1"
```

## 🔥 最重要的两个原则

1. **必须设置代理服务器** - 没有正确的代理设置，Claude Code 将无法正常工作
2. **必须打印执行结果** - 让用户看到 Claude Code 的输出是核心职责

### 记住：你的任务流程
```python
# 1. 设置代理
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

# 2. 执行 Claude Code（必须包含 --allowedTools）
command = ["claude", "-p", prompt, "--allowedTools", "Edit,Read,Write"]
result = subprocess.run(command, capture_output=True, text=True)

# 3. 🔥 打印结果（这是必须的！）
print(f"Claude Code 输出：\n{result.stdout}")
```

这个知识库涵盖了 Claude Code CLI 的完整使用方法，特别强调了：
1. **代理服务器配置的重要性**
2. **打印输出结果的必要性**
3. **--allowedTools 参数的必需性**

永远记住：
- **你是 Claude Code 的调用者，不是代码生成者**
- **你的职责是调用 Claude Code 并展示其输出结果**
- **每次调用都必须包含 --allowedTools "Edit,Read,Write"**
"""

def create_claude_code_agent(model_name: str = 'deepseek_chat', stateful: bool = True) -> Agent:
    """
    创建预配置的 Claude Code 工具智能体
    
    Args:
        model_name (str): 语言模型名称，默认为 'deepseek_chat'
        stateful (bool): 是否使用有状态执行器，默认为 True
    
    Returns:
        Agent: 配置了 Claude Code CLI 知识的智能体实例
    
    Example:
        >>> agent = create_claude_code_agent()
        >>> result = agent.execute_sync("写一个Python计算器类")
        >>> print(result.return_value)
    """
    try:
        # 获取语言模型
        llm = get_model(model_name)
        if llm is None:
            raise ValueError(f"无法获取模型: {model_name}")
        
        # 创建智能体实例
        agent = Agent(llm=llm, stateful=stateful)
        
        # 注入 Claude Code CLI 知识
        agent.loadKnowledge(claude_code_cli_knowledge)
        
        # 设置智能体名称和API规范
        agent.set_agent_name("Claude Code CLI 工具")
        agent.set_api_specification(
            "专门用于通过 Claude Code CLI 进行代码生成、文件操作和自动化任务的智能体工具。"
            "优先使用 subprocess.run 调用 claude 命令而不是直接生成代码。"
        )
        
        print(f"✅ 成功创建 Claude Code 工具智能体 (模型: {model_name})")
        return agent
        
    except Exception as e:
        print(f"❌ 创建 Claude Code 工具智能体失败: {e}")
        raise

def test_claude_code_agent():
    """测试 Claude Code 工具智能体功能"""
    print("=== 测试 Claude Code 工具智能体 ===\n")
    
    try:
        # 创建智能体
        agent = create_claude_code_agent()
        
        # 测试指令
        command = "写一个支持加减乘除的算术解释器Python类。类名Calculator，文件名calculator.py"
        
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
        print(f"执行状态: {'成功' if result.success else '失败'}")
        
        if hasattr(result, 'return_value') and result.return_value:
            print(f"返回值: {result.return_value}")
        
    except Exception as e:
        print(f"测试失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 设置代理环境变量
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
    os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890" 
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    
    # 运行测试
    test_claude_code_agent()